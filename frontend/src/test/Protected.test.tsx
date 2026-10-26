import {describe,it,expect,vi} from 'vitest';import{render,screen}from'@testing-library/react';
import {MemoryRouter,Route,Routes} from'react-router-dom';
import {Protected} from'../components/Protected';
const {state}=vi.hoisted(()=>({state:{user:null as null|{role:'AUTHOR'|'ADMIN';full_name:string},loading:false}}));
vi.mock('../auth',()=>({useAuth:()=>state}));
describe('protected routes',()=>{
  it('sends an anonymous visitor to login',()=>{
    state.user=null;
    render(<MemoryRouter initialEntries={['/admin']}><Routes><Route path="/admin" element={<Protected role="ADMIN"/>}/><Route path="/login" element={<p>Sign in required</p>}/></Routes></MemoryRouter>);
    expect(screen.getByText('Sign in required')).toBeInTheDocument();
  });
  it('keeps an author out of admin pages',()=>{
    state.user={role:'AUTHOR',full_name:'Author'};
    render(<MemoryRouter initialEntries={['/admin']}><Routes><Route path="/admin" element={<Protected role="ADMIN"/>}/><Route path="/author" element={<p>Author area</p>}/></Routes></MemoryRouter>);
    expect(screen.getByText('Author area')).toBeInTheDocument();
  });
});
