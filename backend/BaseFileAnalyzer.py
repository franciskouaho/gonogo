from abc import ABC, abstractmethod


# Classe parent abstraite
class BaseFileAnalyzer(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def get_prompt(self) -> str:
        pass
