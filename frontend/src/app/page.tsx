'use client';

import { ChangeEvent, FunctionComponent, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import api from "@/config/api";
import axios from 'axios';

interface ChatGPTAnalysis {
    BU: string;
    "Métier / Société": string;
    "Donneur d'ordres": string;
    Opportunité: string;
    Calendrier: {
        "Date limite de remise des offres": string;
        "Début de la prestation": string;
        "Délai de validité des offres": string;
        "Autres dates importantes": string[];
    };
    "Critères d'attribution": string[];
    "Description de l'offre": {
        Durée: string;
        "Synthèse Lot": string;
        "CA TOTAL offensif": string;
        "Missions générales": string[];
        "Matériels à disposition": string[];
    };
    "Objet du marché": string;
    "Périmètre de la consultation": string;
    "Description des prestations": string[];
    Exigences: string[];
    "Missions et compétences attendues": string[];
    "Profil des hôtes ou hôtesses d'accueil": {
        Qualités: string[];
        "Compétences nécessaires": string[];
    };
    "Plages horaires": Array<{
        Horaires: string;
        Jour: string;
        "Accueil physique": string;
        "Accueil téléphonique": string;
        "Gestion colis *": string;
        "Gestion courrier": string;
        Bilingue: string;
        Campus: string;
    }>;
    PSE: string;
    Formations: string[];
    "Intérêt pour le groupe": {
        Forces: string[];
        Faiblesses: string[];
        Opportunités: string[];
        Menaces: string[];
    };
    "Formule de révision des prix": string | null;
}

interface ApiResponse {
    message: string;
    fine_tune_id: string;
    chatgpt_analysis: ChatGPTAnalysis;
    word_document: string;
}

const Home: FunctionComponent = () => {
    const [file, setFile] = useState<File | null>(null);
    const [results, setResults] = useState<ApiResponse | null>(null);
    const [chatGPTResponse, setChatGPTResponse] = useState<ChatGPTAnalysis | null>(null);
    const [showDownloadButton, setShowDownloadButton] = useState(false);
    const [isDownloading, setIsDownloading] = useState(false);
    const [isLoading, setIsLoading] = useState(false);

    const handleFileUpload = useMutation<ApiResponse, Error, void>({
        mutationFn: () => {
            if (!file) throw new Error("Aucun fichier sélectionné");
            setIsLoading(true);
            const formData = new FormData();
            formData.append('zip_file', file);
            return api.post<ApiResponse>('read-file', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                }
            }).then(response => response.data);
        },
        onSuccess: (data) => {
            console.log("Réponse complète:", data);
            setResults(data);
            setChatGPTResponse(data.chatgpt_analysis);
            setShowDownloadButton(true);
            setIsLoading(false);
        },
        onError: (error) => {
            console.error("Erreur lors du téléchargement:", error);
            setShowDownloadButton(false);
            setIsLoading(false);
        }
    });

    const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
        if (event.target.files && event.target.files[0]) {
            setFile(event.target.files[0]);
            handleFileUpload.mutate();
        }
    };

    const handleDownload = async () => {
        if (!results || !results.word_document) return;
        
        setIsDownloading(true);
        try {
            const response = await api.get(`download-document`, {
                params: { file_path: results.word_document },
                responseType: 'blob'
            });

            const blob = new Blob([response.data], {
                type: response.headers['content-type']
            });

            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = results.word_document.split('/').pop() || 'document';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error("Erreur lors du téléchargement:", error);
        } finally {
            setIsDownloading(false);
        }
    };

    const renderSection = (title: string, content: any) => (
        <div className="mt-4">
            <h4 className="text-md font-semibold mb-2">{title}</h4>
            <pre className="bg-gray-100 p-4 rounded-lg overflow-auto text-sm">
                {JSON.stringify(content, null, 2)}
            </pre>
        </div>
    );

    return (
        <section className="flex flex-col items-center justify-center min-h-screen py-12 px-4 sm:px-6 lg:px-8">
            <form className="mb-8">
                <div className="w-[400px] relative border-2 border-gray-300 border-dashed rounded-lg p-6" id="dropzone">
                    <input type="file" className="absolute inset-0 w-full h-full opacity-0 z-50"
                           onChange={handleFileChange}/>
                    <div className="text-center">
                        <img className="mx-auto h-12 w-12" src="https://www.svgrepo.com/show/357902/image-upload.svg"
                             alt=""/>
                        <h3 className="mt-2 text-sm font-medium text-gray-900">
                            <label htmlFor="file-upload" className="relative cursor-pointer">
                                <span>Glissez-déposez</span>
                                <span className="text-indigo-600"> ou parcourez</span>
                                <span> pour télécharger</span>
                                <input id="file-upload" name="file-upload" type="file" className="sr-only"/>
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

            {showDownloadButton && results && results.word_document && (
                <button
                    onClick={handleDownload}
                    disabled={isDownloading}
                    className="mt-4 bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded"
                >
                    {isDownloading ? 'Téléchargement en cours...' : 'Télécharger l\'analyse'}
                </button>
            )}

            {chatGPTResponse && (
                <div className="mt-8 w-full max-w-4xl">
                    <h3 className="text-lg font-semibold mb-4">Résultats de l'analyse</h3>
                    <div className="bg-white shadow overflow-hidden sm:rounded-lg">
                        <div className="px-4 py-5 sm:px-6">
                            <h3 className="text-lg leading-6 font-medium text-gray-900">
                                Informations générales
                            </h3>
                        </div>
                        <div className="border-t border-gray-200">
                            <dl>
                                {(Object.entries(chatGPTResponse) as [keyof ChatGPTAnalysis, any][]).map(([key, value]) => {
                                    if (typeof value !== 'object') {
                                        return (
                                            <div key={key} className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                                                <dt className="text-sm font-medium text-gray-500">{key}</dt>
                                                <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{value as string}</dd>
                                            </div>
                                        );
                                    }
                                    return null;
                                })}
                            </dl>
                        </div>
                    </div>
                    
                    {renderSection("Calendrier", chatGPTResponse.Calendrier)}
                    {renderSection("Critères d'attribution", chatGPTResponse["Critères d'attribution"])}
                    {renderSection("Description de l'offre", chatGPTResponse["Description de l'offre"])}
                    {renderSection("Description des prestations", chatGPTResponse["Description des prestations"])}
                    {renderSection("Exigences", chatGPTResponse.Exigences)}
                    {renderSection("Missions et compétences attendues", chatGPTResponse["Missions et compétences attendues"])}
                    {renderSection("Profil des hôtes ou hôtesses d'accueil", chatGPTResponse["Profil des hôtes ou hôtesses d'accueil"])}
                    {renderSection("Plages horaires", chatGPTResponse["Plages horaires"])}
                    {renderSection("PSE", chatGPTResponse.PSE)}
                    {renderSection("Formations", chatGPTResponse.Formations)}
                    {renderSection("Intérêt pour le groupe", chatGPTResponse["Intérêt pour le groupe"])}
                    {renderSection("Formule de révision des prix", chatGPTResponse["Formule de révision des prix"])}
                </div>
            )}
        </section>
    );
};

export default Home;
