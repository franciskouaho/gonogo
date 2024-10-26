from BaseFileAnalyzer import BaseFileAnalyzer
from Enums.FileType import FileType
from Models.RC import RC
from pydantic import BaseModel

class RCFileAnalyzer(BaseFileAnalyzer):
    def __init__(self):
        super().__init__( FileType.RC)

    def get_prompt(self) -> str:
        return (
            """
            Veuillez extraire les informations suivantes du contenu fourni :
            - Calendrier des dates clés (Date limite de remise des offres, Invitation à soumissionner, 
            Remise des livrables, Démarrage, Durée du marché, Notification, etc.).
            - Critères d'attribution (Références, Organisation de l'agence, Moyens humains, Moyens techniques, 
            Certificat et agrément), avec pourcentages si disponibles.
            - Informations sur le démarrage des prestations, problèmes potentiels et formations requises.
            Ne remplacez jamais les informations existantes par une valeur vide. Laissez une information vide si elle n'est pas présente.
            """
        )

    def get_response_model(self) -> BaseModel:
        return RC