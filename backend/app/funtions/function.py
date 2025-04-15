from backend.app.utils.logger import logging
from backend.app.extensions import db
import pinecone
import os
from backend.app.utils.config import s3_bucket_connection, pinecone_connection
from urllib.parse import urlparse
from sqlalchemy import delete
from sqlalchemy.sql import case
from backend.app.models import Face, Photo, photo_faces, User
from sqlalchemy.exc import SQLAlchemyError
from flask import jsonify


# ---------------------------------------check face existence----------------------------------------

def CheckFaceExistence(face_vector, namespace):
    """
    Checks if a face vector exists in the Pinecone index.
    
    Parameters:
        face_vector (list or np.ndarray): The face embedding vector.
        namespace (str): The user-specific namespace.
    
    Returns:
        str: The face ID if found, otherwise None.
    """

    # Validate input
    if face_vector is None or not isinstance(face_vector, (list)):
        logging.error("Invalid face vector provided.")
        return False
    
    if not namespace or not isinstance(namespace, str):
        logging.error("Invalid namespace provided.")
        return False

    try:
        index = pinecone_connection()
        if index is None:
            logging.error("Pinecone connection failed.")
            return False

        query_result = index.query(
            vector=face_vector,
            namespace=namespace,
            top_k=1,
            include_values=False,
            include_metadata=False,
        )
        print(query_result)

        # Validate query result
        if not query_result or not hasattr(query_result, "matches"):
            logging.error("Invalid response from Pinecone query.")
            return False

        # Check if a match exists with score > 0.5
        if query_result.matches and query_result.matches[0].score > 0.5:
            face_id = query_result.matches[0].id
            return {"face_id": face_id}
        
        return False

    except Exception as e:
        logging.error(f"Error checking face existence: {e}")
        return False
    

# -------------------------------------upsert face to pinecone----------------------------------------

def UpsertFaceToPinecone(face_vector, face_id, namespace):
    try:
        # Validate input parameters
        if not isinstance(face_vector, list) or not face_vector:
            logging.error(f"Invalid face vector provided: {face_vector}")
            return False
        
        if not isinstance(face_id, str) or not face_id.strip():
            logging.error(f"Invalid face ID provided: {face_id}")
            return False

        if not isinstance(namespace, str) or not namespace.strip():
            logging.error(f"Invalid namespace provided: {namespace}")
            return False

        # Establish Pinecone connection
        index = pinecone_connection()
        if index is None:
            logging.error("Pinecone connection failed.")
            return False

        # Upsert data to Pinecone
        response = index.upsert(
            vectors=[{"id": face_id, "values": face_vector}],
            namespace=namespace,
        )

        # Validate response properly
        if not response:
            logging.error(f"Unexpected response from Pinecone: {response}")
            return False

        return True

    except pinecone.exceptions.PineconeException as pe:
        logging.error(f"Pinecone error: {pe}")
        return False

    except ValueError as ve:
        logging.error(f"Value error: {ve}")
        return False

    except Exception as e:
        logging.error(f"Unexpected error in UpsertFaceToPinecone: {e}")
        return False



# ----------------------------------- Object Uploader to s3--------------------------------------

bucket_name=os.getenv("AWS_BUCKET")
main_folder=os.getenv("AWS_FOLDER") # if multiple project in bucket you may need different folder so you may need this 

