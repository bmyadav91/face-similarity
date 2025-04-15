from utils.logger import logging
from flask import jsonify, request, render_template, Blueprint, url_for, make_response
from backend.app.funtions.auth_function import (
    InsertOrUpdateUser,
    verify_otp, 
    is_valid_email,
    TimeDifferent,
    hash_token, 
    RefreshToken,
    ChangeName, 
    LogoutFromAllDevices,
    check_account_exist
)
from backend.app.funtions.jwt_encode_decode import (
    jwtEncode,
    JWT_REFRESH_SECRET_KEY, 
    jwtDecode
)
import os, requests
from backend.app.models import User
from backend.app.extensions import db
from datetime import datetime, timezone
from backend.app.utils.decorator import login_required
from backend.app.celery.celery_worker import delete_account_bg


auth = Blueprint('auth', __name__)


# --------------------------------- isAuthenticated --------------------------------- 

@auth.route('/auth-status')
def isAuthenticated():
    try:
        # Get access token from the Authorization header
        access_token = request.headers.get("Authorization")
        if not access_token or not access_token.startswith("Bearer "):
            return jsonify({"success": False, "message": "Unauthorized: Access token missing or invalid"}), 401
        
        # retrieve the token
        access_token = access_token.replace("Bearer ", "").strip()
        if access_token:
            # Check if the access token is valid
            payload = jwtDecode(access_token)
            if "error" in payload:
                return jsonify({'authenticated': False, 'message': payload["error"]}), 401
            return jsonify({'authenticated': True}), 200
        return jsonify({'authenticated': False}), 401
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ---------------------------------- refresh token ---------------------------------- 

