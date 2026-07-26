# 个人数据管家

轻量级个人数据管理平台，支持动态创建数据项、自定义字段、行内编辑、定时提醒和邮件通知。

## 功能特性

- **动态数据管理** — 自由创建管理项（账号信息、备忘录等），自定义字段
- **双击行内编辑** — 双击单元格即可修改，批量保存
- **定时提醒** — 支持一次性/多次/循环提醒，邮件通知
- **CSV 导入导出** — 批量导入导出数据
- **自定义站点标题** — 名称、图标均可自定义
- **SQLite 存储** — 零配置，数据文件独立
- **双平台部署** — Windows 直跑 / Docker 一键部署

## 快速开始

### Windows 本地部署

```bash
# 1. 确保安装了 Python 3.10+
python --version

# 2. 双击运行
start.bat
```

浏览器会自动打开 `http://localhost:5000`，默认账号 `admin` / `admin123`。

### Docker 部署（NAS / 云服务器）

```bash
# 1. 准备数据目录
mkdir data

# 2. 修改 docker-compose.yml 中的 JWT_SECRET
#    （改为至少32位的随机字符串）

# 3. 启动
docker-compose up -d

# 4. 访问 http://你的IP:5000
```

### 绿联 NAS 部署

1. 打开绿联 UGOS Pro → **Docker** → **项目**
2. 点击 **创建** → 输入项目名称（如 `mydb`）
3. 将项目上传到 NAS 的 Docker 共享目录，或直接粘贴 `docker-compose.yml` 内容
4. 设置环境变量 `JWT_SECRET`（随机字符串）
5. 端口映射：`5000:5000`
6. 存储卷映射：`./data` → `/app/data`
7. 点击部署

部署后通过 `http://NAS的IP:5000` 访问。

## 项目结构

```
mydb/
├── backend/                # Flask 后端
│   ├── app.py              # 入口
│   ├── config.py           # 配置
│   ├── requirements.txt    # Python 依赖
│   ├── database/           # 数据库
│   ├── routes/             # API 路由
│   ├── services/           # 业务服务
│   ├── scheduler/          # 定时任务
│   └── utils/              # 工具
├── frontend/               # Vue 3 前端
│   └── src/
├── Dockerfile              # Docker 镜像构建
├── docker-compose.yml      # Docker 编排
├── start.bat               # Windows 启动脚本
└── README.md
```

## 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `JWT_SECRET` | JWT 签名密钥（**Docker 部署必填**） | 随机生成 |
| `PORT` | 服务端口 | `5000` |
| `CORS_ORIGINS` | 外网部署时限制允许的域名 | `*` |
| `FLASK_DEBUG` | 调试模式开关 | `false` |

## 默认账号

| 用户名 | 密码 |
|--------|------|
| admin | admin123 |

> 首次登录后请立即在「系统设置 → 常用设置 → 修改账密」中修改密码。

## 技术栈

- **后端**: Python Flask + SQLite + APScheduler + waitress
- **前端**: Vue 3 + Element Plus + Vite 5
- **部署**: Docker Compose

## 许可证

MIT
