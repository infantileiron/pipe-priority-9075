import {request} from './client'; import type {Entity} from '../types/domain';
export const list=()=>request<Entity[]>('/plans');
export const get=(id:string)=>request<Entity>('/plans/'+id);
export const create=(data:unknown)=>request<Entity>('/plans',{method:'POST',body:JSON.stringify(data)});
export const approve=(id:string,note:string)=>request('/plans/'+id+'/approve',{method:'POST',body:JSON.stringify({note})});
