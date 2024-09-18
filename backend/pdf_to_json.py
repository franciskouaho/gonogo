import fitz
import json

def pdf_to_json(pdf_path):
    document = fitz.open(pdf_path)
    pdf_content = []

    for page_num in range(document.page_count):
        page = document.load_page(page_num)
        text = page.get_text("text")
        pdf_content.append({
            "page": page_num + 1,
            "content": text
        })

    pdf_json = json.dumps(pdf_content, ensure_ascii=False, indent=4)
    return pdf_json
