# 启动和测试指南

## 前端更新状态

✅ 前端已成功更新到 `frontend/index.html`，包含以下改进：

1. **删除了搜索栏**：移除了自定义代码搜索功能
2. **新增市场标签页**：
   - 🏯 亚洲市场
   - 🏰 欧洲市场  
   - 🗽 美洲市场

3. **每个市场包含两个分区**：
   - 📈 权重股票
   - 💰 基金

4. **优化了数据加载**：只加载当前激活市场的数据，提高性能

## 本地测试步骤

### 方法1：使用Conda环境（推荐）

如果你有Conda环境，请执行以下步骤：

```bash
# 1. 进入项目目录
cd d:\dca-calculator

# 2. 激活你的Conda环境（根据你的环境名称调整）
conda activate your_env_name

# 3. 进入后端目录
cd backend

# 4. 安装依赖（如果还没安装）
pip install -r requirements.txt

# 5. 启动后端服务
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 6. 在浏览器中打开
# http://localhost:8000
```

### 方法2：使用Python虚拟环境

```bash
# 1. 创建虚拟环境（如果还没有）
cd d:\dca-calculator\backend
python -m venv venv

# 2. 激活虚拟环境
venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动服务
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 依赖安装要求

确保你的Python环境包含以下依赖（已在 `backend/requirements.txt` 中列出）：

```txt
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
akshare>=1.11.0
pandas>=2.0.0
openpyxl>=3.1.0
pydantic>=2.0.0
```

## 测试要点

启动后端服务后，在浏览器中访问 `http://localhost:8000`，检查以下功能：

1. ✅ 页面标题显示 "定投收益计算器 - 全球市场版"
2. ✅ 左侧显示 "🌍 选择市场" 面板，有三个标签页
3. ✅ 点击不同标签可以切换市场（亚洲、欧洲、美洲）
4. ✅ 每个市场显示"📈 权重股票"和"💰 基金"两个分区
5. ✅ 点击资产卡片可以选中并加载PE数据
6. ✅ 没有搜索栏输入框

## API测试

你也可以直接测试API端点：

```bash
# 测试搜索API - 亚洲市场股票
curl "http://localhost:8000/api/search?region=亚洲市场&asset_type=stock&limit=20"

# 测试搜索API - 欧洲市场基金
curl "http://localhost:8000/api/search?region=欧洲市场&asset_type=fund&limit=20"

# 测试PE数据API
curl "http://localhost:8000/api/pe/000300"
```

## 故障排除

### 问题：前端没有更新
**解决方案**：确保浏览器清除缓存或使用无痕模式打开 `http://localhost:8000`

### 问题：API返回404
**解决方案**：检查后端服务是否正常启动，查看终端是否有错误信息

### 问题：资产数据为空
**解决方案**：这是正常的，因为后端使用的是静态测试数据。你可以检查 `backend/data_modules.py` 中的数据结构。

## 项目文件结构

```
d:/dca-calculator/
├── backend/
│   ├── main.py              # FastAPI后端主文件
│   ├── data_modules.py      # 数据模块（包含GLOBAL_STOCKS, GLOBAL_ETF）
│   ├── search_module.py     # 搜索模块
│   └── requirements.txt     # Python依赖
├── frontend/
│   └── index.html           # 已更新的前端文件 ✅
├── index.html               # 旧版本（已弃用）
└── docs/                    # 文档目录
```

## 后续部署

如果要部署到生产环境，项目已配置支持：
- Railway（通过 `railway.json` 配置）
- Docker（通过 `Dockerfile` 和 `docker-compose.yml` 配置）

## 注意事项

- 后端会自动查找前端文件，优先查找 `backend/frontend/`，然后是 `frontend/`
- 当前前端文件在 `frontend/index.html`，后端应该能正确找到它
- 如果需要修改前端，直接编辑 `frontend/index.html` 即可
