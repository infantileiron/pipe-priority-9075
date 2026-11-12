# 澄川水务 · 漏损巡检优先级

把管龄、压力波动、管材与历史渗漏转化为有成本依据的巡检清单。所有样本均为模拟数据。

## 使用场景

澄川水务城北运维队有 34 位同事，维护 620 段管线。原来从 `pipe_inspection_202611.csv` 人工合并 Excel，按管龄排查；痛点是类别失衡被忽略、随机验证造成信息泄漏、有限工时没有成本口径。历史巡检与压力摘要是上游，本工具负责验证模型与评估优先级，下游为运维负责人审批、值班员现场复核。本应用不负责工单流转。

## 功能与主流程

五个业务页面：巡检概览、样本质量（CSV 导入与校验）、模型试验、评估解释、巡检交接。核心实体 InspectionDataset / ModelSpec / TrainingRun / InspectionPlan / Report 各有独立 model、schema、service、controller、route、前端 API 与 store。共享 PipeTable 用在概览、评估与交接三页；MetricStrip、StatusBadge、Notice 用在多个页面。

### 角色与账号

|角色|邮箱|权限|典型动作|
|---|---|---|---|
|admin|admin@chengchuan.demo|全部页面、创建及审批|复核并批准巡检计划|
|analyst|analyst@chengchuan.demo|导入、训练、创建计划与报告；不能审批|生成日巡 40 段候选清单|
|viewer|viewer@chengchuan.demo|浏览、下载已归档报告|现场查看已审批清单|

三个账号的演示密码均为 **Pipe2026!**。JWT HS256 有效期 8 小时；PBKDF2-SHA256 加盐存储密码；服务端执行角色校验，页面同时禁用无权限按钮。正式部署应替换 JWT_SECRET 与演示密码。

### 一天的验收剧本

1. 08:30，林分析师登录，核查 `pipe_inspection_202611.csv` 的 620 条记录和正负标签。
2. 08:35，检查压力波动缺失值；缺失数据保留，在每个训练折内用中位数填补。
3. 08:40，选择“漏损成本优先 · 日巡40段”，或建立漏检成本25/误检成本1的新情景。
4. 08:42，提交队列任务；worker 运行四折分层验证，选择 C，再计算预算约束下的成本阈值。
5. 08:45，查看独立 155 条留出集的 ROC、PR、混淆矩阵，以及逻辑回归系数。
6. 08:50，从风险排序截取前40段，生成待审计划。
7. 09:00，周工使用 admin 登录，核对道路施工、班组工时，填写审批意见并批准。
8. 09:05，生成 CSV 正式交接报告；值班员用 viewer 下载清单，到场复核。

## 快速启动

要求 Docker Compose v2、可访问 Docker daemon 与镜像源。五个容器 frontend/backend/worker/db/redis，数据库为 MySQL8。命名卷分别保存数据库、Redis AOF 与 worker 心跳/产物。

```sh
cp .env.example .env
docker compose config --quiet
docker compose up -d --build
docker compose ps
docker compose exec -T backend python -m scripts.seed_demo
```

前端：http://localhost:18201 ；后端与 API 文档：http://localhost:19201/docs ；数据库映射17701。Nginx `/api/` 代理到无 `/api` 前缀的 FastAPI 路由。生产容器健康检查依赖数据库、Redis，worker 心跳在 `/artifacts/worker.heartbeat`。

```sh
# 验收完成后销毁本项目的演示数据卷
docker compose down -v --remove-orphans
```

批量起栈由上层调度申请 Docker 槽位，最多3栈并行；此项目不会自行启动其他栈。

## 本地开发与明确的测试模式

```sh
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
# 普通模式需设置 DATABASE_URL=mysql://... 与 REDIS_HOST
.venv/bin/uvicorn src.main:app --port 19201
# 明确的本地测试模式：SQLite + 同步执行，不可作为Docker验收
LOCAL_TEST=true DATABASE_URL=sqlite:///./pipe-local.sqlite3 .venv/bin/uvicorn src.main:app --port 19201
# 另一个终端
cd frontend
npm install
npm run dev
```

