import {createContext,useContext,useEffect,useState,type ReactNode} from 'react';
import {api,clearTokens,hasSession,refreshToken,saveTokens,setSessionLostHandler} from './api';
import type {User} from './types';

type AuthValue={user:User|null;loading:boolean;login:(email:string,password:string)=>Promise<User>;logout:()=>Promise<void>};
const AuthContext=createContext<AuthValue|null>(null);
export function AuthProvider({children}:{children:ReactNode}){
  const[user,setUser]=useState<User|null>(null);
  const[loading,setLoading]=useState(hasSession());
  useEffect(()=>{
    setSessionLostHandler(()=>setUser(null));
    if(hasSession()) api.get<User>('/auth/me/').then(r=>setUser(r.data)).catch(()=>setUser(null)).finally(()=>setLoading(false));
    return()=>setSessionLostHandler(()=>{});
  },[]);
  const login=async(email:string,password:string)=>{
    const tokens=(await api.post('/auth/login/',{email,password})).data;
    saveTokens(tokens);
    const me=(await api.get<User>('/auth/me/')).data;
    setUser(me);return me;
  };
  const logout=async()=>{
    const refresh=refreshToken();
    try{if(refresh)await api.post('/auth/logout/',{refresh});}finally{clearTokens();setUser(null);}
  };
  return <AuthContext.Provider value={{user,loading,login,logout}}>{children}</AuthContext.Provider>;
}
export function useAuth(){const value=useContext(AuthContext);if(!value)throw new Error('AuthProvider missing');return value;}
