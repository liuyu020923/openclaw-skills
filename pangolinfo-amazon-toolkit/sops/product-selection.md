# SOP: Amazon Product Selection (亚马逊智能选品)

> 本文件为选品流程编排文档，由根 SKILL.md 路由后加载。共享铁律见根 SKILL.md。

---

### 阶段一：宏观视野与赛道初筛 (Discovery & Initial Filter)

**Step 1: 种子词提取 (Seed Extraction)**
*   **输入**：用户提供的原始类目或痛点概念（如 Headphones）。
*   **动作**：提取核心名词，作为后续指令的 `{Seed_Keyword}` 变量。

**Step 2: 站外 AI 概念延展 (Pangolinfo AI SERP 强制扩词)**
*   **Sub-Skill 调用**：`pangolinfo-ai-serp`
    ```bash
    python3 skills/pangolinfo-ai-serp/scripts/pangolinfo.py --q "<query>" --mode ai-mode
    ```
*   **强制检索语法 (Must Use)**：必须使用以下 Dorks 组合强制剥离电商广告，只抓取极客论坛、评测媒体和讨论区的趋势预判：
    *   **语法 A (找细分场景)**：`intitle:"{Seed_Keyword}" ("best for" OR "used for" OR "designed for") -site:amazon.com -site:ebay.com`
    *   **语法 B (找新兴技术)**：`"{Seed_Keyword}" (trend OR "new technology" OR alternative) inurl:blog OR inurl:news`
*   **处理逻辑**：从 AI 概览或前 10 个有机搜索结果的 Snippet 中，提取至少 5-10 个长尾的"场景词"或"技术词"（如：Bone conduction headphones for swimming），形成【候选利基词池】。

---

### 阶段二：微观利基锁定与竞争排雷 (Niche Locking)

**Step 3: 亚马逊数据底牌透视 (Niche Metric Filtering)**
*   **Sub-Skill 调用**：`pangolinfo-amazon-niche` (Niche Filter API)
    ```bash
    python3 skills/pangolinfo-amazon-niche/scripts/pangolinfo.py --api niche-filter --marketplace-id ATVPDKIKX0DER --niche-title "{Surviving_Keyword}" ...
    ```
*   **动作**：将 Step 2 筛选出的【候选利基词池】作为 nicheTitle 模糊匹配。如果用户没有指定相关参数，则强制注入以下防御性 Payload 参数（深水区指标），精准阻断红海与内卷市场：
    ```json
    {
     "marketplaceId": "ATVPDKIKX0DER",
     "nicheTitle": "{Surviving_Keyword}",
     "searchVolumeT90Min": 20000,
     "top5BrandsClickShareMax": 0.40,
     "productCountMax": 300,
     "searchVolumeGrowthT90Min": 0.05,
     "returnRateT360Max": 0.10,
     "avgOosRateT360Min": 0.02
    }
    ```
    *(内部演算补充：若可能，同时考察 `avgBrandAge` 避开纯老品牌霸榜池，以及 `successfulLaunchesT360` 评估新品真实存活率。)*
*   **处理逻辑**：提取通过该 API 返回的唯一标识符 `nicheId` 及其精确的 `nicheTitle`。

**Step 4: 外部真实声音与痛点对齐 (Voice of Customer)**
*   **Sub-Skill 调用**：`pangolinfo-ai-serp`（纯净搜索模式）
    ```bash
    python3 skills/pangolinfo-ai-serp/scripts/pangolinfo.py --q "<query>" --mode serp
    ```
*   **强制检索语法 (Must Use)**：必须使用定向站点检索，强制抓取 Reddit/Quora 等 UGC 社区的真实抱怨和求助：
    *   **语法 A (挖痛点/缺陷)**：`"{Exact_Niche_Title}" ("sucks" OR "hate" OR "broken" OR "issue" OR "stopped working") (site:reddit.com OR site:quora.com)`
    *   **语法 B (挖未满足需求)**：`"{Exact_Niche_Title}" ("wish it had" OR "is there a" OR "looking for a") (site:reddit.com OR site:quora.com)`
*   **处理逻辑**：利用 AI 总结提取排名前 3 的核心痛点，作为后续微创新的基准。

**Step 5: 输出高潜利基矩阵与沙盘推演 (Niche Matrix & Selection)**
*   **动作**：筛选出 2-3 个在 Step 3 竞争指标健康、且 Step 4 痛点清晰的**优质、且均强烈建议切入的 Niche 市场**。绝对禁止提供"用来凑数的避坑型/垃圾选项"。
*   **展现形式**：必须向用户展示多维度的"选品数据看板"（沙盘推演），让用户根据自身资源做选择。必须包含以下维度（强制引用 Step 3 的底层数据作支撑）：
    *   **市场规模与拥挤度**（如：搜索量预估、当前竞争商品总数）
    *   **头部垄断性**（如：前三大/前五大品牌占据的市场点击份额，判断是否已被寡头锁死）
    *   **流量与季节性**（如：夏季爆发 vs 全年平稳）
    *   **退货率预估基准**（如：无电子件的纯结构件预估 <5%）
    *   **供应链门槛**（如：公模微改 vs 需重新开注塑模）
    *   **核心痛点与微创新点**（如：原材质易生锈 -> 升级316不锈钢）

---

### 阶段三：标杆 ASIN 提取与风控 (Targeting & Compliance)

