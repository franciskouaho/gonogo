import docx
import json
import tempfile
import os
import subprocess

def doc_to_json(file_content):
    try:
        with tempfile.NamedTemporaryFile(suffix='.doc', delete=False) as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name

        docx_temp_file_path = temp_file_path + 'x'
        subprocess.run(['libreoffice', '--headless', '--convert-to', 'docx', temp_file_path, '--outdir', os.path.dirname(temp_file_path)], check=True)

        doc = docx.Document(docx_temp_file_path)
        paragraphs = [para.text for para in doc.paragraphs]
        data_dict = {
            "content": "\n".join(paragraphs),
            "paragraphs": paragraphs
        }
        return json.loads(json.dumps(data_dict, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"Erreur lors de la conversion du fichier DOC : {str(e)}")
        return None
    finally:
        if 'temp_file_path' in locals():
            os.unlink(temp_file_path)
        if 'docx_temp_file_path' in locals() and os.path.exists(docx_temp_file_path):
            os.unlink(docx_temp_file_path)
