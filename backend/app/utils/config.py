import boto3
from botocore.exceptions import NoCredentialsError
import os
from utils.logger import logging
from pinecone import Pinecone
from redis import Redis

# AWS s3 connection 
LoadedS3Connection = None
def s3_bucket_connection():
    global LoadedS3Connection
    if LoadedS3Connection is not None:
        return LoadedS3Connection
    
    try:
        LoadedS3Connection = boto3.client(
            's3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
            aws_secret_access_key=os.getenv("AWS_SECRET_KEY"),
            region_name=os.getenv("AWS_REGION")
        )
    except NoCredentialsError:
        logging.error("Credentials not available.")
        LoadedS3Connection = None
    except Exception as e:
        logging.error(f"Error connecting to S3: {e}")
        LoadedS3Connection = None
        
    return LoadedS3Connection


# Pinecone connection 
LoadedPineconeConnection = None
def pinecone_connection():
    global LoadedPineconeConnection
    if LoadedPineconeConnection is not None:
        return LoadedPineconeConnection
    
    try:
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))
        LoadedPineconeConnection = index
    except Exception as e:
        logging.error(f"Error connecting to Pinecone: {e}")
        LoadedPineconeConnection = None

    return LoadedPineconeConnection

# redis connection 
LoadedRedisConnection = None
def redis_connection():
    global LoadedRedisConnection
    if LoadedRedisConnection is not None:
        return LoadedRedisConnection
    
    try:
        LoadedRedisConnection = Redis(host='localhost', port=6379, db=0)
    except Exception as e:
        logging.error(f"Error connecting to Redis: {e}")
        LoadedRedisConnection = None

    return LoadedRedisConnection

