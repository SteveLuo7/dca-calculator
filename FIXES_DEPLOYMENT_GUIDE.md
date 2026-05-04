# 修复部署指南

## 本次修复内容

### 1. AMD价格准确性问题 ✅

**问题**: AMD查询出来的价格和谷歌、雅虎搜索出来的价格不一致

**原因**:
- AKShare的美股数据源可能不是最新的
- 缺少备用数据源

**解决方案**:
- 添加了yfinance作为美股的备用数据源
- 优先使用yfinance获取准确的美股价格（Yahoo Finance数据）
- 保留了AKShare作为第一数据源
- 添加了三级降级策略：
  1. AKShare美股实时行情
  2. yfinance实时数据（高精度）
  3. yfinance历史数据（备份）

**修改文件**:
- `backend/main.py` - 在`fetch_quote_data()`函数中添加yfinance支持

### 2. 财报卡片显示问题 ✅

**问题**: 部署后看不到财报卡片

**原因**:
- Railway生产环境没有包含最新的后端代码

**解决方案**:
- 添加了详细的日志记录（logger.info和logger.debug）
- 改进了错误处理和调试信息
- 确保代码已正确提交

**注意事项**:
- 需要重新部署到Railway才能生效
- 使用 `debug_financial.html` 调试工具验证

### 3. 财报下载链接 ✅

**需求**: 希望在财报中外链到完整的财报下载链接

**实现**:
- 在每个财报数据中添加 `download_url` 字段
- A股财报链接格式: `https://data.eastmoney.com/bbsj/{code}/{year}.html`
- 基金链接格式: `http://fund.eastmoney.com/{code}.html`
- 前端显示"📄 查看完整财报"按钮

**修改文件**:
- `backend/main.py` - 在`fetch_financial_reports()`中添加download_url
- `index.html` - 添加下载按钮样式和逻辑

### 4. 搜索后数据更新 ✅

**需求**: 用户每使用搜索一次，总览、新闻、K线图都应该重新根据用户搜索的代码再一次更新

**验证**:
- 代码逻辑已正确实现
- `refreshSelectedCode()`函数会并行获取：
  - PE数据 (`fetchPE`)
  - 新闻 (`fetchNews`)
  - 财报 (`fetchFinancialReports`)
  - 报价 (`fetchQuote`)
  - K线图（如果当前模式是kline）

**确认**: ✅ 无需修改，代码已正确处理

## 部署步骤

### 1. 确认代码已提交

```bash
cd d:/dca-calculator
git status
git add .
git commit -m "修复：AMD价格准确性、财报下载链接、日志改进"
git push origin main
```

### 2. 在Railway重新部署

