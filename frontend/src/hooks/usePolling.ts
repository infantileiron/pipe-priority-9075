import {onUnmounted} from 'vue';export function usePolling(fn:()=>void,ms=3000){const timer=setInterval(fn,ms);onUnmounted(()=>clearInterval(timer));}
