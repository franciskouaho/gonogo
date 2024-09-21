import docx
import json

def docx_to_json(file_path):
    try:
        doc = docx.Document(file_path)
        
        paragraphs = [para.text for para in doc.paragraphs]
        
        data_dict = {
            "content": "\n".join(paragraphs),
            "paragraphs": paragraphs
        }
        
        json_data = json.dumps(data_dict, ensure_ascii=False, indent=2)
        
        return json.loads(json_data)
    except Exception as e:
        print(f"Erreur lors de la conversion du fichier DOCX : {str(e)}")
        print(f"Type de fichier : {type(file_path)}")
        print(f"Contenu du fichier (premiers 100 octets) : {file_path.read(100)}")
        file_path.seek(0)  # Remettre le curseur au début du fichier
        return None
