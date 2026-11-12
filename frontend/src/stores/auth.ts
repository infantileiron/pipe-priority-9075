import {reactive,computed} from 'vue';import {request} from '../api/client';import type {User} from '../types/domain';
export const auth=reactive({user:JSON.parse(sessionStorage.getItem('pipe-user')||'null') as User|null});
export const canEdit=computed(()=>!!auth.user&&auth.user.role!=='viewer');
export const isAdmin=computed(()=>auth.user?.role==='admin');
export async function login(email:string,password:string){const r=await request('/auth/login',{method:'POST',body:JSON.stringify({email,password})});sessionStorage.setItem('pipe-token',r.access_token);sessionStorage.setItem('pipe-user',JSON.stringify(r.user));auth.user=r.user;}
export function logout(){sessionStorage.clear();auth.user=null;}
