from BaseFileAnalyzer import BaseFileAnalyzer
from Enums.FileType import FileType
from Models.CCAP import CCAP
from pydantic import BaseModel

class CCAPFileAnalyzer(BaseFileAnalyzer):
    def __init__(self):
        super().__init__(FileType.CCAP)

    def get_prompt(self) -> str:
        return ("""
            Veuillez extraire les informations suivantes de ce contenu :
            Prix du marché, prestations attendues, tranches et options, prestations supplémentaires, 
            durée du marché, équipes (responsable d’équipe, chef d’équipe), formations, 
            Veuillez extraire **toutes** les pénalités mentionnées, même si elles apparaissent à plusieurs endroits. Retournez-les comme une liste séparée par des points.
            révisions de prix, conditions de paiement, pénalités, qualité, "
            formule de révision commençant par P = , prenez-la exactement comme c'est écrit et donnez les définitions si elles sont présentes dans le document, 
            RSE, clause de réexamen pour modifications d'équipement.
            Ne remplacez jamais les informations existantes par une valeur vide.
            """
        )

    def get_response_model(self) -> BaseModel:
        return CCAP