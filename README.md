# RentFind 租房与物业报修平台

```bash
cp .env.example .env
docker compose up -d --build
```

RentFind 面向房东、租客和物业人员，提供房源发布、搜索预约、合同管理和报修跟踪能力。

## 项目主要功能

- 房源发布：小区、户型、面积、租金、押金、付款方式、照片和设施。
- 搜索筛选：区域、价格、户型、面积、设施，并支持列表和地图视图切换。
- 预约看房：租客选择时间段，房东确认后生成通知。
- 合同管理：生成租赁合同模板并记录租期、租金、双方信息和状态。
- 物业报修：提交故障类型、描述和照片，物业接单并更新进度；按故障类型分级响应，超时工单可升级转派。
- 角色区分：房东、租客、物业人员拥有不同工作台。

## 物业报修分级响应与超时升级

- **分级响应时限**：水电、门锁须 30 分钟内响应；管道、家电、其他须 4 小时内响应，截止时间在提交时按类型写入。
- **接单**：物业人员接单后记录处理人和接单时间，工单进入「处理中」，重复接单会被拒绝。
- **超时升级**：超过时限仍未接单即为超时；超时工单只能升级一次，自动转派给当前未完成工单最少的物业人员，并保留提交、接单、升级、完成全链路流转记录。
- **并发安全**：接单与升级在单个数据库事务内以条件更新（`UPDATE ... WHERE 未接单/未升级`）作为并发闸门，重复或并发升级不会产生第二次转派；状态、处理人、记录要么一并成功，要么全部不变。
- **工作台**：支持按「待响应 / 已超时 / 处理中 / 已完成」与故障类型筛选，工单卡片实时显示剩余/超时计时，刷新页面后状态一致。
- **定时升级（可选）**：执行 `python manage.py escalate_overdue` 可批量升级全部超时未接单工单，命令幂等，可由 cron 每分钟调用。

## 快速启动方式

首次启动前执行：

```bash
cp .env.example .env
docker compose up -d --build
```

访问地址：http://localhost:18407

## 本地开发方式

```bash
cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && python manage.py runserver 0.0.0.0:8000
cd frontend && npm install && npm run dev
```

## 技术栈

| 模块 | 技术 |
| --- | --- |
| 前端 | Vue 3、TypeScript、Element Plus、Vite、高德地图 JS API |
| 后端 | Python、Django、Django REST Framework |
| 数据库 | PostgreSQL |
| 认证 | JWT |
| 部署 | Docker Compose、Nginx |

## 项目目录结构

```text
.
├── backend
│   ├── app
│   ├── database
│   └── manage.py
├── frontend
│   ├── src
│   └── nginx.conf
├── docker-compose.yml
└── README.md
```

## 环境变量说明

| 变量 | 说明 |
| --- | --- |
| COMPOSE_PROJECT_NAME | Compose 项目名，固定为 rentfind |
| DATABASE_URL | Django 连接 PostgreSQL 的地址 |
| DJANGO_SECRET_KEY | Django 密钥 |
| AMAP_KEY | 高德地图 JS API Key |

## Docker 部署说明

Compose 顶层声明 `name: rentfind`，容器名带 `rentfind-` 前缀，数据库和媒体文件分别使用命名卷持久化，前端 Nginx 将 `/api` 代理到后端 `backend:8000`。

## License

MIT