def Object_Uploader_s3(object_details, user_folder="1", img_type="media"):
    """
        user_folder: userid (Parent folder for each user as folder)
        img_type: face -> mean faces folder, media -> media folder

        folder structure will be like:
        bucket_name/
            1/
                faces/
                media/
    """
    try:
        # extract object_details 
        img_bytes = object_details.get('image_bytes')
        FileName = object_details.get('file_name')

        # return success false if img_bytes or FileName is None 
        if not img_bytes or not FileName:
            return {'success': False, 'message': 'Invalid file or file name.'}        

        # create folder structure 
        folder = f"{main_folder}/{user_folder}/{img_type}"
        # replace space with underscore 
        FileName = FileName.replace(" ", "_")
        s3 = s3_bucket_connection()

        # Upload to S3
        s3.upload_fileobj(img_bytes, bucket_name, f"{folder}/{FileName}")

        # returning url generated of the file 
        url = f"https://{bucket_name}.s3.amazonaws.com/{folder}/{FileName}"

        return {'success': True, 'message': 'File uploaded successfully.', 'url': url, 'img_bytes': img_bytes}

    
    except Exception as e:
        logging.error(f"Error uploading file to S3: {e}")
        return {'success': False, 'message': str(e)}
    

# -------------------------- Object key extract from url for s3 ---------------------------------
def object_key_extractor(url):
    """"
    this function will extract object key from s3 url
    """
    try:
        parsed_url = urlparse(url)
        path = parsed_url.path
        object_key = path.lstrip('/')
        return object_key

    except Exception as e:
        logging.error(f"Error uploading file to S3: {e}")
        return {'success': False, 'message': str(e)}


# ----------------------------------- display faces -------------------------------------

def display_faces(user_id, page=1, per_page=10):
    try:
        faces = Face.query.filter(
            Face.user_id == user_id, Face.face_count > 0
        ).order_by(Face.face_count.desc()) \
            .paginate(page=page, per_page=per_page, error_out=False)

        for face in faces.items:
            face.name = face.name or "Untitled"

            # Truncate name if it exceeds 8 characters
            if len(face.name) > 8:
                face.name = face.name[:8] + "..."

        return {
            'faces': [face.to_dict() for face in faces.items],
            'current_page': faces.page,
            'has_next': faces.has_next,
            'success': True
        }

    except Exception as e:
        logging.error(f"Error fetching faces: {e}")
        return {'error': 'An error occurred while fetching faces.', 'details': str(e)}


# ---------------------------------------- display gallery ----------------------------------    

def display_gallery(user_id, page=1, per_page=20):
    try:
        photos = Photo.query.filter(Photo.user_id == user_id) \
                            .order_by(Photo.id.desc()) \
                            .paginate(page=page, per_page=per_page, error_out=False)

        return {
            'photos': [photo.to_dict() for photo in photos.items],
            'current_page': photos.page,
            'has_next': photos.has_next,
            'next_page': photos.next_num,
            'success': True
        }

    except Exception as e:
        logging.error(f"Error fetching gallery: {e}")
        return None  

# ------------------------------ unique faces details ------------------------------------- 

def unique_face_details(user_id, face_id):
    try:
        face = Face.query.filter(Face.id == face_id, Face.user_id == user_id).first()
        # make json response 
        if face:
            return face.to_dict()
        else:
            return {'success': False, 'message': 'Face not found'}
    except Exception as e:
        jsonify({'success': False, 'message': str(e)}), 500

# ------------------------------- photos by face id -------------------------------

