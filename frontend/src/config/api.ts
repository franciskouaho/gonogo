import axios, {AxiosInstance} from 'axios';

const api: AxiosInstance = axios.create({
    baseURL: window.location.hostname === 'localhost' ? 'http://localhost:8000/' : 'https://api.emplica.fr/',
    withCredentials: true,
});

export default api;
