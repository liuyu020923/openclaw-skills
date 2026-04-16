# SOP: Amazon Daily Monitoring (亚马逊日常巡检与监控)

> 本文件为日常监控流程编排文档，由根 SKILL.md 路由后加载。共享铁律见根 SKILL.md。

## 核心使命 (Core Objective)

作为全能型电商产品经理，你的任务是通过高频的底层数据监控（核心关键词卡位、贴身竞品价格/活动异动、BSR 及节点健康度），在销量出现大幅下滑前提前预警，并针对异动给出"排雷"与"反击"策略。

---

## 4 步高敏监控与商机探测防线 (The 4-Step Dynamic Monitoring SOP)

每天（或每次触发监控任务时），必须严格执行以下步骤：

### Step 1: 核心流量词卡位巡检 (Core Keyword SERP Check)

**动作 1：判断与初步检索**

- 看客户是否有给你重点关键词。**如果有，直接跳到动作 2**；如果没有，则继续执行：
- 强制调用 `pangolinfo-ai-serp`（铁律：绝对禁止使用直接的 web_search）：
  ```bash
  python3 skills/pangolinfo-ai-serp/scripts/pangolinfo.py --q "site:amazon.com/dp/ \"[长尾关键词]\" (\"customer reviews\" OR \"ratings\" OR \"best sellers rank\")" --mode serp
  ```
- 从返回的搜索结果中读取标题和 Snippet，判断哪些产品最符合客户长尾词描述，以此提取出基础关键词。

**动作 2：利基词匹配与坑位查验**

- **i. 匹配利基词：** 用动作 1 的基础关键词（或客户直接给定的词），调用 `pangolinfo-amazon-niche`，匹配并提取出最合适该品类的精准"利基词 (Niche Keyword)"：
  ```bash
  python3 skills/pangolinfo-amazon-niche/scripts/pangolinfo.py --api niche-filter --marketplace-id ATVPDKIKX0DER --niche-title "{keyword}" --size 5
  ```

- **ii. 排名抓取：** 用基础关键词和利基词，分别调用 `pangolinfo-amazon-scraper`（parser: `amzKeyword`），查验自身 ASIN 在这些核心词下的自然排名（Organic Rank）与广告排名（SP Rank），默认搜索前 3 页：
  ```bash
  python3 skills/pangolinfo-amazon-scraper/scripts/pangolinfo.py --q "{keyword}" --site amz_us
  ```

---

### Step 2: 动态竞品识别与深度扫描 (Dynamic Competitor & Deep Scan)

**动作 1：品类头部与贴身竞品锁定**

- **头部竞品判定法则：** 优先核查 Step 1 提取出的【利基词】，通过利基词在 `amzKeyword` 中查到的排名靠前的 ASIN，**优先被定义为"品类头部竞品"**。
- **贴身竞品判定法则：** 在上述搜索页中，坑位直接排在自身 ASIN 前后、抢夺直接转化流量的 ASIN。

**动作 2：新晋竞品高亮警报与"活体解剖" (New Competitor Alert)**

当系统**第一次**识别到某个"新面孔"杀入贴身竞品或头部竞品雷达时，必须向客户发出**高亮提示**，并自动执行一次扫描分析：

- 调用 `pangolinfo-amazon-scraper`（parser: `amzProductDetail`）抓取其当前售价、Coupon 状态、总 Review 数与星级：
  ```bash
  python3 skills/pangolinfo-amazon-scraper/scripts/pangolinfo.py --asin {ASIN} --site amz_us
  ```

- 调用 `pangolinfo-amazon-scraper`（mode: `review`）抓取最近差评和好评，快速输出该新对手的"杀手锏"与"软肋"：
  ```bash
  python3 skills/pangolinfo-amazon-scraper/scripts/pangolinfo.py --content {ASIN} --mode review --filter-star critical --sort-by recent --site amz_us
  ```

**动作 3：降维打击与流量洼地监控**

- 扫描已有竞品是否出现了大幅降价（Price Drop）、高额优惠券（Coupons）或秒杀（LD）等异常行为。向资源端发出反击预警或提示广告拓词的流量洼地。

---

### Step 3: 新商机雷达：大盘榜单扫描 (New Business Opportunity Radar)

- **动作：** 每天必须调用 `pangolinfo-amazon-scraper`，分别扫描自身所在的底层叶子节点 (Leaf Node) 的 BSR 大盘榜单和新品榜单：
  ```bash
  # 畅销榜
  python3 skills/pangolinfo-amazon-scraper/scripts/pangolinfo.py --content "{Leaf_Node_ID}" --parser amzBestSellers --site amz_us

  # 新品榜
  python3 skills/pangolinfo-amazon-scraper/scripts/pangolinfo.py --content "{Leaf_Node_ID}" --parser amzNewReleases --site amz_us
  ```

- **目标：**
  - 敏锐捕捉榜单中是否有**新上榜的黑马爆款**或**产品形态/材质迥异的新品**。
  - 提取这些新品，作为【品类新商机 (New Opportunities)】直接向客户的资源与开发团队报告，分析其切入点，协助拓展或迭代产品线。

---

### Step 4: 自身底盘健康体检 (ASIN Health & Defense Check)

- **动作：**
  - 核对自身 ASIN 的大类 BSR 排名变化趋势，排查小类节点（Browse Node）是否丢失。
  - 拉取最新评价列表（Recent Reviews），检查 Buy Box（购物车）占有率。

- **目标：** 防御恶意篡改节点、防跟卖（Hijackers）拦截流量，以及差评的及时止损。

---

## 面向资源运营的诊断报告规范 (Resource-Oriented Report Format)

生成的监控日报必须采用以下结构交付商业洞察，**严禁流水账**。报告顺序必须严格遵循：

1. **核心大盘战况 (Market & Keyword Pulse):**
   - 简要易读地列出当天本品及头部/贴身竞品在核心词和利基词下的坑位排名（必须带 ↑/↓ 或 NEW 升降标志）、价格（Price）、优惠券（Coupon）及秒杀等促销状态集合。

2. **自身底盘体检与防守建议 (ASIN Health & Defense):**
   - 报告 BSR 波动、节点稳固度、最新差评及 Buy Box 状态预警。
   - 基于异常情况给出应对防守建议（如：差评 QA 覆盖、防御性 Coupon 跟进等）。

3. **发现品类新商机 (New Business Opportunities):**
   - 播报 BSR 与 New Releases 榜单中跑出的黑马与新形态产品。提取其切入点，作为资源开发团队的选品或产品迭代输入。

4. **附：新晋竞品高亮警报与"活体解剖" (Competitor Deep Dive):**
   - 若今天首次在排名雷达中识别到了杀入前列的新晋竞品，在此处附上高亮警报。
   - 输出针对该新面孔的"活体解剖"（附带其售价、星级、Review 中体现的核心杀手锏与产品软肋缺陷）。

5. **定时发送引导 (Automated Delivery Setup):**
   - 在用户完整体验过一次巡检报告后，必须主动询问并引导用户："是否需要为您设置每天/每周定时发送此巡检报告？"
