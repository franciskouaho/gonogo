import axios, { AxiosInstance } from 'axios';

const getBaseUrl = () => {
    if (typeof window !== 'undefined') {
        return window.location.hostname === 'localhost' ? 'http://localhost:8000/' : 'https://api.emplica.fr/';
    }
    return 'https://api.emplica.fr/';
};

const api: AxiosInstance = axios.create({
    baseURL: getBaseUrl(),
    withCredentials: true,
});

api.defaults.headers.common['Access-Control-Allow-Origin'] = '*';
api.defaults.headers.common['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS';
api.defaults.headers.common['Access-Control-Allow-Headers'] = 'Content-Type, Authorization';

export default api;
