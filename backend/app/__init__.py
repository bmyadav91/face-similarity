from flask import Flask
from flask_cors import CORS
from backend.app.utils import settings
from backend.app.routes.views import site
from backend.app.routes.auth import auth
from backend.app.extensions import db
from flask_migrate import Migrate 
from backend.app.models import *
from backend.app.celery.celery_config import make_celery


def create_app():
    app = Flask(__name__)
    # Load configurations
    app.config.from_object(settings.Config)

    # site blueprint Register
    app.register_blueprint(site)

    # auth blueprint Register 
    app.register_blueprint(auth)

    # Initialize the database with Flask app
    db.init_app(app)

    # Flask-migration
    Migrate(app, db) # enable during db migration

    # Enable CORS
    CORS(app, resources={r"/*": {"origins": "*"}}, 
     supports_credentials=True, 
     allow_headers=["Authorization", "Content-Type"],
     expose_headers=["Authorization", "Content-Type"]
    )

    # Initialize Celery with Flask
    celery = make_celery(app)
    celery.set_default()

    
    return app, celery
