from utils.logger import logging
from PIL import Image
from deepface import DeepFace
import numpy as np
import tempfile
import os


def generate_embedding(PIL_Object):
    if PIL_Object is None:
        logging.error("No PIL object provided.")
        return None

    if not isinstance(PIL_Object, Image.Image):
        logging.error("Invalid input: Expected a PIL Image object.")
        return None

    try:
        # Convert PIL image to RGB
        PIL_Object = PIL_Object.convert("RGB")

        # Save the image temporarily, as DeepFace requires a file path
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_img:
            PIL_Object.save(temp_img, format="JPEG")
            temp_img_path = temp_img.name  # Get the temp file path

        # Generate embedding with DeepFace
        try:
            embedding = DeepFace.represent(img_path=temp_img_path, model_name="Facenet", enforce_detection=False)
        finally:
            # Cleanup: Remove the temp file
            os.remove(temp_img_path)

        # Validate embedding output
        if not embedding or not isinstance(embedding, list) or "embedding" not in embedding[0]:
            logging.error("Failed to generate valid embedding.")
            return None

        return np.array(embedding[0]["embedding"]).tolist()

    except Exception as e:
        logging.error(f"Error generating embedding: {e}")
        return None
