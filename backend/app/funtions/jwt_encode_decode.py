import base64
import hmac
import hashlib
import json
import time
import os

# load env 
from dotenv import load_dotenv
load_dotenv()


# ---------------------------------- jwt ----------------------------------

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "1fb8d81022d044fd3daf933d6b0bf0541eecc6c254461add7")
JWT_REFRESH_SECRET_KEY = os.getenv("JWT_REFRESH_KEY", "8hVWhBTTZwDQFaObXOKi6sLrIo6HDGgdf5dhG565")



# ---------------------------------------- jwt encoder ---------------------------------------- 

def jwtEncode(data, expiry_days=30, key=JWT_SECRET_KEY):
    """
    Encode a JWT token.
    
    :param data: The payload (dictionary)
    :param expiry_days: Expiry time in days (default: 30)
    :return: Encoded JWT token (string)
    """
    # Define header
    header = {"alg": "HS256", "typ": "JWT"}

    # Set expiration timestamp (expiry_days converted to seconds)
    expiry_timestamp = int(time.time()) + (expiry_days * 24 * 60 * 60)
    data["exp"] = expiry_timestamp  # Add expiry time to payload

    # Convert header & payload to JSON and then Base64 encode
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip("=")

    # Create signature using HMAC-SHA256
    signature = hmac.new(key.encode(), f"{header_b64}.{payload_b64}".encode(), hashlib.sha256).digest()
    signature_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")

    # Combine all parts
    jwt_token = f"{header_b64}.{payload_b64}.{signature_b64}"
    return jwt_token


# ------------------------------------- jwt decoder ------------------------------------- 

def jwtDecode(token, key=JWT_SECRET_KEY, Expired=False):
    """
    Decode a JWT token.

    :param token: The JWT token (string)
    :param key: The secret key to verify signature
    :return: Decoded payload if valid, otherwise error message
    """
    try:
        # Split token into parts
        header_b64, payload_b64, signature_b64 = token.split(".")

        # Decode header & payload
        header_json = json.loads(base64.urlsafe_b64decode(header_b64 + "==").decode())
        payload_json = json.loads(base64.urlsafe_b64decode(payload_b64 + "==").decode())

        # Verify signature
        expected_signature = hmac.new(
            key.encode(), f"{header_b64}.{payload_b64}".encode(), hashlib.sha256
        ).digest()
        expected_signature_b64 = base64.urlsafe_b64encode(expected_signature).decode().rstrip("=")

        if expected_signature_b64 != signature_b64:
            return {"error": "Invalid signature"}

        # Check expiry time
        if Expired:
            return payload_json
        
        if "exp" in payload_json and time.time() > payload_json["exp"]:
            return {"error": "Token expired"}

        return payload_json  # Return decoded payload if valid

    except Exception as e:
        return {"error": "Invalid token", "details": str(e)}