def PhotosByFaceID(user_id, face_id, page=1, per_page=5):
    photos = (
        Photo.query.join(photo_faces, Photo.id == photo_faces.c.photo_id)
        .filter(photo_faces.c.face_id == face_id, Photo.user_id == user_id)
        .order_by(Photo.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return {
        'photos': [photo.to_dict() for photo in photos.items],
        'page': photos.page,
        'has_next': photos.has_next,
        'success': True
    }


# ------------------------------------ chnage face name --------------------------------

def change_face_name(face_id, name, user_id):
    try:
        # Validate inputs
        if not name or not name.strip():
            return {'success': False, 'message': 'Name is required.'}
        
        if not isinstance(face_id, int):
            try:
                face_id = int(face_id)
            except ValueError:
                return {'success': False, 'message': 'Invalid face ID.'}

        if len(name) > 50:
            return {'success': False, 'message': 'Name should not exceed 50 characters.'}

        # Fetch face record
        face = Face.query.filter_by(id=face_id, user_id=user_id).first()
        if not face:
            return {'success': False, 'message': 'Face not found.'}

        # Update and commit
        face.name = name
        db.session.commit()

        return {'success': True, 'message': 'Face name changed successfully.'}

    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Database error: {e}", exc_info=True)
        return {'success': False, 'message': 'Database error occurred.'}

    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        return {'success': False, 'message': 'An unexpected error occurred.'}

    


# ------------------------------delete photo-------------------------------------

def delete_photo(photo_id, user_id):
    """
    Deletes a photo from S3, database, and Pinecone (if necessary).
    Handles face deletion logic based on face count.
    """
    try:        
        photos_url = []  # Store photo URLs to delete from S3
        face_ids = []  # Store unique face IDs to bulk delete from Pinecone

        # Fetch the photo
        photo = Photo.query.filter_by(id=photo_id, user_id=user_id).first()
        if not photo:
            return jsonify({'success': False, 'message': 'Photo not found'}), 404

        # Append photo URL for S3 deletion
        photos_url.append(photo.photo_url)

        # Collect face IDs related to this photo
        face_ids_to_check = [face.id for face in photo.faces]

        if face_ids_to_check:
            # Fetch all unique faces in a **single query**
            unique_faces = Face.query.filter(Face.id.in_(face_ids_to_check)).all()

            for face in unique_faces:
                if face.face_count > 1:
                    face.face_count -= 1
                else:
                    # Append face ID for Pinecone deletion
                    face_ids.append(face.id)
                    # Append face image URL for S3 deletion
                    if face.face_url:
                        photos_url.append(face.face_url)
                    # Delete face from DB
                    db.session.delete(face)


        # Delete the photo from DB
        db.session.delete(photo)
        db.session.commit()

        # Delete faces from Pinecone
        if face_ids:
            delete_vector_from_pinecone(face_ids, user_id)

        # Delete images from S3
        if photos_url:
            delete_objects_from_s3(photos_url)  
            # decrease photo count 
            decrement_photo_count(user_id, 1)

        return jsonify({'success': True, 'message': 'Photo deleted successfully'}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Database error: {e}")
        return jsonify({'success': False, 'message': 'Database error occurred'}), 500

    except Exception as e:
        db.session.rollback()
        logging.error(f"Unexpected error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500



# ------------------------ delete face along with all photos -------------------------------- 

def Delete_Face(face_id, user_id=1):
    """
    Delete a face along with its associated photos, Pinecone index, and S3 objects.
    """
    try:
        photos_url = []  # Store photo URLs for S3 deletion
        mark_delete = []  # Photos to be deleted from db

        # Fetch the face
        face = Face.query.filter_by(id=face_id, user_id=user_id).first()
        if not face:
            return jsonify({'success': False, 'message': 'Face not found'}), 404

        # Get all associated photos
        associated_photos = [photo.id for photo in face.photos]

        # Find photos linked to other faces
        if associated_photos:
            photos_with_other_faces = db.session.query(photo_faces.c.photo_id).filter(
                photo_faces.c.face_id != face_id,
                photo_faces.c.photo_id.in_(associated_photos)
            ).distinct().all()

            # Convert query result to a set
            photos_with_other_faces = {p[0] for p in photos_with_other_faces}

            # Identify photos exclusively linked to this face
            mark_delete = [photo_id for photo_id in associated_photos if photo_id not in photos_with_other_faces]

            # Delete from `photo_faces` first
            if mark_delete:
                db.session.execute(delete(photo_faces).where(photo_faces.c.photo_id.in_(mark_delete)))

            # Fetch photo URLs before deletion
            if mark_delete:
                photos_url = db.session.query(Photo.photo_url).filter(
                    Photo.id.in_(mark_delete), Photo.user_id == user_id
                ).all()
                photos_url = [p[0] for p in photos_url]  # Convert tuples to list

                # Bulk delete photos
                db.session.query(Photo).filter(
                    Photo.id.in_(mark_delete), Photo.user_id == user_id
                ).delete(synchronize_session=False)

        # Store face URL before deleting
        if face.face_url:
            photos_url.append(face.face_url)

        #  Delete all entries in `photo_faces` linked to this face_id before deleting the face
        db.session.execute(delete(photo_faces).where(photo_faces.c.face_id == face_id))

        # Now delete the face using query-based deletion
        db.session.query(Face).filter_by(id=face_id, user_id=user_id).delete(synchronize_session=False)

        #  Commit transaction
        db.session.commit()

        #  Delete face from Pinecone
        delete_vector_from_pinecone([face_id], user_id)

        # Delete objects from S3
        if photos_url:
            delete_objects_from_s3(photos_url)

            # decrease photo count 
            photo_count = len(photos_url) - 1 # Subtract 1 to exclude the face image
            if photo_count > 0:
                decrement_photo_count(user_id, photo_count)

        return jsonify({'success': True, 'message': 'Face deleted successfully'}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Database error: {e}")
        return jsonify({'success': False, 'message': 'Database error occurred'}), 500

    except Exception as e:
        db.session.rollback()
        logging.error(f"Unexpected error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500



# ---------------------------------- get_faces ------------------------------ 

def get_faces(user_id, photo_id, page=1, per_page=10):
    try:
        # Fetch the photo and its linked faces
        photo = Photo.query.filter_by(id=photo_id, user_id=user_id).first()
        linked_face_ids = {face.id for face in photo.faces} if photo else set()

        # Define ordering: First linked faces (1), then unlinked (0), then by face_count DESC
        ordering = case(
            (Face.id.in_(linked_face_ids), 1),  # Linked faces come first
            else_=0  # Unlinked faces come next
        ).desc()

        # Query faces with proper ordering
        faces_query = Face.query.filter_by(user_id=user_id).order_by(ordering, Face.face_count.desc())

        if not faces_query:
            return jsonify({'success': False, 'message': 'No faces found'}), 404

        # Paginate results
        paginated_faces = faces_query.paginate(page=page, per_page=per_page, error_out=False)

        # Prepare response data
        faces_data = [
            {
                'id': face.id,
                'name': face.name,
                'face_url': face.face_url,
                'face_count': face.face_count,
                'linked': face.id in linked_face_ids 
            }
            for face in paginated_faces.items
        ]

        return jsonify({
            'faces': faces_data,
            'photo_id': photo_id,
            'page': page,
            'has_next': paginated_faces.has_next,
            'success': True
        }), 200
    
    except SQLAlchemyError as e:
        logging.error(f"Database error: {e}")
        return jsonify({'success': False, 'message': 'Database error occurred'}), 500
    
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    

# ------------------------------------ link photo to face --------------------------- 

def link_photo_to_this_face(photo_id, face_id, checked, user_id=1):
    try:
        # Fetch photo
        photo = Photo.query.filter_by(id=photo_id, user_id=user_id).first()
        if not photo:
            return jsonify({'success': False, 'message': 'Photo not found'}), 404

        # Fetch face
        face = Face.query.filter_by(id=face_id, user_id=user_id).first()
        if not face:
            return jsonify({'success': False, 'message': 'Face not found'}), 404

        # Check if the relationship exists
        is_linked = db.session.query(photo_faces).filter_by(photo_id=photo_id, face_id=face_id).first()

        if checked:  # If checkbox is checked, link the photo and face
            if not is_linked:
                photo.faces.append(face)  # Add relationship
                face.face_count += 1
        else:  # If checkbox is unchecked, unlink the photo and face
            if is_linked:
                # Delete the relationship from the association table
                db.session.execute(photo_faces.delete().where(
                    (photo_faces.c.photo_id == photo_id) & (photo_faces.c.face_id == face_id)
                ))

                # Reduce the face count
                if face.face_count > 1:
                    face.face_count -= 1
                else:
                    # First, delete all references from the association table to avoid FK errors
                    db.session.execute(photo_faces.delete().where(photo_faces.c.face_id == face_id))

                    # Then, delete the face
                    db.session.delete(face)

                    # Delete associated S3 objects and vector database entries
                    if face.face_url:
                        delete_objects_from_s3([face.face_url])
                    delete_vector_from_pinecone([face_id], user_id)

        db.session.commit()
        message = 'Photo linked to face successfully' if checked else 'Photo unlinked from face successfully'
        return jsonify({'success': True, 'message': message}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Database error occurred'}), 500

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500



# ------------------------------- delete object from s3 -----------------------------

def delete_objects_from_s3(object_urls):
    try:
        if not object_urls:
            logging.warning("No object URLs provided for deletion.")
            return False
        
        if not isinstance(object_urls, list):
            object_urls = [object_urls]  # Convert single URL to list
        
        object_keys = [{"Key": object_key_extractor(url)} for url in object_urls]
        if not object_keys:
            logging.warning("No object keys extracted from URLs.")
            return False

        bucket_name=os.getenv("AWS_BUCKET")
        response = s3_bucket_connection().delete_objects(
            Bucket=bucket_name,
            Delete={"Objects": object_keys}
        )
        # deleted = response.get("Deleted", [])
        errors = response.get("Errors", [])

        if errors:
            logging.error(f"Errors while deleting objects: {errors}")
            return False

        return True
    
    except Exception as e:
        logging.error(f"Error deleting object from S3: {e}")
        return False


# ---------------------------------- delete vector from pinecone --------------------------------

def delete_vector_from_pinecone(face_ids, user_id=1):
    try:
        if not face_ids:
            logging.warning("No face IDs provided for deletion.")
            return False
    
        pinecone_connection().delete(ids=[str(face_id) for face_id in face_ids], namespace=str(user_id))
        return True
    except Exception as e:
        logging.error(f"Error deleting vector from Pinecone: {e}")
        return False
    

# --------------------------- check if max_photos_reached ---------------------------- 

def check_max_photos_reached(user_id):
    try:
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return {'success': False, 'message': 'User not found.'}

        photo_count_now = user.photo_count
        max_photo_allowed = user.max_photos

        if photo_count_now >= max_photo_allowed:
            return {
                'success': False,
                'message': f'You have uploaded the maximum number of photos. Max limit is {max_photo_allowed}. If you want to upload more photos, please contact us.'
            }

        return True
    
    except Exception as e:
        logging.error(f"Error checking max photos reached: {e}")
        return {'success': False, 'message': 'An error occurred while checking photo limit.'}
    
# ----------------------------- increament photo count ------------------------------ 

def increment_photo_count(user_id):
    try:
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return False
        
        # Ensure max_photos is not None before incrementing
        if user.photo_count is None:
            user.photo_count = 0

        user.photo_count += 1
        db.session.commit()
        return True
    except Exception as e:
        logging.error(f"Error incrementing photo count for user {user_id}: {e}")
        return False
    
# ------------------------------ decreament photo count ------------------------------ 

def decrement_photo_count(user_id, decrement_by=1):
    try:
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return False

        # Ensure max_photos does not go negative
        if user.photo_count >= decrement_by:
            user.photo_count = max(0, user.photo_count - decrement_by)
            db.session.commit()
            return True  
        
        return False  # If photos are already at 0, return False
    except Exception as e:
        logging.error(f"Error decrementing photo count: {e}")
        return False


# ------------------------------- create photo object ------------------------------- 

def create_photo_object(user_id, photo_url):
    try:
        photo = Photo(user_id=user_id, photo_url=photo_url)
        db.session.add(photo)
        db.session.commit()
        return photo
    except Exception  as e:
        logging.error(f"Error while create photo object: {e}")


# --------------------------------- add face row ----------------------- 