**Step 6: 双盲交叉筛选爆款基因 (Double-Blind ASIN Cross)**
*   **Sub-Skill 调用 A (找流量入口)**：`pangolinfo-amazon-scraper` (Search)
    ```bash
    python3 skills/pangolinfo-amazon-scraper/scripts/pangolinfo.py --q "{Exact_Niche_Title}" --site amz_us
    ```
    *   **动作**：抓取第 1 页的自然位 ASIN，并**精准提取这些商品共同的最底层叶子节点 (Leaf Node ID)**。
*   **Sub-Skill 调用 B (找飙升势能)**：`pangolinfo-amazon-scraper` (New Releases)
    ```bash
    python3 skills/pangolinfo-amazon-scraper/scripts/pangolinfo.py --content "{Leaf_Node_ID}" --parser amzNewReleases --site amz_us
    ```
*   **处理逻辑 (强制交集)**：比对 API A 与 API B 的结果。仅保留同时出现在"关键词首页"且打入"同底层节点新品榜"的 ASIN（兼具流量与转化势能的标杆竞品）。

**Step 7: 自动化合规初筛 (WIPO Brand Check)**
*   **Sub-Skill 调用**：`pangolinfo-wipo`
    ```bash
    python3 skills/pangolinfo-wipo/scripts/pangolinfo.py --q "{query}"
    ```
*   **动作 1 (提取高危检索词)**：从选出的标的 ASIN 中，提取：(1) 疑似垄断的品类通用词；(2) 核心技术/功能修饰词；(3) 交集 ASIN 的 Brand Name 字段。
*   **动作 2 (强制调用 WIPO API)**：将提取出的词汇作为 query 调用接口，重点核查目标销售国（如 US）和对应尼斯分类（Nice Classification）。若返回状态为 Active (已注册) 且持有人为大集团/知名律所，立即将该产品或词汇剔除。
*   **动作 3 (风控逻辑研判)**：结合 API 返回数据，分析该选品的切入可行性，剔除有明确高危文字商标保护的备选品。

---

### 阶段四：价格带战略分层与互动下钻 (Pricing & Micro-Innovation)

**Step 8: 价格带切割与优劣势对齐 (Price Tier Stratification)**
*   **动作**：将 Step 6 洗出的高潜力 ASIN 集合，根据 price 强制分为三组：Low (< P33)、Mid (P33-P66)、High (> P66)。

**Step 9: 负评定向爆破与战术输出 (Review Analysis & Action Plan)**
*   **Sub-Skill 调用**：`pangolinfo-amazon-scraper` (Review)
    ```bash
    python3 skills/pangolinfo-amazon-scraper/scripts/pangolinfo.py --content "{Target_ASIN}" --mode review --filter-star critical --sort-by recent --site amz_us
    ```
*   **清洗规则 (Must Obey)**：剔除所有与 FBA 仓储物流迟滞、卖家发错货相关的非产品设计差评；**必须保留包装破损问题**（作为产品包装改良需求），以及材质、功能失效、人体工学等核心产品缺陷。

---

## 报告生成与输出规范 (Report Generation Rules)

**【实战交付铁令 (Execution Mandates)】**
*   **顾问级交付 (Consultant Persona)**：以"资深亚马逊卖家咨询顾问"的身份输出建议。直接交付商业洞察和落地策略，**绝对禁止**在最终报告中罗列中间的操作步骤。
*   **绝对真实 (Data Integrity)**：必须 100% 使用 API 和工具抓取的真实市场数据。如果查不到、爬不到，就明确告知"数据缺失"或"需人工复核"，**严禁任何形式的编造、幻觉或使用占位符假装数据**。

当需要将选品结果整理为项目报告时，**最终交付物必须包含完整的 GTM (Go-To-Market) 落地策略**：

1.  **推演透明化 (Analytical Transparency)**: 当输出深层商业判断时，必须展示解题过程。使用 `[推演逻辑：因为A+B，结合亚马逊A9特性，推断出C]` 的句式。
2.  **靶向 ASIN 活体解剖 (Target ASIN Tear-down)**: 在推荐切入的价格带中，必须直接给出一个或多个具体的标杆竞品（ASIN），并解析：
    *   **它的打法特点**：靠什么词、什么主图差异化打上去的。
    *   **它的软肋**：根据最新差评，我们在打它时，应该着重攻击它哪个产品缺陷。
3.  **GTM 落地策略 - 生产与品控预警 (Production QC)**: 重点提示"打样和验货时必须做哪些极限测试"（如压胶防水测试、防风扣暴力拉扯测试），严控退货率。
4.  **GTM 落地策略 - 视觉与埋词 (Listing SEO & CRO)**: 明确指出未来 Listing 的核心流量词，以及主图和 A+ 页面必须重点展示的"痛点解决方案"。
5.  **GTM 落地策略 - 运营与冷启动节奏 (Operations)**: 给出基础运营节奏建议。
6.  **ROI 预测底线**: 允许基于截面数据逻辑推演，禁止直接输出毫无根据的绝对数值。缺毛利数据时以"比例"或"公式"呈现。
7.  **知识产权与合规板块 (IP & Compliance Section)**:
    *   **文字商标雷区**: 标出标题和 Search Terms 严禁写入的高危词及持有人（引用 WIPO 数据）。
    *   **外观专利免责声明**: **必须声明"AI 暂不具备图片外观专利检索能力"**，提醒客户采购私模产品前人工复核。
    *   **最终红绿灯建议**: 给出明确结论（放弃 / 微调规避 / 安全切入）。
