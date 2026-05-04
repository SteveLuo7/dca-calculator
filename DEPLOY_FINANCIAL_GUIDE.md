# 财报功能部署指南

## 问题诊断

你报告的问题：部署成功后看不到财报卡片

### 根本原因

Railway 的生产环境部署没有包含最新的后端代码（包含 `/api/financial_reports` 端点）。

## 解决方案

### 方案 1: 重新部署到 Railway（推荐）

1. **确认代码已推送到 GitHub**
   ```bash
   cd d:/dca-calculator
   git status  # 确认所有修改已提交
   git push origin main  # 确保代码已推送
   ```

2. **在 Railway 控制台触发重新部署**
   - 登录 [Railway](https://railway.app)
   - 进入你的 `dca-calculator` 项目
   - 点击 "Deployments" 标签
   - 找到最新的部署，点击 "Redeploy" 按钮
   - 等待部署完成（约 2-3 分钟）

3. **验证部署**
   ```bash
   # 测试新端点
   curl https://dca-calculator-production.up.railway.app/api/financial_reports/600519
   ```
   
   应该返回类似这样的 JSON：
   ```json
   {
     "code": "600519",
     "name": "贵州茅台",
     "reports": [
       {
         "year": "2023",
         "roe": 25.5,
         "eps": 43.6,
         ...
       }
     ],
     "count": 5
   }
   ```

4. **刷新前端页面**
   - 访问 `https://dca-calculator-production.up.railway.app`
   - 选择一个 A 股股票（如 600519 贵州茅台）
   - 检查"财报信息"面板是否显示

### 方案 2: 使用 Railway CLI（如果已安装）

```bash
# 登录 Railway
railway login

# 触发重新部署
railway up

# 或者直接重启
railway restart
```

### 方案 3: 检查部署日志

如果重新部署后仍有问题，检查部署日志：

1. 在 Railway 控制台
2. 点击项目名称
3. 查看 "Deployments" 标签下的最新部署日志
4. 检查是否有构建错误

## 常见问题

### Q1: 重新部署后仍然看不到财报？

**A:** 检查以下几点：
1. 确保浏览器缓存已清除（Ctrl+F5 或 Cmd+Shift+R）
2. 打开浏览器开发者工具（F12），查看 Console 是否有错误
3. 查看 Network 标签，检查 `/api/financial_reports/{code}` 请求是否成功
4. 确认选择的是 A 股股票代码（如 600519、000001），不是指数或基金

### Q2: API 返回 404？

**A:** 说明后端代码未更新。需要：
1. 确认 `backend/main.py` 包含 `get_financial_reports` 函数
2. 确认 Dockerfile 正确复制了后端文件
3. 重新部署到 Railway

### Q3: API 返回 500 错误？

**A:** 说明后端代码已更新但有运行时错误：
1. 检查 Railway 的日志
2. 可能是 AKShare 数据源问题
3. 可能是 Python 依赖未安装

## 验证步骤

### 1. 测试后端 API

```bash
# 本地测试
curl http://localhost:8000/api/financial_reports/600519

# 部署测试
curl https://dca-calculator-production.up.railway.app/api/financial_reports/600519
```

### 2. 测试前端页面

```bash
# 本地测试
python -m http.server 8080 --directory frontend

# 然后访问 http://localhost:8080
```

### 3. 使用调试工具

打开 `debug_financial.html` 页面，它会自动测试：
- API 配置是否正确
- API 端点是否可用
- 前端面板是否存在

## 代码检查清单

### 后端 (backend/main.py)
- [x] `fetch_financial_reports()` 函数存在
- [x] `@app.get("/api/financial_reports/{code}")` 端点存在
- [x] 函数能正确返回 JSON 数据

### 前端 (index.html)
- [x] `#financialPanel` 面板存在
- [x] `#financialList` 容器存在
- [x] `fetchFinancialReports()` 函数存在
- [x] `renderFinancialReports()` 函数存在
- [x] 在 `refreshSelectedCode()` 中调用 `fetchFinancialReports()`

### 样式
- [x] `.financial-list` 样式存在
- [x] `.financial-item` 样式存在
- [x] `.financial-header` 样式存在
- [x] `.financial-metrics` 样式存在
- [x] `.metric-item` 和 `.metric-value` 样式存在

## 数据支持

目前支持的财务数据：

- ✅ A 股股票（6位数字代码）：完整财务数据
  - ROE（净资产收益率）
  - ROA（总资产收益率）
  - EPS（每股收益）
  - 营业收入
  - 净利润
  - 总资产

- ✅ ETF/基金：显示基金信息提示
  - 提示：基金产品无传统财务报表

- ⚠️ 指数：无财务数据
  - 显示：暂无财务年报数据

- ⚠️ 海外市场：无财务数据
  - 显示：暂无财务年报数据

## 下一步

重新部署后，如果还有问题：

1. 查看浏览器控制台错误
2. 查看 Network 请求详情
3. 检查 Railway 部署日志
4. 使用 `debug_financial.html` 进行诊断
5. 运行 `test_api_endpoint.py` 测试 API

## 联系支持

如果以上方法都无法解决问题，请提供以下信息：

1. 部署日志截图
2. 浏览器控制台错误信息
3. Network 请求详情
4. Railway 项目链接
5. 测试的股票代码
