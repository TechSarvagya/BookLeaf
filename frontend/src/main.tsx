import React from 'react';
import {createRoot} from 'react-dom/client';
import {BrowserRouter,Navigate,Route,Routes} from 'react-router-dom';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {AuthProvider,useAuth} from './auth';
import {Loading} from './components/States';
import {Protected} from './components/Protected';
import {Login} from './pages/Login';
import {Dashboard} from './pages/Dashboard';
import {Books,BookDetail} from './pages/Books';
import {TicketQueue} from './pages/TicketQueue';
import {CreateTicket} from './pages/CreateTicket';
import {TicketDetail} from './pages/TicketDetail';
import {Account} from './pages/Account';
import './style.css';

function Home(){const{user,loading}=useAuth();if(loading)return <Loading/>;return <Navigate to={user?.role==='ADMIN'?'/admin':user?'/author':'/login'} replace/>}
const query=new QueryClient({defaultOptions:{queries:{staleTime:10000,retry:1,refetchOnWindowFocus:false}}});
createRoot(document.getElementById('root')!).render(<React.StrictMode><QueryClientProvider client={query}><BrowserRouter><AuthProvider><Routes><Route path="/login" element={<Login/>}/><Route path="/author" element={<Protected role="AUTHOR"/>}><Route index element={<Dashboard/>}/><Route path="books" element={<Books/>}/><Route path="books/:id" element={<BookDetail/>}/><Route path="tickets" element={<TicketQueue/>}/><Route path="tickets/new" element={<CreateTicket/>}/><Route path="tickets/:id" element={<TicketDetail/>}/><Route path="account" element={<Account/>}/></Route><Route path="/admin" element={<Protected role="ADMIN"/>}><Route index element={<Dashboard/>}/><Route path="tickets" element={<TicketQueue/>}/><Route path="assigned" element={<TicketQueue assigned/>}/><Route path="tickets/:id" element={<TicketDetail/>}/></Route><Route path="*" element={<Home/>}/></Routes></AuthProvider></BrowserRouter></QueryClientProvider></React.StrictMode>);
