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
            Veuillez extraire **toutes** les pénalités mentionnées, même si elles apparaissent à plusieurs endroits. Retournez-les comme une liste séparée par des points.
            composition des équipes, équipements à fournir, PSE, pénalités, 
            et tout détail lié aux processus opérationnels.
            Ne remplacez jamais les informations existantes par une valeur vide.
            """
        )

    def get_response_model(self) -> BaseModel:
        return CCTP