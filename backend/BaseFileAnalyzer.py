from abc import ABC, abstractmethod
from pydantic import BaseModel


# Classe parent abstraite
class BaseFileAnalyzer(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def get_prompt(self) -> str:
        pass

    @abstractmethod
    def get_response_model(self) -> BaseModel:
        pass
