from pydantic import BaseModel

class CCAP(BaseModel):
    prix_marche: list[str] 
    prestations_attendues: list[str] 
    tranches_et_options: list[str] 
    prestations_supplementaires: list[str] 
    duree_marche: list[str] 
    equipes: list[str]   # Informations sur les équipes (responsable, chef)
    formations: list[str] 
    penalites: list[str]   # Liste de toutes les pénalités extraites
    revisions_prix: list[str] 
    conditions_paiement: list[str] 
    qualite: list[str] 
    formule_revision: list[str]   # Formule de révision exacte commençant par "P ="
    definitions_formule: list[str]   # Définitions liées à la formule si présentes
    rse: list[str] 
    clause_reexamen_modifications: list[str] 