import {describe,it,expect,vi} from 'vitest';
import {render,screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {MemoryRouter,Route,Routes} from 'react-router-dom';
import {Login} from '../pages/Login';

const {login}=vi.hoisted(()=>({login:vi.fn()}));
vi.mock('../auth',()=>({useAuth:()=>({login})}));
describe('login',()=>{
  it('validates fields and routes staff after successful authentication',async()=>{
    login.mockResolvedValue({role:'ADMIN'});
    render(<MemoryRouter initialEntries={['/login']}><Routes><Route path="/login" element={<Login/>}/><Route path="/admin" element={<p>Admin dashboard</p>}/></Routes></MemoryRouter>);
    const user=userEvent.setup();
    await user.click(screen.getByRole('button',{name:/sign in/i}));
    expect(await screen.findByText('Enter a valid email address')).toBeInTheDocument();
    await user.type(screen.getByLabelText('Email address'),'staff@example.com');
    await user.type(screen.getByLabelText('Password'),'secret123');
    await user.click(screen.getByRole('button',{name:/sign in/i}));
    expect(await screen.findByText('Admin dashboard')).toBeInTheDocument();
    expect(login).toHaveBeenCalledWith('staff@example.com','secret123');
  });
});
