import os
from io import BytesIO
import uuid
from utils.logger import logging
from backend.app.extensions import db
from backend.app.models import Face
from backend.app.utils.config import s3_bucket_connection
from backend.app.funtions.function import (
    check_max_photos_reached,
    object_key_extractor,
    create_photo_object,
    increment_photo_count,
    CheckFaceExistence,
    Object_Uploader_s3,
    UpsertFaceToPinecone,
    delete_objects_from_s3,
)
from backend.app.funtions.auth_function import (
    Delete_User
) 
# importing from model 
from models.face_detection import Detect_Face_Function
from celery import shared_task




# ------------------------detect face function ---------------------------------


@shared_task(bind=True)
def detect_face(self, uploaded_url, user_id):
    """
    Detects human faces in an uploaded image, checks if they already exist in the database, 
    and either classifies the face or creates a new entry.

    Args:
        uploaded_url (str): The URL of the uploaded image in the S3 bucket.
        user_id (int): The ID of the user uploading the image.

    Returns:
        bool: True if the image was processed successfully, False otherwise.
    """
    try:
        DeleteS3Object = True
        # Check if user already uploaded max allowed images
        is_max_photos_reached = check_max_photos_reached(user_id)
        if isinstance(is_max_photos_reached, dict) and not is_max_photos_reached.get('success', False):
            return False

        # Retrieve image bytes from S3 bucket
        Object_key = object_key_extractor(uploaded_url)
        bucket_name = os.getenv("AWS_BUCKET")

        with s3_bucket_connection().get_object(Bucket=bucket_name, Key=Object_key)['Body'] as s3_body:
            img_bytes = s3_body.read() 

        # Create & Commit Photo First
        photo = create_photo_object(user_id, uploaded_url)
        if not photo:
            return False

        # Increment photo count for the user
        if not increment_photo_count(user_id):
            return False
        
        # on above code success mark not delete image from s3
        DeleteS3Object = False
        
        # Get face embedding and cropped face
        face_data = Detect_Face_Function(img_bytes)
        if not face_data:
            return False  # No human face detected

        new_faces = []
        for face_pil, face_embedding in face_data:
            face_id = CheckFaceExistence(face_embedding, str(user_id))
            
            if not face_id or not face_id.get('face_id'):
                img_bytes_io = BytesIO()
                face_pil.save(img_bytes_io, format="JPEG")
                img_bytes_io.seek(0)

                Upload_to_s3 = Object_Uploader_s3(
                    {"image_bytes": img_bytes_io, "file_name": uuid.uuid4().hex[:12] + ".jpg"},
                    user_folder=str(user_id),
                    img_type="faces"
                )

                if not Upload_to_s3.get('url', False):
                    logging.error("Failed to upload face image to S3.")
                    continue
                
                new_face = Face(user_id=user_id, face_url=Upload_to_s3.get('url'))
                db.session.add(new_face)
                new_faces.append((new_face, face_embedding))  # Storing new faces for batch commit
            else:
                existing_face = db.session.get(Face, face_id['face_id'])
                if existing_face:
                    existing_face.face_count += 1
                    db.session.add(existing_face)
                    photo.faces.append(existing_face)

        if new_faces:
            db.session.commit()  # Batch commit new faces to reduce DB load
            
            for new_face, face_embedding in new_faces:
                face_id = str(new_face.id)  # Get ID after commit
                UpsertFaceToPinecone(face_embedding, face_id, str(user_id))
                photo.faces.append(new_face)

        db.session.commit()  # Final commit to save all changes
        return True

    except Exception as e:
        db.session.rollback()
        logging.error(f"Database error while detecting faces: {e}")
        return False
    
    finally:
        if DeleteS3Object:
            delete_objects_from_s3(uploaded_url)


    

    



# delete permanent account 

@shared_task(bind=True)
def delete_account_bg(self, user_id):
    try:
        return Delete_User(user_id)
    except Exception as e:
        logging.error(f"Unexpected error in delete_account: {e}")
        raise  # Raising the error ensures Celery retries it