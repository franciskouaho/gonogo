'use client';

import {ChangeEvent, FunctionComponent, useState} from "react";
import {useMutation} from "@tanstack/react-query";
import api from "@/config/api";

const Home: FunctionComponent = () => {
    const [file, setFile] = useState<File | null>(null);
    const [results, setResults] = useState(null);
    const [showDownloadButton, setShowDownloadButton] = useState(false);

    const handleFileUpload = useMutation({
        mutationFn: (file: File) => {
            const formData = new FormData();
            formData.append('file', file);
            return api.post('read-file', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            });
        },
        onSuccess: (data) => {
            setResults(data.data);
            setShowDownloadButton(true);
        },
        onError: (error) => {
            console.error("Erreur lors du téléchargement:", error);
            setShowDownloadButton(false);
        }
    });

    const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
        if (event.target.files) {
            const selectedFile = event.target.files[0];
            setFile(selectedFile);
            handleFileUpload.mutate(selectedFile);
        }
    };

    const downloadFile = (word_document_url: string) => {
        if (word_document_url) {
            window.open(word_document_url, '_blank');
        } else {
            console.error("L'URL du document n'est pas disponible");
        }
    };

    console.log("results", results);

    return (
        <section className="flex flex-col items-center justify-center min-h-screen py-12 px-4 sm:px-6 lg:px-8">
            <form className="">
                <div className="w-[400px] relative border-2 border-gray-300 border-dashed rounded-lg p-6" id="dropzone">
                    <input type="file" className="absolute inset-0 w-full h-full opacity-0 z-50"
                           onChange={handleFileChange}/>
                    <div className="text-center">
                        <img className="mx-auto h-12 w-12" src="https://www.svgrepo.com/show/357902/image-upload.svg"
                             alt=""/>

                        <h3 className="mt-2 text-sm font-medium text-gray-900">
                            <label htmlFor="file-upload" className="relative cursor-pointer">
                                <span>Drag and drop</span>
                                <span className="text-indigo-600"> or browse</span>
                                <span> to upload</span>
                                <input id="file-upload" name="file-upload" type="file" className="sr-only"/>
                            </label>
                        </h3>
                        <p className="mt-1 text-xs text-gray-500">
                            PNG, JPG, GIF up to 10MB
                        </p>
                    </div>

                    {file && <img src={URL.createObjectURL(file)} alt="Preview" className="mt-4 mx-auto max-h-40"
                                  id="preview"/>}
                </div>
            </form>

            <div className="mt-4">
                {handleFileUpload.isLoading && <p>Traitement du fichier en cours...</p>}
                {handleFileUpload.isError && (
                    <p className="text-red-500 mt-2">
                        Erreur lors du traitement du fichier. Veuillez réessayer.
                    </p>
                )}
                {handleFileUpload.isSuccess && <p>Fichier traité avec succès!</p>}
            </div>

            {showDownloadButton && results && results.word_document_url && (
                <button
                    onClick={() => downloadFile(results.word_document_url)}
                    className="mt-4 bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded"
                >
                    Télécharger l'analyse
                </button>
            )}
        </section>
    )
}

export default Home;