后端主语言 Python3.11；FastAPI0.115.12、scikit-learn1.6.1、NumPy2.2.5、PyMySQL1.1.1。前端 Vue3.5.13、TypeScript5.7.3、Vite5.4.21。Docker 镜像 node20-alpine / nginx1.27-alpine / mysql8 / redis7-alpine。Redis 队列通过 RESP 客户端执行 RPUSH / BLPOP，worker 写状态与错误；LOCAL_TEST=true 才同步计算，默认不会启用。

### 环境变量

|变量|默认值|用途|
|---|---|---|
|COMPOSE_PROJECT_NAME|pipe-priority|五容器命名与卷作用域|
|FRONTEND_PORT/BACKEND_PORT/DB_PORT|18201/19201/17701|宿主端口|
|MYSQL_DATABASE/USER/PASSWORD/ROOT_PASSWORD|见 .env.example|数据库初始化|
|DATABASE_URL|本地SQLite|Docker覆盖为 MySQL 地址|
|REDIS_HOST/REDIS_PORT|127.0.0.1/6379|队列地址，Docker覆盖redis|
|JWT_SECRET|本地演示值|HS256签名，部署须替换|
|SEED_DEMO|true|后端启动自动seed；失败只记录不阻塞|
|ARTIFACT_DIR|/tmp/pipe-priority-artifacts|worker心跳路径|
|LOCAL_TEST|false|显式SQLite/同步测试模式|

## 算法与口径

输入620个样本，特征为 age（年）、pressure_var（压力波动）、diameter（口径）、past_leaks（历史漏损次数）、soil_corrosion（土壤腐蚀指数）及四类 material；二元标签 leak。样本数40–5000，正负类各至少12，管段唯一，拒绝负数、NaN、无标签、未知管材和全缺失列。

1. 75%/25% 分层拆分（固定seed42）；训练部分进行四折分层验证，每折单独拟合中位数填补、标准化与管材独热编码。候选 C=[0.05,0.25,1,4]，按训练 OOF Average Precision 最大选择 C，逻辑回归使用 balanced class weight。独立留出集只用于最终评价。
2. 在训练 OOF 概率上枚举阈值，最小化 `FN×漏检成本 + FP×误检成本`，同时要求选中比例不超过 `日预算/总样本数`。并列选择更少的管段。保留“全部不检”候选以免被迫选择高成本样本。阈值不是按留出集调优。最终部署重拟合全样本得到管段排序，清单按预算严格截取。此时概率为模型分数，未做校准；预算截取与阈值候选数量可以不同。

输出 ROC AUC、AP、精确率、召回率、混淆矩阵、成本、实际ROC/PR坐标、折外C比较、系数、逐段概率、样本剖析与SHA256校验和。系数来自留出评价前的训练模型；部署重拟合只用于清单排序。相关性不等于因果；模拟样本表现不能外推真实漏损效果。CSV仅在计划审批后生成，包含管段、顺位、概率与审批人。数据以有自然键的独立JSON实体表持久化（非逐特征关系表）；大批量训练尚未引入分区与任务取消。

## seed与错误恢复

`backend/scripts/seed_demo.py` 固定random seed20261111，620管段、4片区、3账号、2配置、1完成运行、1批准计划、1报告。自然键存在即保留用户修改；重复运行不会重复新增或覆盖。Redis故障使新运行返回503并标失败；恢复后新建运行。全局ValueError返回422，其他错误返回可重试500。队列最多8个待执行/运行任务。worker异常记录到run.error。

## 目录与枚举位置

`backend/src/{models,schemas,services,controllers,routes,middlewares,config,constants,utils}` 分层；`backend/migrations/001_mysql.sql` 提供幂等建表。`frontend/src/{api,stores,pages,components/common,hooks,utils,constants,types,router}` 分层。

共享 Role/RunStatus/PlanStatus 分别定义在 `backend/src/constants/enums.py` 与 `frontend/src/constants/enums.ts`；服务端服务与种子使用相同字符串值，前端角色store、StatusBadge与页面统一展示。所有测试、截图与日志在批次 `test-artifacts/gb-2102/`，源码不混入测试产物。

## 测试状态

实际结果见 `../../test-artifacts/gb-2102/TESTING.md`。当前环境 Docker socket 权限受限；不能将本地测试视为容器验收。标准库脚本 `tests/docker_acceptance.py` 可在真实5服务健康后执行三角色、403、创建→队列→结果→审批→CSV主流程；默认拒绝本地同步模式。

License: MIT，见 LICENSE。
