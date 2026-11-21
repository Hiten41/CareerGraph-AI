import {render,screen,fireEvent} from '@testing-library/react';
import {expect,it,vi} from 'vitest';
import {JobCard} from './job-card';
import type {Result} from '../types/domain';
it('shows unknown compensation, missing skills, and invokes the selected save action',()=>{
 const result:Result={job:{id:'a',title:'Search Intern',company:'Fictional',description:'Build search',skills:['Python'],optional_skills:[],location:null,mode:'remote',employment:'internship',salary:null,currency:null,period:null,url:'https://example.invalid',synthetic:true,last_seen_at:'2026-01-01'},eligibility:'uncertain',unknown:['salary comparison'],explanation:{score:0.2,matched:[],missing:['Python'],missing_optional:[],features:{},score_label:'Relevance'}};
 const save=vi.fn();render(<JobCard result={result} onSave={save} onOpen={()=>{}} onDismiss={()=>{}}/>);
 expect(screen.getByText('Compensation not disclosed')).toBeTruthy();
 expect(screen.getByText('Skills to build: Python')).toBeTruthy();
 fireEvent.click(screen.getByRole('button',{name:'Save Search Intern'}));expect(save).toHaveBeenCalledOnce();
});
