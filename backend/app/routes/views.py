from flask import jsonify, request, Blueprint
from models.validation import FileValidation #importing from model
from models.image_compress import compress_image # importing from model

from backend.app.funtions.function import *
from backend.app.utils.decorator import login_required
from backend.app.celery.celery_worker import detect_face

site = Blueprint('site', __name__)
 
# ------------------------------- faces -----------------------------------

@site.route('/faces', methods=['GET'])
@login_required
def face(userID):
   try:
      page = int(request.args.get('page', 1))
      faces_obj = display_faces(userID, page)
      return jsonify(faces_obj)
   except Exception as e:
      return jsonify({'success': False, 'message': str(e)}), 500
   


# ------------------------------ photos --------------------------------------

@site.route('/photos', methods=['GET'])
@login_required
def photos(userID):
   try:
      page = int(request.args.get('page', 1))
      gallery_obj = display_gallery(userID, page, 20)
      return jsonify(gallery_obj)
   except Exception as e:
      return jsonify({'success': False, 'message': str(e)}), 500


# ------------------------------- face details ----------------------------------------

@site.route('/face/<int:face_id>', methods=['GET'])
@login_required
def FaceDetails(userID, face_id):
   try:
      face = unique_face_details(userID, face_id)
      return jsonify({'face': face, 'success': True})
   except Exception as e:
      return jsonify({'success': False, 'message': str(e)}), 500



# -------------------------- photo by face ------------------------------------

@site.route('/photo_by_face', methods=['GET'])
@login_required
def face_photo_pagination(userID):
   try:
      current_page = int(request.args.get('page', 1))
      face_id = int(request.args.get('face_id', 0))
      gallery_obj = PhotosByFaceID(userID, face_id, current_page)
      return jsonify(gallery_obj)
   except Exception as e:
      return jsonify({'success': False, 'message': str(e)}), 500

# --------------------------- file upload route -------------------------------------  

@site.route('/upload', methods=['GET', 'POST'])
@login_required
def upload(userID):
   if request.method == 'POST':
      try:
         file = request.files['file']
         if file:            
            # Validate file
            validation_img = FileValidation(file)
            if not validation_img.get('success', False):
                  return jsonify(validation_img), 400
            
            # compress image 
            compressed_bytes = compress_image(file)
            if not compressed_bytes.get('success', False):
                  return jsonify(compressed_bytes), 400

            # upload to s3
            file_upload = Object_Uploader_s3(compressed_bytes, userID, 'media')
            if not file_upload.get('success', False):
               return jsonify(file_upload), 400
            
            # face detection 
            uploaded_url = file_upload.get('url')
            detect_face.delay(uploaded_url, userID)

            
            return jsonify({'success': True, 'message': 'File uploaded successfully.'}), 200
         else:
            return jsonify({'success': False, 'message': 'No file uploaded.'}), 400
      
      except Exception as e:
         return jsonify({'success': False, 'message': str(e)}), 500
         
   check_max_limit = check_max_photos_reached(userID)
   max_photos_reached = False
   if isinstance(check_max_limit, dict) and not check_max_limit.get('success', False):
      max_photos_reached = True
   return jsonify({'success': True, 'max_photos_reached': max_photos_reached}), 200
   # return render_template('upload.html', max_photos_reached=max_photos_reached)



# ----------------------------------- delete photo ----------------------------------------

@site.route('/delete_photo', methods=['POST'])
@login_required
def DeletePhoto(userID):
   try:
      data = request.get_json()
      photo_id = int(data.get('photo_id', '0'))
      delete_result = delete_photo(photo_id, userID)
      return delete_result
   except Exception as e:
      return jsonify({'success': False, 'message': str(e)}), 500



# --------------------------------- chnage face name ---------------------------------------

@site.route('/update-face-name', methods=['POST'])
@login_required
def update_face_name(userID):
   try:
      data = request.get_json()
      face_id = data.get('face_id')
      new_name = data.get('name')
      change_result = change_face_name(face_id, new_name, userID)
      return jsonify(change_result)
   except Exception as e:
      return jsonify({'success': False, 'message': str(e)}), 500
   

# ----------------------------------- delete face ---------------------------------------- 

@site.route('/delete_face', methods=['POST'])
@login_required
def DeleteFace(userID):
   try:
      data = request.get_json()
      face_id = data.get('face_id')
      delete_result = Delete_Face(face_id, userID)
      return delete_result
   except Exception as e:
      return jsonify({'success': False, 'message': str(e)}), 500
   
   

# -------------------------------------- get_faces ------------------------------------- 

@site.route('/get_faces', methods=['POST'])
@login_required
def Get_faces(userID):
   try:
      data = request.get_json()
      photo_id = int(data.get('photo_id', 0))
      page = int(data.get('page', 1))
      faces_result = get_faces(userID, photo_id, page)
      return faces_result 
   except Exception as e:
      return jsonify({'success': False, 'message': str(e)}), 500
   

# ----------------------------- link unlink any photo with face ------------------------------- 

@site.route('/link_unlink_photo_with_face', methods=['POST'])
@login_required
def link_photo_to_face(userID):
   try:
      data = request.get_json()
      photo_id = int(data.get('photo_id', 0))
      face_id = int(data.get('face_id', 0))
      checked = data.get('checked')
      linked_result = link_photo_to_this_face(photo_id, face_id, checked, userID)
      return linked_result 
   except Exception as e:
      return jsonify({'success': False, 'message': str(e)}), 500

   