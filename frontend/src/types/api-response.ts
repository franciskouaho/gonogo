import ChatGPTAnalysis from "@/types/chatgpt-analysis";

interface ApiResponse {
    message: string;
    fine_tune_id: string;
    chatgpt_analysis: ChatGPTAnalysis;
    word_document: string;
}

export default ApiResponse;
