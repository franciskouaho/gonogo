import re
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
from .convert_to_pdf import convert_to_pdf

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

def analyze_content_with_gpt(client, file_name: str, content: str, variables: dict):
    """
    Analyse the content of a document and fills the corresponding variables.
    Variables will not be overwritten by empty values.
    """

    # Prompts based on the document type
    if "rc" in file_name.lower() or "ae" in file_name.lower() or "Reglement de la consultation" in file_name.lower():
        prompt = (
            f"Veuillez extraire les informations suivantes du contenu fourni :\n"
            f"- Calendrier des dates clés (Date limite de remise des offres, Invitation à soumissionner, "
            f"Remise des livrables, Démarrage, Durée du marché, Notification, etc.).\n"
            f"- Critères d'attribution (Références, Organisation de l'agence, Moyens humains, Moyens techniques, "
            f"Certificat et agrément), avec pourcentages si disponibles.\n"
            f"- Informations sur le démarrage des prestations, problèmes potentiels et formations requises.\n\n"
            f"Ne remplacez jamais les informations existantes par une valeur vide. Laissez une information vide si elle n'est pas présente."
        )
    elif "ccap" in file_name:
        prompt = (
            f"Veuillez extraire les informations suivantes de ce contenu :\n"
            f"Prix du marché, prestations attendues, tranches et options, prestations supplémentaires, "
            f"durée du marché, équipes (responsable d’équipe, chef d’équipe), formations, "
            f"Veuillez extraire **toutes** les pénalités mentionnées, même si elles apparaissent à plusieurs endroits. Retournez-les comme une liste séparée par des points.\n"
            f"révisions de prix, conditions de paiement, pénalités, qualité, "

            f"formule de révision commençant par P =  , prenez-la exactement comme c'est écrit et donnez les définitions si elles sont présentes dans le document, "
            f"RSE, clause de réexamen pour modifications d'équipement.\n"
            f"Ne remplacez jamais les informations existantes par une valeur vide."
        )
    elif "cctp" in file_name:
        prompt = (
            f"Veuillez extraire les informations suivantes de ce contenu :\n"
            f"Périmètre géographique (localisation), horaires d'ouvertures, missions, prestations attendues, "
            f"Veuillez extraire **toutes** les pénalités mentionnées, même si elles apparaissent à plusieurs endroits. Retournez-les comme une liste séparée par des points.\n"
            f"composition des équipes, équipements à fournir, PSE, pénalités, "
            f"et tout détail lié aux processus opérationnels.\n\n"
            f"Ne remplacez jamais les informations existantes par une valeur vide."
        )
    elif "bpu" in file_name:
        prompt = (
            f"Veuillez extraire les informations suivantes de ce contenu :\n"
            f"Nombre d'agents, CDI, CDD, et tous autres détails sur le personnel.\n\n"
            f"Ne remplacez jamais les informations existantes par une valeur vide."
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

        return {"filename": file_name, "info": " ".join(results)}
    except Exception as e:
        logger.error(f"Error extracting information with GPT for file '{file_name}': {e}")
        return {"filename": file_name, "info": "Error during GPT analysis."}


def extract_revision_prix(text):
    # Rechercher la section contenant la formule et les définitions
    formula_pattern = re.compile(r"Formule de révision\s*:\s*(P\s*=\s*Po\s*\*\s*\(.*?\))", re.IGNORECASE)
    definitions_pattern = re.compile(r"Définitions\s*:\s*(.*?)\n\n", re.IGNORECASE | re.DOTALL)

    # Recherche de la formule
    formula_match = formula_pattern.search(text)
    formula = formula_match.group(1) if formula_match else "Formule non trouvée"

    # Recherche des définitions associées
    definitions_match = definitions_pattern.search(text)
    definitions = definitions_match.group(1) if definitions_match else "Définitions non trouvées"

    # Retourner la formule et les définitions dans un format structuré
    result = f"- **Formule de révision** : {formula}\n"
    result += f"- **Définitions** :\n{definitions.strip()}"

def analyze_final_file(client, final_content):
    """
    Final analysis that fills out the pre-collected variables with all information, including lists and multiple points.
    """

    # prompt = (
    #     "Vous êtes un expert en analyse de documents. Votre mission est d'extraire toutes les informations du contenu fourni, sans en faire de résumé, en capturant chaque détail tel qu'il est, y compris les éléments multiples, les listes à puces et les informations répétées."
    #     "Ne combinez, ne résumez et n'ignorez aucune donnée. Chaque élément doit être restitué tel quel, même s'il se répète ou apparaît sous une forme similaire dans plusieurs sections."
    #
    #     "### Instructions strictes :\n"
    #     "Aucun résumé : Chaque élément doit être copié exactement tel qu'il apparaît dans le document.\n"
    #     "Listez chaque élément séparément : Si plusieurs éléments existent dans une catégorie (par exemple, plusieurs pénalités), listez-les tous individuellement, sans combiner les informations.\n"
    #     "Ne reformulez pas et ne réécrivez pas : Copiez chaque morceau de texte tel qu'il est.\n"
    #     "Aucune omission, même pour les sections longues (comme les pénalités) : Si une section contient plus de 10 éléments, divisez votre réponse en plusieurs parties si nécessaire.\n"
    #     "Ne remplacez jamais une information existante par une valeur vide.\n"
    #     "Laissez les sections vides si une information est absente.\n"
    #     "Utilisez des listes pour organiser les informations multiples (pénalités, conditions de paiement, etc.).\n"
    #
    #
    #
    #     "### Architecture à respecter :\n"
    #
    #     "CONTEXTE ET ATTENTES \n"
    #     "Avant de rédiger le champ 'Contexte et attentes', tu dois analyser les documents suivants : le dossier RC (Règlement de la Consultation) et le CCTP (Cahier des Clauses Techniques Particulières). Certains éléments peuvent être présents dans l'un ou l'autre de ces documents, et il est crucial de les prioriser et de les organiser comme suit : \n"
    #     "• Objet du marché : Extraire la description précise de l'objet du marché. Si cette information est présente à la fois dans le RC et le CCTP, privilégier celle du CCTP. \n"
    #     "• Périmètre géographique : Identifier la zone géographique couverte par le marché. Cette information se trouve principalement dans le CCTP.\n"
    #     "• Horaires d’ouverture du site : Extraire les horaires d’ouverture et de fermeture, ainsi que l’information sur une ouverture potentielle à l’année. Ces éléments sont à rechercher dans le CCTP. \n"
    #     "• Nombre de lot(s) : Déterminer le nombre de lots mentionnés (RC).  \n"
    #     "• Budget ou chiffre d’affaires : Relever le budget alloué ou le chiffre d’affaires estimé (RC). \n"
    #     "• Calendrier et dates clés :  \n"
    #     "• Identifier la date limite de remise des offres pour la phase candidature (RC). Si cette date n'est pas présente dans le RC, la rechercher dans le CCTP. \n"
    #     "• Relever la date de remise des offres (RC). Si cette information manque dans le RC, la vérifier dans le CCTP. \n"
    #     "• Identifier la date de démarrage du marché (RC). Si elle n'est pas trouvée dans le RC, la chercher dans le CCTP. \n"
    #     "• Extraire la durée du marché (RC). Si cette information n'est pas disponible dans le RC, la compléter à partir du CCAP. \n"
    #     "• Relever la date de visite de site, si applicable (RC). Si cette date n’est pas mentionnée dans le RC, consulter le CCTP. \n"
    #     "• Identifier et extraire les autres dates importantes (RC). Si certaines dates sont absentes du RC, vérifier leur présence dans le CCTP.\n"
    #     "• Critères d’attribution : Extraire chaque critère et indiquer les pourcentages de pondération associés à chaque critère (RC). \n"
    #     "• Missions et/ou prestations attendues : Extraire précisément les missions et prestations décrites dans le CCTP.\n"
    #
    #
    #
    #     "RISQUES D’EXPLOITATION :\n"
    #     "Avant de rédiger le champ 'Risques d’exploitation', tu dois analyser le document suivant : le CCTP (Cahier des Clauses Techniques Particulières) pour extraire les informations suivantes : \n"
    #     "Démarrage : Tu dois rechercher dans le CCTP les éléments suivants : \n"
    #     " Les profils requis. \n"
    #     "Les livrables attendus. \n"
    #     "Les formations spécifiques. \n"
    #     "Exploitation courante : Tu dois, à partir des documents CCTP et CCAP (Cahier des Clauses Administratives Particulières), extraire les informations suivantes : \n"
    #     "Le délai de remplacement des profils (nombre d'heures). \n"
    #     "La gestion des absences. \n"
    #     "Les différentes formations attendues (mentionnées dans le CCAP). \n"
    #     "Le matériel mis à disposition (informatique et communication).\n"
    #     "Les tenues vestimentaires requises.\n"
    #     "La reprise de personnel (le cas échéant).\n"
    #     "La présence d’un chef d’équipe et/ou responsable de site (spécifié dans le CCAP).\n"
    #
    #
    #     "RISQUES CDC :\n"
    #     "Pour cette section, tu dois utiliser le document CCAP pour extraire les informations suivantes :\n"
    #
    #     "Points d’attention : Tu dois relever les éléments mentionnés comme points sensibles ou spécifiques à surveiller.\n"
    #     "Pénalités : Tu dois noter toutes les pénalités, même si elles sont répétées ou listées à différents endroits dans le CCAP. Copie chaque pénalité une par une sans en ignorer aucune.\n"
    #
    #
    #     "CADRE CONTRACTUEL :\n"
    #     "Tu dois analyser le CCAP pour extraire les informations suivantes :\n"
    #
    #     "Révision des prix : Tu dois expliquer les modalités de révision des prix mentionnées. \n"
    #     "Pénalités : Tu dois copier chaque pénalité, ligne par ligne. Si la liste est trop longue, divise les informations et continue à lister jusqu'à ce que tout soit capturé.\n"
    #     "Système de RFA (Remise de Fin d’Année) : Tu dois relever les conditions et modalités de la RFA.\n"
    #     "Délai de paiement : Tu dois indiquer les délais de paiement mentionnés pour chaque type de prestation.\n"
    #
    #     "Remplis chaque section avec toutes les informations collectées sans écraser les informations existantes. Ne laisse aucune information de côté, et laisse vides les sections si aucune information n’a été trouvée.\n"
    #
    # )

    prompt = (
        "Instructions :\n"
        
        "Ne combinez, ne résumez et n'ignorez aucune donnée. Chaque élément doit être restitué tel quel, même s'il se répète ou apparaît de manière similaire dans plusieurs sections."
        "Aucun résumé : Copiez chaque élément exactement comme il apparaît dans le document."
        "Listez chaque élément séparément : Si plusieurs éléments existent dans une catégorie (par exemple, plusieurs pénalités), listez-les tous individuellement sans combiner les informations."
        "Ne reformulez pas et ne réécrivez pas : Copiez chaque morceau de texte tel qu'il est."
        "Aucune omission, même pour les sections longues : Si une section contient plus de 10 éléments, divisez votre réponse en plusieurs parties si nécessaire."
        "Ne remplacez jamais une information existante par une valeur vide."
        "Laissez les sections vides si une information est absente."
        "Utilisez des listes pour organiser les informations multiples (pénalités, conditions de paiement, etc.)."
        "Architecture à respecter :\n"
        
        "CONTEXTE ET ATTENTES :\n"

        "Avant de rédiger le champ 'Contexte et attentes', tu dois analyser les documents suivants : "
        "le dossier RC (Règlement de la Consultation) et le CCTP (Cahier des Clauses Techniques Particulières)."
         "Certains éléments peuvent être présents dans l'un ou l'autre de ces documents. Organise et priorise les informations comme suit : \n"

        "Objet du marché : Extraire la description précise de l'objet du marché. Si cette information est présente à la fois dans le RC et le CCTP, privilégie celle du CCTP. \n"
        "Périmètre géographique : Identifier la zone géographique couverte par le marché (principalement dans le CCTP). \n"
        "Horaires d’ouverture du site : Extraire les horaires d’ouverture et de fermeture, ainsi que l’information sur une ouverture potentielle à l’année (à rechercher dans le CCTP).\n"
        "Nombre de lot(s) : Déterminer le nombre de lots mentionnés (RC)\n."
        "Budget ou chiffre d’affaires : Relever le budget alloué ou le chiffre d’affaires estimé (RC).\n"
        "Calendrier et dates clés :\n"
        "Identifier la date limite de remise des offres pour la phase candidature (RC). Si absente du RC, la rechercher dans le CCTP."
        "Relever la date de remise des offres (RC). Si absente du RC, la vérifier dans le CCTP."
        "Identifier la date de démarrage du marché (RC). Si absente du RC, la chercher dans le CCTP."
        "Extraire la durée du marché (RC). Si absente du RC, la compléter à partir du CCAP."
        "Relever la date de visite de site, si applicable (RC). Si absente du RC, consulter le CCTP."
        "Identifier et extraire les autres dates importantes (RC). Si absentes du RC, vérifier leur présence dans le CCTP."
        "Critères d’attribution : Extraire chaque critère et indiquer les pourcentages de pondération associés (RC).\n"
        "Missions et/ou prestations attendues : Extraire précisément les missions et prestations décrites dans le CCTP."
        
        "RISQUES D’EXPLOITATION : \n"
        
        "Avant de rédiger le champ 'Risques d’exploitation', tu dois analyser le CCTP pour extraire les informations suivantes : \n"
        
        "Démarrage : \n"
        "Les profils requis."
        "Les livrables attendus."
        "Les formations spécifiques.\n"
        "Exploitation courante : À partir du CCTP et du CCAP (Cahier des Clauses Administratives Particulières), extraire : \n"
        "Le délai de remplacement des profils (nombre d'heures)."
       "La gestion des absences."
        "Les différentes formations attendues (CCAP)."
        "Le matériel mis à disposition (informatique et communication)."
        "Les tenues vestimentaires requises."
        "La reprise de personnel (le cas échéant)"
        "La présence d’un chef d’équipe et/ou responsable de site (CCAP)."
        ". RISQUES CDC"
        
        "Utilise le CCAP pour extraire les informations suivantes : \n"
        
        "Points d’attention : Tu dois relever les éléments mentionnés comme points sensibles ou spécifiques à surveiller."
        "Pénalités : Tu dois noter toutes les pénalités, même si elles sont répétées ou listées à différents endroits dans le CCAP. Copie chaque pénalité une par une sans en ignorer aucune."
        
        "CADRE CONTRACTUEL : \n"
        
        "Tu dois analyser le CCAP pour extraire les informations suivantes : \n"

        "Révision des prix : Tu dois expliquer les modalités de révision des prix mentionnées."
        "Pénalités : Tu dois copier chaque pénalité, ligne par ligne. Si la liste est trop longue, divise les informations et continue à lister jusqu'à ce que tout soit capturé."
        "Système de RFA (Remise de Fin d’Année) : Tu dois relever les conditions et modalités de la RFA."
        "Délai de paiement : Tu dois indiquer les délais de paiement mentionnés pour chaque type de prestation."
        "Remplis chaque section avec toutes les informations collectées sans écraser les informations existantes. Ne laisse aucune information de côté. Laisse les sections vides si aucune information n’a été trouvée."
        
        "Formule de révision des prix"
        
        "Tu es chargé de repérer et d'extraire précisément la formule de révision des prix ainsi que son explication détaillée dans le document fourni. Ne captures que la formule et l'explication des termes qui la composent, en ignorant les autres parties non pertinentes."
        
        "Formule attendue : Identifie la formule de calcul pour la révision des prix (par exemple, 'P = ...')."
        "Explication des termes : Extrais l'explication de chaque variable mentionnée dans la formule (par exemple, P, Po, I0-4, Im-4), en décrivant leur rôle et leur signification dans le calcul."
        "Ne résume pas les informations : Copie chaque terme et sa description exactement comme ils apparaissent dans le texte."
        "Ne captures que ce qui est lié à la formule de révision des prix, en ignorant les autres sections du document non pertinentes pour ce calcul."

    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Vous êtes un expert en analyse de documents. Votre mission est d'extraire toutes les informations du contenu fourni, sans en faire de résumé, en capturant chaque détail tel qu'il est, y compris les éléments multiples, les listes à puces et les informations répétées."},
            {"role": "user", "content": prompt + final_content}
        ],
        max_tokens=2000,  # Augmenter la limite de tokens pour capturer plus d'informations si nécessaire
        temperature=0.5
    )

    return response.choices[0].message.content

