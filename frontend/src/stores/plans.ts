import {entityStore} from './entity';import {list} from '../api/plans';export const plansStore=()=>entityStore(list);
