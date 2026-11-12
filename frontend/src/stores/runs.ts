import {entityStore} from './entity';import {list} from '../api/runs';export const runsStore=()=>entityStore(list);
