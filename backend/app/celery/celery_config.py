from celery import Celery
from kombu import Queue
from backend.app.utils import settings
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()


def make_celery(app):
    """
    Initialize Celery with the Flask application context.
    """
    celery = Celery(app.import_name)
    celery.conf.update(app.config["CELERY_CONFIG"])  

    class ContextTask(celery.Task):
        """Ensure tasks run within the Flask application context."""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return super().__call__(*args, **kwargs)

    celery.Task = ContextTask
    return celery






















# flask_app = create_app()


# celery = Celery(
#     __name__,
#     broker=flask_app.config["CELERY_BROKER_URL"],
# )

# celery.conf.update(flask_app.config)

# # Bind Celery to Flask App
# class ContextTask(celery.Task):
#     """Ensure all tasks run within the Flask application context."""
#     def __call__(self, *args, **kwargs):
#         with flask_app.app_context():
#             return super().__call__(*args, **kwargs)

# celery.Task = ContextTask


# def make_celery():
#     """
#     Create a Celery instance without direct Flask dependency.
#     """
#     celery = Celery(
#         "face_album",
#         broker=settings.Config.CELERY_BROKER_URL,  # Access settings directly
#         include=["backend.app.celery.celery_worker"],  # Import tasks, not worker
#     )

#     # Update Celery config
#     celery.conf.update(
#         task_serializer="json",
#         result_serializer="json",
#         accept_content=["json"],
#         timezone="UTC",
#         enable_utc=True,
#         task_queues=[Queue("sequential_queue")],
#         task_default_queue="sequential_queue",
#         worker_concurrency=1,
#         result_expires=86400,
#     )

#     return celery

# celery = make_celery()  # Global Celery instance
