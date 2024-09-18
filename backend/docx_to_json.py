import docx
import json

def docx_to_json(file_path):
    try:
        # Ouvrir le document DOCX
        doc = docx.Document(file_path)
        
        # Extraire le texte de chaque paragraphe
        paragraphs = [para.text for para in doc.paragraphs]
        
        # Créer un dictionnaire avec le contenu
        data_dict = {
            "content": "\n".join(paragraphs),
            "paragraphs": paragraphs
        }
        
        # Convertir le dictionnaire en JSON
        json_data = json.dumps(data_dict, ensure_ascii=False, indent=2)
        
        return json.loads(json_data)
    except Exception as e:
        print(f"Erreur lors de la conversion du fichier DOCX : {str(e)}")
        return None