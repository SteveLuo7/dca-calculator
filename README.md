# 定投收益计算器

基于市盈率的长期定投收益模拟工具。
实时获取 A 股主流指数 PE 数据（AKShare），支持 Excel/CSV 导出。

---

## 功能特性

- 📊 **实时 PE 数据**：接入 AKShare，自动获取沪深300、上证50、中证500、创业板指等指数的最新 PE、PB 及10年历史分位
- 📈 **三情景预测**：基于盈利收益率模型，自动估算悲观/基准/乐观三种年化回报
- 🗂 **30年收益明细**：逐年展示累计投入、组合价值、总收益率、年化回报
- 📉 **PE历史走势图**：可视化过去10年PE走势，判断当前估值位置
- ⬇ **多格式导出**：导出 Excel（含三情景工作表）/ CSV / 打印PDF

---

## 快速启动

### 方式一：Docker Compose（推荐）

```bash
# 克隆项目
git clone <your-repo>
cd dca-calculator

# 一键启动
docker-compose up -d

# 访问
# 前端：http://localhost
# API：http://localhost:8000
```

### 方式二：本地开发

**后端：**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**前端：**
```bash
# 直接用浏览器打开
open frontend/index.html

# 或用 nginx/caddy 托管
# 确保 API_BASE 指向 http://localhost:8000
```

---

## 部署到云服务器

### 腾讯云 / 阿里云

```bash
# 1. 安装 Docker
curl -fsSL https://get.docker.com | sh

# 2. 上传文件
scp -r dca-calculator/ user@your-server:/opt/

# 3. 启动
cd /opt/dca-calculator
docker-compose up -d
```

### Vercel（仅前端）+ Railway（后端）

**前端 → Vercel：**
- 将 `frontend/index.html` 推送到 GitHub
- 在 `index.html` 中将 API 地址改为 Railway 后端的 URL
- Vercel 导入 GitHub 仓库，自动部署

**后端 → Railway：**
- 推送整个项目到 GitHub
- Railway 新建项目，选择 GitHub 仓库
- 设置启动命令：`uvicorn main:app --host 0.0.0.0 --port $PORT`
- 设置根目录：`backend`

---

## API 接口说明

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/indices` | 获取所有支持的指数列表 |
| GET | `/api/pe/{code}` | 获取指定指数的实时PE、PB、分位数 |
| GET | `/api/pe/{code}/history` | 获取PE历史数据（`?years=10`）|
| GET | `/api/export/excel` | 生成 Excel 报告并下载 |

**示例：**
```bash
# 获取沪深300 PE
curl http://localhost:8000/api/pe/000300

# 导出Excel
curl "http://localhost:8000/api/export/excel?code=000300&name=沪深300&pe=13&monthly_amount=2000&freq=12&bear_rate=0.05&base_rate=0.10&bull_rate=0.15" -o report.xlsx
```

---

## 收益率估算模型

```
悲观年化 = (1/PE) × 0.65
基准年化 = (1/PE) + 盈利增长率 × 0.5
乐观年化 = (1/PE) + 盈利增长率
```

各指数参考盈利增长率：
- 沪深300：6%  |  上证50：5%  |  中证500：7%
- 创业板指：10%  |  标普500：7%  |  纳斯达克100：10%

---

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | FastAPI · AKShare · Pandas · openpyxl |
| 前端 | 原生 HTML/CSS/JS · Chart.js · SheetJS |
| 部署 | Docker · Nginx · Docker Compose |

---

## 注意事项

- AKShare 数据来源为天天基金等公开平台，仅支持 A 股主流指数的实时PE
- 港股、美股指数暂使用离线默认PE值，可在 `main.py` 的 `INDEX_CONFIG` 中扩展
- 收益率估算基于历史规律，不构成投资建议
