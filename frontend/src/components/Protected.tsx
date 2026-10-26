import {Navigate} from 'react-router-dom';
import {useAuth} from '../auth';
import {Layout} from './Layout';
import {Loading} from './States';
export function Protected({role}:{role:'ADMIN'|'AUTHOR'}){
  const{user,loading}=useAuth();
  if(loading)return <Loading/>;
  if(!user)return <Navigate to="/login" replace/>;
  if(user.role!==role)return <Navigate to={user.role==='ADMIN'?'/admin':'/author'} replace/>;
  return <Layout/>;
}
