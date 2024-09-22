interface ChatGPTAnalysis {
    BU: string;
    "Métier / Société": string;
    "Donneur d'ordres": string;
    Opportunité: string;
    Calendrier: {
        "Date limite de remise des offres": string;
        "Début de la prestation": string;
        "Délai de validité des offres": string;
        "Autres dates importantes": string[];
    };
    "Critères d'attribution": string[];
    "Description de l'offre": {
        Durée: string;
        "Synthèse Lot": string;
        "CA TOTAL offensif": string;
        "Missions générales": string[];
        "Matériels à disposition": string[];
    };
    "Objet du marché": string;
    "Périmètre de la consultation": string;
    "Description des prestations": string[];
    Exigences: string[];
    "Missions et compétences attendues": string[];
    "Profil des hôtes ou hôtesses d'accueil": {
        Qualités: string[];
        "Compétences nécessaires": string[];
    };
    "Plages horaires": Array<{
        Horaires: string;
        Jour: string;
        "Accueil physique": string;
        "Accueil téléphonique": string;
        "Gestion colis *": string;
        "Gestion courrier": string;
        Bilingue: string;
        Campus: string;
    }>;
    PSE: string;
    Formations: string[];
    "Intérêt pour le groupe": {
        Forces: string[];
        Faiblesses: string[];
        Opportunités: string[];
        Menaces: string[];
    };
    "Formule de révision des prix": string | null;
}

export default ChatGPTAnalysis;
