import csv, io, math
from fastapi import HTTPException
from src.config import database as db
from src.models.inspection_dataset import InspectionDataset
from src.utils.ids import new_id,now
FEATURES=["age","pressure_var","diameter","past_leaks","soil_corrosion","material"]
NUMERIC=FEATURES[:-1]
def validate(rows):
    if not 40<=len(rows)<=5000:raise ValueError("样本数必须在 40–5000 之间")
    keys=set();counts={0:0,1:0}
    for r in rows:
        if not r.get("pipe_id") or str(r["pipe_id"]) in keys:raise ValueError("管段编号缺失或重复")
        keys.add(str(r["pipe_id"]))
        if not set(FEATURES+['leak']).issubset(r):raise ValueError("缺少必需特征或标签")
        try:y=int(r["leak"])
        except (ValueError,TypeError):raise ValueError("leak 必须为 0 或 1")
        if str(r["leak"]) not in ("0","1") and r["leak"] not in (0,1):raise ValueError("leak 必须为 0 或 1")
        if y not in counts:raise ValueError("leak 必须为 0 或 1")
        counts[y]+=1
        for f in NUMERIC:
            if r[f] in (None,""):continue
            try:value=float(r[f])
            except (ValueError,TypeError):raise ValueError("数值特征格式无效")
            if not math.isfinite(value) or value<0:raise ValueError("数值特征必须非负且有限")
        if r["material"] not in ("铸铁","钢管","PE","球墨铸铁"):raise ValueError("未知管材")
    if min(counts.values())<12:raise ValueError("正负类各至少需要 12 条样本以完成分层验证")
    if any(all(r[f] in (None,"") for r in rows) for f in NUMERIC):raise ValueError("特征列不能全部缺失")
    return counts

def create(data):
    validate(data["rows"])
    obj=InspectionDataset(new_id("data"),data["name"],data["rows"],data["filename"]).to_dict();obj["created_at"]=now()
    return db.insert("datasets",obj)
def create_csv(data):
    rows=list(csv.DictReader(io.StringIO(data["csv_text"])))
    for r in rows:
        if not set(FEATURES+['pipe_id','leak']).issubset(r):raise ValueError("CSV 缺少必需字段")
        for f in NUMERIC:r[f]=float(r[f]) if r.get(f) not in (None,"") else None
        r["leak"]=int(r["leak"])
    return create({"name":data["name"],"filename":data["filename"],"rows":rows})
def get(key):
    obj=db.get("datasets",key)
    if not obj:raise HTTPException(404,"样本集不存在")
    return obj
def summary(obj):
    rows=obj["rows"];validate(rows)
    return {k:v for k,v in obj.items() if k!="rows"}|{"count":len(rows),"positives":sum(int(r["leak"]) for r in rows),"missing":{f:sum(r[f] in (None,"") for r in rows) for f in NUMERIC}}
def listing():return [summary(x) for x in db.all_rows("datasets")]
