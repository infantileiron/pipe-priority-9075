import {entityStore} from './entity';import {list} from '../api/reports';export const reportsStore=()=>entityStore(list);
