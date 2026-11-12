"""Leak-priority analysis: no estimator or scaler sees held-out evaluation labels."""
import hashlib, json
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler,OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold,train_test_split
from sklearn.metrics import average_precision_score,roc_auc_score,confusion_matrix,roc_curve,precision_recall_curve
from src.services.dataset_service import validate,NUMERIC

def choose_threshold(labels,probabilities,fn_cost,fp_cost,budget_rate):
    y=np.asarray(labels);p=np.asarray(probabilities)
    if len(y)==0 or len(y)!=len(p) or fn_cost<=0 or fp_cost<=0 or not 0<budget_rate<=1:raise ValueError("阈值输入无效")
    candidates=np.r_[np.unique(p),1.000001]
    best=None
    for t in candidates:
        pred=p>=t;tn,fp,fn,tp=confusion_matrix(y,pred,labels=[0,1]).ravel()
        if pred.mean()>budget_rate+1e-9:continue
        item={"threshold":float(t),"cost":float(fn*fn_cost+fp*fp_cost),"tn":int(tn),"fp":int(fp),"fn":int(fn),"tp":int(tp),"selected":int(pred.sum())}
        if best is None or (item["cost"],item["selected"])<(best["cost"],best["selected"]):best=item
    return best

def pipeline(c,seed):
    numeric=Pipeline([("impute",SimpleImputer(strategy="median")),("scale",StandardScaler())])
    transform=ColumnTransformer([("numeric",numeric,list(range(5))),("material",OneHotEncoder(handle_unknown="ignore",sparse_output=False),[5])])
    return Pipeline([("features",transform),("logistic",LogisticRegression(C=c,max_iter=800,random_state=seed,class_weight="balanced"))])

def train(rows,config):
    validate(rows);seed=int(config.get("seed",42));n=len(rows)
    X=np.array([[float(r[f]) if r[f] not in (None,"") else np.nan for f in NUMERIC]+[r['material']] for r in rows],dtype=object)
    y=np.array([int(r['leak']) for r in rows]);idx=np.arange(n)
    tr,te=train_test_split(idx,test_size=.25,stratify=y,random_state=seed)
    folds=StratifiedKFold(n_splits=4,shuffle=True,random_state=seed)
    scores=[];best=None
    for c in [.05,.25,1,4]:
        oof=np.zeros(len(tr))
        for fit,val in folds.split(X[tr],y[tr]):
            estimator=pipeline(c,seed);estimator.fit(X[tr[fit]],y[tr[fit]]);oof[val]=estimator.predict_proba(X[tr[val]])[:,1]
        ap=float(average_precision_score(y[tr],oof));scores.append({"C":c,"cv_average_precision":ap})
        if best is None or ap>best[0]:best=(ap,c,oof)
    budget_rate=min(1,config['daily_budget']/n)
    selected=choose_threshold(y[tr],best[2],config['false_negative_cost'],config['false_positive_cost'],budget_rate)
    estimator=pipeline(best[1],seed);estimator.fit(X[tr],y[tr]);test_p=estimator.predict_proba(X[te])[:,1]
    pred=test_p>=selected['threshold'];tn,fp,fn,tp=confusion_matrix(y[te],pred,labels=[0,1]).ravel()
    fpr,tpr,_=roc_curve(y[te],test_p);precision,recall,_=precision_recall_curve(y[te],test_p)
    features=list(NUMERIC)+list(estimator.named_steps['features'].named_transformers_['material'].get_feature_names_out(['material']))
    coefficients=[{"feature":f,"coefficient":float(v)} for f,v in zip(features,estimator.named_steps['logistic'].coef_[0])]
    # Deployment refit occurs only after evaluation; held-out metrics above stay unchanged.
    deployed=pipeline(best[1],seed);deployed.fit(X,y);all_p=deployed.predict_proba(X)[:,1]
    ranking=sorted([{"pipe_id":r['pipe_id'],"district":r.get('district','未标记'),"material":r['material'],"age":r['age'],"probability":float(p),"above_threshold":bool(p>=selected['threshold'])} for r,p in zip(rows,all_p)],key=lambda z:(-z['probability'],z['pipe_id']))
    profile={f:{"missing":sum(r[f] in (None,'') for r in rows),"mean":float(np.nanmean([float(r[f]) if r[f] not in (None,'') else np.nan for r in rows]))} for f in NUMERIC}
    return {"seed":seed,"checksum":hashlib.sha256(json.dumps(rows,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),"sample_count":n,"training_count":len(tr),"holdout_count":len(te),"positives":int(y.sum()),"best_C":best[1],"cv":scores,"threshold_selection":selected,"threshold_source":"training out-of-fold only; holdout untouched","metrics":{"roc_auc":float(roc_auc_score(y[te],test_p)),"average_precision":float(average_precision_score(y[te],test_p)),"precision":float(tp/max(1,tp+fp)),"recall":float(tp/max(1,tp+fn)),"tn":int(tn),"fp":int(fp),"fn":int(fn),"tp":int(tp),"cost":float(fn*config['false_negative_cost']+fp*config['false_positive_cost'])},"roc":[{"x":float(a),"y":float(b)} for a,b in zip(fpr,tpr)],"pr":[{"x":float(a),"y":float(b)} for a,b in zip(recall,precision)],"coefficients":coefficients,"ranking":ranking,"profile":profile,"warning":"模拟数据；管段概率仅用于巡检排序，不等同于因果解释。预算约束在训练 OOF 比例上选择阈值；清单严格按预算截取。"}
