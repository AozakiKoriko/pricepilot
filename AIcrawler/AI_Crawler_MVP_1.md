# AI Product Aggregation Crawler (MVP, LLM-Generated Whitelist Version)

Enter a **product keyword** to crawl across multiple channels and aggregate: **Channel/URL/Price/Stock Status**.

---

## 0) MVP Description

- Strategy:  
  1) **LLM generates a channel whitelist based on the keyword** (Top-K most relevant e-commerce/retail domains)；  
  2) Use a search API to precisely retrieve candidate product pages within these domains；  
  3) Site adapters (rule parsing) take priority; fallback to **LLM extraction** if failed；  
  4) Concurrent crawling, rate limiting, respecting robots/ai.txt.  
- Price and stock are **volatile data**: set **cache expiration** (e.g., 10–60 minutes) and mark fetch time in results.

---

## 1) MVP Architecture Overview (LLM-Driven Whitelist)

**Input**: Product keyword (e.g., 'iPhone 15 Pro 256GB' / 'RTX 4070 Ti' / 'Bose QC Ultra')  
**Output**: Channel, URL, Price, Stock, Fetch Time

**流程**  
1. **Whitelist Layer（LLM 生成渠道白名单）**  
   - LLM 依据**品牌/品类/地区/语言**等语义，返回最相关的**域名/零售商列表**（Top-K，如 10–30 个）。  
   - 约束：仅输出**域名清单**与**零售类型**标签（官方/自营/大型连锁/垂直类目/二手平台等），**禁止编造不合理域名**。  
   - 校验：对域名做 **DNS/HTTP 探测与负面词过滤**（见 §4）。

2. **Search Layer（域内精准检索）**  
   - 使用搜索 API（Bing/Google/Brave/SerpAPI），**限制 site:** 到白名单域名，检索商品详情页/品类页。  
   - 结合标题匹配与关键属性（容量/型号/代数）过滤低质结果。

3. **Fetch Layer**：Playwright（动态）或 httpx（静态）抓页面。

4. **Extract Layer**：  
   - 站点适配器优先（CSS/XPath/JSON-LD/可视文本多策略）；  
   - 失败 → **LLM 兜底**（只投喂卡片/详情主体 DOM 片段，要求 JSON-only 输出）。

5. **Normalize**：统一币种、价格格式、库存枚举（in_stock / out_of_stock / unknown）。

6. **Dedup + Rank**：同款合并、按价格/可信度排序。

7. **Output API**：返回标准 JSON。

**技术选型**  
- LLM：任意供应商（需要支持函数式/JSON 输出或强约束的响应格式）  
- 抓取：Playwright / httpx  
- 后端：FastAPI  
- 缓存：SQLite（MVP）或 Redis  
- 并发：Python async + 域名级限速（2–4）  
- 存储：对象存储（快照）+ PostgreSQL / SQLite（结构化）

---

## 2) 数据模型（统一输出）

```json
[
  {
    "retailer": "BestBuy",
    "product_title": "MSI GeForce RTX 4070 Ti",
    "url": "https://www.bestbuy.com/...",
    "price": 749.99,
    "currency": "USD",
    "in_stock": "in_stock",
    "fetched_at": 1724130000
  }
]
```

---

## 3) 目录结构（可直接创建）

```
ai-crawler-mvp/
├─ app/
│  ├─ main.md                 # 设计文档（可选）
│  ├─ main.py                 # FastAPI 入口（/search?query=）
│  ├─ whitelist.py            # ★ LLM 生成渠道白名单（核心变更点）
│  ├─ search.py               # 搜索封装（Bing/SerpAPI，site: 限域检索）
│  ├─ fetcher.py              # 抓取与限速（httpx/Playwright）
│  ├─ normalize.py            # 价格/库存/货币标准化
│  ├─ extract/
│  │  ├─ base.py              # 抽取器接口定义
│  │  ├─ generic_llm.py       # LLM 兜底抽取器（HTML→JSON）
│  │  ├─ bestbuy.py           # 规则解析适配示例
│  │  ├─ amazon.py            # 规则解析适配示例
│  │  └─ walmart.py           # 规则解析适配示例
│  ├─ cache.py                # SQLite/Redis 缓存（含 TTL）
│  └─ utils.py                # 去重、域名识别、重试等
├─ requirements.txt
└─ README.md
```

> **依赖建议（requirements.txt）**  
> `fastapi`, `uvicorn[standard]`, `httpx`, `playwright`, `lxml`, `beautifulsoup4`, `pydantic`  
> 另加你所选 LLM SDK；安装后执行：`playwright install`

