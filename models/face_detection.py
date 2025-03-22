from io import BytesIO
from utils.logger import logging
from mtcnn import MTCNN
from PIL import Image
import numpy as np
from models.embedding_extraction import generate_embedding

def Detect_Face_Function(img_bytes, max_face=10):
    """
    The function detects faces from image (image bytes it will convert image and array). If faces are found, it returns a list of embeddings.
    """
    try:
        # convert image bytes to image rgb 
        image = Image.open(BytesIO(img_bytes)).convert("RGB")
        # convert image to array 
        image_array = np.array(image)


        # Initiate MTCNN
        detector = MTCNN()
        faces = detector.detect_faces(image_array)
        if not faces:
            return None  # No faces detected

        results = []  # Store (cropped_face, embedding)

        for face in faces[:max_face]:  # Limit face processing
            x, y, width, height = face['box']
            x, y = max(x, 0), max(y, 0)
            cropped_face = image.crop((x, y, x + width, y + height))

            if cropped_face.width > 150:
                aspect_ratio = cropped_face.height / cropped_face.width
                cropped_face = cropped_face.resize((150, int(150 * aspect_ratio)))

            face_embedding = generate_embedding(cropped_face)
            if face_embedding is not None:
                results.append((cropped_face, face_embedding))  # return both face and embedding

        return results if results else None  # Return list of (cropped_face, embedding)

    except Exception as e:
        logging.error(f"Error in Detect_Face_Function: {e}")
        return None