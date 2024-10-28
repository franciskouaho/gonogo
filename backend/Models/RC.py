from pydantic import BaseModel

class RC(BaseModel):
    calendrier_dates_cles: list[str]   # Informations sur les dates clés
    criteres_attribution: list[str]   # Détails des critères d'attribution
    pourcentages_criteres: list[str]   # Pourcentages associés aux critères si disponibles
    informations_demarrage_prestations: list[str] 
    problemes_potentiels: list[str] 
    formations_requises: list[str]
    note_sociale : list[str]
    reprise_personnel : list[str]
    livrables_attendus : list[str]
    points_attention : list[str]
    budget_ou_CA : list[str]
    formations : list[str]
    objet_consultation : list[str]
    titre : list[str]
