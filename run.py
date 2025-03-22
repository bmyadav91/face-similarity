from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

from backend.app import create_app
app, celery = create_app()
# app.app_context().push()

# run app 
if __name__ == '__main__':  
  app.run(host='0.0.0.0', port=5000)

