# RentFind 租房与物业报修平台

```bash
cp .env.example .env
docker compose up -d --build
```

RentFind 面向房东、租客和物业人员，提供房源发布、搜索预约、合同管理和报修跟踪能力。物业报修支持**分级响应、接单留痕、超时单次升级**。

## 项目主要功能

- 房源发布：小区、户型、面积、租金、押金、付款方式、照片和设施。
- 搜索筛选：区域、价格、户型、面积、设施，并支持列表和地图视图切换。
- 预约看房：租客选择时间段，房东确认后生成通知。
- 合同管理：生成租赁合同模板并记录租期、租金、双方信息和状态。
- 物业报修：
  - 住户提交工单（故障类型：水电 / 门锁 / 管道 / 家电 / 其他 + 描述 + 照片）。
  - **分级响应**：水电、门锁须 **30 分钟内**响应；管道、家电、其他须 **4 小时内**响应，提交时按类型计算响应截止时间。
  - 物业人员**接单**即记录处理人和接单时间，状态变为处理中，全部操作写入工单事件流水。
  - **超时升级**：超过响应时限仍未接单的工单只能升级一次，自动转派给**未完成工单最少**的在岗物业人员，并保留升级记录（原处理人、新处理人、时间、备注）。
  - 重复或并发升级不会重复转派：数据库行锁 + 升级幂等标记，工单状态、处理人和升级记录在同一事务内，要么一并成功，要么全部不变。
  - 页面支持按**待响应、已超时**等状态筛选，实时显示剩余响应时间 / 已超时时长（以服务端时间校正），刷新后状态一致。
- 角色区分：房东、租客、物业人员拥有不同工作台。

### 报修接口一览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/repair/tickets/?status=all/pending/overdue/processing/completed` | 工单列表与状态筛选 |
| POST | `/api/repair/tickets/` | 住户提交报修（自动计算响应截止时间） |
| GET | `/api/repair/tickets/{id}/` | 工单详情（含完整事件流水） |
| POST | `/api/repair/tickets/{id}/accept/` | 物业接单，记录处理人与接单时间 |
| POST | `/api/repair/tickets/{id}/complete/` | 处理人完成工单 |
| POST | `/api/repair/tickets/{id}/escalate/` | 超时工单升级（仅一次） |
| POST | `/api/repair/tickets/escalate-overdue/` | 扫描并升级全部超时工单（幂等） |
| GET | `/api/repair/staff/` | 在岗物业人员 |
| GET | `/api/repair/time/` | 服务器时间（前端校时用） |

## 快速启动方式

首次启动前执行：

```bash
cp .env.example .env
docker compose up -d --build
```

访问地址：http://localhost:18407

后端容器启动时会自动执行数据库迁移并灌入演示数据（3 名物业人员、7 个覆盖各状态的工单），同时每 60 秒扫描一次超时工单并升级。也可手动执行：

```bash
docker compose exec backend python manage.py escalate_overdue
```

## 本地开发方式

```bash
cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
python manage.py migrate && python manage.py runserver 0.0.0.0:19407
```

```bash
cd frontend && npm install && npm run dev
```

运行后端测试（含分级时限、接单、升级幂等、最少负载转派、事务回滚、API 筛选；并发行锁用例在 PostgreSQL 下运行）：

```bash
cd backend && python manage.py test app.apps.repair
```

## 技术栈

| 模块 | 技术 |
| --- | --- |
| 前端 | Vue 3、TypeScript、Element Plus、Vite、高德地图 JS API |
| 后端 | Python、Django、Django REST Framework |
| 数据库 | PostgreSQL（本地开发可使用 SQLite） |
| 认证 | JWT |
| 部署 | Docker Compose、Nginx、Gunicorn |

## 项目目录结构

```text
.
├── backend
│   ├── app
│   │   ├── apps
│   │   │   ├── users
│   │   │   ├── properties
│   │   │   ├── booking
│   │   │   ├── contract
│   │   │   └── repair
│   │   │       ├── models/          # 物业人员 / 工单 / 事件流水
│   │   │       ├── services/        # 提交、接单、完成、SLA、超时升级（事务）
│   │   │       ├── serializers/
│   │   │       ├── views/
│   │   │       ├── selectors.py     # 待响应 / 已超时筛选
│   │   │       └── management/commands/escalate_overdue.py
│   │   ├── constants/               # 枚举、分级时限、错误码
│   │   ├── middleware/
│   │   └── utils/                   # 日志、统一异常、数据库锁重试
│   ├── database
│   ├── entrypoint.sh                # 迁移 + 定时升级扫描 + gunicorn
│   └── manage.py
├── frontend
│   └── src
│       ├── api
│       ├── components/repair
│       ├── composables
│       ├── constants
│       ├── utils
│       └── views
├── docker-compose.yml
└── README.md
```

## 环境变量说明

| 变量 | 说明 |
| --- | --- |
| COMPOSE_PROJECT_NAME | Compose 项目名，固定为 rentfind |
| POSTGRES_DB / POSTGRES_USER / POSTGRES_PASSWORD | PostgreSQL 数据库名、账号、密码 |
| DATABASE_URL | Django 连接 PostgreSQL 的地址 |
| DJANGO_SECRET_KEY | Django 密钥 |
| DJANGO_DEBUG | 是否开启调试模式 |
| AMAP_KEY | 高德地图 JS API Key |

## Docker 部署说明

Compose 顶层声明 `name: rentfind`，容器名带 `rentfind-` 前缀，数据库和媒体文件分别使用命名卷持久化，前端 Nginx 将 `/api` 与 `/media` 代理到后端 `backend:8000`。前端映射 18407:80，后端映射 19407:8000，PostgreSQL 配置了 healthcheck。

## License

MIT
