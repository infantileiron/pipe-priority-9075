import {request} from './client'; import type {Entity} from '../types/domain';
export const list=()=>request<Entity[]>('/runs');
export const get=(id:string)=>request<Entity>('/runs/'+id);
export const create=(data:unknown)=>request<Entity>('/runs',{method:'POST',body:JSON.stringify(data)});
