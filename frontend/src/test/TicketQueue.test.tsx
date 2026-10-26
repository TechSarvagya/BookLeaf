import {beforeEach,describe,expect,it,vi} from 'vitest';
import {render,screen,waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {MemoryRouter} from 'react-router-dom';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {TicketQueue} from '../pages/TicketQueue';
import {ErrorState} from '../components/States';

const {get}=vi.hoisted(()=>({get:vi.fn()}));
vi.mock('../api',()=>({api:{get}}));
vi.mock('../auth',()=>({useAuth:()=>({user:{id:3,role:'ADMIN',full_name:'Staff'}})}));

function renderQueue(){
  const queryClient=new QueryClient({defaultOptions:{queries:{retry:false}}});
  return render(<QueryClientProvider client={queryClient}><MemoryRouter><TicketQueue/></MemoryRouter></QueryClientProvider>);
}

describe('admin ticket queue',()=>{
  beforeEach(()=>get.mockReset());

  it('shows a loading state and applies priority filtering on the server',async()=>{
    let resolveFirst!: (value:{data:{count:number;results:never[];next:null;previous:null}})=>void;
    get.mockReturnValueOnce(new Promise(resolve=>{resolveFirst=resolve;}));
    get.mockResolvedValue({data:{count:0,results:[],next:null,previous:null}});
    renderQueue();
    expect(screen.getByText('Loading information…')).toBeInTheDocument();
    resolveFirst({data:{count:0,results:[],next:null,previous:null}});
    await screen.findByText('No tickets here');
    await userEvent.selectOptions(screen.getByRole('combobox',{name:'Priority'}),'HIGH');
    await waitFor(()=>expect(get).toHaveBeenCalledWith(expect.stringContaining('priority=HIGH')));
  });

  it('shows a retryable error state',async()=>{
    const retry=vi.fn();
    render(<ErrorState onRetry={retry}/>);
    expect(screen.getByText('Could not load this page')).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button',{name:'Try again'}));
    expect(retry).toHaveBeenCalledOnce();
  });
});
