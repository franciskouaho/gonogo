from pydantic import BaseModel

class CCTP(BaseModel):
    perimetre_geographique: list[str] 
    horaires_ouverture: list[str] 
    missions: list[str] 
    prestations_attendues: list[str] 
    penalites: list[str]   # Liste de toutes les pénalités extraites
    composition_equipes: list[str] 
    equipements_a_fournir: list[str] 
    pse: list[str] 
    details_processus_operationnels: list[str] 