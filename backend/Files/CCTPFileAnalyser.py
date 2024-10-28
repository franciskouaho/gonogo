from BaseFileAnalyzer import BaseFileAnalyzer
from Enums.FileType import FileType
from Models.CCTP import CCTP
from pydantic import BaseModel

class CCTPFileAnalyzer(BaseFileAnalyzer):
    def __init__(self):
        super().__init__(FileType.CCTP)

    def get_prompt(self) -> str:
        return ( """
            Veuillez extraire les informations suivantes de ce contenu :
            Périmètre géographique (localisation), horaires d'ouvertures, missions, prestations attendues,
            condition_delai_remplacement : conditions et délais de remplacement du personnel 
            Veuillez extraire **toutes** les pénalités mentionnées, même si elles apparaissent à plusieurs endroits. Retournez-les comme une liste séparée par des points.
            composition des équipes ( dire si c'est un chef d'équipe un responsable ou autre), équipements à fournir, PSE, pénalités, gestion des absences
            et tout détail lié aux processus opérationnels.
            - Livrables attendus ( tu dois recherhcer tout type de livrable attendu mentionné)
            - points_attention ( trouve tous les points d'attentions
            - budget ou CA
            Trouve le Résume l'objet de la consultation => objet_consultation
            
            Ne remplacez jamais les informations existantes par une valeur vide.
            """
        )

    def get_response_model(self) -> BaseModel:
        return CCTP