import math,random
from src.config import database as db
from src.utils.security import hash_password
from src.services.modeling import train

def sample_rows():
    rng=random.Random(20261111);rows=[]
    materials=['铸铁','钢管','PE','球墨铸铁']
    for i in range(620):
        age=rng.randint(2,48);pv=round(rng.uniform(.1,3.5),3);diam=rng.choice([80,100,150,200,300]);past=rng.choices([0,1,2,3],[.62,.23,.1,.05])[0];soil=round(rng.uniform(0,1),3);material=rng.choice(materials)
        score=-4.8+.055*age+.9*pv+.7*past+1.3*soil+(.65 if material=='铸铁' else -.5 if material=='PE' else 0)
        leak=int(rng.random()<1/(1+math.exp(-score)))
        rows.append({'pipe_id':f'CC-{i+1:04}','district':['城北一片','金河片区','龙潭片区','新桥片区'][i%4],'age':age,'pressure_var':pv if i%37 else None,'diameter':diam,'past_leaks':past,'soil_corrosion':soil,'material':material,'leak':leak})
    return rows

def seed():
    db.initialize()
    for role,name in [('admin','周工'),('analyst','林分析师'),('viewer','巡检值班员')]:
        db.insert('users',{'id':role,'email':role+'@chengchuan.demo','name':name,'role':role,'password_hash':hash_password('Pipe2026!')},role,preserve=True)
    data=db.insert('datasets',{'id':'data-demo','name':'城北管段巡检样本 · 2026.11','filename':'pipe_inspection_202611.csv','rows':sample_rows(),'created_at':'2026-11-11T00:30:00+00:00'},'data-demo',preserve=True)
    for ident,name,fn,budget in [('model-demo','漏损成本优先 · 日巡40段',25,40),('model-balanced','均衡巡检 · 日巡80段',10,80)]:
        db.insert('models',{'id':ident,'name':name,'dataset_id':'data-demo','false_negative_cost':fn,'false_positive_cost':1,'daily_budget':budget,'seed':42,'created_at':'2026-11-11T00:35:00+00:00'},ident,preserve=True)
    if not db.get('runs','run-demo'):
        result=train(data['rows'],db.get('models','model-demo'))
        db.insert('runs',{'id':'run-demo','model_id':'model-demo','status':'completed','result':result,'error':None,'created_at':'2026-11-11T00:40:00+00:00'},'run-demo',preserve=True)
    run=db.get('runs','run-demo')
    demo_plan=db.get('plans','plan-demo')
    if demo_plan:
        # 兼容历史种子数据：补齐作业日期、班组与占用，保证新口径可核对
        changed=False
        if not demo_plan.get('work_date'):demo_plan['work_date']='2026-11-12';changed=True
        if not demo_plan.get('crew'):demo_plan['crew']='城北运维一班';changed=True
        demo_plan.setdefault('budget',40);demo_plan.setdefault('shortfall',0)
        demo_plan.setdefault('occupied_pipe_ids',[]);demo_plan.setdefault('conflicts',[])
        if changed:db.insert('plans',demo_plan,'plan-demo')
    else:
        demo_plan={'id':'plan-demo','name':'11月12日 · 城北40段优先巡检','run_id':'run-demo','budget':40,
                   'pipes':run['result']['ranking'][:40],'status':'draft','work_date':'2026-11-12',
                   'crew':'城北运维一班','shortfall':0,'occupied_pipe_ids':[],'conflicts':[],
                   'created_at':'2026-11-11T01:00:00+00:00','review_note':''}
        db.insert('plans',demo_plan,'plan-demo')
    if demo_plan['status']!='approved':
        demo_plan.update(status='approved',review_note='结合道路施工约束，优先复查高风险管段。',
                         approved_by='admin@chengchuan.demo',approved_at='2026-11-11T01:02:00+00:00',conflicts=[])
        db.insert('plans',demo_plan,'plan-demo')
    for p in demo_plan['pipes']:
        db.insert('occupancies',{
            'id':'occ-demo-'+p['pipe_id'].lower().replace('-',''),
            'work_date':demo_plan['work_date'],'pipe_id':p['pipe_id'],'plan_id':'plan-demo',
            'plan_name':demo_plan['name'],'crew':demo_plan['crew'],
            'created_at':'2026-11-11T01:02:00+00:00',
        },demo_plan['work_date']+'|'+p['pipe_id'],preserve=True)
    db.insert('reports',{'id':'report-demo','name':'城北巡检交接清单 · 已审批','plan_id':'plan-demo','format':'csv','created_at':'2026-11-11T01:05:00+00:00'},'report-demo',preserve=True)
    print({table:len(db.all_rows(table)) for table in db.TABLES})
if __name__=='__main__':seed()
