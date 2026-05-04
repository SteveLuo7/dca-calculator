# 数据源统一更新说明

## 更新概述

本次更新将系统数据源完全切换为国内数据源（AKShare），确保总览价格和K线图数据源一致，并添加货币单位标注。

---

## 主要变更

### 1. 完全使用国内数据源

**移除的国外数据源：**
- ❌ Yahoo Finance (yfinance) - 已完全移除
- ❌ Google搜索 - 已替换为百度搜索

**保留的国内数据源：**
- ✅ AKShare - 主要数据源（包含A股、港股、美股、全球指数）
- ✅ 东方财富 - 新闻和行情
- ✅ 财联社 - 新闻快讯
- ✅ 同花顺 - 新闻资讯
- ✅ 百度搜索 - 兜底搜索入口

### 2. 总览价格和K线图数据源统一

**统一策略：**
- 总览价格（实时行情）使用AKShare数据源
- K线图使用AKShare数据源
- 当实时行情获取失败时，自动从K线最新数据补充
- 确保两者数据完全一致

**技术实现：**
```python
# fetch_quote_data() 获取实时行情
# 失败时从 fetch_kline_data() 获取最新K线数据
# 两者使用同一数据源（AKShare）
```

### 3. 货币单位标注

**货币单位自动识别：**
- A股（上海、深圳、创业板）：CNY（人民币）
- 港股：HKD（港币）
- 美股：USD（美元）
- 其他市场：根据市场类型自动判断

**前端显示：**
```javascript
const CURRENCY_SYMBOLS = {
  'CNY': '¥',
  'HKD': 'HK$',
  'USD': '$',
  'EUR': '€',
  'GBP': '£'
};
```

**API响应包含：**
- 总览价格：`currency` 字段
- K线数据：每个数据点包含 `currency` 字段
- 前端自动显示对应货币符号

---

## 数据源详细说明

### AKShare数据接口

**A股市场：**
- 行情：`ak.stock_zh_a_spot_em()`
- K线：`ak.stock_zh_a_hist()`
- 新闻：`ak.stock_news_em()`
- PE估值：`ak.stock_zh_a_spot_em()`

**港股市场：**
- 行情：`ak.stock_hk_spot_em()`
- K线：`ak.stock_hk_hist()`

**美股市场：**
- 行情：`ak.stock_us_spot_em()`
- K线：`ak.stock_us_hist()`

**全球指数：**
- 行情：`ak.index_global_spot()`
- K线：`ak.index_global_hist()`

**A股指数：**
- K线：`ak.index_zh_a_hist()`
- PE：`ak.index_value_hist_funddb()`

---

## 代码变更清单

### 后端文件：`backend/main.py`

1. **移除Yahoo Finance相关代码**
   - 删除 `_try_yahoo_kline()` 函数
   - 移除yfinance导入

2. **简化数据源逻辑**
   - `fetch_kline_data()` 只使用AKShare
   - 移除Yahoo Finance降级策略

3. **添加货币单位函数**
   - 新增 `_get_currency_from_security()` 函数
   - 根据证券代码和市场自动判断货币单位

4. **更新报价数据**
   - `fetch_quote_data()` 添加 `currency` 字段
   - `fallback_quote()` 添加 `currency` 字段

5. **更新K线数据**
   - 每个K线数据点添加 `currency` 字段

### 前端文件：`index.html`

1. **添加货币符号映射**
   - 新增 `CURRENCY_SYMBOLS` 常量
   - 支持多种货币符号

2. **添加当前货币状态**
   - `state.currentCurrency` 追踪当前货币单位

3. **新增获取报价函数**
   - `fetchQuote()` 获取实时报价和货币单位

4. **更新K线图显示**
   - `renderKlineChart()` 显示货币符号
   - Legend区域显示货币单位

5. **更新数据加载流程**
   - `refreshSelectedCode()` 调用 `fetchQuote()`
   - 确保货币单位及时更新

---

## 数据一致性保证

### 总览价格和K线图数据同步

**场景1：实时行情可用**
```
用户选择标的 → fetch_quote_data() 获取实时价格 → 显示在总览
同时 → loadKline() 获取K线数据 → 显示K线图
两者数据源相同，时间点可能略有差异但趋势一致
```

**场景2：实时行情不可用**
```
用户选择标的 → fetch_quote_data() 失败
         ↓
调用 fetch_kline_data() 获取最新K线数据
         ↓
使用K线最新收盘价作为总览价格
         ↓
显示"与K线图数据源一致"提示
```

**场景3：K线数据不足**
```
用户选择标的 → fetch_kline_data() 返回空或不足
         ↓
使用 fallback_quote() 提供静态基准价格
         ↓
显示"静态行情基准"提示
```

---

## 测试验证

### 测试用例

**A股测试：**
- 代码：000300（沪深300）
- 预期货币：CNY（¥）
- 数据源：AKShare
- 验证：总览价格和K线图价格一致

**港股测试：**
- 代码：HSI（恒生指数）
- 预期货币：HKD（HK$）
- 数据源：AKShare
- 验证：总览价格和K线图价格一致

**美股测试：**
- 代码：SPX（标普500）
- 预期货币：USD（$）
- 数据源：AKShare
- 验证：总览价格和K线图价格一致

### 验证步骤

1. 启动服务：`docker-compose up -d`
2. 访问：`http://localhost`
3. 选择不同市场标的
4. 检查总览价格和K线图价格
5. 确认货币单位显示正确
6. 确认数据源标注为AKShare

---

## 注意事项

1. **AKShare数据延迟**
   - 美股数据可能有15-20分钟延迟
   - 这是AKShare数据源的特性

2. **货币单位显示**
   - 前端自动根据市场类型显示货币符号
   - 所有价格均标注货币单位

3. **数据源唯一性**
   - 系统不再使用国外数据源
   - 所有数据均来自国内可访问的AKShare

4. **回滚说明**
   - 如需恢复Yahoo Finance，可恢复 `_try_yahoo_kline()` 函数
   - 建议保留AKShare优先策略

---

## 更新完成标志

- [x] 移除Yahoo Finance数据源
- [x] 统一使用AKShare数据源
- [x] 总览价格和K线图数据源一致
- [x] 添加货币单位标注
- [x] 更新前端显示逻辑
- [x] 更新文档说明
- [x] 测试验证功能正常
