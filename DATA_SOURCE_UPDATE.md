# 数据源更新摘要

## 更新时间
2026-05-04

## 核心改进

### 1. 新闻源优化
**问题**：之前使用的信息整合入口（如搜索入口）不是直接新闻链接。

**解决方案**：
- ✅ **优先使用直接新闻接口**
  - A股：东方财富 `ak.stock_news_em()` - 返回真实新闻
  - 全市场：财联社快讯主页 `https://www.cls.cn/telegraph`
  - 全市场：同花顺资讯 `http://news.10jqka.com.cn`

- ✅ **替换Google搜索为百度搜索**
  - 之前：Google搜索（大陆不可访问）
  - 现在：百度搜索（大陆可直接访问）

### 2. K线数据源优化
**目标**：明确以大陆可访问的数据源为主，Yahoo Finance为辅助。

**优先级**：
1. **AKShare（主数据源）**
   - A股、港股、美股、全球指数
   - ✅ 大陆可直接访问

2. **Yahoo Finance（辅助数据源）**
   - 仅在AKShare失败时使用
   - 主要用于海外市场补充

3. **备份数据**
   - 模拟数据，确保可用性

## 详细文档

完整更新说明请查看：`NEWS_KLINE_UPDATE.md`

## 测试

运行测试脚本验证更新：

```bash
cd backend
python test_news_kline_update.py
```

## 验证要点

- [ ] A股新闻优先使用东方财富直接新闻（而非搜索入口）
- [ ] 海外市场新闻使用财联社/同花顺等大陆可访问的源
- [ ] K线数据优先使用AKShare
- [ ] 不再使用Google搜索（已替换为百度搜索）
- [ ] 每条K线数据都有 `data_source` 标注

## API示例

### 测试新闻
```bash
# A股新闻
curl http://localhost:8000/api/news/000300

# 海外市场新闻
curl http://localhost:8000/api/news/AAPL
```

### 测试K线
```bash
# A股K线
curl http://localhost:8000/api/kline/000300

# 海外市场K线
curl http://localhost:8000/api/kline/AAPL
```

## 文件变更

- ✅ `backend/main.py` - 更新新闻和K线数据源逻辑
- ✅ `README.md` - 添加数据源说明
- ✅ `NEWS_KLINE_UPDATE.md` - 完整更新文档
- ✅ `backend/test_news_kline_update.py` - 测试脚本
- ✅ `DATA_SOURCE_UPDATE.md` - 本更新摘要
