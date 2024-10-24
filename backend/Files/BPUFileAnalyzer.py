from BaseFileAnalyzer import BaseFileAnalyzer
from Enums.FileType import FileType

class BPUFileAnalyzer(BaseFileAnalyzer):
    def __init__(self):
        super().__init__(FileType.BPU)

    def get_prompt(self) -> str:
        return (
            "Veuillez extraire les informations suivantes de ce contenu :\n"
            "Nombre d'agents, CDI, CDD, et tous autres détails sur le personnel.\n\n"
            "Ne remplacez jamais les informations existantes par une valeur vide."
        )