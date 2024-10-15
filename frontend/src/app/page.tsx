'use client';

import { ChangeEvent, FunctionComponent, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import api from "@/config/api";
import ApiResponse from "@/types/api-response";

interface FileResult {
    filename: string;
    info: string | object;  // 'info' peut être une chaîne ou un objet JSON
}

const Home: FunctionComponent = () => {
    const [file, setFile] = useState<File | null>(null);
    const [results, setResults] = useState<FileResult[]>([]);
    const [showDownloadButton, setShowDownloadButton] = useState(false);
    const [isDownloading, setIsDownloading] = useState(false);
    const [isLoading, setIsLoading] = useState(false);

    // Mutation pour envoyer le fichier et obtenir les résultats
    const handleFileUpload = useMutation<ApiResponse, Error, void>({
        mutationFn: async () => {
            if (!file) throw new Error("Aucun fichier sélectionné");
            setIsLoading(true);
            const formData = new FormData();
            formData.append('zip_file', file);
            const response = await api.post<ApiResponse>('read-file', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                }
            });
            return response.data;
        },
        onSuccess: (data) => {
            console.log("Réponse complète:", data);
            setResults(data.results);  // Stocke les résultats pour chaque fichier
            setShowDownloadButton(true);
            setIsLoading(false);
        },
        onError: (error) => {
            console.error("Erreur lors du téléchargement:", error);
            setShowDownloadButton(false);
            setIsLoading(false);
        }
    });

    // Gérer le changement de fichier
    const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
        if (event.target.files && event.target.files[0]) {
            setFile(event.target.files[0]);
            handleFileUpload.mutate();
        }
    };

    // Logique de téléchargement (si nécessaire)
    const handleDownload = async () => {
        // Implémente la logique de téléchargement si nécessaire
    };

    // Affiche les résultats
    const renderResult = (result: FileResult) => {
        return (
            <div key={result.filename} className="bg-white shadow overflow-hidden sm:rounded-lg mb-6">
                <div className="px-4 py-5 sm:px-6">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">
                        Résultats pour: {result.filename}
                    </h3>
                </div>
                <div className="border-t border-gray-200 px-4 py-5">
                    {/* Si result.info est un objet, on le transforme en chaîne JSON */}
                    <pre className="bg-gray-100 p-4 rounded-lg overflow-auto text-sm">
                        {typeof result.info === 'object' ? JSON.stringify(result.info, null, 2) : result.info}
                    </pre>
                </div>
            </div>
        );
    };

    return (
        <section className="flex flex-col items-center justify-center min-h-screen py-12 px-4 sm:px-6 lg:px-8">
            <form className="mb-8">
                <div className="w-[400px] relative border-2 border-gray-300 border-dashed rounded-lg p-6" id="dropzone">
                    <input type="file" className="absolute inset-0 w-full h-full opacity-0 z-50"
                           onChange={handleFileChange} />
                    <div className="text-center">
                        <img className="mx-auto h-12 w-12" src="https://www.svgrepo.com/show/357902/image-upload.svg"
                             alt="Upload" />
                        <h3 className="mt-2 text-sm font-medium text-gray-900">
                            <label htmlFor="file-upload" className="relative cursor-pointer">
                                <span>Glissez-déposez</span>
                                <span className="text-indigo-600"> ou parcourez</span>
                                <span> pour télécharger</span>
                                <input id="file-upload" name="file-upload" type="file" className="sr-only" />
                            </label>
                        </h3>
                        <p className="mt-1 text-xs text-gray-500">
                            ZIP jusqu'à 10MB
                        </p>
                    </div>
                </div>
            </form>

            <div className="mt-4">
                {isLoading && (
                    <div className="flex items-center justify-center">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                        <p className="ml-2">Traitement du fichier en cours...</p>
                    </div>
                )}
                {handleFileUpload.isError && (
                    <p className="text-red-500 mt-2">
                        Erreur lors du traitement du fichier. Veuillez réessayer.
                    </p>
                )}
                {handleFileUpload.isSuccess && <p>Fichier traité avec succès!</p>}
            </div>

            {showDownloadButton && results && (
                <button
                    onClick={handleDownload}
                    disabled={isDownloading}
                    className="mt-4 bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded"
                >
                    {isDownloading ? 'Téléchargement en cours...' : 'Télécharger l\'analyse'}
                </button>
            )}

            {/* Affichage des résultats */}
            {results.length > 0 && (
                <div className="mt-8 w-full max-w-4xl">
                    <h3 className="text-lg font-semibold mb-4">Résultats de l'analyse</h3>
                    {results.map((result) => renderResult(result))}
                </div>
            )}
        </section>
    );
};

export default Home;
