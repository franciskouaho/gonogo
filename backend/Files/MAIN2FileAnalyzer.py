from BaseFileAnalyzer import BaseFileAnalyzer
from Enums.FileType import FileType
from Models.RC import RC
from pydantic import BaseModel

class MAINFileAnalyzer(BaseFileAnalyzer):
    def __init__(self):
        super().__init__(FileType.MAIN2)

    def get_prompt(self) -> str:
     return """
    Vous êtes un expert en analyse de documents. Votre mission est d'extraire toutes les informations du contenu fourni, en naviguant à travers plusieurs documents (3 à 4 documents). Vous devez capturer chaque détail tel qu'il est, y compris les éléments multiples, les listes à puces et les informations répétées. Ne combinez, ne résumez et n'ignorez aucune donnée. Chaque élément doit être restitué tel quel, même s'il se répète ou apparaît sous une forme similaire dans plusieurs sections.
Instructions générales :
•	Aucun résumé : Chaque élément doit être copié exactement tel qu'il apparaît dans les documents.
•	Listez chaque élément séparément : Si plusieurs éléments existent dans une catégorie, listez-les individuellement sans les combiner.
•	Ne reformulez pas et ne réécrivez pas : Copiez chaque morceau de texte tel qu'il est.
•	Aucune omission : Ne laissez rien de côté, même pour les sections longues.
•	Ne remplacez jamais une information existante par une valeur vide.
•	Sections vides : Laissez les sections vides si une information est absente.
•	Organisation : Utilisez des listes pour organiser les informations multiples (pénalités, conditions de paiement, etc.).
•	Sélection de l'information la plus détaillée : Si la même information est présente dans plusieurs documents, choisissez celle qui est la plus détaillée pour l'extraire.
Architecture à respecter :
1.	CONTEXTE ET ATTENTES
o	Objet du marché : Extraire la description précise de l'objet du marché. Si cette information est présente dans plusieurs documents (RC, CCTP, etc.), privilégiez celle qui est la plus détaillée.
o	Périmètre géographique : Identifier la zone géographique couverte par le marché (principalement dans le CCTP).
o	Horaires d’ouverture du site : Extraire les horaires d’ouverture et de fermeture, y compris l'information sur une ouverture potentielle à l’année (CCTP).
o	Nombre de lot(s) : Déterminer le nombre de lots mentionnés (RC).
o	Budget ou chiffre d’affaires : Relever le budget alloué ou le chiffre d’affaires estimé (RC).
o	Calendrier et dates clés :
	Date limite de remise des offres pour la phase candidature (RC ou CCTP).
	Date de remise des offres (RC ou CCTP).
	Date de démarrage du marché (RC ou CCTP).
	Durée du marché (RC ou CCAP).
	Date de visite de site, si applicable (RC ou CCTP).
	Autres dates importantes (RC ou CCTP).
o	Critères d’attribution : Extraire chaque critère avec les pourcentages de pondération associés (RC).
o	Missions et/ou prestations attendues : Extraire précisément les missions et prestations décrites dans le CCTP.
2.	RISQUES D’EXPLOITATION
o	Démarrage (CCTP) :
	Les profils requis.
	Les livrables attendus.
	Les formations spécifiques.
o	Exploitation courante (CCTP et CCAP) :
	Le délai de remplacement des profils (nombre d'heures).
	La gestion des absences.
	Les différentes formations attendues (CCAP).
	Le matériel mis à disposition (informatique et communication).
	Les tenues vestimentaires requises.
	La reprise de personnel, le cas échéant.
	La présence d’un chef d’équipe et/ou responsable de site (CCAP).
3.	RISQUES CDC
o	Points d’attention (CCAP) : Relever les éléments mentionnés comme points sensibles ou spécifiques à surveiller.
o	Pénalités (CCAP) : Noter toutes les pénalités, même si elles sont répétées ou listées à différents endroits. Copier chaque pénalité une par une sans en ignorer aucune.
4.	CADRE CONTRACTUEL
o	Révision des prix (CCAP) : Expliquer les modalités de révision des prix mentionnées.
o	Pénalités (CCAP) : Copier chaque pénalité, ligne par ligne. Si la liste est trop longue, divisez-la en plusieurs parties.
o	Système de RFA (Remise de Fin d’Année) : Relever les conditions et modalités de la RFA.
o	Délai de paiement : Indiquer les délais de paiement mentionnés pour chaque type de prestation.
Instructions spécifiques pour la formule de révision des prix :
Votre tâche est de repérer et d'extraire précisément la formule de révision des prix ainsi que son explication détaillée dans les documents fournis. Ne capturez que la formule et l'explication des termes qui la composent, sans inclure les autres parties non pertinentes.
•	Formule attendue : Identifiez la formule de calcul pour la révision des prix (par exemple, "P = ...").
•	Explication des termes : Extraire l'explication de chaque variable mentionnée dans la formule (par exemple, P, P0, I0-4, Im-4), en décrivant leur rôle et leur signification dans le calcul.
•	Précision : Copiez chaque terme et sa description exactement comme ils apparaissent dans le texte.
•	Focalisation : Ne capturez que ce qui est lié à la formule de révision des prix, en ignorant les autres sections des documents non pertinentes pour ce calcul.
•	Reformulation autorisée : Vous pouvez reformuler uniquement lors de l'explication des termes techniques pour clarifier leur signification.
Note finale :
•	Sélection de l'information la plus détaillée : Lorsque vous rencontrez des informations identiques dans plusieurs documents, sélectionnez celle qui est la plus détaillée pour l'inclure dans votre extraction.
•	Exhaustivité : Remplissez chaque section avec toutes les informations collectées sans écraser les informations existantes.
•	Aucune omission : Ne laissez aucune information de côté, et laissez les sections vides si aucune information n’a été trouvée.


     """

    def get_response_model(self) -> BaseModel:
        return RC