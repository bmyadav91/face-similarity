from functools import wraps
from flask import request, jsonify, redirect, url_for
from backend.app.funtions.jwt_encode_decode import jwtDecode

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # return f(1, *args, **kwargs) # un comment for testing purpose 
            
            # get access token from header barier 
            access_token = request.headers.get("Authorization", None)

            # Check if the token is present
            if not access_token or not access_token.startswith("Bearer "):
                return jsonify({"success": False, "message": "Unauthorized: Token not found"}), 401
            
            # Extract the token
            access_token = access_token.replace("Bearer ", "").strip()

            if not access_token:
                return jsonify({"success": False, "message": "Unauthorized: Token not found"}), 401

            # Decode the token
            payload_json = jwtDecode(access_token) 

            if "error" in payload_json:
                return jsonify({"success": False, "message": payload_json["error"]}), 401

            user_id = int(payload_json.get("user_id", None))

            if not user_id:
                return jsonify({"success": False, "message": "Unauthorized: User ID not found in token"}), 401

            return f(user_id, *args, **kwargs) 

        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    return decorated_function
