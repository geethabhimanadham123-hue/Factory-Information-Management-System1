import {createContext,useContext,useEffect,useState} from 'react';import api from '../api/client';
const C=createContext(null);
export function AuthProvider({children}){const [user,setUser]=useState(()=>{try{return JSON.parse(localStorage.getItem('electrofims_user'))}catch{return null}});const [loading,setLoading]=useState(!!localStorage.getItem('electrofims_token'));
useEffect(()=>{if(!localStorage.getItem('electrofims_token'))return;api.get('/auth/me').then(r=>{setUser(r.data);localStorage.setItem('electrofims_user',JSON.stringify(r.data))}).catch(()=>logout()).finally(()=>setLoading(false));},[]);
function logout(){localStorage.removeItem('electrofims_token');localStorage.removeItem('electrofims_user');setUser(null);}
async function login(payload){const {data}=await api.post('/auth/login',payload);localStorage.setItem('electrofims_token',data.access_token);localStorage.setItem('electrofims_user',JSON.stringify(data.user));setUser(data.user);return data;}
async function register(payload){return (await api.post('/auth/register',payload)).data;}
return <C.Provider value={{user,loading,login,register,logout}}>{children}</C.Provider>}
export const useAuth=()=>useContext(C);
