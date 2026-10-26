import {useState} from 'react';
import {useNavigate} from 'react-router-dom';
import {useForm} from 'react-hook-form';
import {zodResolver} from '@hookform/resolvers/zod';
import {z} from 'zod';
import {BookOpen,ArrowRight} from 'lucide-react';
import {useAuth} from '../auth';
import {apiError} from '../api';

const schema=z.object({email:z.string().email('Enter a valid email address'),password:z.string().min(1,'Enter your password')});
type Fields=z.infer<typeof schema>;
export function Login(){
  const{login}=useAuth();const navigate=useNavigate();const[serverError,setServerError]=useState('');
  const{register,handleSubmit,formState:{errors,isSubmitting}}=useForm<Fields>({resolver:zodResolver(schema)});
  const submit=handleSubmit(async values=>{try{setServerError('');const user=await login(values.email,values.password);navigate(user.role==='ADMIN'?'/admin':'/author',{replace:true})}catch(error){setServerError(apiError(error))}});
  return <main className="login"><section className="login-intro"><div className="brand"><BookOpen size={28}/>BookLeaf</div><div><p className="eyebrow">PUBLISHING SUPPORT</p><h1>Every book has a story. We’re here for yours.</h1><p>A calm place to track publishing progress, royalties and conversations with our support team.</p></div><small>BookLeaf Publishing · Author portal</small></section><form className="login-form" onSubmit={submit} noValidate><div className="login-title"><h2>Welcome back</h2><p>Sign in to continue to your workspace.</p></div><label>Email address<input autoComplete="username" type="email" {...register('email')} aria-invalid={!!errors.email}/></label>{errors.email&&<small className="field-error">{errors.email.message}</small>}<label>Password<input autoComplete="current-password" type="password" {...register('password')} aria-invalid={!!errors.password}/></label>{errors.password&&<small className="field-error">{errors.password.message}</small>}{serverError&&<p className="form-error" role="alert">{serverError}</p>}<button className="primary full" disabled={isSubmitting}>{isSubmitting?'Signing in…':<>Sign in <ArrowRight size={17}/></>}</button><p className="login-hint">Accounts are provided by BookLeaf. Contact support if you need access.</p></form></main>;
}
