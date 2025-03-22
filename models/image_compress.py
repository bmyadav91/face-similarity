import cv2
import numpy as np
from io import BytesIO
import os

def compress_image(image, keep_quality=85):
    try:
        # Extract the file extension
        file_extension = os.path.splitext(image.filename)[-1].lower()
        valid_formats = [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"]

        if file_extension not in valid_formats:
            return {'success': False, "message": f"Unsupported image format (only {valid_formats} are supported)."}

        # Read the image file with OpenCV
        file_bytes = np.frombuffer(image.read(), np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        # Determine the output format based on the original extension
        if file_extension in [".webp"]:
            encode_format = ".webp"
            encode_param = [int(cv2.IMWRITE_WEBP_QUALITY), keep_quality]
        elif file_extension in [".png"]:
            encode_format = ".png"
            encode_param = []  # PNG doesn't have a "quality" parameter in OpenCV
        else:
            encode_format = ".jpg"
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), keep_quality]

        # Compress the image
        success, buffer = cv2.imencode(encode_format, img, encode_param)
        if not success:
            return {'success': False, "message": "Image compression failed"}

        # Convert the buffer to a BytesIO stream for S3 upload
        img_bytes = BytesIO(buffer.tobytes())
        img_bytes.seek(0)

        # generate file name 
        file_name = f"{os.path.splitext(image.filename)[0]}{encode_format}"

        return {
            'success': True,
            'image_bytes': img_bytes,
            'file_name': file_name
        }
    except Exception as e:
        return {'success': False, "message": str(e)}
    

    