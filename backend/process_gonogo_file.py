import json
import logging
import os
import time
import asyncio

from botocore.exceptions import NoCredentialsError
from docx import Document
from docx.shared import Pt
from dotenv import load_dotenv
from openai import OpenAI, AsyncOpenAI
from backend.s3_config import put_object

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def prepare_fine_tuning_data(results):
    fine_tuning_data = []
    for item in results:
        fine_tuning_data.append({
            "messages": [
                {"role": "system", "content": "Vous êtes un expert en bureau d'études, capable d'analyser des documents techniques et de fournir des analyses détaillées. BU: '', Métier / Société: '', Donneur d'ordres: '', Opportunité: '', Calendrier: { Date limite de remise des offres: '', Début de la prestation: '', Délai de validité des offres: '', Autres dates importantes: [] }, Critères d'attribution: [], Description de l'offre: { Durée: '', Synthèse Lot: '', CA TOTAL offensif: '', Missions générales: [], Matériels à disposition: [] }, Objet du marché: '', Périmètre de la consultation: '', Description des prestations: [], Exigences: [], Missions et compétences attendues: [], Profil des hôtes ou hôtesses d'accueil: { Qualités: [], Compétences nécessaires: [] }, Plages horaires: [], PSE: '', Formations: [], Intérêt pour le groupe: { Forces: [], Faiblesses: [], Opportunités: [], Menaces: [] }, Formule de révision des prix: ''"},
                {"role": "user", "content": f"Analysez le contenu suivant : {item}"},
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
        with open(file_path, 'rb') as file:
            response = client.files.create(file=file, purpose='fine-tune')
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

def split_content(content, max_tokens=4000):
    if not isinstance(content, str):
        content = json.dumps(content, indent=2)

    words = content.split()
    chunks = []
    current_chunk = []
    current_length = 0

    for word in words:
        if current_length + len(word) + 1 > max_tokens:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_length = len(word)
        else:
            current_chunk.append(word)
            current_length += len(word) + 1

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks

async def get_chatgpt_response_async(client, chunk):
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Vous êtes un assistant d'analyse de documents."},
                {"role": "user", "content": f"Analysez le contenu suivant : {chunk}"}
            ]
        )
        chatgpt_response = response.choices[0].message.content
        logger.debug(f"Réponse brute de ChatGPT : {chatgpt_response}")
        return {"analyse": chatgpt_response}
    except Exception as e:
        logger.error(f"Erreur lors de l'appel à l'API ChatGPT : {str(e)}", exc_info=True)
        return {"erreur": str(e)}

async def process_chunks(chunks):
    client = AsyncOpenAI()
    tasks = [get_chatgpt_response_async(client, chunk) for chunk in chunks]
    return await asyncio.gather(*tasks)

def upload_to_s3(local_file, s3_file):
    try:
        with open(local_file, 'rb') as file:
            file_data = file.read()
            content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            if put_object('jobpilot', s3_file, file_data, len(file_data), content_type):
                return s3_file
            else:
                logger.error(f"Échec de l'upload du fichier {local_file} sur MinIO")
                return s3_file
    except Exception as e:
        logger.error(f"Erreur lors de l'upload vers MinIO : {str(e)}")
        return False

def download_from_s3(s3_file, local_file):
    try:
        s3_client.download_file("jobpilot", s3_file, local_file)
        logger.info(f"Fichier {s3_file} téléchargé depuis S3 avec succès")
        return True
    except NoCredentialsError:
        logger.error("Identifiants non valides pour accéder à S3")
        return False

def create_word_document(chatgpt_analysis):
    try:
        doc = Document()
        file_path = f"analyse_{int(time.time())}.docx"

        if isinstance(chatgpt_analysis, str):
            chatgpt_analysis = json.loads(chatgpt_analysis)

        def add_heading(text, level):
            heading = doc.add_heading(text, level=level)
            heading.style.font.size = Pt(14 - level)

        def add_paragraph(text):
            p = doc.add_paragraph(text)
            p.style.font.size = Pt(11)

        def add_list(items):
            for item in items:
                p = doc.add_paragraph(item, style='List Bullet')
                p.style.font.size = Pt(11)

        add_heading("Analyse ChatGPT", 0)

        for key, value in chatgpt_analysis.items():
            add_heading(key, 1)
            if isinstance(value, str):
                add_paragraph(value)
            elif isinstance(value, list):
                add_list(value)
            elif isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    add_paragraph(f"{sub_key}:")
                    if isinstance(sub_value, list):
                        add_list(sub_value)
                    else:
                        add_paragraph(str(sub_value))

        doc.save(file_path)
        logger.info(f"Document Word créé avec succès : {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Erreur lors de la création du document Word : {str(e)}")
        raise

def split_results(results, max_tokens):
    parts = []
    current_part = []
    current_tokens = 0

    for result in results:
        result_tokens = len(json.dumps(result)) // 8
        if current_tokens + result_tokens > max_tokens:
            parts.append(current_part)
            current_part = []
            current_tokens = 0
        current_part.append(result)
        current_tokens += result_tokens

    if current_part:
        parts.append(current_part)

    return parts

def merge_analyses(analyses):
    merged = {
        "BU": "",
        "Métier / Société": "",
        "Donneur d'ordres": "",
        "Opportunité": "",
        "Calendrier": {
            "Date limite de remise des offres": "",
            "Début de la prestation": "",
            "Délai de validité des offres": "",
            "Autres dates importantes": []
        },
        "Critères d'attribution": [],
        "Description de l'offre": {
            "Durée": "",
            "Synthèse Lot": "",
            "CA TOTAL offensif": "",
            "Missions générales": [],
            "Matériels à disposition": []
        },
        "Objet du marché": "",
        "Périmètre de la consultation": "",
        "Description des prestations": [],
        "Exigences": [],
        "Missions et compétences attendues": [],
        "Profil des hôtes ou hôtesses d'accueil": {
            "Qualités": [],
            "Compétences nécessaires": []
        },
        "Plages horaires": [],
        "PSE": "",
        "Formations": [],
        "Intérêt pour le groupe": {
            "Forces": [],
            "Faiblesses": [],
            "Opportunités": [],
            "Menaces": []
        },
        "Formule de révision des prix": ""
    }

    for analysis in analyses:
        if isinstance(analysis, str):
            try:
                analysis_dict = json.loads(analysis)
            except json.JSONDecodeError:
                logger.warning(f"Impossible de décoder l'analyse JSON : {analysis}")
                continue
        elif isinstance(analysis, dict):
            analysis_dict = analysis
        else:
            logger.warning(f"Type d'analyse inattendu : {type(analysis)}")
            continue

        for key, value in analysis_dict.items():
            if isinstance(value, list):
                merged[key].extend(value)
            elif isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, list):
                        merged[key][sub_key].extend(sub_value)
                    else:
                        merged[key][sub_key] = sub_value
            else:
                merged[key] = value

    return merged

