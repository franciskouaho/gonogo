import logging
import asyncio
import os
from io import BytesIO
from openai import AsyncOpenAI

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from file_extraction import extract_files_from_zip,extract_text_from_file, read_zip_file
from analyze import analyze_processed_files, analyze_final_file
from Enums.FileType import FileType
from FileAnalyzerRegistry import FileAnalyzerRegistry
from BaseFileAnalyzer import BaseFileAnalyzer

logger = logging.getLogger(__name__)

app = FastAPI()

origins = ["http://localhost:3000", "https://emplica.fr"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
FileAnalyzerRegistry.initialize_registry()

@app.post("/read-file")
async def match(zip_file: UploadFile = File(...)):
    logger.info(f"Received file: {zip_file.filename}")

    # Lire le contenu du fichier ZIP
    zip_content = await read_zip_file(zip_file)
    processed_files, missing_info_files, unrecognized_files = extract_files_from_zip(zip_content)

    final_results = await analyze_processed_files(client,processed_files)

    final_results = await analyze_final_file(client, final_results)
    return {
        "results": final_results,
        "final_results": final_results
    }
