const base='/api';
export async function request<T=any>(path:string, options:RequestInit={}):Promise<T>{
 const token=sessionStorage.getItem('pipe-token');
 const response=await fetch(base+path,{...options,headers:{'Content-Type':'application/json',...(token?{Authorization:'Bearer '+token}:{}),...options.headers}});
 if(!response.ok){const body=await response.json().catch(()=>({detail:'网络请求失败'}));const detail=body.detail;throw new Error(typeof detail==='string'?detail:detail?.message?detail.message:JSON.stringify(detail));}
 return response.json();
}
export async function downloadReport(id:string){
 const res=await fetch(base+'/reports/'+id+'/download',{headers:{Authorization:'Bearer '+sessionStorage.getItem('pipe-token')}});
 if(!res.ok)throw new Error('下载失败，请重新登录后重试');
 const url=URL.createObjectURL(await res.blob());const a=document.createElement('a');a.href=url;a.download='chengchuan-inspection-'+id+'.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),2000);
}
