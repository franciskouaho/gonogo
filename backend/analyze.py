from file_extraction import extract_text_from_file
import logging
import asyncio
from Enums.FileType import FileType
from FileAnalyzerRegistry import FileAnalyzerRegistry
from BaseFileAnalyzer import BaseFileAnalyzer

logger = logging.getLogger(__name__)



async def analyze_processed_files(client,processed_files):
    results = []
    final_results = ""

    tasks = []

    for file in processed_files:
        file_name = file["filename"].lower()
        print(file_name)
        file_content = extract_text_from_file(file)
        if file_content:
            print('here')# Proceed only if text extraction was successful
            task = asyncio.create_task(analyze_content_with_gpt(client, file_name, file_content))
            if task is not None:
                tasks.append(task)

    results_list = await asyncio.gather(*tasks)
    for analysis_result in results_list:
        results.append(analysis_result)
        final_results += analysis_result["info"] + "\n"

    print(final_results)
    return final_results




async def analyze_content_with_gpt(client, file_name: str, content: str):
    """
    Analyse the content of a document and fills the corresponding variables.
    Variables will not be overwritten by empty values.
    """

    analyzer: BaseFileAnalyzer = FileAnalyzerRegistry.get_analyzer(file_name)

    # Si aucun analyseur n'est trouvé, ignorer le fichier
    if analyzer is None:
        logger.info(f"No analyzer found for file '{file_name}'. Skipping.")
        return {"filename": file_name, "info": "Type de fichier non reconnu pour l'extraction."}

    prompt = analyzer.get_prompt()
    results = []

    try:
        # Split the content into chunks and process each one asynchronously
        for chunk in split_text_into_chunks(content):
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Vous êtes un analyseur de documents."},
                    {"role": "user", "content": prompt + chunk}
                ],
                max_tokens=1000,
                temperature=0.5
            )
            gpt_summary = response.choices[0].message.content
            results.append(gpt_summary)

        return {"filename": file_name, "info": " ".join(results)}
    except Exception as e:
        logger.error(f"Error extracting information with GPT for file '{file_name}': {e}")
        return {"filename": file_name, "info": "Error during GPT analysis."}


async def analyze_final_file(client, final_content):
    """
    Final analysis that fills out the pre-collected variables with all information, including lists and multiple points.
    """
    analyzer: BaseFileAnalyzer = FileAnalyzerRegistry.get_analyzer(FileType.MAIN.value)
    prompt = analyzer.get_prompt()

    if isinstance(final_content, list):
        final_content = ' '.join(final_content)

    # Directly make the API request without semaphore
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Vous êtes un expert en analyse de documents. Votre mission est d'extraire toutes les informations du contenu fourni, sans en faire de résumé, en capturant chaque détail tel qu'il est, y compris les éléments multiples, les listes à puces et les informations répétées."},
            {"role": "user", "content": prompt + final_content}
        ],
        max_tokens=2000,  # Augmenter la limite de tokens pour capturer plus d'informations si nécessaire
        temperature=0.5
    )

    return response.choices[0].message.content


def split_text_into_chunks(text, max_tokens=1500):
    words = text.split()
    for i in range(0, len(words), max_tokens):
        yield " ".join(words[i:i + max_tokens])
