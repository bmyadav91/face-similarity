from backend.app.utils.logger import logging
from backend.app.extensions import db
from backend.app.models import User, Photo, Face, photo_faces
from sqlalchemy.exc import SQLAlchemyError
from flask import jsonify, make_response
import random
from email_validator import validate_email, EmailNotValidError
from datetime import datetime, timezone
from backend.app.funtions.jwt_encode_decode import (
    jwtEncode,
    jwtDecode,
    JWT_REFRESH_SECRET_KEY, JWT_SECRET_KEY
)
from backend.app.funtions.function import (
    delete_objects_from_s3,
    delete_vector_from_pinecone
)
from backend.app.funtions.send_email import send_email
import hashlib
import os

# -------------------------------------Insert or Update User -------------------------------------

def InsertOrUpdateUser(user_email):
    try:
        # Validate email
        if not is_valid_email(user_email):
            return jsonify({'success': False, 'message': 'Invalid email'}), 400

        user_email = user_email.strip().lower()
        current_time = datetime.now(timezone.utc)

        # Fetch only required columns instead of full User object
        user = db.session.query(
            User.id, User.account_status, User.last_otp, User.login_attempt, User.login_at, User.name
        ).filter_by(email=user_email).first()

        generated_otp = generate_otp()
        hash_otp = hash_token(generated_otp)

        if user:
            # Check if account status is active or pending (not suspended or deleted)
            if user.account_status not in ['active', 'pending']:
                return jsonify({'success': False, 'message': 'Your account has been suspended or deleted.'}), 400

            # Check if user exceeded login attempts in the last 5 minutes
            if user.login_attempt >= 10 and TimeDifferent(current_time, user.login_at) < 5:
                return jsonify({'success': False, 'message': 'Too many login attempts. Try again after 5 minutes.'}), 429

            # Fetch full ORM object for updates
            user_obj = User.query.get(user.id)
            if user_obj:
                user_obj.last_otp = hash_otp
                user_obj.login_attempt += 1
                user_obj.login_at = current_time
        else:
            # Create new user entry
            user_obj = User(email=user_email, last_otp=hash_otp, login_attempt=1, login_at=current_time)
            db.session.add(user_obj)

        db.session.commit()

        # Send OTP to user's email
        user_name = user.name or "User" if user and hasattr(user, "name") else "User"
        send_email_response = send_email({
            "to_email": user_email,
            "to_name": user_name,
            "subject": "Verification Code for whatBM Photos",
            "template_name": "otp.html",
            "context": {"otp": generated_otp, "name": user_name}
        })

        if not send_email_response.get('success', False):
            return jsonify(send_email_response), 500

        return jsonify({'success': True, 'message': 'OTP sent to your email'}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Database error: {e}")
        return jsonify({'success': False, 'message': 'Database error'}), 500

    except Exception as e:
        db.session.rollback()
        logging.error("Unexpected error occurred", exc_info=True)
        return jsonify({'success': False, 'message': 'An error occurred during checking email'}), 500
    

# -------------------------------------- verify / match otp -------------------------------------- 

def verify_otp(user_email, otp):
    try:
        # Validate email
        if not is_valid_email(user_email):
            return jsonify({'success': False, 'message': 'Invalid email'}), 400
        
        user_email = user_email.strip().lower()

        # Validate OTP format
        otp = otp.strip()
        otp = str(otp).zfill(4)  # Ensure OTP is always 4 digits
        if not otp.isdigit() or len(otp) != 4:
            return jsonify({'success': False, 'message': 'Invalid OTP'}), 400

        current_time = datetime.now(timezone.utc)

        # Fetch only required columns
        user = db.session.query(
            User.id, User.account_status, User.last_otp, 
            User.login_attempt, User.login_at, User.token_hash
        ).filter_by(email=user_email).first()

        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        # Check account status
        if user.account_status not in ['active', 'pending']:
            return jsonify({'success': False, 'message': 'Your account has been suspended or deleted.'}), 400

        # Check OTP expiration (15 mins)
        if TimeDifferent(current_time, user.login_at) > 15:
            return jsonify({'success': False, 'message': 'OTP has been expired. Please go back and initiate a new'}), 400

        # Check login attempts
        if user.login_attempt >= 10 and TimeDifferent(current_time, user.login_at) < 15:
            return jsonify({'success': False, 'message': 'Too many login attempts. Try again after 15 minutes.'}), 429

        # Verify OTP
        user_db_otp = user.last_otp
        if not user_db_otp:
            return jsonify({'success': False, 'message': 'OTP has expired. Please request a new one.'}), 400

        if verify_token(otp, user_db_otp):
            user_obj = User.query.get(user.id)
            if user_obj:
                user_obj.last_otp = None
                user_obj.login_attempt = 0
                user_obj.login_at = current_time
                user_obj.account_status = "active" if user_obj.account_status == "pending" else user_obj.account_status

                # Generate JWT tokens
                data = {'user_id': user_obj.id}
                access_token = jwtEncode(data, expiry_days=1)
                refresh_token = jwtEncode(data, expiry_days=150, key=JWT_REFRESH_SECRET_KEY)

                # Store refresh token in database
                user_obj.token_hash = hash_token(refresh_token)
                db.session.commit()

                # Determine if name update is needed
                NeedNameUpdate = user_obj.name is None or user_obj.name.strip() == ""

                # Create response
                response = make_response(jsonify({
                    'success': True, 
                    'access_token': access_token, 
                    'message': 'OTP verified successfully', 
                    'need_name_update': NeedNameUpdate
                }))

                # Set refresh token in HTTP-only cookie
                response.set_cookie(
                    "refresh_token", refresh_token, httponly=True, 
                    secure=True, samesite="Strict", max_age=150 * 24 * 60 * 60
                )

                return response
            else:
                return jsonify({'success': False, 'message': 'User not found after verification'}), 404

        else:
            # Incorrect OTP: Increment login attempts
            user_obj = User.query.get(user.id)
            if user_obj:
                user_obj.login_attempt += 1
                db.session.commit()

            return jsonify({'success': False, 'message': 'Invalid OTP.'}), 400

    except SQLAlchemyError:
        db.session.rollback()
        logging.error("Database error", exc_info=True)
        return jsonify({'success': False, 'message': 'Database error'}), 500

    except Exception:
        db.session.rollback()
        logging.error("Unexpected error", exc_info=True)
        return jsonify({'success': False, 'message': 'An unexpected error occurred'}), 500
    



# ---------------------------------- chnage name function ------------------------------------ 

def ChangeName(user_id, name):
    try:
        if not name or not name.strip():
            return jsonify({'success': False, 'message': 'Name cannot be empty'}), 400
        
        name = name.strip()
        
        if len(name) < 2 or len(name) > 50:
            return jsonify({'success': False, 'message': 'Name should be between 2 and 50 characters'}), 400

        # Use update to modify only the name column
        result = db.session.query(User).filter_by(id=user_id).update({'name': name})

        if result == 0:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Name updated successfully'}), 200
    
    except SQLAlchemyError as e:
        db.session.rollback() 
        logging.error(f"Database error: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Database error', 'error': str(e)}), 500

    except Exception:
        db.session.rollback()
        logging.error("Unexpected error", exc_info=True)
        return jsonify({'success': False, 'message': 'An unexpected error occurred'}), 500


    
# --------------------------------- refresh token --------------------------------- 

def RefreshToken(access_token, refresh_token):
    try:
        # Decode both tokens
        access_token_payload = jwtDecode(access_token, JWT_SECRET_KEY, True)
        refresh_token_payload = jwtDecode(refresh_token, JWT_REFRESH_SECRET_KEY)

        if "error" in access_token_payload or "error" in refresh_token_payload:
            return jsonify({"success": False, "message": "Unauthorized: Invalid token"}), 401

        # Ensure both tokens belong to the same user
        if access_token_payload["user_id"] != refresh_token_payload["user_id"]:
            return jsonify({"success": False, "message": "Unauthorized: Token mismatch"}), 401

        # Fetch user from the database
        user = db.session.query(User.id, User.token_hash).filter_by(id=access_token_payload["user_id"]).first()
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404
        
        # Validate refresh token hash
        if not verify_token(refresh_token, user.token_hash): 
            return jsonify({"success": False, "message": "Unauthorized: Invalid refresh token"}), 401

        # Generate new access token
        new_access_token = jwtEncode({"user_id": user.id}, 1)
        response = make_response(jsonify({"success": True, "access_token": new_access_token, "message": "Token refreshed successfully"}))
        
        # Set refresh token cookie
        response.set_cookie(
            "refresh_token",
            refresh_token,
            httponly=True,
            secure=True,
            samesite="Strict",
            max_age=150 * 24 * 60 * 60  # 150 days
        )

        return response
    
    except Exception as e:
        logging.error(f"Error in RefreshToken: {str(e)}")
        return jsonify({"success": False, "message": "An unexpected error occurred"}), 500


# ------------------------------- logoutfrom all devices ------------------------------- 

def LogoutFromAllDevices(user_id):
    try:
        # Fetch full user object from database
        user = db.session.query(User).filter_by(id=user_id).first()
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404
        
        # Update token hash to None
        user.token_hash = None
        db.session.commit()

        # Expire the refresh token cookie
        response = make_response(jsonify({"success": True, "message": "Logout successful"}))
        response.set_cookie("refresh_token", "", expires=0, httponly=True)
        return response
    
    except Exception as e:
        logging.error(f"Error in LogoutFromAllDevices: {str(e)}")
        return jsonify({"success": False, "message": "An unexpected error occurred"}), 500



# ------------------------------ check account existence ------------------------------ 

def check_account_exist(user_id):
    try:
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return ({'success': False, 'message': 'User not found. it does not exist.'})
        return ({'success': True, 'message': 'User found.'})
    except Exception as e:
        logging.error(f"Error checking account existence: {e}")
        return ({'success': False, 'message': 'An error occurred while checking account existence.'})    

# ------------------------------ delete user account ------------------------------- 
def Delete_User(user_id):
    try:
        # Fetch the user
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        user_email = user.email

        #  Collect user photo URLs for S3 deletion
        user_photos = Photo.query.filter_by(user_id=user_id).all()
        mark_delete_url = [photo.photo_url for photo in user_photos]

        # Collect face IDs for Pinecone deletion
        user_faces = Face.query.filter_by(user_id=user_id).all()
        face_ids = [face.id for face in user_faces]  # Pinecone deletion
        mark_delete_url.extend([face.face_url for face in user_faces if face.face_url])


        #  Delete Many-to-Many relationships (photo_faces)
        db.session.execute(photo_faces.delete().where(photo_faces.c.photo_id.in_([photo.id for photo in user_photos])))

        #  Delete user’s photos
        Photo.query.filter_by(user_id=user_id).delete()

        #  Delete user's faces
        Face.query.filter_by(user_id=user_id).delete()

        #  Finally, delete the user
        db.session.delete(user)
        db.session.commit()

        # Delete objects from S3
        delete_objects_from_s3(mark_delete_url)

        # Delete vectors from Pinecone
        delete_vector_from_pinecone(face_ids, user_id)

        return {'success': True, 'message': 'User deleted successfully'}

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Database error occurred'}), 500





# ------------------------------------- additional functions ------------------------------------- 

# generate otp 
def generate_otp():
    """generate 4 digit otp """
    return random.randint(1000, 9999)

# validate email 
def is_valid_email(email):
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False
    
# time different 
def TimeDifferent(current_time, old_time):
    try:
        # Convert old_time from string if necessary
        if isinstance(old_time, str):
            old_time = datetime.strptime(old_time, "%Y-%m-%d %H:%M:%S")

        # convert to UTC
        if old_time.tzinfo is None:
            old_time = old_time.replace(tzinfo=timezone.utc)
        else:
            old_time = old_time.astimezone(timezone.utc)

        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)

        # Normalize precision (remove microseconds)
        current_time = current_time.replace(microsecond=0)
        old_time = old_time.replace(microsecond=0)

        # Compute time difference in minutes
        time_diff = (current_time - old_time).total_seconds() / 60
        # print("Time difference (minutes):", time_diff)

        return time_diff

    except Exception as e:
        logging.error(f"Unexpected error: {e}, current_time: {current_time}, old_time: {old_time}")
        return float('inf')
    



# Hash any text, OTP, etc.
def hash_token(token):
    """Securely hash any token (e.g., OTP, passwords) using PBKDF2."""
    # convert to string if token is int 
    if isinstance(token, int): 
        token = str(token)

    salt = os.urandom(16)  # Generate a 16-byte random salt
    hash_val = hashlib.pbkdf2_hmac('sha256', token.encode(), salt, 100000, dklen=32)  # 100K iterations
    return f"{salt.hex()}${hash_val.hex()}"  # Store as salt$hash format

# Verify token against stored hash
def verify_token(token, stored_hash):
    """Verifies a token (e.g., OTP, password) against a stored hash."""
    try:
        # convert to string if token is int 
        if isinstance(token, int): 
            token = str(token)

        salt_hex, stored_hash_val = stored_hash.split("$")  # Split salt and hash
        salt = bytes.fromhex(salt_hex)  # Convert back to bytes
        new_hash = hashlib.pbkdf2_hmac('sha256', token.encode(), salt, 100000, dklen=32).hex()
        return new_hash == stored_hash_val  # Compare securely
    except ValueError:
        return False  # Return False if stored_hash is malformed
