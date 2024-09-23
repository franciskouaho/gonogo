import io
import json
import PyPDF2

def pdf_to_json(pdf_input):
    if isinstance(pdf_input, io.BytesIO):
        reader = PyPDF2.PdfReader(pdf_input)
    elif isinstance(pdf_input, str):
        reader = PyPDF2.PdfReader(pdf_input)
    else:
        raise ValueError("L'entrée doit être un chemin de fichier ou un objet BytesIO")

    pdf_content = []

    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        pdf_content.append({
            "page": page_num + 1,
            "content": text
        })

    pdf_json = json.dumps(pdf_content, ensure_ascii=False, indent=4)
    return pdf_json
