import {createRouter,createWebHashHistory} from 'vue-router';import {auth} from '../stores/auth';
import Login from '../pages/Login.vue';import Overview from '../pages/Overview.vue';import Datasets from '../pages/Datasets.vue';import Models from '../pages/Models.vue';import Results from '../pages/Results.vue';import Plans from '../pages/Plans.vue';
export const router=createRouter({history:createWebHashHistory(),routes:[{path:'/login',component:Login},{path:'/',component:Overview},{path:'/datasets',component:Datasets},{path:'/models',component:Models},{path:'/results',component:Results},{path:'/plans',component:Plans}]});
router.beforeEach(to=>{if(!auth.user&&to.path!='/login')return '/login';});
