import json
import logging
import os
import time

from docx import Document
from docx.shared import Pt
from dotenv import load_dotenv
from openai import OpenAI
from backend.s3_config import put_object

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

gonogo_path = 'backend/gonogo_data.jsonl'

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

def get_chatgpt_response(results):
    try:
        with open(gonogo_path, 'r', encoding='utf-8') as f:
            gonogo_example = json.load(f)

        prompt = """Analysez les documents suivants et extrayez les informations selon la structure exacte ci-dessous. Si une information n'est pas disponible, laissez le champ vide. Utilisez le format JSON pour la réponse.

        Structure à suivre :
        {
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

        Exemple de structure (à adapter selon le contenu réel) :
        """
        prompt += json.dumps(gonogo_example, ensure_ascii=False, indent=2)

        prompt += "\n\nMaintenant, analysez les fichiers suivants en utilisant la même structure :\n\n"

        for item in results:
            prompt += f"Fichier: {item['file']}\n"
            content = item['content']
            if isinstance(content, str):
                content_summary = content[:3000]
            elif isinstance(content, dict):
                content_summary = json.dumps(content, ensure_ascii=False)[:3000]
            else:
                content_summary = str(content)[:3000]
            prompt += f"Contenu: {content_summary}...\n\n"

        response = client.chat.completions.create(
            model="gpt-3.5-turbo-16k",
            messages=[
                {"role": "system", "content": "Vous êtes un expert en analyse de documents d'appels d'offres, capable d'extraire des informations structurées selon un format spécifique."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000,
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Erreur dans l'appel API : {str(e)}")
        raise

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

        # Fonction pour ajouter un titre
        def add_heading(text, level):
            heading = doc.add_heading(text, level=level)
            heading.style.font.size = Pt(14 - level)  # Ajuster la taille en fonction du niveau

        # Fonction pour ajouter un paragraphe
        def add_paragraph(text):
            p = doc.add_paragraph(text)
            p.style.font.size = Pt(11)

        # Fonction pour ajouter une liste
        def add_list(items):
            for item in items:
                p = doc.add_paragraph(item, style='List Bullet')
                p.style.font.size = Pt(11)

        # Titre principal
        add_heading("Analyse ChatGPT", 0)

        # Informations générales
        add_heading("Informations générales", 1)
        for key, value in chatgpt_analysis.items():
            if isinstance(value, str):
                add_paragraph(f"{key}: {value}")

        # Calendrier
        add_heading("Calendrier", 1)
        for key, value in chatgpt_analysis['Calendrier'].items():
            if isinstance(value, str):
                add_paragraph(f"{key}: {value}")
            elif isinstance(value, list):
                add_paragraph(f"{key}:")
                add_list(value)

        # Critères d'attribution
        add_heading("Critères d'attribution", 1)
        if chatgpt_analysis["Critères d'attribution"]:
            add_list(chatgpt_analysis["Critères d'attribution"])
        else:
            add_paragraph("Aucun critère d'attribution n'est spécifié.")

        # Description de l'offre
        add_heading("Description de l'offre", 1)
        for key, value in chatgpt_analysis["Description de l'offre"].items():
            if isinstance(value, str):
                add_paragraph(f"{key}: {value}")
            elif isinstance(value, list):
                add_paragraph(f"{key}:")
                add_list(value)

        # Description des prestations
        add_heading("Description des prestations", 1)
        if chatgpt_analysis["Description des prestations"]:
            add_list(chatgpt_analysis["Description des prestations"])
        else:
            add_paragraph("Aucune description des prestations n'est disponible.")

        # Exigences
        add_heading("Exigences", 1)
        if chatgpt_analysis["Exigences"]:
            add_list(chatgpt_analysis["Exigences"])
        else:
            add_paragraph("Aucune exigence n'est spécifiée.")

        # Missions et compétences attendues
        add_heading("Missions et compétences attendues", 1)
        if chatgpt_analysis["Missions et compétences attendues"]:
            add_list(chatgpt_analysis["Missions et compétences attendues"])
        else:
            add_paragraph("Aucune mission ou compétence attendue n'est spécifiée.")

        # Profil des hôtes ou hôtesses d'accueil
        add_heading("Profil des hôtes ou hôtesses d'accueil", 1)
        for key, value in chatgpt_analysis["Profil des hôtes ou hôtesses d'accueil"].items():
            add_paragraph(f"{key}:")
            if value:
                add_list(value)
            else:
                add_paragraph("Aucune information disponible.")

        # Plages horaires
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

        # PSE
        add_heading("PSE", 1)
        add_paragraph(chatgpt_analysis["PSE"] if chatgpt_analysis["PSE"] else "Aucune information PSE disponible.")

        # Formations
        add_heading("Formations", 1)
        if chatgpt_analysis["Formations"]:
            add_list(chatgpt_analysis["Formations"])
        else:
            add_paragraph("Aucune information sur les formations n'est disponible.")

        # Intérêt pour le groupe
        add_heading("Intérêt pour le groupe", 1)
        for key, value in chatgpt_analysis["Intérêt pour le groupe"].items():
            add_paragraph(f"{key}:")
            if value:
                add_list(value)
            else:
                add_paragraph("Aucune information disponible.")

        # Formule de révision des prix
        add_heading("Formule de révision des prix", 1)
        add_paragraph(chatgpt_analysis["Formule de révision des prix"] if chatgpt_analysis["Formule de révision des prix"] else "Aucune formule de révision des prix spécifiée.")

        # Sauvegarde du document
        doc.save(file_path)
        logger.info(f"Document Word créé avec succès : {file_path}")
    except Exception as e:
        logger.error(f"Erreur lors de la création du document Word : {str(e)}")
        raise

def process_gonogo_file(results):
    try:
        logger.info(f"Début du traitement des résultats")

        chatgpt_analysis = get_chatgpt_response(results)
        logger.info("Analyse ChatGPT obtenue")

        # Parser la réponse JSON
        structured_analysis = json.loads(chatgpt_analysis)

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

        # Création du document Word
        word_file_path = 'chatgpt_analysis.docx'
        create_word_document(structured_analysis, word_file_path)

        # Upload du fichier Word vers MinIO
        if upload_to_s3(word_file_path, f"documents/{word_file_path}"):
            logger.info(f"Document Word uploadé vers MinIO : documents/{word_file_path}")
        else:
            logger.error("Échec de l'upload du document Word vers MinIO")

        return {
            "message": f"Fine-tuning démarré avec succès. Statut actuel : {status}",
            "fine_tune_id": fine_tune_id,
            "chatgpt_analysis": structured_analysis,
            "word_document": f"documents/{word_file_path}"
        }

    except json.JSONDecodeError:
        logger.error("Erreur lors du parsing de la réponse ChatGPT")
        return {"error": "Erreur lors de l'analyse structurée des documents"}
    except Exception as e:
        logger.exception(f"Erreur lors du traitement : {str(e)}")
        return {"error": f"Erreur lors du traitement : {str(e)}"}
    finally:
        if 'jsonl_filename' in locals() and os.path.exists(jsonl_filename):
            os.remove(jsonl_filename)
            logger.info(f"Fichier temporaire {jsonl_filename} supprimé")
        # Nettoyage des fichiers temporaires
        if os.path.exists(word_file_path):
            os.remove(word_file_path)
            logger.info(f"Fichier temporaire {word_file_path} supprimé")

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