async def process_gonogo_file(results):
    try:
        logger.info("Début du traitement des résultats")

        all_analyses = []
        for result in results:
            content = json.dumps(result, indent=2)
            chunks = split_content(content)
            
            chunk_analyses = await process_chunks(chunks)
            
            valid_analyses = [analysis["analyse"] for analysis in chunk_analyses if "erreur" not in analysis]
            if valid_analyses:
                merged_analysis = merge_analyses(valid_analyses)
                all_analyses.append(merged_analysis)

        final_analysis = merge_analyses(all_analyses)

        word_document = create_word_document(final_analysis)
        logger.info(f"Document Word créé avec succès : {word_document}")

        s3_file_path = upload_to_s3(word_document, f"analyses/{os.path.basename(word_document)}")
        logger.info(f"Document Word uploadé vers MinIO : {s3_file_path}")

        if word_document:
            os.remove(word_document)
            logger.info(f"Fichier temporaire {word_document} supprimé")

        return {
            "message": "Traitement terminé avec succès",
            "chatgpt_analysis": final_analysis,
            "word_document": s3_file_path
        }
    except Exception as e:
        logger.error(f"Erreur lors du traitement : {str(e)}", exc_info=True)
        return {"error": str(e)}

def read_jsonl_file(file_path):
    logging.info(f"Tentative de lecture du fichier : {file_path}")
    try:
        local_file = 'temp_jsonl_file.jsonl'
        if download_from_s3(file_path, local_file):
            with open(local_file, 'r') as file:
                content = [json.loads(line) for line in file]
            os.remove(local_file)
            logging.info(f"Fichier {file_path} lu avec succès depuis S3.")
            return content
        else:
            logging.error(f"Impossible de télécharger le fichier {file_path} depuis S3.")
    except Exception as e:
        logging.error(f"Erreur inattendue lors de la lecture du fichier {file_path} : {str(e)}")
    return None
