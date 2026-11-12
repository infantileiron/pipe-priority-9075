import {request} from './client'; import type {Entity} from '../types/domain';
export const list=()=>request<Entity[]>('/models');
export const get=(id:string)=>request<Entity>('/models/'+id);
export const create=(data:unknown)=>request<Entity>('/models',{method:'POST',body:JSON.stringify(data)});
