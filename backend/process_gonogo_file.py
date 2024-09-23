import json
import logging
import os
import time
import tiktoken

from botocore.exceptions import NoCredentialsError
from docx import Document
from docx.shared import Pt
from dotenv import load_dotenv
from openai import OpenAI
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

def get_chatgpt_response(part):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Vous êtes un assistant spécialisé dans l'analyse de documents techniques. Veuillez fournir une analyse structurée au format JSON."},
                {"role": "user", "content": f"Analysez le contenu suivant et retournez le résultat au format JSON : {part}"}
            ]
        )
        chatgpt_response = response.choices[0].message.content
        logger.info(f"Réponse brute de ChatGPT : {chatgpt_response}")
        
        # Tentative de parsing JSON
        try:
            json_response = json.loads(chatgpt_response)
            return json_response
        except json.JSONDecodeError:
            logger.warning("La réponse n'est pas au format JSON. Traitement comme texte brut.")
            return {"analyse_brute": chatgpt_response}
    except Exception as e:
        logger.error(f"Erreur lors de l'appel à l'API ChatGPT : {str(e)}")
        return {"erreur": str(e)}

def upload_to_s3(local_file, s3_file):
    try:
        with open(local_file, 'rb') as file:
            file_data = file.read()
            content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            if put_object('jobpilot', s3_file, file_data, len(file_data), content_type):
                logger.info(f"Fichier {local_file} téléchargé sur MinIO avec succès")
                return True
            else:
                logger.error(f"Échec de l'upload du fichier {local_file} sur MinIO")
                return False
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

def create_word_document(chatgpt_analysis, file_path):
    try:
        doc = Document()

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

        add_heading("Informations générales", 1)
        for key, value in chatgpt_analysis.items():
            if isinstance(value, str):
                add_paragraph(f"{key}: {value}")

        add_heading("Calendrier", 1)
        for key, value in chatgpt_analysis['Calendrier'].items():
            if isinstance(value, str):
                add_paragraph(f"{key}: {value}")
            elif isinstance(value, list):
                add_paragraph(f"{key}:")
                add_list(value)

        add_heading("Critères d'attribution", 1)
        if chatgpt_analysis["Critères d'attribution"]:
            add_list(chatgpt_analysis["Critères d'attribution"])
        else:
            add_paragraph("Aucun critère d'attribution n'est spécifié.")

        add_heading("Description de l'offre", 1)
        for key, value in chatgpt_analysis["Description de l'offre"].items():
            if isinstance(value, str):
                add_paragraph(f"{key}: {value}")
            elif isinstance(value, list):
                add_paragraph(f"{key}:")
                add_list(value)

        add_heading("Description des prestations", 1)
        if chatgpt_analysis["Description des prestations"]:
            add_list(chatgpt_analysis["Description des prestations"])
        else:
            add_paragraph("Aucune description des prestations n'est disponible.")

        add_heading("Exigences", 1)
        if chatgpt_analysis["Exigences"]:
            add_list(chatgpt_analysis["Exigences"])
        else:
            add_paragraph("Aucune exigence n'est spécifiée.")

        add_heading("Missions et compétences attendues", 1)
        if chatgpt_analysis["Missions et compétences attendues"]:
            add_list(chatgpt_analysis["Missions et compétences attendues"])
        else:
            add_paragraph("Aucune mission ou compétence attendue n'est spécifiée.")

        add_heading("Profil des hôtes ou hôtesses d'accueil", 1)
        for key, value in chatgpt_analysis["Profil des hôtes ou hôtesses d'accueil"].items():
            add_paragraph(f"{key}:")
            if value:
                add_list(value)
            else:
                add_paragraph("Aucune information disponible.")

        add_heading("Plages horaires", 1)
        if chatgpt_analysis["Plages horaires"]:
            headers = ["Horaires", "Jour", "Accueil physique", "Accueil téléphonique", "Gestion colis *", "Gestion courrier", "Bilingue", "Campus"]
            table = doc.add_table(rows=1, cols=len(headers))
            table.style = 'Table Grid'
            hdr_cells = table.rows[0].cells
            for i, header in enumerate(headers):
                hdr_cells[i].text = header
            for plage in chatgpt_analysis["Plages horaires"]:
                row_cells = table.add_row().cells
                for i, key in enumerate(headers):
                    row_cells[i].text = str(plage.get(key, ''))  # Utilisation de .get() avec une valeur par défaut
        else:
            add_paragraph("Aucune information sur les plages horaires n'est disponible.")

        add_heading("PSE", 1)
        add_paragraph(chatgpt_analysis["PSE"] if chatgpt_analysis["PSE"] else "Aucune information PSE disponible.")

        add_heading("Formations", 1)
        if chatgpt_analysis["Formations"]:
            add_list(chatgpt_analysis["Formations"])
        else:
            add_paragraph("Aucune information sur les formations n'est disponible.")

        add_heading("Intérêt pour le groupe", 1)
        for key, value in chatgpt_analysis["Intérêt pour le groupe"].items():
            add_paragraph(f"{key}:")
            if value:
                add_list(value)
            else:
                add_paragraph("Aucune information disponible.")

        add_heading("Formule de révision des prix", 1)
        add_paragraph(chatgpt_analysis["Formule de révision des prix"] if chatgpt_analysis["Formule de révision des prix"] else "Aucune formule de révision des prix spécifiée.")

        doc.save(file_path)
        logger.info(f"Document Word créé avec succès : {file_path}")
    except Exception as e:
        logger.error(f"Erreur lors de la création du document Word : {str(e)}")
        raise

