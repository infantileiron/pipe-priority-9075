import {request} from './client'; import type {Entity} from '../types/domain';
export const list=()=>request<Entity[]>('/datasets');
export const get=(id:string)=>request<Entity>('/datasets/'+id);
export const create=(data:unknown)=>request<Entity>('/datasets',{method:'POST',body:JSON.stringify(data)});
export const importCSV=(data:unknown)=>request('/datasets/import-csv',{method:'POST',body:JSON.stringify(data)});
