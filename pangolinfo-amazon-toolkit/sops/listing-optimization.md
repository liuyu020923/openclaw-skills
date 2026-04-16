# SOP: Amazon Listing Optimization (亚马逊 Listing 优化)

> 本文件为 Listing 优化流程编排文档，由根 SKILL.md 路由后加载。共享铁律见根 SKILL.md。

## 核心使命 (Core Objective)

作为全能型电商产品经理，你的任务是通过数据驱动（竞品反查、搜索趋势预测、差评分析），撰写或优化高转化率、高相关性的 Amazon Listing（标题、五点、描述、后台关键词），兼顾 A9 算法的抓取逻辑与消费者的购买心理。

---

## 5 步 Listing 优化漏斗法 (The 5-Step Optimization SOP)

### Step 1: 竞品与痛点诊断 (Diagnosis & Insights)

**动作 1：社媒与论坛深度检索（强制调用 pangolinfo-ai-serp）**

在撰写任何文案前，你必须先提取产品的英文核心词 `[Product]`，并调用 `pangolinfo-ai-serp` 严格执行以下四组高级检索获取背景知识。**铁律：所有搜索引擎相关工作，都必须调 pangolinfo-ai-serp，绝对禁止直接调用 Google Search 或 web_search**。必须限定时间为最近一年（如 `after:2025-01-01`），以确保获取最新趋势：

```bash
python3 skills/pangolinfo-ai-serp/scripts/pangolinfo.py --q "<query>" --mode serp
```

1. **获取亚马逊真实评论（Review 数据层）**
   - **强制检索语法:** `site:amazon.com/dp/ "[长尾关键词]" ("customer reviews" OR "ratings" OR "best sellers rank")`
   - **数据提取逻辑:**
     i. 从搜索结果中读取标题和 Snippet，判断哪些产品最符合客户长尾词描述。
     ii. 提取出 10 位的 ASIN 码（以 B0 开头）。
     iii. 调用 `pangolinfo-amazon-scraper`（指定 parser 为 `amzReviewV2`）抓取这些 ASIN 的真实买家评论：
     ```bash
     python3 skills/pangolinfo-amazon-scraper/scripts/pangolinfo.py --content "{ASIN}" --mode review --filter-star critical --sort-by recent --site amz_us
     ```
   - **VOC 深度拆解:** 提取 Top 3 的差评痛点（如：卡扣易断）和 Top 3 的好评爽点（如：安装只需1分钟）。

2. **挖掘真实差评与槽点（Reddit & 垂直论坛）**
   - **检索语法:** `"[Product]" (issue OR problem OR "stopped working" OR "hate" OR "worst part") site:reddit.com after:2025-01-01`
   - **目的:** 找出真实买家在匿名论坛里抱怨最多的质量或设计缺陷。

3. **挖掘新奇使用场景与种草词汇（TikTok / YouTube / 社媒）**
   - **检索语法:** `"[Product]" ("lifehack" OR "game changer" OR "how I use" OR "must have") (site:tiktok.com OR site:youtube.com)`
   - **目的:** 发现买家开发出的"意想不到的用途"及视频里的"情绪表达词"。

4. **挖掘购买前的犹豫点（Quora & 问答社区）**
   - **检索语法:** `"[Product]" ("is it worth it" OR "should I buy" OR vs) site:quora.com`
   - **目的:** 找出阻碍消费者下单的最后一道心理防线。

**动作 2：AI 提炼与痛点反转（核心逻辑与产品自证）**

分析完上述结果后，不能直接把差评扔给客户，必须执行"痛点到卖点（Pain-point to Selling-point）"的转化，**但必须加上一道"产品自证"防线**：
- **文案反转（如果产品已解决）：** 例如论坛抱怨"电池用不到一天"，且客户确认自家产品是长续航，则在文案强化"升级版 7 天长续航 (Upgraded 7-Day Battery Life)"。
- **迭代预警（如果产品存在同类缺陷）：** 必须明确提醒客户："请务必核实您的产品是否也存在【卡扣易断】的通病。如果存在，强行在 Listing 中夸大或虚假宣传会带来极高的风险，可能引发毁灭性的差评和退货潮。建议将此痛点转化为【产品迭代建议】，反馈给供应链进行下一代开模优化。"
- 提炼社媒高频词（VOC），用买家的原话写 Listing。

**动作 3：严格执行知识产权过滤（WIPO API 风控层）**

提取具有"修饰属性"、"技术属性"或"疑似他人品牌"的敏感词（如 Velcro, Kevlar 等）。
- **强制动作:** 调用 `pangolinfo-wipo` 验证：
  ```bash
  python3 skills/pangolinfo-wipo/scripts/pangolinfo.py --q "{sensitive_term}"
  ```
- **红线规则:** 若返回为目标销售国（如 US）的有效注册商标（Active Trademark），将该词写入 Listing 存在极高的商标侵权风险，极易导致 Listing 变狗或账号受限。建议强制替换为"安全通用词"。

---

### Step 2: 撰写高权重标题 (Title Formulation)

- **动作:** 将排雷后最核心的词汇埋入标题前端。
- **结构:** `[核心关键词/Brand] + [产品核心卖点/功能] + [材质/型号/适配性] + [规格/颜色/数量]`
- **目标:** 既要让 A9 算法在第一权重位置抓取到大词，又要让手机端买家在截断前看到最重要的购买理由。

---

### Step 3: 打造攻心五点描述 (Bullet Points Strategy)

- **动作:** 使用 "【核心总结提取】+ 益处（Benefit） + 特点（Feature）" 的结构。
- **目标:** 第 1、2 点打痛点和核心卖点，第 3、4 点讲材质与适用场景，第 5 点提供售后承诺或品牌保证。

---

### Step 4: 布局后台搜索词与描述 (Backend Search Terms & Description)

- **动作:** 提取未能放入标题和五点的高转化长尾词、拼写错误词等，绝对去重并确保无侵权词。

---

### Step 5: 输出与交付

## 输出规范 (Output Format)

在正式输出五点描述前，先向客户展示调研依据，按以下结构输出：

1. **VOC 洞察与社媒舆情总结 (Data Insights)**
   - 总结亚马逊 Review 核心痛点及社媒总体情绪。
   - 列出排名前 3 的"致命痛点"（标明数据来源，如 Reddit）。
   - 列出排名前 3 的"爽点/最受欢迎的使用场景"（标明数据来源，如 TikTok）。

2. **侵权词排雷记录 (IP Compliance Filter)**
   - 向客户展示你拦截了哪些"看似通用实则侵权"的词汇，并给出替换方案（如：拦截 "Velcro"，替换为 "Hook and loop fastener"）。

3. **痛点反转与产品迭代建议 (Listing & Product Iteration)**
   - 列出【竞品核心痛点/槽点】。
   - **文案应对策略:** 如果客户产品无此缺陷，应如何在五点中放大此优势。
   - **产品迭代预警:** 明确提醒客户自查自身产品是否存在该缺陷。若存在，给出具体的供应链优化/微创新建议，并提示过度承诺和虚假宣传的可能后果（如退货率飙升、负面评价集中等）。

4. **高安全、高转化 Listing 正式输出 (Final Output)**
   - 输出英文 Title, 5 Bullet Points, Search Terms。
   - 在每个核心卖点后，用括号中文批注："（注：此处回应了 Review 痛点 / 借用了 TikTok 热门场景词）"。
