import boto3
from botocore.config import Config
import json
import io
import logging
from botocore.exceptions import ClientError

custom_config = Config(
    retries={
        'max_attempts': 10,
        'mode': 'standard'
    },
    signature_version='s3v4'
)

def get_s3_client():
    return boto3.client('s3',
                        endpoint_url='http://minio:9000',
                        aws_access_key_id='cRyj3AP81BxrHzn4F1ZJ',
                        aws_secret_access_key='Yt7hmfloOwcCIWPlaKbGbajpGGU52Asd34sWLs24',
                        region_name='us-east-1',
                        config=boto3.session.Config(signature_version='s3v4'))

def put_json_object(bucket_name, object_name, data):
    s3_client = get_s3_client()
    json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
    s3_client.put_object(
        Bucket=bucket_name,
        Key=object_name,
        Body=io.BytesIO(json_data),
        ContentType="application/json"
    )

def get_json_object(bucket_name: str, object_name: str):
    s3_client = get_s3_client()
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=object_name)
        content = response['Body'].read().decode('utf-8')
        return json.loads(content)
    except ClientError as e:
        logging.error(f"Erreur lors de la lecture de l'objet {object_name} depuis le bucket {bucket_name}: {e}")
        raise

def put_object(bucket_name, object_name, data, length, content_type):
    s3_client = get_s3_client()
    try:
        s3_client.put_object(Bucket=bucket_name, Key=object_name, Body=data, ContentLength=length, ContentType=content_type)
        return True
    except ClientError as e:
        logging.error(f"Erreur lors de l'upload de l'objet : {e}")
        return False

def generate_presigned_url(bucket_name, object_name, expiration=3600):
    """Génère une URL présignée pour permettre l'accès au fichier"""
    s3_client = get_s3_client()
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
    except Exception as e:
        logging.error(f"Erreur lors de la génération de l'URL présignée : {str(e)}")
        return None
    return response

def get_presigned_url(bucket_name: str, object_name: str, expiration=3600):
    s3_client = get_s3_client()
    try:
        url = s3_client.generate_presigned_url('get_object',
                                               Params={'Bucket': bucket_name,
                                                       'Key': object_name},
                                               ExpiresIn=expiration)
        return url
    except ClientError as e:
        logging.error(f"Erreur lors de la génération de l'URL présignée : {e}")
        return None

def get_json_object(bucket_name, object_name):
    s3_client = get_s3_client()
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=object_name)
        return json.loads(response['Body'].read().decode('utf-8'))
    except ClientError as e:
        logging.error(f"Erreur lors de la lecture de l'objet JSON : {e}")
        return None

def get_object(bucket_name, object_name):
    s3_client = get_s3_client()
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=object_name)
        return response['Body'].read()
    except Exception as e:
        print(f"Erreur lors de la récupération de l'objet : {str(e)}")
        return None
