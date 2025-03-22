import os
from dotenv import load_dotenv

load_dotenv()
# configration with flask
class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "@#$%^UTFRGFYGJHHJFGFDURTF&^T")
    CELERY_BROKER_URL= os.getenv("CELERY_BROKER_URL")

    # MySQL Database Config
    SQLALCHEMY_DATABASE_URI = os.getenv("MYSQL_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # celery setup 
    CELERY_CONFIG = {
        'broker_url': os.getenv('CELERY_BROKER_URL'),
        'worker_concurrency': 1,
    }


# other settins to control backend app 
AWS_BUCKET = os.getenv("AWS_BUCKET")
AWS_FOLDER = os.getenv("AWS_FOLDER")