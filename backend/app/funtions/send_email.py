from utils.logger import logging
from flask import render_template
from jinja2 import TemplateNotFound
import requests
import json
import os

# load env 
from dotenv import load_dotenv
load_dotenv()


# ZeptoMail API details (or any email service)
ZEPTOMAIL_URL = "https://api.zeptomail.in/v1.1/email"
ZEPTOMAIL_TOKEN = os.getenv("ZEPTOMAIL_TOKEN")
DEFAULT_SENDER = "noreply@whatbm.com"


def send_email(kwargs):
    try:
        # Validate required fields
        if not all(key in kwargs for key in ["to_email", "context"]):
            return {"success": False, "message": "Missing required fields: 'to_email' and 'context'."}

        # Extract required fields
        from_email = kwargs.get("from_email", DEFAULT_SENDER)
        from_name = kwargs.get("from_name", "whatBM Photos")
        to_email = kwargs.get("to_email")
        to_name = kwargs.get("to_name", "User")
        template_name = kwargs.get("template_name", "default.html")
        context = kwargs.get("context", {})
        subject = kwargs.get("subject", "Email Hits")

        # Try rendering the template
        try:
            html_content = render_template(f"email_templates/{template_name}", **context)
        except TemplateNotFound:
            return {"success": False, "message": f"Email template '{template_name}' not found."}

        # Define email payload
        payload = {
            "from": {"name": from_name, "address": from_email},
            "to": [{"email_address": {"name": to_name, "address": to_email}}],
            "subject": subject,
            "htmlbody": html_content
        }

        # Set headers for API request
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": ZEPTOMAIL_TOKEN
        }

        # Send request
        response = requests.post(ZEPTOMAIL_URL, data=json.dumps(payload), headers=headers)

        # Try parsing the response
        try:
            response_data = response.json() if response.content else {}
        except json.JSONDecodeError:
            response_data = {}

        # Extract message from response
        response_message = response_data.get("message", "")

        return {
            "success": response_message == "OK",
            "message": "Email sent successfully" if response_message == "OK" else "Failed to send email",
        }

    except requests.exceptions.RequestException as req_error:
        logging.error(f"API request failed: {req_error}")
        return {"success": False, "message": "Failed to connect to the email API."}

    except Exception as e:
        logging.error(f"Unexpected error in send_email: {e}")
        return {"success": False, "message": str(e)}