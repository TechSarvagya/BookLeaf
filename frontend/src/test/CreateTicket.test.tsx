import {describe,it,expect,vi,beforeEach} from 'vitest';
import {render,screen} from '@testing-library/react';import userEvent from '@testing-library/user-event';
import {MemoryRouter,Route,Routes} from 'react-router-dom';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {CreateTicket} from '../pages/CreateTicket';
const {get,post}=vi.hoisted(()=>({get:vi.fn(),post:vi.fn()}));
vi.mock('../api',()=>({api:{get,post},apiError:()=> 'Request failed'}));
describe('create ticket',()=>{
  beforeEach(()=>{get.mockReset();post.mockReset();get.mockResolvedValue({data:[{id:12,title:'My Book'}]});post.mockResolvedValue({data:{id:7,ticket_number:'BL-1234'}})});
  it('submits a real book selection and navigates to the created ticket',async()=>{
    const qc=new QueryClient({defaultOptions:{queries:{retry:false}}});
    render(<QueryClientProvider client={qc}><MemoryRouter initialEntries={['/author/tickets/new']}><Routes><Route path="/author/tickets/new" element={<CreateTicket/>}/><Route path="/author/tickets/7" element={<p>Created ticket detail</p>}/></Routes></MemoryRouter></QueryClientProvider>);
    const user=userEvent.setup();
    await screen.findByRole('option',{name:'My Book'});
    await user.selectOptions(screen.getByLabelText('Related book'),'12');
    await user.type(screen.getByLabelText('Subject'),'Royalty question');
    await user.type(screen.getByLabelText('Detailed description'),'I need help with my latest royalty statement.');
    await user.click(screen.getByRole('button',{name:'Submit ticket'}));
    expect(await screen.findByText('Created ticket detail')).toBeInTheDocument();
    expect(post).toHaveBeenCalledWith('/tickets/',expect.objectContaining({book:12,subject:'Royalty question'}));
  });
});
