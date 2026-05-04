# 定投收益计算器

基于市盈率的长期定投收益模拟工具。
实时获取 A 股主流指数 PE 数据（AKShare），支持 Excel/CSV 导出。

---

## 功能特性

- **实时 PE/PB 数据**：接入 AKShare，获取 A 股指数实时 PE、PB 及 10 年历史分位；海外/缺失数据自动降级为默认值
- **指数 / 股票查询**：支持预设指数，也支持输入股票或指数代码，例如 `000300`、`600519`、`SPX`、`AAPL`
- **三情景预测**：基于盈利收益率模型，估算悲观、基准、乐观三种年化回报
- **30 年收益明细**：逐年展示累计投入、组合价值、收益额、总收益率、年化回报
- **图表分析**：支持收益曲线、PE 历史走势、K 线行情和成交量图（支持日K/周K/月K/年K、近一年/历史至今）
- **相关新闻**：查询标的相关新闻，A 股股票优先使用东方财富新闻源
- **多格式导出**：支持 Excel、CSV、打印 / PDF
- **全球市场支持**：支持 A 股、港股、美股等全球市场指数和股票的实时行情与K线数据

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

# 测试模块导入（可选）
python test_imports.py

# 启动服务
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

### Railway / Vercel / GitHub Pages

**Railway 单服务部署：**
- 本项目的 `Dockerfile` 会复制 `frontend/` 并由 FastAPI 直接托管前端页面
- 页面入口是 `frontend/index.html`，不是仓库根目录的 `index.html`
- Railway 部署时使用根目录和 `Dockerfile` 即可

**Vercel 或 GitHub Pages 仅前端部署：**
- Vercel 建议部署 `frontend/index.html`
- GitHub Pages 通常会读取 `docs/index.html`，需要保持它和 `frontend/index.html` 同步
- 前端中的 API 地址需要指向 Railway 后端 URL

---

## API 接口说明

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/indices` | 获取所有支持的指数列表 |
| GET | `/api/market/indices` | 按地区分组获取指数列表 |
| GET | `/api/search` | 搜索指数/股票/基金 |
| GET | `/api/pe/{code}` | 获取指定指数的实时PE、PB、分位数 |
| GET | `/api/pe/{code}/history` | 获取PE历史数据（`?years=10`）|
| GET | `/api/quote/{code}` | 获取实时行情（价格、涨跌幅等）|
| GET | `/api/kline/{code}` | 获取K线数据（`?period=daily&range=all`）|
| GET | `/api/news/{code}` | 获取相关新闻 |
| GET | `/api/export/excel` | 生成 Excel 报告并下载 |

**示例：**
```bash
# 获取沪深300 PE
curl http://localhost:8000/api/pe/000300

# 获取标普500实时行情
curl http://localhost:8000/api/quote/SPX

# 获取苹果股票K线（周线）
curl "http://localhost:8000/api/kline/AAPL?period=weekly&range=all"

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
- 海外市场（港股、美股等）的实时行情和K线数据通过AKShare提供，若获取失败会自动降级为静态基准数据
- 收益率估算基于历史规律，不构成投资建议

## 支持的市场和标的

### A股市场
- 指数：沪深300、上证50、中证500、中证1000、创业板指等
- 股票：600000-699999（沪市）、000000-003999（深市）、300000-309999（创业板）
- 基金：159/160/161/162/164/510/511/512/513/515/516/517/518/588开头的基金

### 港股市场
- 指数：恒生指数 (HSI)
- 股票：0700.HK（腾讯控股）、9988.HK（阿里巴巴）等，代码格式为 `XXXX.HK`

### 美股市场
- 指数：标普500 (SPX)、纳斯达克100 (NDX)、道琼斯工业指数 (DJI)、罗素2000 (RUT)
- 股票：AAPL（苹果）、MSFT（微软）、NVDA（英伟达）、TSLA（特斯拉）等

### 其他全球市场
- 欧洲市场：欧洲STOXX50、德国DAX、英国富时100、法国CAC40
- 亚洲市场：日经225、韩国KOSPI、印度SENSEX
- 美洲市场：巴西Bovespa、加拿大TSX
