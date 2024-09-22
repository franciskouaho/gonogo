import re

def nettoyer_json(json_data):
    def nettoyer_texte(texte):
        texte = re.sub(r'u00([0-9a-f]{2})', lambda m: chr(int(m.group(1), 16)), texte)
        texte = re.sub(r'[^a-zA-Z0-9\s.,;:!?()-]', '', texte)
        texte = re.sub(r'\s+', ' ', texte).strip()
        texte = re.sub(r'\.{2,}', '', texte)
        texte = re.sub(r'(?<!\w)\.(?!\w)', '', texte)
        return texte

    def nettoyer_recursif(element):
        if element is None:
            return None
        if isinstance(element, str):
            element_nettoye = nettoyer_texte(element)
            if element_nettoye.lower() in ["null"] or not element_nettoye:
                return None
            return element_nettoye
        elif isinstance(element, list):
            return [item for item in (nettoyer_recursif(e) for e in element) if item is not None and item != '']
        elif isinstance(element, dict):
            return {k: v for k, v in ((k, nettoyer_recursif(v)) for k, v in element.items()) if v is not None and v != ''}
        else:
            return element

    json_nettoye = nettoyer_recursif(json_data)

    if isinstance(json_nettoye, dict):
        json_nettoye = {k: v for k, v in json_nettoye.items() if v not in ([], {}, None, '')}
    elif isinstance(json_nettoye, list):
        json_nettoye = [item for item in json_nettoye if item not in ([], {}, None, '')]

    return json_nettoye
