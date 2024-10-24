import zipfile
import pdfplumber
import openpyxl
import docx
from io import BytesIO
from fastapi import FastAPI, File, UploadFile

import logging

logger = logging.getLogger(__name__)

def extract_files_from_zip(zip_content: BytesIO):
    processed_files = []
    missing_info_files = []
    unrecognized_files = []

    with zipfile.ZipFile(zip_content, 'r') as z:
        file_list = z.namelist()

        for file_name in file_list:
            if (
                file_name.endswith('/') or  # directories
                "__MACOSX" in file_name or  # Mac system files
                file_name.startswith('.') or  # hidden files (e.g., .DS_Store)
                file_name.startswith('._') or  # Mac resource fork files
                file_name.startswith('~$') or   # temporary Office files
                file_name.endswith('.DS_Store')  # Specific .DS_Store files
            ):
                logger.info(f"Skipping directory or unwanted file: {file_name}")
                continue

            with z.open(file_name) as extracted_file:
                file_data = extracted_file.read()

                if file_name.lower().endswith('.xlsx'):
                    try:
                        # Pass the file data for later processing
                        processed_files.append({"filename": file_name, "content": file_data, "type": "excel"})
                    except Exception as e:
                        logger.error(f"Invalid .xlsx file '{file_name}': {str(e)}")
                        continue

                elif file_name.lower().endswith('.pdf'):
                    # Process the PDF files directly
                    processed_files.append({"filename": file_name, "content": file_data, "type": "pdf"})

                elif file_name.lower().endswith('.docx'):
                    # Process .docx files
                    processed_files.append({"filename": file_name, "content": file_data, "type": "docx"})

                else:
                    logger.info(f"Unrecognized file type: {file_name}")
                    unrecognized_files.append(file_name)

                # Classification logic based on keywords
                file_name_lower = file_name.lower()
                if any(keyword in file_name_lower for keyword in ["rc", "ccap", "cctp", "bpu"]):
                    missing_info_files.append(file_name)

    return processed_files, missing_info_files, unrecognized_files

def extract_text_from_file(file):
    file_type = file.get("type")
    file_content = file.get("content")

    if file_type == "pdf":
        return extract_text_from_pdf(file_content)
    elif file_type == "excel":
        return extract_text_from_excel(file_content)
    elif file_type == "docx":
        return extract_text_from_word(file_content)
    else:
        logger.error(f"Unsupported file type: {file_type}")
        return ""

def extract_text_from_excel(excel_content: bytes) -> str:
    text = ""
    try:
        workbook = openpyxl.load_workbook(BytesIO(excel_content))
        for sheet in workbook:
            for row in sheet.iter_rows(values_only=True):
                row_text = " ".join([str(cell) if cell is not None else "" for cell in row])
                text += row_text + "\n"
    except Exception as e:
        logger.error(f"Error extracting text from Excel file: {str(e)}")
        return ""

    return text

def extract_text_from_pdf(pdf_content):
    text = ""
    with pdfplumber.open(BytesIO(pdf_content)) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text

def extract_text_from_word(word_content: bytes) -> str:
    print("word")
    text = ""
    try:
        doc = docx.Document(BytesIO(word_content))
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
    except Exception as e:
        logger.error(f"Error extracting text from Word file: {str(e)}")
        return ""
    return text

async def read_zip_file(zip_file: UploadFile) -> BytesIO:
    content = await zip_file.read()
    return BytesIO(content)