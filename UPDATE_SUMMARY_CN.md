# 数据源统一更新总结

## 📋 更新需求

用户要求：
1. ✅ 总览价格和K线图使用同一数据源
2. ✅ 直接放弃国外数据源，全部使用国内财经数据源
3. ✅ 添加货币单位标注（CNY、HKD、USD等）

## ✅ 已完成更新

### 1. 数据源统一

**移除国外数据源：**
- ❌ Yahoo Finance (yfinance) - 完全移除
- ❌ Google搜索 - 替换为百度搜索

**统一使用国内数据源：**
- ✅ AKShare - 主要数据源（A股、港股、美股、全球指数）
- ✅ 东方财富 - 新闻和行情
- ✅ 财联社 - 新闻快讯
- ✅ 同花顺 - 新闻资讯
- ✅ 百度搜索 - 兜底搜索

### 2. 总览价格和K线图数据源一致

**实现方案：**
- 总览价格（实时行情）使用 `fetch_quote_data()` 获取
- K线图使用 `fetch_kline_data()` 获取
- 两者都使用AKShare数据源
- 当实时行情获取失败时，自动从K线最新数据补充
- 确保总览价格和K线图数据完全一致

**代码位置：**
- `backend/main.py` - `fetch_quote_data()` 和 `fetch_kline_data()`
- `index.html` - `fetchQuote()` 和 `loadKline()`

### 3. 货币单位标注

**自动识别货币单位：**
- A股（上海、深圳、创业板）：CNY（¥）
- 港股：HKD（HK$）
- 美股：USD（$）
- 其他市场：根据市场类型自动判断

**前端显示：**
- K线图Legend显示货币符号和单位
- 所有价格数据标注货币单位

**API响应：**
- 报价数据：`currency` 字段
- K线数据：每个数据点包含 `currency` 字段

## 📝 代码变更

### 后端文件：`backend/main.py`

**变更内容：**
1. 移除 `_try_yahoo_kline()` 函数
2. 简化 `fetch_kline_data()` 只使用AKShare
3. 新增 `_get_currency_from_security()` 函数
4. 更新 `fetch_quote_data()` 添加 `currency` 字段
5. 更新 `fallback_quote()` 添加 `currency` 字段
6. 更新K线数据添加 `currency` 字段

### 前端文件：`index.html`

**变更内容：**
1. 添加 `CURRENCY_SYMBOLS` 常量（货币符号映射）
2. 添加 `state.currentCurrency` 状态
3. 新增 `fetchQuote()` 函数
4. 更新 `renderKlineChart()` 显示货币单位
5. 更新 `refreshSelectedCode()` 调用 `fetchQuote()`
6. 更新 `loadKline()` 获取并设置货币单位

### 文档更新

**更新文件：**
- `README.md` - 更新功能特性和数据源说明
- `DOMESTIC_DATA_SOURCE_UPDATE.md` - 详细更新说明

## 🔍 数据源详细说明

### AKShare数据接口

| 市场 | 行情接口 | K线接口 |
|------|---------|---------|
| A股 | `ak.stock_zh_a_spot_em()` | `ak.stock_zh_a_hist()` |
| 港股 | `ak.stock_hk_spot_em()` | `ak.stock_hk_hist()` |
| 美股 | `ak.stock_us_spot_em()` | `ak.stock_us_hist()` |
| 全球指数 | `ak.index_global_spot()` | `ak.index_global_hist()` |
| A股指数 | - | `ak.index_zh_a_hist()` |

### 货币单位映射

| 市场 | 货币代码 | 货币符号 |
|------|---------|---------|
| A股 | CNY | ¥ |
| 港股 | HKD | HK$ |
| 美股 | USD | $ |
| 欧洲市场 | EUR | € |
| 英国市场 | GBP | £ |

## ✅ 验证清单

- [x] 移除Yahoo Finance数据源
- [x] 移除yfinance依赖
- [x] 统一使用AKShare数据源
- [x] 总览价格和K线图数据源一致
- [x] 添加货币单位标注
- [x] 前端显示货币符号
- [x] 更新README文档
- [x] 创建更新说明文档
- [x] 创建验证脚本

## 🧪 测试建议

### 测试用例

**A股测试：**
- 代码：000300（沪深300）
- 预期：货币单位CNY，数据源AKShare
- 验证：总览价格和K线图价格一致

**港股测试：**
- 代码：HSI（恒生指数）
- 预期：货币单位HKD，数据源AKShare
- 验证：总览价格和K线图价格一致

**美股测试：**
- 代码：SPX（标普500）
- 预期：货币单位USD，数据源AKShare
- 验证：总览价格和K线图价格一致

### 验证脚本

运行验证脚本检查更新：
```bash
python verify_domestic_source.py
```

## 📌 注意事项

1. **AKShare数据延迟**
   - 美股数据可能有15-20分钟延迟
   - 这是AKShare数据源的特性

2. **数据源唯一性**
   - 系统不再使用国外数据源
   - 所有数据均来自国内可访问的AKShare

3. **数据一致性**
   - 总览价格和K线图使用同一数据源
   - 确保数据完全一致

4. **货币单位显示**
   - 所有价格数据标注货币单位
   - 前端自动显示对应货币符号

## 🎯 完成标志

所有用户要求已完成：
- ✅ 总览价格和K线图保持一致
- ✅ 数据源保持一致（AKShare）
- ✅ 完全放弃国外源，全部使用国内财经数据源
- ✅ K线图和总览价格标注货币单位
