from BaseFileAnalyzer import BaseFileAnalyzer
from Enums.FileType import FileType


class RCFileAnalyzer(BaseFileAnalyzer):
    def __init__(self):
        super().__init__( FileType.RC)

    def get_prompt(self) -> str:
        return (
            "Veuillez extraire les informations suivantes du contenu fourni :\n"
            "- Calendrier des dates clés (Date limite de remise des offres, Invitation à soumissionner, "
            "Remise des livrables, Démarrage, Durée du marché, Notification, etc.).\n"
            "- Critères d'attribution (Références, Organisation de l'agence, Moyens humains, Moyens techniques, "
            "Certificat et agrément), avec pourcentages si disponibles.\n"
            "- Informations sur le démarrage des prestations, problèmes potentiels et formations requises.\n"
            "Ne remplacez jamais les informations existantes par une valeur vide. Laissez une information vide si elle n'est pas présente."
        )