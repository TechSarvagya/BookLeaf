import {describe,it,expect,vi,beforeEach} from 'vitest';
import {render,screen} from '@testing-library/react';import userEvent from '@testing-library/user-event';
import {MemoryRouter,Route,Routes} from 'react-router-dom';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {TicketDetail} from '../pages/TicketDetail';
const {get,post}=vi.hoisted(()=>({get:vi.fn(),post:vi.fn()}));
vi.mock('../api',()=>({api:{get,post,patch:vi.fn()},apiError:()=> 'Request failed'}));
vi.mock('../auth',()=>({useAuth:()=>({user:{id:3,role:'ADMIN',full_name:'Staff'}})}));
describe('ticket detail',()=>{
  beforeEach(()=>{
    get.mockReset();post.mockReset();
    get.mockImplementation((url:string)=>Promise.resolve({data:url.includes('/messages/')?[]:{id:1,ticket_number:'BL-001',subject:'Royalty question',description:'Where is my payment?',book_data:null,created_at:'2026-10-01',updated_at:'2026-10-02',category:'ROYALTY',priority:'MEDIUM',status:'OPEN',author_name:'Author',assigned_admin_name:null,notes:[],ai_draft:''}}));
    post.mockImplementation((url:string)=>Promise.resolve({data:url.includes('/ai/draft/')?{ai_draft:'We will review the royalty records and confirm the status.'}:{id:1}}));
  });
  it('loads an AI suggestion into an editable reply and sends the edited text',async()=>{
    const qc=new QueryClient({defaultOptions:{queries:{retry:false}}});
    render(<QueryClientProvider client={qc}><MemoryRouter initialEntries={['/admin/tickets/1']}><Routes><Route path="/admin/tickets/:id" element={<TicketDetail/>}/></Routes></MemoryRouter></QueryClientProvider>);
    const user=userEvent.setup();
    await screen.findByText('Where is my payment?');
    await user.click(screen.getByRole('button',{name:'Generate suggestion'}));
    const editor=await screen.findByPlaceholderText('Write or edit the response you will send…');
    expect(editor).toHaveValue('We will review the royalty records and confirm the status.');
    await user.type(editor,' Thank you for your patience.');
    await user.click(screen.getByRole('button',{name:'Send message'}));
    expect(post).toHaveBeenCalledWith('/admin/tickets/1/reply/',{message:'We will review the royalty records and confirm the status. Thank you for your patience.'},expect.objectContaining({headers:expect.objectContaining({'Idempotency-Key':expect.any(String)})}));
  });
});
