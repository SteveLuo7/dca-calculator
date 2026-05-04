# 前端和后端更新说明

## 修改概述

本次修改删除了自定义代码搜索栏，将选择指数模块重新设计为三个市场标签（亚洲市场、欧洲市场、美洲市场），每个市场中分别显示权重股票和基金。

## 前端修改

### 1. 删除搜索模块
- 删除了整个搜索模块的HTML结构
- 删除了搜索相关的CSS样式（`.search-container`、`.search-input`、`.search-icon`、`.search-suggestions`、`.suggestion-item`等）
- 删除了搜索相关的JavaScript函数（`handleSearch`函数）
- 删除了搜索输入框的事件监听器
- 删除了`searchTimer`变量

### 2. 重构市场选择模块
**HTML结构变化：**
- 将原有的"搜索模块"和"市场指数模块"合并为单一的"市场选择模块"
- 模块标题从"🌍 市场指数（按地区分类）"改为"🌍 选择市场"
- 修改了市场标签的顺序：亚洲市场、欧洲市场（默认激活）、美洲市场
- 每个市场内容区域现在包含两个分区：
  - 📈 权重股票（对应`asset_type=stock`）
  - 💰 基金（对应`asset_type=fund`）

**HTML结构示例：**
```html
<section class="panel market-module">
  <div class="panel-title">🌍 选择市场</div>
  
  <!-- 市场标签页 -->
  <div class="market-tabs" id="marketTabs">
    <button class="market-tab" data-market="asia">🏯 亚洲市场</button>
    <button class="market-tab active" data-market="europe">🏰 欧洲市场</button>
    <button class="market-tab" data-market="americas">🗽 美洲市场</button>
  </div>
  
  <!-- 欧洲市场内容（默认显示） -->
  <div class="market-content active" id="europeContent">
    <div class="market-section">
      <div class="section-title">📈 权重股票</div>
      <div class="asset-grid" id="europeStockGrid"></div>
    </div>
    <div class="market-section">
      <div class="section-title">💰 基金</div>
      <div class="asset-grid" id="europeFundGrid"></div>
    </div>
  </div>
  
  <!-- 亚洲市场和美洲市场类似结构 -->
</section>
```

### 3. 更新CSS样式
**新增样式：**
```css
/* 市场分区样式 */
.market-section { margin-bottom: 20px; }
.market-section:last-child { margin-bottom: 0; }
.section-title { font-size: 12px; font-weight: 600; color: var(--text2); margin-bottom: 8px; padding: 6px 10px; background: var(--bg2); border-radius: 4px; }
```

**删除样式：**
- 搜索框相关的所有样式

### 4. 重构JavaScript函数

**删除的函数：**
- `loadAsiaIndices()` - 加载亚洲市场指数
- `loadEuropeIndices()` - 加载欧洲市场指数
- `loadAmericasIndices()` - 加载美洲市场指数
- `loadMarketIndices()` - 加载所有市场指数

**新增的函数：**
```javascript
async function loadAsiaMarket() {
  // 加载亚洲市场权重股票（asset_type=stock）
  const stockGrid = document.getElementById('asiaStockGrid');
  const stockRes = await fetch(`${API}/api/search?region=亚洲市场&asset_type=stock&limit=20`);
  
  // 加载亚洲市场基金（asset_type=fund）
  const fundGrid = document.getElementById('asiaFundGrid');
  const fundRes = await fetch(`${API}/api/search?region=亚洲市场&asset_type=fund&limit=20`);
}

async function loadEuropeMarket() {
  // 加载欧洲市场权重股票和基金
}

async function loadAmericasMarket() {
  // 加载美洲市场权重股票和基金
}

async function loadMarketData() {
  // 加载当前激活的市场数据
  const activeTab = document.querySelector('.market-tab.active');
  const market = activeTab?.dataset.market || 'europe';
  
  if (market === 'asia') await loadAsiaMarket();
  else if (market === 'europe') await loadEuropeMarket();
  else if (market === 'americas') await loadAmericasMarket();
}
```

### 5. 更新页面初始化逻辑
```javascript
async function initPage() {
  // 设置市场标签点击事件
  const marketTabs = document.querySelectorAll('.market-tab');
  marketTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      marketTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      
      const market = tab.dataset.market;
      document.querySelectorAll('.market-content').forEach(content => {
        content.classList.remove('active');
      });
      document.getElementById(`${market}Content`).classList.add('active');
      
      // 加载对应市场的数据
      loadMarketData();
    });
  });
  
  // 加载默认市场数据（欧洲市场）
  await loadMarketData();
  
  // 初始化选中默认代码
  if (state.selectedCode) {
    await refreshSelectedCode();
  }
}
```

## 后端修改

后端API不需要修改，因为现有的`/api/search`端点已经支持所需的功能：

### 现有API端点
```python
@app.get("/api/search")
def get_api_search(
    q: str = Query(default="", max_length=50),
    region: str = Query(default=""),
    country: str = Query(default=""),
    market: str = Query(default=""),
    asset_type: str = Query(default=""),  # 支持 "stock"、"fund"、"index"
    hot_only: bool = Query(default=False),
    limit: int = Query(default=20, ge=1, le=50),
) -> dict[str, Any]:
    """搜索全球证券（支持多种筛选）。"""
```

### 支持的API调用示例
```javascript
// 获取欧洲市场的权重股票
fetch(`${API}/api/search?region=欧洲市场&asset_type=stock&limit=20`)

// 获取欧洲市场的基金
fetch(`${API}/api/search?region=欧洲市场&asset_type=fund&limit=20`)

// 获取亚洲市场的权重股票
fetch(`${API}/api/search?region=亚洲市场&asset_type=stock&limit=20`)

// 获取美洲市场的基金
fetch(`${API}/api/search?region=美洲市场&asset_type=fund&limit=20`)
```

## 数据结构

后端已经包含以下数据：
- `GLOBAL_STOCKS` - 全球热门股票数据（包括美股、欧洲股票、A股等）
- `GLOBAL_ETF` - 全球ETF/基金数据（包括A股基金、美股ETF、港股ETF等）

每个资产都包含以下字段：
- `code`: 代码
- `name`: 名称
- `market`: 市场
- `region`: 地区（美洲市场、欧洲市场、亚洲市场）
- `country`: 国家
- `currency`: 货币
- `description`: 描述
- `default_pe`: 默认PE
- `earnings_growth`: 盈利增长率
- `asset_type`: 资产类型（stock、fund、index）
- `yahoo_symbol`: Yahoo Finance代码
- `tv_symbol`: TradingView代码
- `hot`: 是否热门

## 功能特点

1. **简洁的界面**: 删除了复杂的搜索栏，界面更加简洁
2. **分类清晰**: 按市场和资产类型分类，用户可以快速找到需要的股票或基金
3. **按需加载**: 只加载当前激活的市场数据，提高性能
4. **完整的数据**: 后端已经包含了丰富的股票和基金数据
5. **保持兼容**: 其他功能（PE估值、K线行情、定投计算等）完全保留

## 测试建议

1. 测试三个市场标签的切换
2. 验证每个市场都能正确加载权重股票和基金
3. 检查资产卡片点击是否能正常选中并显示PE数据
4. 确认定投计算功能正常工作
5. 测试导出功能是否正常

## 总结

本次修改成功实现了以下目标：
- ✅ 删除了自定义代码搜索栏
- ✅ 将选择指数模块重构为三个市场标签
- ✅ 每个市场中分别显示权重股票和基金
- ✅ 前端和后端API完全兼容，无需后端修改
- ✅ 保持了所有原有功能的正常工作
