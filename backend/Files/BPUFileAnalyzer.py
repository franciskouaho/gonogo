from BaseFileAnalyzer import BaseFileAnalyzer
from Enums.FileType import FileType
from Models.BPU import BPU
from pydantic import BaseModel

class BPUFileAnalyzer(BaseFileAnalyzer):
    def __init__(self):
        super().__init__(FileType.BPU)

    def get_prompt(self) -> str:
        return ("""
            Veuillez extraire les informations suivantes de ce contenu :
            Nombre d'agents, CDI, CDD, et tous autres détails sur le personnel.
            Ne remplacez jamais les informations existantes par une valeur vide.
            """
        )

    def get_response_model(self) -> BaseModel:
        return BPU