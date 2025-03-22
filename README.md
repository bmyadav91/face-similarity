
## How to setup
After pull repo ensure conda is installed in your PC.
run following command.
`conda env create --prefix /app/env -f environment.yml`
activate env 
`conda activate .\env`
after these create a .env file or rename .env.prod to .env ensure all varibale should be there.

### AWS 
1. Pull the repo
2. Create an Account on AWS -> Get Access Key, Security Key, Regeion.
3. Setup S3 Bucket and create a main project name folder.
4. put all in .env file

### mysql
1. start your mysql server and create face_album database -> set root password root it is default. if you want to use different password change it in .env file
2. put all in .env file

### setup celery 
before start celery ensure salary is intalled into your system and running on 6379 port.

run following command to start and log backround task like -> face detction and classification.
`celery -A run.celery --loglevel=info`

### PineCone
1. Create account -> create an index with default 128D
2. Get API Access Key and Index
3. put all in .env file

### google auth 
if you want to setup google login then go to google auth console and create api and secret paste it into .env's varibale

### Email sending
in this project we have used ZeptoMail for sending email like OTP.
so create account there and setup your domain. or you can use another email service for email but you may need to modify backend/app/functions/send_email.py.
after that you can paste it into .env file

### Domain allowed 
There is varibale called `ALLOWED_ORIGINS` in .env so you can set those origins where you want to request it helps to secure you google auth.

### migration of Database run the following command to migrate columns to database

`flask --app run.py db init`
`flask --app run.py db migrate -m "initial commit"`
`flask --app run.py db upgrade`


<!-- Dockerize (if you needed) -->

## Dockerize
to dockerize the project make sure you have latest version of Docker (>24) and Dockert Composer (>2.2)

ensure port is available for running there are 4 ports 5000, 80, 6379, 3306

run following command to build docker and setup

`docker compose build`
`docker-compose up -d`

ensure your docker images are running 

`docker compose ps`

[Now you can open localhost:80](http://localhost:80)

now you can test your project is ready on even docker. 

you can push the images on aws ECR, Docker, or any and pull on server.

