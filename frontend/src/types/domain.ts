export interface Entity {id:string;name?:string;[key:string]:any}
export interface User {id:string;email:string;name:string;role:'admin'|'analyst'|'viewer'}
export interface Pipe {pipe_id:string;district:string;material:string;age:number;probability:number}
export interface Run extends Entity {model_id:string;status:string;result?:any;error?:string}