def num_tokens_from_string(string: str, encoding_name: str = "cl100k_base") -> int:
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

def split_results(results, max_tokens):
    parts = []
    current_part = []
    current_tokens = 0

    for result in results:
        result_tokens = num_tokens_from_string(json.dumps(result))
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
        for key, value in analysis.items():
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

def process_gonogo_file(results):
    try:
        logger.info(f"Début du traitement des résultats")

        max_tokens = 8000  # Réduire la taille maximale des tokens
        result_parts = split_results(results, max_tokens)

        all_analyses = []
        for part in result_parts:
            chatgpt_analysis = get_chatgpt_response(part)
            
            # Vérifier si la réponse est un dictionnaire et contient la clé 'analysis'
            if isinstance(chatgpt_analysis, dict):
                if 'analysis' in chatgpt_analysis:
                    all_analyses.append(chatgpt_analysis['analysis'])
                elif 'analyse' in chatgpt_analysis:  # Pour gérer les réponses en français
                    all_analyses.append(chatgpt_analysis['analyse'])
                else:
                    all_analyses.append(chatgpt_analysis)
            else:
                all_analyses.append({"analyse_brute": str(chatgpt_analysis)})

        merged_analysis = merge_analyses(all_analyses)

        fine_tuning_data = prepare_fine_tuning_data(results)
        logger.info(f"Données préparées pour le fine-tuning. Nombre d'exemples : {len(fine_tuning_data)}")

        jsonl_filename = "gonogo_data.jsonl"
        save_jsonl(fine_tuning_data, jsonl_filename)
        logger.info(f"Données sauvegardées dans {jsonl_filename}")

        file_id = upload_file_for_fine_tuning(jsonl_filename)
        if not file_id:
            logger.error("Échec du téléchargement du fichier")
            return {"error": "Échec du téléchargement du fichier"}
        logger.info(f"Fichier téléchargé avec succès. ID : {file_id}")

        fine_tune_id = start_fine_tuning(file_id)
        if not fine_tune_id:
            logger.error("Échec du démarrage du fine-tuning")
            return {"error": "Échec du démarrage du fine-tuning"}
        logger.info(f"Fine-tuning démarré avec succès. ID : {fine_tune_id}")

        time.sleep(2)

        status = client.fine_tuning.jobs.retrieve(fine_tune_id).status

        word_file_path = 'chatgpt_analysis.docx'
        create_word_document(merged_analysis, word_file_path)
        logger.info(f"Document Word créé avec succès : {word_file_path}")

        if upload_to_s3(word_file_path, f"documents/{word_file_path}"):
            logger.info(f"Document Word uploadé vers MinIO : documents/{word_file_path}")
        else:
            logger.error("Échec de l'upload du document Word vers MinIO")

        os.remove(jsonl_filename)
        os.remove(word_file_path)
        logger.info(f"Fichier temporaire {jsonl_filename} supprimé")
        logger.info(f"Fichier temporaire {word_file_path} supprimé")

        return {
            "message": f"Fine-tuning démarré avec succès. Statut actuel : {status}",
            "fine_tune_id": fine_tune_id,
            "chatgpt_analysis": merged_analysis,
            "word_document": f"documents/{word_file_path}"
        }
    except Exception as e:
        logger.error(f"Erreur lors du traitement : {str(e)}")
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
