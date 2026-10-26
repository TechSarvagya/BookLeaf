import {BookOpen,LayoutDashboard,Ticket,Plus,LogOut,UserRound,Menu,X} from 'lucide-react';
import {useState} from 'react';
import {NavLink,Outlet} from 'react-router-dom';
import {useAuth} from '../auth';

export function Layout(){
  const{user,logout}=useAuth();const[open,setOpen]=useState(false);const admin=user?.role==='ADMIN';
  const links=admin?[['/admin',LayoutDashboard,'Dashboard'],['/admin/tickets',Ticket,'Ticket queue'],['/admin/assigned',UserRound,'Assigned to me']]:[['/author',LayoutDashboard,'Dashboard'],['/author/books',BookOpen,'My books'],['/author/tickets',Ticket,'My tickets'],['/author/tickets/new',Plus,'Create ticket'],['/author/account',UserRound,'Account']];
  return <div className="shell"><button className="mobile-menu" onClick={()=>setOpen(!open)} aria-label="Toggle menu">{open?<X/>:<Menu/>}</button><aside className={open?'sidebar open':'sidebar'}><div className="brand"><BookOpen size={25}/>BookLeaf</div><p className="role">{admin?'SUPPORT TEAM':'AUTHOR PORTAL'}</p><nav aria-label="Main navigation">{links.map(([to,Icon,label]:any)=><NavLink key={to} end className={({isActive})=>`nav ${isActive?'active':''}`} to={to} onClick={()=>setOpen(false)}><Icon size={18}/><span>{label}</span></NavLink>)}</nav><div className="sidebar-bottom"><span className="signed-in">{user?.full_name}</span><button className="nav" onClick={()=>void logout()}><LogOut size={18}/>Sign out</button></div></aside><main className="content"><header><div><p className="eyebrow">{admin?'Support operations':'Author workspace'}</p><h1>BookLeaf Portal</h1></div><div className="avatar" title={user?.full_name}>{user?.full_name[0]}</div></header><Outlet/></main></div>;
}
