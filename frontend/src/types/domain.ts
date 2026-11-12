export interface Entity {id:string;name?:string;[key:string]:any}
export interface User {id:string;email:string;name:string;role:'admin'|'analyst'|'viewer'}
export interface Pipe {pipe_id:string;district:string;material:string;age:number;probability:number}
export interface Run extends Entity {model_id:string;status:string;result?:any;error?:string}
export interface PlanConflict {pipe_id:string;plan_id:string;plan_name:string;crew:string;work_date:string}
export interface Plan extends Entity {
  run_id:string;status:'draft'|'approved';pipes:Pipe[];
  work_date:string;crew:string;budget:number;shortfall:number;
  occupied_pipe_ids:string[];conflicts:PlanConflict[];
  review_note?:string;approved_by?:string;approved_at?:string;
}
