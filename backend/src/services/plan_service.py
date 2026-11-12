import json
from fastapi import HTTPException
from src.config import database as db
from src.constants.enums import PlanStatus, RunStatus
from src.services.run_service import get as get_run
from src.models.inspection_plan import InspectionPlan
from src.utils.ids import new_id, now

def _occupied_pipe_ids(work_date, plans):
    """同一作业日期内，已批准计划占用的管段编号集合。不同日期互不影响。"""
    ids = set()
    for plan in plans:
        if plan.get("work_date") == work_date and plan["status"] == PlanStatus.APPROVED.value:
            ids.update(p["pipe_id"] for p in plan.get("pipes", []))
    return ids

def create(data):
    run = get_run(data["run_id"])
    if run["status"] != RunStatus.COMPLETED.value:
        raise HTTPException(409, "请先完成模型训练")
    work_date = data["work_date"].isoformat() if hasattr(data["work_date"], "isoformat") else str(data["work_date"])
    crew = data["crew"].strip()
    budget = data["budget"]
    # 草稿按风险排序（沿用模型 ranking），跳过同日已批准计划占用的管段
    occupied = _occupied_pipe_ids(work_date, db.all_rows("plans"))
    ranking = run["result"]["ranking"]
    available = [p for p in ranking if p["pipe_id"] not in occupied]
    pipes = available[:budget]
    shortfall = max(0, budget - len(pipes))
    obj = InspectionPlan(
        new_id("plan"), data["name"], data["run_id"], PlanStatus.DRAFT.value, pipes,
        work_date=work_date, crew=crew, budget=budget, shortfall=shortfall,
        occupied_pipe_ids=sorted(p["pipe_id"] for p in ranking if p["pipe_id"] in occupied),
        conflicts=[],
    ).to_dict()
    obj.update(created_at=now(), review_note="")
    return db.insert("plans", obj)

def get(key):
    obj = db.get("plans", key)
    if not obj:
        raise HTTPException(404, "巡检计划不存在")
    return obj

def listing():
    return db.all_rows("plans")

def _conflict_exception(plan, conflicts):
    return HTTPException(409, {
        "message": f"作业日期 {plan['work_date']} 有 {len(conflicts)} 段管段已被其他班组的已批准计划占用，本份计划整份保留为待审批状态，请调整清单或作业日期后再提交。",
        "plan_id": plan["id"],
        "work_date": plan["work_date"],
        "crew": plan.get("crew", ""),
        "conflicts": conflicts,
    })

def approve(key, note, user):
    try:
        return _approve_in_transaction(key, note, user)
    except HTTPException as exc:
        # 事务已回滚：另开连接把冲突说明写回计划，整份清单保留待审
        if exc.status_code == 409 and isinstance(exc.detail, dict):
            latest = db.get("plans", key)
            if latest and latest["status"] == PlanStatus.APPROVED.value:
                # 并发下另一个请求已批准同一份计划：按幂等成功处理，不重复占用
                return latest
            if latest:
                latest["conflicts"] = exc.detail["conflicts"]
                db.insert("plans", latest)
        raise

def _approve_in_transaction(key, note, user):
    # 单事务：占用校验 + 占用写入 + 状态翻转一次完成，并发重叠草稿只有一份成功
    with db.transaction() as conn:
        plan = db.tx_get(conn, "plans", key)
        if not plan:
            raise HTTPException(404, "巡检计划不存在")
        # 重复批准直接返回既有计划，不重复占用、不重复写状态
        if plan["status"] == PlanStatus.APPROVED.value:
            return plan
        work_date = plan.get("work_date")
        if not work_date:
            raise HTTPException(422, "历史计划缺少作业日期，无法登记占用，请重新生成计划")
        # 批准前再次检查同日占用
        approved = [p for p in db.tx_all_rows(conn, "plans")
                    if p.get("work_date") == work_date and p["status"] == PlanStatus.APPROVED.value]
        owner = {}
        for other in approved:
            for pipe in other.get("pipes", []):
                owner.setdefault(pipe["pipe_id"], other)
        conflicts = []
        for pipe in plan.get("pipes", []):
            other = owner.get(pipe["pipe_id"])
            if other:
                conflicts.append({
                    "pipe_id": pipe["pipe_id"],
                    "plan_id": other["id"],
                    "plan_name": other.get("name", ""),
                    "crew": other.get("crew", ""),
                    "work_date": work_date,
                })
        if conflicts:
            raise _conflict_exception(plan, conflicts)
        plan.update(
            status=PlanStatus.APPROVED.value,
            review_note=note,
            approved_by=user["email"],
            approved_at=now(),
            conflicts=[],
        )
        for pipe in plan["pipes"]:
            pipe_id = pipe["pipe_id"]
            occupancy = {
                "id": new_id("occ"),
                "work_date": work_date,
                "pipe_id": pipe_id,
                "plan_id": plan["id"],
                "plan_name": plan.get("name", ""),
                "crew": plan.get("crew", ""),
                "created_at": now(),
            }
            try:
                # natural_key 唯一约束兜底并发：同日同管段只能占用一次，不同日期互不影响
                db.tx_insert(conn, "occupancies", occupancy, f"{work_date}|{pipe_id}")
            except db.integrity_error():
                row = db.execute(conn, "SELECT payload FROM occupancies WHERE natural_key=?",
                                 (f"{work_date}|{pipe_id}",)).fetchone()
                info = json.loads(row[0]) if row else {}
                if info.get("plan_id") == plan["id"]:
                    continue
                conflicts.append({
                    "pipe_id": pipe_id,
                    "plan_id": info.get("plan_id", ""),
                    "plan_name": info.get("plan_name", ""),
                    "crew": info.get("crew", ""),
                    "work_date": work_date,
                })
        if conflicts:
            raise _conflict_exception(plan, conflicts)
        db.tx_update(conn, "plans", plan)
    return plan
