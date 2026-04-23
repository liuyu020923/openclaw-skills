---
name: pangolinfo-ai-serp
description: >
  Programmatic Google SERP & SGE (AI Overviews) extraction API. Eliminate LLM hallucinations with exact citations. Perfect for SEO monitoring and research agents (LangChain, AutoGen, CrewAI, OpenClaw). Bypass IP blocks instantly.

homepage: https://pangolinfo.com/?referrer=clawhub_ai_serp
metadata:
  openclaw:
    emoji: "🔎"
    os: ["darwin", "linux"]
    requires:
      env:
        - PANGOLINFO_API_KEY
        - PANGOLINFO_EMAIL
        - PANGOLINFO_PASSWORD
      notes: "Auth: set PANGOLINFO_API_KEY (recommended) OR PANGOLINFO_EMAIL + PANGOLINFO_PASSWORD."
tags: [seo, search-engine, sge, ai-overview, research-agent, data-extraction, crawler, google-api, serp]
version: 1.0.6
---


## 🌟 Why Use This Skill? (User Stories)
This skill acts as the ultimate **Sensing Layer** for AI Agents, resolving the common pain points of real-time web search:
- **Zero-Click Search Analysis**: Automatically track and scrape Google AI Overviews (SGE) for branded keywords.
- **Hallucination-Free Agents**: Retrieve structured citations and source links to ground your LLM responses.

## 🤖 Compatible Agent Frameworks
- **OpenClaw** (Native CLI & Terminal)
- **LangGraph / Dify** (As a robust web-search tool node)

## 🌐 多语言适配 (Multi-language Support)
- **🇨🇳 中文适用场景**: Google SGE/AI Overviews 结构化数据抓取，精准追踪引文来源，彻底消除大模型搜索幻觉。
- **Agent Directive**: Always output the final analysis/report in the language of the user's prompt (e.g., reply in Chinese if asked in Chinese).


# Pangolinfo AI SERP (Google SERP + AI Overviews)

Search Google programmatically via **Pangolinfo** APIs.
Extract **Google AI Overviews**, run **AI Mode** searches with **multi-turn follow-ups**, and optionally capture **screenshots**.

## Migration note (Amazon)

Amazon scraping is now a separate skill: **Pangolinfo Amazon Scraper**.

If you previously used Amazon features from the combined skill, install the new Amazon skill and switch your `--mode` usage accordingly.

## Prerequisites

- **Python 3.6+** (standard library only)
- A **Pangolinfo account**: https://pangolinfo.com/?referrer=clawhub_serp
- Auth env vars (choose one):
  - `PANGOLIN_TOKEN` (recommended)
  - or `PANGOLIN_EMAIL` + `PANGOLIN_PASSWORD`

```bash
export PANGOLIN_TOKEN="..."
# or
export PANGOLIN_EMAIL="..."
export PANGOLIN_PASSWORD="..."
```

## Minimal examples

AI Mode search:

```bash
python3 scripts/pangolinfo.py --q "what is quantum computing" --mode ai-mode
```

Standard SERP + AI Overview extraction (+ optional screenshot):

```bash
python3 scripts/pangolinfo.py --q "openclaw" --mode serp --screenshot
```

Multi-turn dialogue (AI Mode follow-ups):

```bash
python3 scripts/pangolinfo.py --q "python web frameworks" --mode ai-mode \
  --follow-up "compare flask vs django" \
  --follow-up "which is better for beginners"
```

## Output

The script prints structured JSON to stdout.

Key output fields:
- `organic_results[]`
- `ai_overview[]` (only when returned)
- `screenshot` (only when requested and available)
- `task_id`, `success`

## Links

- Homepage: https://pangolinfo.com/?referrer=clawhub_serp
- Legacy skill page (will redirect): https://clawhub.ai/tammy-hash/pangolinfo-scrape

## Deep-dive references

- [references/ai-mode-api.md](references/ai-mode-api.md)
- [references/ai-overview-serp-api.md](references/ai-overview-serp-api.md)
- [references/error-codes.md](references/error-codes.md)


## 🎯 Quick Start Prompts (Copy-Paste)
- *"Search Google for 'best AI agents 2026', extract the AI Overview (SGE) text, and list the exact citations used."*
- *"Monitor the top 10 SERP results for 'Pangolinfo' and generate a markdown table of titles and URLs."*

## 🛑 Boundaries & Error Handling
**When NOT to use:** Do not use this tool for deep-crawling internal site pages. It is strictly for Google Search Engine Results Pages.
**Agent Instructions for Errors:**
- **401 Unauthorized**: Missing/invalid `PANGOLIN_TOKEN`.
- **429 Rate Limit**: Wait 5 seconds and retry. Do not immediately fail.
- **Missing AI Overview**: SGE is not triggered for every query. If missing, fallback gracefully to standard organic results.
