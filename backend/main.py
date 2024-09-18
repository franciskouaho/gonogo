import os
import zipfile
import shutil
import json
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.pdf_to_json import pdf_to_json
from backend.xlsx_to_json import xlsx_to_json
from backend.docx_to_json import docx_to_json
from backend.process_gonogo_file import process_gonogo_file
from backend.s3_config import get_s3_client, put_json_object, get_json_object
import io

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/read-file")
async def read_file(file: UploadFile = File(...)):
    try:
        logging.info(f"Fichier reçu : {file.filename}")
        logging.info(f"Content-Type : {file.content_type}")

        result = process_gonogo_file(file)

        return {"message": "Fichier traité avec succès", "word_document_url": result["word_document_url"]}
    except Exception as e:
        logging.error(f"Erreur lors du traitement : {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def process_zip_from_minio(zip_filename):
    s3_client = get_s3_client()

    response = s3_client.get_object(Bucket="jobpilot", Key=zip_filename)
    zip_content = response['Body'].read()

    results = []
    with zipfile.ZipFile(io.BytesIO(zip_content)) as zip_ref:
        for file_info in zip_ref.infolist():
            if file_info.filename.startswith('__MACOSX') or file_info.filename.startswith('._'):
                continue

            file_content = zip_ref.read(file_info.filename)
            file_extension = os.path.splitext(file_info.filename)[1].lower()

            try:
                if file_extension == '.pdf':
                    cv_json = pdf_to_json(io.BytesIO(file_content))
                elif file_extension == '.xlsx':
                    cv_json = xlsx_to_json(io.BytesIO(file_content))
                elif file_extension == '.docx':
                    cv_json = docx_to_json(io.BytesIO(file_content))
                else:
                    continue

                results.append({"file": file_info.filename, "content": cv_json})
            except Exception as e:
                logger.error(f"Erreur lors de la conversion du fichier {file_info.filename} : {str(e)}")

    return results