@app.post("/read-file")
async def match(zip_file: UploadFile = File(...)):
    logger.info(f"Received file: {zip_file.filename}")

    content = await zip_file.read()
    zip_content = BytesIO(content)
    processed_files = []
    missing_info_files = []
    unrecognized_files = []

    variables = {
        # CONTEXTE
        "objet_du_marché": "",
        "prestataire_en_place": "",
        "autres_concurrents_identifiés": "",
        "calendrier_date_limite_remise_offres": "",
        "calendrier_invitation_soumissionner": "",
        "calendrier_remise_livrables": "",
        "calendrier_démarrage": "",
        "calendrier_durée_marché": "",
        "calendrier_notification": "",

        # CONTEXTE ET ATTENTES
        "principales_attentes": "",
        "intérêt_stratégique_pour_ONET": "",
        "contexte": "",
        "critères_attribution_références": "",
        "critères_attribution_organisation_agence": "",
        "critères_attribution_moyens_humains": "",
        "critères_attribution_moyens_techniques": "",
        "critères_attribution_certificat_et_agrément": "",

        # RISQUES D'EXPLOITATION
        "risques_exploitation_démarrage": "",
        "risques_exploitation_courante": "",

        # RISQUES CDC
        "points_attention": [],
        "pénalités": [],  # Liste pour accumuler plusieurs pénalités
        "délais_de_paiement": [],
        "préconisation_visite_qse_formation": [],
        "profils_ssiaps": "",
        "assurances_contrat": [],

        # CADRE CONTRACTUEL
        "Revision_des_prix": "",
        "cadre_pénalités": [],
        "système_rfa": "",
        "cadre_délais_de_paiement": "",

        # CADRE TARIFAIRE
        "masse_salariale": "",
        "aléas_exploitation": "",
        "cadre_formations": [],
        "matériels_fournir": [],
        "tenues_et_équipements": [],
        "sous_traitance": [],
        "commandes_supplémentaires_1": "",
        "commandes_supplémentaires_2": "",

        # POSITIONNEMENT SALARIAL
        "positionnement_salarial": ""
    }


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
    final_results = ""

    for file in processed_files:
        file_name = file["filename"].lower()
        file_content = extract_text_from_pdf(file["content"])


        analysis_result = analyze_content_with_gpt(client, file_name, file_content, variables)
        results.append(analysis_result)

        final_results += analysis_result["info"] + "\n"

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

    # create_pdf([{"filename": "Processed Results", "info": final_results.strip()}])

    if variables["Revision_des_prix"]:
        final_results += "\n" + variables["Revision_des_prix"] + "\n"

    final_results = analyze_final_file(client, final_results)

    return {
        "message": f"{len(results)} files processed and analyzed.",
        "results": results,
        "missing_info_message": missing_info_message,
        "unrecognized_files_message": unrecognized_files_message,
        "final_results": final_results
    }