1. 访问 [Railway](https://railway.app)
2. 进入 `dca-calculator` 项目
3. 点击 "Deployments" 标签
4. 找到最新部署，点击 "Redeploy" 按钮
5. 等待 2-3 分钟让部署完成

### 3. 验证部署

#### 方法1: 使用API测试

```bash
# 测试AMD价格
curl https://dca-calculator-production.up.railway.app/api/quote/AMD

# 测试A股财报
curl https://dca-calculator-production.up.railway.app/api/financial_reports/600519
```

#### 方法2: 使用浏览器

1. 访问 `https://dca-calculator-production.up.railway.app`
2. 按 `Ctrl+F5` 清除缓存
3. 测试不同股票代码：
   - `AMD` - 验证价格准确性（与Yahoo Finance对比）
   - `600519` - 验证财报显示和下载链接
   - `000001` - 验证新闻和K线图更新

#### 方法3: 使用调试工具

1. 打开 `debug_financial.html`
2. 按照页面提示测试API端点
3. 检查每个测试的结果

### 4. 本地测试

在部署前，可以先在本地测试：

```bash
# 启动后端
cd d:/dca-calculator/backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# 或者在另一个终端
cd d:/dca-calculator
python test_fixes.py
```

## 测试脚本说明

### test_fixes.py

自动测试所有修复：

```bash
python test_fixes.py
```

测试内容：
- AMD价格准确性
- A股财报数据
- 财报下载链接
- 所有API端点

### debug_financial.html

浏览器调试页面：
- 自动检测API配置
- 测试多个股票代码
- 检查前端面板是否存在

### verify_financial_deployment.py

代码验证脚本：
- 检查后端代码是否包含财报功能
- 检查前端代码是否包含财报面板
- 检查Dockerfile配置

## 数据源说明

### AMD（美股）价格数据源

1. **AKShare** (东方财富)
   - 数据源: `stock_us_spot_em()`
   - 优点: 国内访问快速
   - 缺点: 可能不是最新数据

2. **yfinance** (Yahoo Finance)
   - 数据源: `ticker.info` 或 `ticker.history()`
   - 优点: 数据准确，与Yahoo Finance一致
   - 缺点: 访问可能较慢

**推荐**: 使用yfinance获取AMD价格，因为它与Yahoo Finance和Google Finance的数据一致。

### A股财报数据源

1. **东方财富 - 财务分析指标**
   - 接口: `stock_financial_analysis_indicator()`
   - 数据: ROE、ROA、EPS、营业收入、净利润、总资产
   - 频率: 年度/季度

2. **东方财富 - 财务报表摘要**
   - 接口: `stock_financial_abstract()`
   - 数据: 营业收入、净利润、每股收益
   - 频率: 年度/季度

**财报下载链接**:
- A股: `https://data.eastmoney.com/bbsj/{code}/{year}.html`
- 基金: `http://fund.eastmoney.com/{code}.html`

## 常见问题

### Q1: 重新部署后AMD价格还是不准确？

**A**:
1. 检查后端日志，确认使用了哪个数据源
2. 确认yfinance已正确安装
3. 手动访问Yahoo Finance对比价格
4. 清除浏览器缓存（Ctrl+F5）

### Q2: 财报卡片仍然不显示？

**A**:
1. 打开浏览器开发者工具（F12）
2. 查看Console标签的错误信息
3. 查看Network标签，找到 `/api/financial_reports/` 请求
4. 检查响应状态码和内容
5. 使用 `debug_financial.html` 进行诊断

### Q3: 财报下载链接点击无效？

**A**:
1. 检查链接格式是否正确
2. 尝试在新标签页打开链接
3. 确认东方财富网站可访问
4. 检查股票代码和年份是否正确

### Q4: 搜索后数据没有更新？

**A**:
1. 打开浏览器开发者工具（F12）
2. 查看Network标签，确认API请求已发送
3. 检查响应是否成功
4. 清除浏览器缓存
5. 检查前端JavaScript是否有错误

## 性能优化

### 缓存策略

- PE数据: 15分钟缓存
- K线数据: 5分钟缓存
- 新闻: 无缓存（实时获取）
- 财报: 无缓存（实时获取）

### 并行请求

前端使用 `Promise.all()` 并行获取数据：
```javascript
await Promise.all([
  fetchPE(code),
  fetchNews(code),
  fetchFinancialReports(code)
]);
```

这样可以显著提高页面加载速度。

## 下一步

### 部署后验证清单

- [ ] AMD价格与Yahoo Finance一致
- [ ] 选择A股股票后能看到财报卡片
- [ ] 财报卡片包含完整财务指标
- [ ] 点击"查看完整财报"可以打开东方财富页面
- [ ] 搜索不同代码后所有数据都正确更新
- [ ] 新闻、K线图、总览都能正常显示

### 持续改进

1. 添加更多美股数据源备份
2. 支持季度财报数据
3. 添加财报数据导出功能
4. 改进财报数据可视化

## 联系支持

如果遇到问题：

1. 查看浏览器控制台错误（F12）
2. 查看Railway部署日志
3. 运行 `test_fixes.py` 本地测试
4. 打开 `debug_financial.html` 诊断
5. 提供错误信息和重现步骤
