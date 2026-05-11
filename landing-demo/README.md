# Pangolinfo Skills 落地页 Demo（方案 C 全景）

完整可视化原型，5 个 Star 引导触点全部可演示。**汇报时建议从 `tour.html` 开始**，按顺序点开。

## 文件结构

```
landing-demo/
├── tour.html              ← 总览导航（汇报入口）
├── index.html             ← 触点 1：落地页
├── touch2-banner.html     ← 触点 2：安装脚本 banner
├── touch3-progress.html   ← 触点 3：安装过程
├── touch4-success.html    ← 触点 4：安装完成（转化率最高）
├── touch5-delayed.html    ← 触点 5：CLI 使用 10 次后延迟引导
└── feasibility.html       ← 技术可行性确认报告（汇报技术背书）
```

## 5 个触点

| # | 文件 | 内容 |
|---|---|---|
| 1 | `index.html` | 落地页：导航栏 Star 徽章 + Hero 一行命令 + Skill 卡片 + 社会证明 + Final CTA |
| 2 | `touch2-banner.html` | 终端动画：脚本开头 ASCII banner 露出 GitHub URL + Star 数 |
| 3 | `touch3-progress.html` | 终端动画：安装步骤每行打印 "Downloading from github.com/..." |
| 4 | `touch4-success.html` | 终端动画："We're a small team... Press ENTER to open GitHub" |
| 5 | `touch5-delayed.html` | 终端动画：第 10 次使用时弹出"已为你节省 4.2 小时"+ Star 引导 |

## 汇报演示路径（5 分钟）

1. 打开 `tour.html` → 介绍整体策略
2. 点触点 1 → 落地页效果
3. 点触点 2 → "用户复制命令执行的瞬间"
4. 点触点 3 → "安装进行中"
5. 点触点 4 → **重点讲这个**：转化率最高的一击
6. 点触点 5 → "用户已经获得价值后再请求"
7. 回到 `tour.html` 底部漏斗图 → 给出预期转化数据

## 本地打开

```bash
# Windows
start D:/newCode/openclaw-skills/landing-demo/tour.html

# 或者直接双击 tour.html
```

## 待真实化的占位

- 品牌色 `#ff5b1f`（橙色）→ 抓 pangolinfo.com 主站配色后替换
- GitHub URL `github.com/pangolinfo/skills` → 实际仓库路径
- 域名 `pangolinfo.dev/install` → 最终落地域名
- 数字 `1,247 stars` / `12,847 installs` → 真实数据或合理初始值
- 6 个 skill 名称 → 最终对外命名
