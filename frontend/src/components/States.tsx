import {AlertCircle,Inbox} from 'lucide-react';
import type {ReactNode} from 'react';
export function Loading({label='Loading information'}:{label?:string}){return <div className="panel-state" role="status"><div className="skeleton"/><div className="skeleton short"/><span>{label}…</span></div>}
export function Empty({title,detail,action}:{title:string;detail?:string;action?:ReactNode}){return <div className="panel-state"><Inbox size={28}/><h3>{title}</h3>{detail&&<p>{detail}</p>}{action}</div>}
export function ErrorState({onRetry}:{onRetry?:()=>void}){return <div className="panel-state error-state" role="alert"><AlertCircle size={28}/><h3>Could not load this page</h3><p>Check your connection and try again.</p>{onRetry&&<button onClick={onRetry}>Try again</button>}</div>}
export function Badge({value}:{value:string}){return <span className={`badge ${value.toLowerCase().replace(/_/g,'-')}`}>{value.replace(/_/g,' ')}</span>}
