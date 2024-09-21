import io
import logging
import os
import zipfile
import shutil
import json
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.s3_config import put_object, get_s3_client, get_object
from backend.process_gonogo_file import process_gonogo_file
from backend.pdf_to_json import pdf_to_json
from backend.xlsx_to_json import xlsx_to_json
from backend.docx_to_json import docx_to_json
from backend.doc_to_json import doc_to_json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

origins = [
    "http://localhost:3000",
    "https://emplica.fr",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/read-file")
async def match(zip_file: UploadFile = File(...)):
    logger.info(f"Réception d'un fichier : {zip_file.filename}")
    s3_bucket = "jobpilot"
    results_file_key = f"results/{zip_file.filename}.json"

    try:
        content = await zip_file.read()
        put_object(s3_bucket, zip_file.filename, content, len(content), 'application/zip')
        logger.info(f"Fichier ZIP uploadé dans S3 : {zip_file.filename}")

        results = process_zip_from_s3(s3_bucket, zip_file.filename)

        if results:
            s3_client = get_s3_client()
            s3_client.put_object(Bucket=s3_bucket, Key=results_file_key, Body=json.dumps(results, ensure_ascii=False).encode('utf-8'))
            logger.info(f"Résultats sauvegardés dans S3 : {results_file_key}")

            logger.info(f"Traitement terminé. Nombre de fichiers traités : {len(results)}")
            response_result = process_gonogo_file(results)
            logger.info(f"Résultat du traitement : {response_result}")
            return response_result
        else:
            raise HTTPException(status_code=400, detail="Aucun fichier valide trouvé dans le zip")

    except Exception as e:
        logger.exception(f"Erreur lors du traitement : {str(e)}")
        return {"error": str(e)}, 500

@app.get("/download-document")
async def download_document(file_path: str):
    logger.info(f"Demande de téléchargement pour le fichier : {file_path}")
    s3_bucket = "jobpilot"

    try:
        s3_client = get_s3_client()
        response = s3_client.get_object(Bucket=s3_bucket, Key=file_path)

        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension == '.docx':
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif file_extension == '.pdf':
            media_type = "application/pdf"
        else:
            media_type = "application/octet-stream"

        return StreamingResponse(
            response['Body'].iter_chunks(),
            media_type=media_type,
            headers={
                'Content-Disposition': f'attachment; filename="{os.path.basename(file_path)}"'
            }
        )
    except Exception as e:
        logger.exception(f"Erreur lors du téléchargement du fichier : {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors du téléchargement : {str(e)}")

def process_zip_from_s3(bucket, key):
    s3_client = get_s3_client()
    zip_obj = s3_client.get_object(Bucket=bucket, Key=key)
    zip_content = zip_obj['Body'].read()

    results = []
    processed_files = 0
    valid_files = 0
    with zipfile.ZipFile(io.BytesIO(zip_content)) as zip_ref:
        for file_info in zip_ref.infolist():
            if file_info.filename.startswith('__MACOSX') or file_info.filename.startswith('._') or file_info.filename == '.DS_Store':
                continue

            file_extension = file_info.filename.split('.')[-1].lower()
            if file_extension not in ['pdf', 'xlsx', 'xls', 'docx', 'doc']:
                logger.info(f"Extension non prise en charge pour le fichier {file_info.filename}")
                continue

            valid_files += 1
            file_content = zip_ref.read(file_info.filename)

            try:
                if file_extension == 'pdf':
                    cv_json = pdf_to_json(io.BytesIO(file_content))
                elif file_extension in ['xlsx', 'xls']:
                    cv_json = xlsx_to_json(io.BytesIO(file_content))
                elif file_extension == 'docx':
                    cv_json = docx_to_json(io.BytesIO(file_content))
                elif file_extension == 'doc':
                    cv_json = doc_to_json(file_content)
                else:
                    continue

                if cv_json:
                    results.append({"file": file_info.filename, "content": cv_json})
                    processed_files += 1
                else:
                    logger.warning(f"Résultat vide pour le fichier {file_info.filename}")

            except zipfile.BadZipFile:
                logger.error(f"Erreur lors de la conversion du fichier {file_info.filename} : Le fichier est corrompu ou n'est pas un fichier zip valide")
            except Exception as e:
                logger.error(f"Erreur lors de la conversion du fichier {file_info.filename} : {str(e)}")

    logger.info(f"Total des fichiers valides dans le zip : {valid_files}")
    logger.info(f"Fichiers traités avec succès : {processed_files}")
    return results
