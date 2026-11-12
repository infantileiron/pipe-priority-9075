import {request} from './client'; import type {Entity} from '../types/domain';
export const list=()=>request<Entity[]>('/reports');
export const get=(id:string)=>request<Entity>('/reports/'+id);
export const create=(data:unknown)=>request<Entity>('/reports',{method:'POST',body:JSON.stringify(data)});
