import json
import logging
import os
import tempfile
from fastapi import UploadFile
from backend.s3_config import get_json_object, put_object, get_presigned_url
from io import BytesIO

from docx import Document
from dotenv import load_dotenv
from openai import OpenAI

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

gonogo_path = 'backend/GoNoGo.json'

def prepare_fine_tuning_data(results):
    fine_tuning_data = []
    for item in results:
        fine_tuning_data.append({
            "messages": [
                {"role": "system", "content": "Vous êtes un expert en bureau d'études, capable d'analyser des documents techniques et de fournir des analyses détaillées."},
                {"role": "user", "content": f"Analysez le contenu suivant : {item['content']}"},
                {"role": "assistant", "content": "Voici l'analyse du contenu fourni : [Insérez ici une analyse détaillée]"}
            ]
        })
    return fine_tuning_data

def save_jsonl(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        for item in data:
            json.dump(item, f, ensure_ascii=False)
            f.write('\n')

def upload_file_for_fine_tuning(file_path):
    try:
        file_content = get_json_object('jobpilot', file_path)

        file_object = BytesIO(json.dumps(file_content).encode('utf-8'))

        response = client.files.create(file=file_object, purpose='fine-tune')
        return response.id
    except Exception as e:
        logger.error(f"Erreur lors du téléchargement du fichier : {str(e)}")
        return None

def start_fine_tuning(file_id):
    try:
        response = client.fine_tuning.jobs.create(training_file=file_id, model="gpt-3.5-turbo")
        return response.id
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du fine-tuning : {str(e)}")
        return None

def get_chatgpt_response(results):
    try:
        with open(gonogo_path, 'r', encoding='utf-8') as f:
            gonogo_example = json.load(f)
            print(f"Exemple GoNoGo chargé avec succès. Nombre de messages : {len(gonogo_example)}")

        prompt = """T'es un expert en bureau d'études. Commence par extraire précisément les informations techniques et les données clés du document A. Analyse ensuite comment ces données sont réutilisées et transformées dans le document B, en respectant les spécifications techniques et les normes en vigueur...(line too long; chars omitted)

        Voici un exemple de structure d'analyse basé sur le fichier GoNoGo.json :
        """
        prompt += json.dumps(gonogo_example, ensure_ascii=False, indent=2)

        prompt += "\n\nMaintenant, analysez les fichiers suivants en utilisant la même structure avec des exemples de contenu basés sur le fichier GoNoGo.json :\n\n"

        for item in results:
            prompt += f"Fichier: {item['file']}\n"
            content_summary = json.dumps(item['content'], ensure_ascii=False)[:500]
            prompt += f"Contenu: {content_summary}...\n\n"


        print(f"Prompt généré avec succès. Longueur : {prompt}")

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Vous êtes un expert en bureau d'études, capable d'analyser des documents techniques et de fournir des analyses détaillées."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Erreur dans l'appel API : {str(e)}")
        raise

def process_gonogo_file(file: UploadFile):
    logger.info(f"Début du traitement du fichier : {file.filename}")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
            temp_file_path = temp_file.name
            content = file.file.read()
            temp_file.write(content)
        logger.info(f"Fichier temporaire créé : {temp_file_path}")

        logger.info("Traitement du fichier ZIP en cours...")

        doc = Document()
        doc.add_heading('Analyse du fichier', 0)
        doc.add_paragraph(f'Analyse du fichier {file.filename} complétée.')
        logger.info("Document Word créé")

        word_filename = "analyse_result.docx"
        word_temp_path = f"/tmp/{word_filename}"
        doc.save(word_temp_path)
        logger.info(f"Document Word sauvegardé temporairement : {word_temp_path}")

        with open(word_temp_path, 'rb') as word_file:
            contenu = word_file.read()
            longueur = len(contenu)
            type_contenu = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            put_object('jobpilot', word_filename, contenu, longueur, type_contenu)
        logger.info(f"Document Word uploadé dans Minio : {word_filename}")

        download_url = get_presigned_url('jobpilot', word_filename)
        logger.info(f"URL présignée générée : {download_url}")

        download_url = download_url.replace("http://minio:9000", "http://127.0.0.1:9001")
        logger.info(f"URL modifiée : {download_url}")

        os.unlink(temp_file_path)
        os.unlink(word_temp_path)
        logger.info("Fichiers temporaires supprimés")

        return {"word_document_url": download_url}  # Modifié ici

    except Exception as e:
        logger.error(f"Erreur lors du traitement : {str(e)}", exc_info=True)
        raise

def read_jsonl_file(file_path):
    logging.info(f"Tentative de lecture du fichier depuis Minio : {file_path}")
    try:
        content = get_json_object('jobpilot', file_path)
        logging.info(f"Fichier {file_path} lu avec succès depuis Minio.")
        return json.dumps(content, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Erreur lors de la lecture du fichier {file_path} depuis Minio : {str(e)}")
    return None

def create_word_document(content, output_file):
    doc = Document()

    doc.add_heading('Contenu JSONL', 0)

    for line in content.split('\n'):
        doc.add_paragraph(line)

    doc.save(output_file)
    logging.info(f"Document Word créé : {output_file}")

jsonl_file_path = 'gonogo_data.jsonl'
jsonl_content = read_jsonl_file(jsonl_file_path)

if jsonl_content:
    word_file_path = 'gonogo_data_content.docx'
    create_word_document(jsonl_content, word_file_path)
    with open(word_file_path, 'rb') as word_file:
        contenu = word_file.read()
        longueur = len(contenu)
        type_contenu = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        put_object('jobpilot', word_file_path, contenu, longueur, type_contenu)

    logger.info(f"Document Word sauvegardé dans Minio : {word_file_path}")
    os.remove(word_file_path)
else:
    logging.error("Impossible de créer le document Word car le contenu JSONL n'a pas pu être lu depuis Minio.")