@auth.route('/refresh-token', methods=['POST'])
def refresh_token():
    try:
        # Get access token from the Authorization header
        access_token = request.headers.get("Authorization")
        if not access_token or not access_token.startswith("Bearer "):
            return jsonify({"success": False, "message": "Unauthorized: Access token missing or invalid"}), 401
        
        # retrieve the token
        access_token = access_token.replace("Bearer ", "").strip()

        # Get refresh token from cookies
        refresh_token = request.headers.get('x-refresh-token', None)
        if not refresh_token:
            refresh_token = request.cookies.get('refresh_token', None)

        if not refresh_token:
            return jsonify({"success": False, "message": "Unauthorized: Refresh token missing or invalid"}), 401

        # Process token refresh
        return RefreshToken(access_token, refresh_token)

    except Exception as e:
        logging.error(f"Error in refresh_token: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
    
# ------------------------------------- login page -------------------------------------

@auth.route('/login')
def login():
    return render_template('login.html')


# ------------------------------------ send otp ------------------------------------- 

@auth.route('/send_otp', methods=['POST'])
def send_otp():
   try:
      data = request.get_json()
      email = data.get('email', '')
      return InsertOrUpdateUser(email)
   except Exception as e:
      return jsonify({'success': False, 'message': str(e)}), 500


# ------------------------------------- verify otp ------------------------------------- 

@auth.route('/verify_otp', methods=['POST'])
def verifyOtp():
   try:
      data = request.get_json()
      email = data.get('email', '')
      otp = data.get('otp', '')
      return verify_otp(email, otp)
   except Exception as e:
      return jsonify({'success': False, 'message': str(e)}), 500
   


# ---------------------------------- google auth ---------------------------------- 
# get google auth credential 
def google_auth_credential():
    return os.environ.get('GOOGLE_CLIENT_ID'), os.environ.get('GOOGLE_CLIENT_SECRET')
GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET = google_auth_credential()

# allowed domains 
allowed_origins = os.environ.get('ALLOWED_ORIGINS', '').split(',')

# build google auth url 
@auth.route('/google-auth', methods=['GET'])
def google_auth():
    try:
        domain = request.args.get('domain', allowed_origins[0]).rstrip('/')
        auth_type = request.args.get('auth_type', 'web')

        #  redirect URL
        redirect_url = f"{domain}{url_for('auth.google_auth_callback').replace('/api', '')}"

        # Generate Google Auth URL
        auth_url = (
            'https://accounts.google.com/o/oauth2/auth?'
            f'client_id={GOOGLE_CLIENT_ID}&'
            f'redirect_uri={redirect_url}&'
            'scope=email profile&'
            'response_type=code'
            f'&state={auth_type}'
        )

        return jsonify({'success': True, 'message': 'Google auth URL generated', 'auth_url': auth_url})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# google auth callback 
@auth.route('/google-auth/callback', methods=['GET'])
def google_auth_callback():
    """Handle Google OAuth callback."""
    try:
        code = request.args.get('code')
        if not code:
            return jsonify({'success': False, 'message': 'Authorization code missing'}), 400
        
        domain = request.args.get('domain', allowed_origins[0]).rstrip('/')
        auth_type = request.args.get('state', 'web')


        redirect_url = f"{domain}{url_for('auth.google_auth_callback').replace('/api', '')}"
        
        if not redirect_url:
            return jsonify({'success': False, 'message': 'Redirect URL missing'}), 400
        
        # Exchange code for access token
        token_url = 'https://oauth2.googleapis.com/token'
        token_payload = {
            'code': code,
            'client_id': GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
            'redirect_uri': redirect_url,
            'grant_type': 'authorization_code'
        }

        token_response = requests.post(token_url, data=token_payload)
        if 'error' in token_response.json():
            return jsonify({'success': False, 'message': token_response.json()['error']}), 400

        token_data = token_response.json()

        if 'access_token' not in token_data:
            return jsonify({'success': False, 'message': 'Failed to retrieve access token'}), 400

        access_token_google = token_data['access_token']

        # Fetch user info
        user_info_url = 'https://www.googleapis.com/oauth2/v1/userinfo'
        headers = {'Authorization': f'Bearer {access_token_google}'}
        user_info_response = requests.get(user_info_url, headers=headers)
        user_info = user_info_response.json()

        if not user_info or 'email' not in user_info:
            return jsonify({'success': False, 'message': 'User info not found'}), 400

        # Validate email
        user_email = user_info.get('email', None).strip().lower()
        if not is_valid_email(user_email):
            return jsonify({'success': False, 'message': 'Invalid email address'}), 400

        # Check if user exists
        user = db.session.query(User.id, User.account_status, User.token_hash, User.login_attempt, User.login_at).filter_by(email=user_email).first()

        current_time = datetime.now(timezone.utc)

        if user:
            # Check if account status is active or pending, not suspended or deleted
            if user.account_status not in ['active', 'pending']:
                return jsonify({'success': False, 'message': 'Your account has been suspended or deleted.'}), 400

            # Check if user exceeded login attempts in the last 15 minutes
            if user.login_attempt >= 10 and TimeDifferent(current_time, user.login_at) < 15:
                return jsonify({'success': False, 'message': 'Too many login attempts. Try again after 15 minutes.'}), 429

            # Fetch full ORM object for updates
            user_obj = User.query.get(user.id)
            if user_obj:
                # Generate JWT tokens 
                access_token = jwtEncode({'user_id': user.id}, 1)
                refresh_token = jwtEncode({'user_id': user.id}, 150, JWT_REFRESH_SECRET_KEY)

                user_obj.token_hash = hash_token(refresh_token)
                user_obj.login_attempt = 0
                user_obj.login_at = current_time
                user_obj.account_status = 'active'
                db.session.commit()

        else:
            user_full_name = user_info.get('name', 'Anonymous')

            new_user = User(email=user_email, name=user_full_name, login_at=current_time)
            db.session.add(new_user)
            db.session.commit()

            # generate tokens with the new user ID
            access_token = jwtEncode({'user_id': new_user.id}, 1)
            refresh_token = jwtEncode({'user_id': new_user.id}, 150, JWT_REFRESH_SECRET_KEY)

            new_user.token_hash = hash_token(refresh_token) 
            db.session.commit()

        # Create response directly using jsonify
        response_data = {
            'success': True,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'auth_type': auth_type,
            'message': 'Account signed in successfully'
        }

        response = jsonify(response_data)

        # If not app_redirect_url, set the refresh token cookie
        if auth_type != 'app':
            response.set_cookie(
                "refresh_token",
                refresh_token,
                httponly=True,
                secure=True,
                samesite="Lax",
                max_age=150 * 24 * 60 * 60
            )

        return response    

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': {str(e)}}), 400
    


# ------------------------------- change name ------------------------------------- 

@auth.route('/change-name', methods=['POST'])
@login_required
def change_name(UserID):
    try:
        data = request.get_json()
        new_name = data.get('name', '')
        change_result = ChangeName(UserID, new_name)
        return change_result
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500






# --------------------------------- logout ------------------------------------- 

@auth.route('/logout', methods=['POST'])
@login_required
def logout(UserID):
    try:
        data = request.get_json() or {}  # Ensure data is a dictionary
        isLogoutFromAll = data.get('allDevices', False)

        if isLogoutFromAll:
            return LogoutFromAllDevices(UserID)

        # Expire the refresh token cookie
        response = make_response(jsonify({'success': True, 'message': 'Logout successful'}))
        response.set_cookie("refresh_token", "", expires=0, httponly=True)
        return response
    
    except Exception as e:
        logging.error(f"Error in logout: {str(e)}")
        return jsonify({'success': False, 'message': 'An unexpected error occurred'}), 500


# --------------------------------- delete account ------------------------------------- 

@auth.route('/delete_account', methods=['POST'])
@login_required
def DeleteAccount(userID):
   try:
      # check account existance 
      account_existance = check_account_exist(userID)
      if not account_existance.get('success', False):
         return jsonify(account_existance), 400
      delete_account_bg.delay(userID)
      response = make_response(jsonify({'success': True, 'message': 'Account deletion process has been started in the background.'}), 200)
      response.set_cookie("refresh_token", "", expires=0, httponly=True)
      return response
   except Exception as e:
      return jsonify({'success': False, 'message': str(e)}), 500