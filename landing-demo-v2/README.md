# Pangolinfo Skills + MCP 双轨方案 Demo (v2)

老板要的最终版方案：**Skills + MCP 双轨 + 适配多 Agent**。延续 v1 视觉风格，新增双轨架构、多 Agent 选择器、安装演示、两周交付计划。

## 文件结构

```
landing-demo-v2/
├── index.html              ← 主落地页（汇报入口）· 9 个 Agent 手风琴
├── how-it-works.html       ← 原理详解 · 脚本/Skills/MCP 三者职责 + FAQ
├── architecture.html       ← 双轨架构图 + MCP 跨 agent 说明
├── installer.html          ← 完整安装流程演示（5 段终端动画可切换）
├── maintenance.html        ← 开发与维护方案 · 仓库结构/分阶段/CI-CD/月维护工时
└── plan.html               ← 两周交付计划 + 每日任务清单 + 风险点
```

## 推荐汇报顺序（约 12 分钟）

| # | 页面 | 时长 | 讲什么 |
|---|---|---|---|
| 1 | `index.html` | 2 min | 整体方案：Skills + MCP 双轨 · 9 个 Agent 手风琴展开 |
| 2 | `how-it-works.html` | 3 min | **核心说明**：脚本做什么 / Skills 解决什么 / MCP 解决什么 + 全链路示例 |
| 3 | `architecture.html` | 1.5 min | 技术架构图：5 层结构 + MCP 跨 agent ASCII 示意 |
| 4 | `installer.html` | 2 min | 真实用户体验：用户选 Agent → 自动安装 Skills + MCP → Key 引导 |
| 5 | `maintenance.html` | 2 min | **开发维护**：3 个仓库分工 / 5 阶段开发 / 1.5d 月维护 / CI-CD 流水线 |
| 6 | `plan.html` | 1.5 min | 两周 10 天每日任务、砍掉项、3 个风险点 |

## 产品策略亮点（最新加入）

**Skills 与 MCP 解耦**——三种安装方案按需选择（**注：三者都需要 API Key**，差异在部署场景而非付费门槛）：

| 方案 | 内容 | 适合用户 | 核心卖点 |
|---|---|---|---|
| 📘 仅 Skills | 只装经验手册（Markdown） | 企业 IT 严格 / 网页端用户 | **纯文本无二进制 · 企业友好 · 网页端唯一选择** |
| 🧰 仅 MCP | 只装工具箱 | 开发者 / 二开团队 | **调用准确率 99%+ · 接口集成最佳** |
| ✨ Both（推荐）| 全套装好 | 大多数电商运营用户 | **既懂业务又能办事 · 综合体验最优** |

落地点：
- `index.html` 新增"3 种安装方案"section（Hero 下方）
- `how-it-works.html` 新增"能力对比表"展示三种方案的差异
- `installer.html` 终端动画在选完 Agent 后追加"What do you want to install?" 三选一

---

## 文案优化（上一轮）

为让<strong>非技术老板能一眼看懂</strong>，全量重写所有页面文案，把技术术语翻译成生活化比喻：

| 原术语 | 改写后 |
|---|---|
| install.sh / 安装脚本 | **🚚 安装小助手 / 搬运工人** |
| Skills | **📘 经验手册 / 老员工的工作 SOP** |
| MCP Server | **🧰 工具箱 / 一排按钮** |
| 9 个 Agent 适配 | **像 App 同时支持 iOS / 安卓 / 鸿蒙** |
| API Key | **会员账号** |
| 调用 tool / Schema 强约束 | **"按按钮"——查 Amazon、查专利** |

核心新增：**how-it-works.html 加入"小张的下午茶时间"完整故事**，用具体角色和时间线代替抽象流程图。

## 与 v1 (landing-demo) 的核心差异

| 维度 | v1 | v2（完整版） |
|---|---|---|
| 核心定位 | 用户选择式 Skills 分发 | **Skills + MCP 双轨** |
| Agent 适配 | 3 个自动 + 其他文档 | **9 个全适配**（含 MCP 自动注册） |
| MCP Server | 不做 | **3 个完整 MCP server**（amazon / serp / wipo） |
| 触点 | 4 个 | **5 个全部上线**（含 CLI 延迟引导） |
| 多语言 | 仅中文 | **中英双语同发** |
| 埋点系统 | 无 | **完整漏斗 + 看板** |
| 工作量 | 8.5d | **10d**（多 Agent 并行支撑） |
| 关键加速 | — | **多 Agent 编程并行 = 3 倍人力** |

## Agent 手风琴面板

`index.html` 中 9 个 Agent 项每个可独立展开，包含：
- 安装方式说明
- 目录路径 / 命令 / 配置文件代码片段
- 脚本自动化覆盖说明

点击任一项展开（同时收起其他项），用户能在不离开页面的情况下查看自己 Agent 的具体安装步骤。

## 待替换占位

- 品牌色 `#ff5b1f` → 主站实际配色
- GitHub URL `github.com/pangolinfo/skills` → 实际仓库
- 域名 `pangolinfo.dev/install` → 最终域名
- Star 数 / 安装量数字 → 真实数据或合理初始值
- API Key 注册页 URL `pangolinfo.com/api/register` → 后端确认后的路径

## 本地预览

```bash
# Windows
start D:/newCode/openclaw-skills/landing-demo-v2/index.html
```