---

## 4) LLM 生成白名单：设计细节

### 4.1 目标与输出
- **输入**：商品关键词（含品牌/型号/容量/代数等），可选国家/语言（默认从 IP/配置推断）。  
- **输出**：去重后的 **Top-K 域名清单** + 每个域名的**标签**：  
  - `{"domain": "bestbuy.com", "label": "big_box", "locale": "US"}`  
  - `{"domain": "apple.com", "label": "official", "locale": "US"}`  
  - `{"domain": "bhphotovideo.com", "label": "vertical_electronics", "locale": "US"}`

### 4.2 提示词要点（思路模版）
- 识别**品牌/品类/配件**与**主要销售渠道类型**；  
- 按**国家/地区**与**语言**给出本地化渠道；  
- 排除：内容站、测评站、C2C 平台（除非你明确允许），以及与关键词不匹配的成人/灰产站；  
- 严禁编造：若不确定，返回 `candidate_reason: "uncertain"` 并降低权重；  
- 限制输出 **JSON-only**；每项包含 `domain/label/locale/confidence`；  
- Top-K 建议 10–30，按 `confidence` 与**覆盖度（官方、自营、连锁、垂直）**平衡。

### 4.3 验证与过滤（防幻觉）
1. **DNS/HTTP 快探**：解析域名 + HEAD/GET（超时短）；失败剔除或降权。  
2. **负面词过滤**：域名或标题含“论坛/新闻/百科/下载/破解/种子”等剔除。  
3. **品类一致性**：随机抓取首页或搜索页关键字，若主类目不符（例如服饰站点却匹配“显卡”），降权或剔除。  
4. **品牌匹配**：若关键词包含品牌（Apple、Sony、MSI），优先包含**官方/旗舰店**与**授权经销商**。  
5. **地域一致性**：根据用户地区/币种/物流可达性过滤（US/UK/EU/JP/CN 等）。

### 4.4 排序策略
- `confidence`（LLM 自评 + 验证得分）× `historical_success_rate`（历史解析成功率）× `coverage_diversity`（渠道多样性）；  
- 通过**多头采样/温度**获取候选集合，再做一致性交集（减小单次偏差）。

---

## 5) 搜索层（域内精准检索）

- 使用 `site:domain.com` 限定域搜索，关键词包含**型号/容量/颜色**等约束；  
- 结果过滤：标题/URL 必须包含关键子串（如 “4070 Ti”/“RTX 4070 Ti”）；  
- 优先抓取**商品详情页**，其次是**品类聚合页**（再进行二跳抓取）；  
- 为每个域控制 `max_pages`（如 3–5），避免过深。

---

## 6) Extract Layer（解析）

- **规则适配器优先**：CSS/XPath/JSON-LD/可视文本多策略，解析 `title/price/stock/url`；  
- **LLM 兜底**：只投喂**卡片/详情主体**片段；强制 JSON-only 输出；无字段不编造，返回 `null`；  
- **库存判定词典**： “In stock / Add to cart / Pickup today / Backordered / Sold out / Currently unavailable”。  
- **价格多策略**：优先 JSON-LD、meta、显式货币符号；保留原价/促销价字段以便排序。

---

## 7) 逐步增强路线（基于 LLM 白名单）

1. **白名单记忆与学习**：将人工确认的优质域名写入“可信库”，下次同类词优先引用，节省模型调用。  
2. **多区域支持**：依据用户地区返回对应渠道（US/EU/JP/CN…），并在 Normalize 中做币种换算。  
3. **类别包**：为 3C、家电、鞋服、美妆、生鲜等，维护一份“基础渠道候选集”，供 LLM 参考以降低幻觉。  
4. **结果去重与同款合并**：标题相似度 + 参数抽取（型号、内存、颜色）。  
5. **成本控制**：LLM 采用短上下文、少样例；对热门词缓存白名单输出（TTL 1–7 天）。

---

## 8) 质量、成本与合规

- **解析优先级**：规则解析 > LLM 兜底（只在必要时调用）。  
- **白名单验证**：域名探测 + 负面词过滤 + 品类/地域一致性检查。  
- **缓存策略**：关键词→白名单（长 TTL），URL→价格库存（短 TTL）。  
- **监控**：白名单命中率、域内搜索点击率、解析成功率、单位成本（￥/结果）。  
- **合规**：遵守服务条款、`robots.txt`、`ai.txt`；标注 `User-Agent` 与联系邮箱；不抓登录/付费墙内容；不采集个人敏感信息。

---

