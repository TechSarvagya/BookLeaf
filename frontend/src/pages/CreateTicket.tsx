import {useState} from 'react';
import {useNavigate} from 'react-router-dom';
import {useMutation,useQuery,useQueryClient} from '@tanstack/react-query';
import {useForm} from 'react-hook-form';import {zodResolver} from '@hookform/resolvers/zod';import {z} from 'zod';
import {api,apiError} from '../api';import type {Book,Ticket} from '../types';import {ErrorState,Loading} from '../components/States';
const schema=z.object({book:z.string(),subject:z.string().trim().min(3,'Enter at least 3 characters').max(180),description:z.string().trim().min(10,'Please add at least 10 characters').max(5000)});
type Fields=z.infer<typeof schema>;
export function CreateTicket(){
  const go=useNavigate(),qc=useQueryClient(),[serverError,setServerError]=useState('');
  const books=useQuery({queryKey:['books'],queryFn:()=>api.get<Book[]>('/authors/me/books/').then(r=>r.data)});
  const{register,handleSubmit,formState:{errors}}=useForm<Fields>({resolver:zodResolver(schema),defaultValues:{book:'',subject:'',description:''}});
  const create=useMutation({mutationFn:(values:Fields)=>api.post<Ticket>('/tickets/',{...values,book:values.book?Number(values.book):null}).then(r=>r.data),onSuccess:(ticket)=>{
    qc.invalidateQueries({queryKey:['tickets']});
    go(`/author/tickets/${ticket.id}`,{state:{created:ticket.ticket_number}});
    // Ticket persistence has already succeeded; a separate request does the optional AI work.
    void api.post(`/tickets/${ticket.id}/ai/classify/`).then(()=>qc.invalidateQueries({queryKey:['ticket',String(ticket.id)]})).catch(()=>{console.warn('AI classification request did not complete; staff can retry it.');});
  }});
  const submit=handleSubmit(values=>{setServerError('');create.mutate(values,{onError:e=>setServerError(apiError(e))})});
  if(books.isLoading)return <Loading/>;if(books.isError)return <ErrorState onRetry={()=>void books.refetch()}/>;
  return <><div className="page-heading"><p className="eyebrow">AUTHOR SUPPORT</p><h2>Create a support ticket</h2><p>Tell us what happened and which book it concerns. We’ll keep the conversation here.</p></div><form className="panel form" onSubmit={submit} noValidate><label>Related book<select {...register('book')}><option value="">General / account-level question</option>{books.data?.map(book=><option key={book.id} value={book.id}>{book.title}</option>)}</select></label><label>Subject<input {...register('subject')} maxLength={180} placeholder="A short summary of your question" aria-invalid={!!errors.subject}/></label>{errors.subject&&<small className="field-error">{errors.subject.message}</small>}<label>Detailed description<textarea {...register('description')} maxLength={5000} placeholder="Add dates, figures and context that may help us understand the issue" aria-invalid={!!errors.description}/></label>{errors.description&&<small className="field-error">{errors.description.message}</small>}<p className="hint">File attachments are unavailable in this demo. You can describe any supporting evidence in your message.</p>{serverError&&<p className="form-error" role="alert">{serverError}</p>}<button className="primary" disabled={create.isPending}>{create.isPending?'Creating ticket…':'Submit ticket'}</button></form></>;
}
