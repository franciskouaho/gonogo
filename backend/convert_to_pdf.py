import os
import shutil
import subprocess
import tempfile
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def convert_to_pdf_via_libreoffice(file_name, file_data):
    input_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_name)[1])
    with open(input_file.name, 'wb') as f:
        f.write(file_data)
    logger.info(f"Temporary input file created: {input_file.name}")

    output_dir = tempfile.mkdtemp()
    try:
        subprocess.run(['libreoffice', '--headless', '--convert-to', 'pdf', '--outdir', output_dir, input_file.name],
                       check=True)
        output_files = os.listdir(output_dir)
        logger.info(f"Files in output directory after conversion: {output_files}")

        pdf_files = [f for f in output_files if f.endswith('.pdf')]
        if not pdf_files:
            raise FileNotFoundError(f"No PDF file found in output directory: {output_dir}")

        pdf_output_path = os.path.join(output_dir, pdf_files[0])
        logger.info(f"Converted {file_name} to PDF at {pdf_output_path}")

        # Read the PDF data
        with open(pdf_output_path, 'rb') as pdf_file:
            pdf_data = pdf_file.read()

        return pdf_data
    finally:
        os.remove(input_file.name)
        for file in os.listdir(output_dir):
            os.remove(os.path.join(output_dir, file))
        os.rmdir(output_dir)

def convert_to_pdf(file_name, file_data):
    logger.info(f"Starting conversion for file: {file_name}")

    if file_name.lower().endswith(('.docx', '.doc', '.xlsx', '.txt')):
        logger.info(f"Detected compatible file for LibreOffice conversion: {file_name}")
        pdf_data = convert_to_pdf_via_libreoffice(file_name, file_data)

    else:
        logger.error(f"Unsupported file type: {file_name}")
        raise ValueError(f"Unsupported file type: {file_name}")

    logger.info(f"File {file_name} successfully converted to PDF")
    return pdf_data
