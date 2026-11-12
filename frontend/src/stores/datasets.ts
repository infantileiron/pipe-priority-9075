import {entityStore} from './entity';import {list} from '../api/datasets';export const datasetsStore=()=>entityStore(list);
