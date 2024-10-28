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
            - Récupère tout le titre
            - Note sociale, reprise personnel
            - Calendrier des dates clés :  Reprend toutes les dates que tu trouves  dans avec des dates mais aussi l'intitulé ( exemple => "Durée du marché" : 
              "Le marché est conclu pour une durée de 4 ans qui prend effet à compter du 1er mars 2025") Il faut que tu trouves au minimum ces dates (Réception des offres, Date de publication, Date limite de remise des offres, Invitation à soumissionner,
#             Remise des livrables, Démarrage, Durée du marché, Notification, etc.)
            - Critères d'attribution, Critères de JUGEMENT  (Références, Organisation de l'agence, Moyens humains, Moyens techniques, 
            Certificat et agrément), avec pourcentages si disponibles.
            - points_attention ( trouve tous les points d'attentions
            Trouve le Résume l'objet de la consultation => objet_consultation
            - Livrables attendus ( tu dois recherhcer tout type de livrable attendu mentionné)
            - Informations sur le démarrage des prestations, problèmes potentiels et formations requises.
            Ne remplacez jamais les informations existantes par une valeur vide. Laissez une information vide si elle n'est pas présente.
            """
        )

    def get_response_model(self) -> BaseModel:
        return RC


# """
#             - Calendrier des dates clés (Réception des offres, Date de publication, Date limite de remise des offres, Invitation à soumissionner,
#             Remise des livrables, Démarrage, Durée du marché, Notification, etc.).
#             """