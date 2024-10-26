import logging
import asyncio
import os
from io import BytesIO
from openai import AsyncOpenAI

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from file_extraction import extract_files_from_zip,extract_text_from_file, read_zip_file
from analyze import analyze_processed_files,print_file
from Enums.FileType import FileType
from FileAnalyzerRegistry import FileAnalyzerRegistry
from BaseFileAnalyzer import BaseFileAnalyzer

logger = logging.getLogger(__name__)

app = FastAPI()

origins = ["http://localhost:3000", "https://emplica.fr"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
FileAnalyzerRegistry.initialize_registry()

@app.post("/read-file")
async def match(zip_file: UploadFile = File(...)):
    logger.info(f"Received file: {zip_file.filename}")

    # Lire le contenu du fichier ZIP
    zip_content = await read_zip_file(zip_file)
    processed_files, missing_info_files, unrecognized_files = extract_files_from_zip(zip_content)

    final_results = await analyze_processed_files(client,processed_files)

    final_results = print_file(final_results)
    return {
        "results": final_results,
        "final_results": final_results
    }




def test ():

    return """
    Voici les informations extraites du contenu fourni :

Prix du marché : Montant maximum de 300 000 HT par an.
Prestations attendues :
Pilotage des prestations et gestion administrative.
Missions de mise en exploitation (formation technique, déploiement des moyens humains et matériels).
Présence 24h/24 et 7j/7 d’agents SSIAP 2 et SSIAP 1.
Mise en place et tenue à jour des livrables d’exploitation (registre de sécurité, planning d’intervention, etc.).
Fourniture d’équipements (tenues vestimentaires, EPI, matériel informatique, etc.).
Mise à disposition d’un chef de service SSIAP 3 pour missions de conseil technique.
Renfort de l’équipe avec agents SSIAP 1 ou chefs d’équipes SSIAP 2 supplémentaires.
Tranches et options : Tranches optionnelles sans objet.
Prestations supplémentaires : Prestation supplémentaire éventuelle obligatoire : mise en place d’un agent de sécurité incendie SSIAP 1 supplémentaire.
Durée du marché : Prévue jusqu'en 2028.
Équipes :
Responsable d’équipe : Non spécifié.
Chef d’équipe : Non spécifié.
Formations : Formation technique par les entreprises travaux aux installations en lien avec les prestations.
Pénalités :
Si le Titulaire n’est pas en mesure d’honorer une prestation, le pouvoir adjudicateur peut recourir à un marché sans publicité ni mise en concurrence.
Le Titulaire ne pourra se prévaloir d’une connaissance insuffisante des lieux pour réclamer une révision en hausse du prix des prestations.
Révisions de prix : Non spécifié dans le document.
Conditions de paiement : Non spécifié dans le document.
Qualité : Obligation générale de résultats pour les prestations.
Formule de révision : Non spécifiée dans le document.
RSE : Non spécifié dans le document.
Clause de réexamen pour modifications d'équipement : Non spécifiée dans le document.
Les pénalités extraites sont :

Si le Titulaire n’est pas en mesure d’honorer une prestation, le pouvoir adjudicateur peut recourir à un marché sans publicité ni mise en concurrence.

Le Titulaire ne pourra se prévaloir d’une connaissance insuffisante des lieux pour réclamer une révision en hausse du prix des prestations. Voici les informations extraites du contenu :

Prix du marché : Non mentionné.

Prestations attendues : Organisation du travail, respect des consignes, bonne tenue du personnel, contrôle du bon déroulement de la mission, conformité aux normes et règlements, restitution des installations en bon état.

Tranches et options : Reconduction tacite du marché trois fois maximum pour des périodes de douze mois chacune.

Prestations supplémentaires : Non mentionnées.

Durée du marché : 12 mois après notification de l’ordre de service de démarrage, reconductible trois fois.

Équipes :

Responsable d’équipe : Non spécifié par nom, mais décrit comme étant l'interlocuteur direct auprès de l’EP RNDP.
Chef d’équipe : Doit posséder compétence technique et administrative suffisante, remplaçant approuvé par l’EP RNDP en cas d'absence.
Formations : Formations, habilitations et examens de qualification prévus par la législation en vigueur, formation spécifique au site.

Pénalités mentionnées :

Le Titulaire ne peut se prévaloir d’aucune indemnité en cas d’absence de reconduction.

En cas de dégradation ou de perte des matériels ou équipements par la faute du Titulaire, celui-ci doit assumer les frais de réparation ou de remplacement.

Toute dépense pour remise en état des équipements, des installations ou documents provenant d’un manquement du Titulaire aux obligations du présent marché, lui est imputable.

Révisions de prix : Non mentionnées.

Conditions de paiement : Non mentionnées.

Pénalités : Mentionnées ci-dessus.

Qualité : Le Titulaire est responsable du contrôle de la qualité et du respect des règles de sécurité.

Formule de révision : Non mentionnée.

RSE : Non mentionnée.

Clause de réexamen pour modifications d'équipement : Non mentionnée.

Ces informations ont été extraites directement du texte fourni. Voici les informations extraites du contenu :

Prix du marché : Non spécifié dans le texte.
Prestations attendues : Non spécifié dans le texte.
Tranches et options : Non spécifié dans le texte.
Prestations supplémentaires : Non spécifié dans le texte.
Durée du marché : Non spécifié dans le texte.
Équipes :
Responsable d’équipe : Non spécifié dans le texte.
Chef d’équipe : Non spécifié dans le texte.
Formations : Le Titulaire doit établir et communiquer à l’EP RNDP un rapport d’avancement des formations, fournir les attestations et certificats des formations de l’ensemble du personnel dans les dix (10) jours ouvrés suivant leur réalisation, et tenir à jour le planning des formations.
Pénalités mentionnées :

La constatation du non-respect des mesures de sécurité peut entraîner, après mise en demeure restée sans effet, la résiliation du présent marché aux torts du Titulaire.

En cas de non-respect des mesures de sécurité, le personnel du Titulaire pourra être exclu du Site sans délai et sans recours possible de la part du Titulaire.

Révisions de prix : Non spécifié dans le texte.

Conditions de paiement : Non spécifié dans le texte.

Pénalités : Mentionnées ci-dessus.

Qualité : Non spécifié dans le texte.

Formule de révision : Non spécifié dans le texte.

RSE : Non spécifié dans le texte.

Clause de réexamen pour modifications d'équipement : Non spécifié dans le texte.

Aucune définition n'est présente dans le document pour les termes demandés. Voici les informations extraites du contenu :

Prix du marché : Prix mixtes, comprenant un prix global et forfaitaire et des prix unitaires. Les prix sont révisables.

Prestations attendues : Exécution de toutes les prestations attribuées, y compris celles non décrites mais nécessaires à la parfaite réalisation de la prestation.

Tranches et options : Non spécifié dans le document.

Prestations supplémentaires : Pour les prestations non figurant dans le bordereau des prix unitaires, un devis doit être établi et accepté par le pouvoir adjudicateur.

Durée du marché : Non spécifié dans le document.

Équipes : Non spécifié dans le document (pas de mention de responsable d’équipe ou chef d’équipe).

Formations : Non spécifié dans le document.

Pénalités :

A défaut de réponse dans un délai de 1 jour ouvré, la notification est réputée acquise.
En cas de non-information par écrit dans un délai de cinq (5) jours ouvrés, le Titulaire est sous peine de forclusion.
L’EP RNDP se réserve le droit de renvoyer toute facture ne comportant pas les mentions requises ou d'effectuer une suspension de paiement par manque de pièces.
Révisions de prix : Les prix sont révisables suivant des modalités spécifiques.

Conditions de paiement :

Facturation unique au terme de la période de mise en exploitation.
Facturation trimestrielle ou mensuelle sur demande.
Les prestations exécutées par bons de commande sont réglées sur présentation d’une facture mensuelle.
Pénalités : Liste déjà fournie ci-dessus.

Qualité : Non spécifié dans le document.

Formule de révision :

P = Po x [0,2 + 0,8 Im-4 / I0-4]
Définitions :

P : prix révisé.
Po : prix initial.
I0-4 : valeur de l’indice pour le mois antérieur de 4 mois au mois zéro.
Im-4 : valeur de cet indice pour le mois antérieur de 4 mois à la date de notification.
RSE : Non spécifié dans le document.
    
    """
