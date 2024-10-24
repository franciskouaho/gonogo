from BaseFileAnalyzer import BaseFileAnalyzer
from Enums.FileType import FileType

class MAINFileAnalyzer(BaseFileAnalyzer):
    def __init__(self):
        super().__init__(FileType.MAIN)

    def get_prompt(self) -> str:
        return (
               "Instructions :\n"
               
                "Ne combinez, ne résumez et n'ignorez aucune donnée. Chaque élément doit être restitué tel quel, même s'il se répète ou apparaît de manière similaire dans plusieurs sections."
                "Aucun résumé : Copiez chaque élément exactement comme il apparaît dans le document."
                "Listez chaque élément séparément : Si plusieurs éléments existent dans une catégorie (par exemple, plusieurs pénalités), listez-les tous individuellement sans combiner les informations."
                "Ne reformulez pas et ne réécrivez pas : Copiez chaque morceau de texte tel qu'il est."
                "Aucune omission, même pour les sections longues : Si une section contient plus de 10 éléments, divisez votre réponse en plusieurs parties si nécessaire."
                "Ne remplacez jamais une information existante par une valeur vide."
                "Laissez les sections vides si une information est absente."
                "Utilisez des listes pour organiser les informations multiples (pénalités, conditions de paiement, etc.)."
                "Architecture à respecter :\n"
            
                "CONTEXTE ET ATTENTES :\n"
            
                "Avant de rédiger le champ 'Contexte et attentes', tu dois analyser les documents suivants : "
                "le dossier RC (Règlement de la Consultation) et le CCTP (Cahier des Clauses Techniques Particulières)."
                "Certains éléments peuvent être présents dans l'un ou l'autre de ces documents. Organise et priorise les informations comme suit : \n"
            
                "Objet du marché : Extraire la description précise de l'objet du marché. Si cette information est présente à la fois dans le RC et le CCTP, privilégie celle du CCTP. \n"
                "Périmètre géographique : Identifier la zone géographique couverte par le marché (principalement dans le CCTP). \n"
                "Horaires d’ouverture du site : Extraire les horaires d’ouverture et de fermeture, ainsi que l’information sur une ouverture potentielle à l’année (à rechercher dans le CCTP).\n"
                "Nombre de lot(s) : Déterminer le nombre de lots mentionnés (RC)\n."
                "Budget ou chiffre d’affaires : Relever le budget alloué ou le chiffre d’affaires estimé (RC).\n"
                "Calendrier et dates clés :\n"
                "Identifier la date limite de remise des offres pour la phase candidature (RC). Si absente du RC, la rechercher dans le CCTP."
                "Relever la date de remise des offres (RC). Si absente du RC, la vérifier dans le CCTP."
                "Identifier la date de démarrage du marché (RC). Si absente du RC, la chercher dans le CCTP."
                "Extraire la durée du marché (RC). Si absente du RC, la compléter à partir du CCAP."
                "Relever la date de visite de site, si applicable (RC). Si absente du RC, consulter le CCTP."
                "Identifier et extraire les autres dates importantes (RC). Si absentes du RC, vérifier leur présence dans le CCTP."
                "Critères d’attribution : Extraire chaque critère et indiquer les pourcentages de pondération associés (RC).\n"
                "Missions et/ou prestations attendues : Extraire précisément les missions et prestations décrites dans le CCTP."
            
                "RISQUES D’EXPLOITATION : \n"
            
                "Avant de rédiger le champ 'Risques d’exploitation', tu dois analyser le CCTP pour extraire les informations suivantes : \n"
            
                "Démarrage : \n"
                "Les profils requis."
                "Les livrables attendus."
                "Les formations spécifiques.\n"
                "Exploitation courante : À partir du CCTP et du CCAP (Cahier des Clauses Administratives Particulières), extraire : \n"
                "Le délai de remplacement des profils (nombre d'heures)."
                "La gestion des absences."
                "Les différentes formations attendues (CCAP)."
                "Le matériel mis à disposition (informatique et communication)."
                "Les tenues vestimentaires requises."
                "La reprise de personnel (le cas échéant)"
                "La présence d’un chef d’équipe et/ou responsable de site (CCAP)."
                ". RISQUES CDC"
            
                "Utilise le CCAP pour extraire les informations suivantes : \n"
            
                "Points d’attention : Tu dois relever les éléments mentionnés comme points sensibles ou spécifiques à surveiller."
                "Pénalités : Tu dois noter toutes les pénalités, même si elles sont répétées ou listées à différents endroits dans le CCAP. Copie chaque pénalité une par une sans en ignorer aucune."
            
                "CADRE CONTRACTUEL : \n"
            
                "Tu dois analyser le CCAP pour extraire les informations suivantes : \n"
            
                "Révision des prix : Tu dois expliquer les modalités de révision des prix mentionnées."
                "Pénalités : Tu dois copier chaque pénalité, ligne par ligne. Si la liste est trop longue, divise les informations et continue à lister jusqu'à ce que tout soit capturé."
                "Système de RFA (Remise de Fin d’Année) : Tu dois relever les conditions et modalités de la RFA."
                "Délai de paiement : Tu dois indiquer les délais de paiement mentionnés pour chaque type de prestation."
                "Remplis chaque section avec toutes les informations collectées sans écraser les informations existantes. Ne laisse aucune information de côté. Laisse les sections vides si aucune information n’a été trouvée."
            
                "Formule de révision des prix"
            
                "Tu es chargé de repérer et d'extraire précisément la formule de révision des prix ainsi que son explication détaillée dans le document fourni. Ne captures que la formule et l'explication des termes qui la composent, en ignorant les autres parties non pertinentes."
            
                "Formule attendue : Identifie la formule de calcul pour la révision des prix (par exemple, 'P = ...')."
                "Explication des termes : Extrais l'explication de chaque variable mentionnée dans la formule (par exemple, P, Po, I0-4, Im-4), en décrivant leur rôle et leur signification dans le calcul."
                "Ne résume pas les informations : Copie chaque terme et sa description exactement comme ils apparaissent dans le texte."
                "Ne captures que ce qui est lié à la formule de révision des prix, en ignorant les autres sections du document non pertinentes pour ce calcul."
        )


