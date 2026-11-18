import axios from 'axios';
const api=axios.create({baseURL:import.meta.env.VITE_API_URL||'http://localhost:8000/api',timeout:12000});
api.interceptors.request.use(c=>{const token=localStorage.getItem('electrofims_token');if(token)c.headers.Authorization=`Bearer ${token}`;return c;});
export default api;
