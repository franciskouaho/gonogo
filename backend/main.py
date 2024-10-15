import zipfile
from io import BytesIO
import os
import logging
import pdfplumber
import openpyxl
from openai import OpenAI
from dotenv import load_dotenv

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from backend.convert_to_pdf import convert_to_pdf

logger = logging.getLogger(__name__)

app = FastAPI()

origins = [
    "http://localhost:3000",
    "https://emplica.fr",
]

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_text_from_pdf(pdf_content):
    text = ""
    with pdfplumber.open(BytesIO(pdf_content)) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text

def split_text_into_chunks(text, max_tokens=1500):
    words = text.split()
    for i in range(0, len(words), max_tokens):
        yield " ".join(words[i:i + max_tokens])

def analyze_content_with_gpt(client, file_name: str, content: str):
    if "rc" in file_name.lower() or "ae" in file_name.lower():
        prompt = (
            f"Veuillez extraire les informations suivantes du contenu fourni :\n"
            f"- Calendrier des dates clés (Date limite de remise des offres, Invitation à soumissionner, "
            f"Remise des livrables, Démarrage, Durée du marché, Notification, etc.).\n"
            f"- Critères d'attribution (Références, Organisation de l'agence, Moyens humains, Moyens techniques, "
            f"Certificat et agrément), avec pourcentages si disponibles.\n"
            f"- Informations sur le démarrage des prestations, problèmes potentiels et formations requises.\n\n"
            f"Contenu :\n"
        )
    elif "ccap" in file_name:
        prompt = (
            f"Veuillez extraire les informations suivantes de ce contenu :\n"
            f"Prix du marché, prestations attendues, tranches et options, prestations supplémentaires, "
            f"durée du marché, équipes (responsable d’équipe, chef d’équipe), formations, "
            f"révisions de prix, conditions de paiement, pénalités, qualité, "
            f"formule de révision (exemple : P = Po x [0,2 + 0,8 Im-4 / I0-4]), "
            f"RSE, clause de réexamen pour modifications d'équipement.\n"
            f"Ne pas inventer de données ou faire d'hypothèses, mais se limiter à ce qui est écrit.\n\nContenu :\n"
        )
    elif "cctp" in file_name:
        prompt = (
            f"Veuillez extraire les informations suivantes de ce contenu :\n"
            f"Périmètre géographique (localisation), horaires d'ouvertures, missions, prestations attendues, "
            f"composition des équipes, équipements à fournir, PSE, pénalités, "
            f"et tout détail lié aux processus opérationnels.\n\nContenu :\n"
        )
    elif "bpu" in file_name:
        prompt = (
            f"Veuillez extraire les informations suivantes de ce contenu :\n"
            f"Nombre d'agents, CDI, CDD, et tous autres détails sur le personnel.\n\nContenu :\n"
        )
    else:
        logger.info(f"File '{file_name}' did not match any known types. Skipping.")
        return {"filename": file_name, "info": "Type de fichier non reconnu pour l'extraction."}

    results = []
    try:
        for chunk in split_text_into_chunks(content):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Vous êtes un analyseur de documents."},
                    {"role": "user", "content": prompt + chunk}
                ],
                max_tokens=1000,
                temperature=0.5
            )
            gpt_summary = response.choices[0].message.content
            results.append(gpt_summary)

        print(f"Results for file '{file_name}':", " ".join(results))

        return {"filename": file_name, "info": " ".join(results)}
    except Exception as e:
        logger.error(f"Error extracting information with GPT for file '{file_name}': {e}")
        return {"filename": file_name, "info": "Error during GPT analysis."}

@app.post("/read-file")
async def match(zip_file: UploadFile = File(...)):
    logger.info(f"Received file: {zip_file.filename}")

    content = await zip_file.read()
    zip_content = BytesIO(content)
    processed_files = []
    missing_info_files = []
    unrecognized_files = []

    with zipfile.ZipFile(zip_content, 'r') as z:
        file_list = z.namelist()

        for file_name in file_list:
            if (
                file_name.endswith('/') or  # directories
                "__MACOSX" in file_name or  # Mac system files
                file_name.startswith('.') or  # hidden files (e.g., .DS_Store)
                file_name.startswith('._') or  # Mac resource fork files
                file_name.startswith('~$') or   # temporary Office files
                file_name.endswith('.DS_Store')  # Specific .DS_Store files

            ):
                logger.info(f"Skipping directory or unwanted file: {file_name}")
                continue

            with z.open(file_name) as extracted_file:
                file_data = extracted_file.read()

                if file_name.lower().endswith('.xlsx'):
                    try:
                        workbook = openpyxl.load_workbook(BytesIO(file_data))
                    except Exception as e:
                        logger.error(f"Invalid .xlsx file '{file_name}': {str(e)}")
                        continue

                if not file_name.lower().endswith('.pdf'):
                    try:
                        file_data = convert_to_pdf(file_name, file_data)
                        file_name = f"{file_name}.pdf"
                    except ValueError as e:
                        logger.error(f"Error converting file {file_name}: {str(e)}")
                        continue

                processed_files.append({"filename": file_name, "content": file_data})

                file_name_lower = file_name.lower()
                if any(keyword in file_name_lower for keyword in ["rc", "ccap", "cctp", "bpu"]):
                    missing_info_files.append(file_name)
                else:
                    unrecognized_files.append(file_name)

    results = []
    for file in processed_files:
        file_name = file["filename"].lower()
        file_content = extract_text_from_pdf(file["content"])

        analysis_result = analyze_content_with_gpt(client,file_name, file_content)
        results.append(analysis_result)

    if missing_info_files:
        missing_info_message = (
            f"Some information might be missing for the following files: {', '.join(missing_info_files)}"
        )
    else:
        missing_info_message = "All files processed without missing information."

    if unrecognized_files:
        unrecognized_files_message = (
            f"The following files were not recognized for extraction: {', '.join(unrecognized_files)}"
        )
    else:
        unrecognized_files_message = "All files were recognized for extraction."

    return {
        "message": f"{len(results)} files processed and analyzed.",
        "results": results,
        "missing_info_message": missing_info_message,
        "unrecognized_files_message": unrecognized_files_message
    }
