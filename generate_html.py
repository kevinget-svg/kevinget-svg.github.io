#!/usr/bin/env python3
"""Generate weekly report HTML from the SKILL template + Markdown data.
Usage: python3 generate_html.py reports/2026/08-10/08-10.md
"""
import sys, re, json, shutil, os
from pathlib import Path

md_path = Path(sys.argv[1])
md_text = md_path.read_text()

# ── parse markdown into structured data ──
sections = {}
# sections are: 新药研发, 监管资讯, 科研进展, AI发展, 商业布局
cat_map = {
    '新药研发': 'drug',
    '监管资讯': 'reg',
    '科研进展': 'research',
    'AI 发展': 'ai',
    '商业布局': 'biz',
}
cat_emoji = {
    '新药研发': '🆕',
    '监管资讯': '📋',
    '科研进展': '🔬',
    'AI 发展': '🤖',
    '商业布局': '💰',
}
counts = {}

# Split by ## headers
blocks = re.split(r'\n## ', md_text)
current_cat = None
items = []

for block in blocks:
    for cat_name in cat_map:
        if cat_name in block[:20]:
            current_cat = cat_name
            items = []
            sections[current_cat] = items
            break

    # Extract table rows: | N | **title** - summary | [source](url) | date |
    if current_cat == '科研进展':
        # Research has different format
        rows = re.findall(r'\|\s*\d+\s*\|\s*\*?\*?(.+?)\*?\*?\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|', block)
        for title, journal, source in rows:
            # Clean title - remove trailing ** pairs
            title = re.sub(r'\*+$', '', title).strip()
            url = ''
            src_match = re.search(r'\[([^\]]*)\]\(([^\)]*)\)', source)
            if src_match:
                src_name = src_match.group(1)
                url = src_match.group(2)
            else:
                src_name = source.strip()
            items.append({
                'title': title,
                'summary': '',
                'source': src_name,
                'source_url': url,
                'date': '',
                'journal': journal.strip(),
            })
    else:
        rows = re.findall(r'\|\s*\d+\s*\|\s*\*\*(.+?)\*\*\s*[-–—:：]?\s*(.*?)\s*\|\s*\[([^\]]*)\]\(([^\)]*)\)[^|]*\|\s*(\S+)\s*\|', block, re.DOTALL)
        for title, summary, src_name, url, date in rows:
            title = title.strip()
            summary = re.sub(r'\*\*', '', summary).strip()
            src_name = src_name.strip()
            url = url.strip()
            date = date.strip()
            items.append({
                'title': title,
                'summary': summary,
                'source': src_name,
                'source_url': url,
                'date': date,
                'journal': '',
            })

    counts[current_cat] = len(items)

# ── highlight cards ──
highlights = [
    {
        'tag': '历史性突破',
        'tag_class': 'breakthrough',
        'title': 'OX2R激动剂获批——发作性睡病进入病因治疗时代',
        'desc': '武田Orzeyful（oveporexton）8月5日获FDA批准，成为全球首个口服食欲素2型受体激动剂。该药从病因层面恢复食欲素信号通路，此前已于7月21日获NMPA全球首发批准，实现中美同步获批，标志着发作性睡病1型治疗范式的根本转变。',
        'source': 'FDA',
        'url': 'https://www.fda.gov/drugs/novel-drug-approvals-fda/novel-drug-approvals-2026',
        'date': '2026-08-05',
    },
    {
        'tag': '重大进展',
        'tag_class': 'major',
        'title': '核药赛道史上最大并购：Curium 80亿美元收购Lantheus',
        'desc': '每股$102.5现金，基础对价70亿美元，里程碑最高可达80亿美元（约540亿人民币）。Lantheus覆盖70+国家和地区，此次收购将重塑全球核药竞争格局，凸显放射性药物领域的战略价值。',
        'source': '药渡',
        'url': 'https://www.pharmacodia.com',
        'date': '2026-08-03',
    },
    {
        'tag': '重要动态',
        'tag_class': 'important',
        'title': 'AZ-BMS洽谈4000亿美元超级合并？制药史上最大并购传闻',
        'desc': '《金融时报》独家爆料阿斯利康与BMS洽谈合并，若达成将是制药行业历史上最大并购。消息一出，AZ伦敦股价应声下跌7.8%，BMS盘前涨3.8%，市场对这一潜在交易的复杂情绪可见一斑。',
        'source': 'Financial Times',
        'url': 'https://www.ft.com',
        'date': '2026-08-02',
    },
    {
        'tag': '重大进展',
        'tag_class': 'major',
        'title': '首个mRNA流感疫苗获批：Moderna mFLUSIVA',
        'desc': 'FDA批准Moderna mFLUSIVA（mRNA-1010）用于50岁及以上成人，成为全球首个mRNA流感疫苗。基于40,000例Phase 3数据，VRBPAC全票支持，mRNA技术平台在流感领域正式落地。',
        'source': 'RTTNews',
        'url': 'https://www.rttnews.com',
        'date': '2026-08-05',
    },
    {
        'tag': '重大进展',
        'tag_class': 'major',
        'title': 'BMS部署制药业最强AI超级计算机',
        'desc': '与NVIDIA合作搭建DGX SuperPOD，采用新一代Vera Rubin NVL72系统，搭载BioNeMo Agent Toolkit。预计2027年Q1上线，将数十亿化合物筛选时间从数月压缩至数天，加速从靶点发现到临床候选分子全流程。',
        'source': 'PharmaVoice',
        'url': 'https://www.pharmavoice.com/news/big-pharma-nvidia-ai-supercomputer-drug-research/827245',
        'date': '2026-08',
    },
]

# ── build HTML ──
def news_item_html(item, cat_key):
    title = item['title']
    summary = item['summary']
    src = item['source']
    url = item['source_url']
    date = item['date']
    journal = item.get('journal', '')

    if cat_key == 'research':
        summary_extra = f' | 期刊：{journal}' if journal else ''
        summary_html = f'<p class="item-summary">{summary}{summary_extra}</p>'
    else:
        summary_html = f'<p class="item-summary">{summary}</p>' if summary else ''

    source_html = f'<span class="item-source"><a href="{url}" target="_blank" rel="noopener">{src}</a></span>' if url else f'<span class="item-source">{src}</span>'
    date_html = f'<span class="item-date">{date}</span>' if date else ''

    return f'''<div class="news-item">
  <div class="item-head">
    <span class="item-title">{title}</span>
  </div>
  {summary_html}
  <div class="item-meta">
    {source_html}
    {date_html}
  </div>
</div>'''

def section_html(cat_name, cat_key, items_list):
    badge_map = {
        'drug': '新药研发',
        'reg': '监管资讯',
        'research': '科研进展',
        'ai': 'AI 发展',
        'biz': '商业布局',
    }
    title_map = {
        'drug': '🆕 新药研发 — Drug R&D',
        'reg': '📋 监管资讯 — Regulatory',
        'research': '🔬 科研进展 — Research',
        'ai': '🤖 AI 发展 — AI in Pharma',
        'biz': '💰 商业布局 — Business',
    }
    count = len(items_list)
    items_html = '\n'.join(news_item_html(i, cat_key) for i in items_list)
    return f'''<div class="section visible" data-cat="{cat_key}">
  <div class="section-header">
    <span class="cat-badge cat-{cat_key}">{badge_map[cat_key]}</span>
    <h2>{title_map[cat_key]}</h2>
    <span class="count">共 {count} 条</span>
  </div>
  {items_html}
</div>'''

def highlight_html(h):
    return f'''<div class="highlight-card">
  <span class="hl-tag {h['tag_class']}">{h['tag']}</span>
  <h3>{h['title']}</h3>
  <p class="hl-desc">{h['desc']}</p>
  <div class="hl-meta">
    <a href="{h['url']}" target="_blank" rel="noopener">{h['source']} →</a>
    <span class="hl-date">{h['date']}</span>
  </div>
</div>'''

sections_order = ['新药研发', '监管资讯', '科研进展', 'AI 发展', '商业布局']
all_sections_html = '\n'.join(
    section_html(c, cat_map[c], sections.get(c, []))
    for c in sections_order
)

total = sum(counts.values())

# ── CSS ──
css = '''    /* ===== 主题变量 ===== */
    :root {
      --bg: #ffffff; --bg-soft: #f5f7fa;
      --surface: #ffffff; --surface-2: #f0f3f7;
      --border: rgba(10,37,64,.10); --border-strong: rgba(10,37,64,.20);
      --text-1: #0a2540; --text-2: #425466; --text-3: #8898aa;
      --accent: #0a2540; --accent-2: #1d4ed8; --accent-3: #64748b;
      --good: #0e9f6e; --warn: #d97706; --bad: #dc2626;
      --grad: linear-gradient(135deg,#0a2540,#1d4ed8);
      --grad-soft: linear-gradient(135deg,#f0f4fb,#e4ecf7);
      --radius: 12px; --radius-lg: 18px;
      --shadow: 0 1px 3px rgba(10,37,64,.08),0 4px 12px rgba(10,37,64,.05);
      --shadow-lg: 0 4px 12px rgba(10,37,64,.10),0 16px 40px rgba(10,37,64,.08);
      --shadow-xl: 0 8px 24px rgba(10,37,64,.12),0 24px 56px rgba(10,37,64,.10);
      --font-sans: 'Inter','Noto Sans SC',sans-serif;
      --cat-drug: #1d4ed8; --cat-drug-bg: #eff6ff; --cat-drug-grad: linear-gradient(135deg,#1d4ed8,#3b82f6);
      --cat-reg: #d97706; --cat-reg-bg: #fffbeb; --cat-reg-grad: linear-gradient(135deg,#d97706,#f59e0b);
      --cat-research: #0e9f6e; --cat-research-bg: #ecfdf5; --cat-research-grad: linear-gradient(135deg,#0e9f6e,#34d399);
      --cat-ai: #7c3aed; --cat-ai-bg: #f5f3ff; --cat-ai-grad: linear-gradient(135deg,#7c3aed,#a78bfa);
      --cat-biz: #b45309; --cat-biz-bg: #fffbeb; --cat-biz-grad: linear-gradient(135deg,#b45309,#d97706);
    }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: var(--font-sans); background: var(--bg-soft); color: var(--text-1); line-height: 1.6; -webkit-font-smoothing: antialiased; }
    .container { max-width: 1000px; margin: 0 auto; padding: 24px; }
    .hero { background: var(--grad); color: #fff; border-radius: var(--radius-lg); padding: 56px 48px; margin-bottom: 32px; position: relative; overflow: hidden; }
    .hero::after { content: ''; position: absolute; right: -60px; top: -60px; width: 260px; height: 260px; background: rgba(255,255,255,.04); border-radius: 50%; }
    .hero .week { font-size: 14px; opacity: .75; font-family: 'JetBrains Mono', monospace; margin-bottom: 10px; letter-spacing: .04em; }
    .hero h1 { font-size: 44px; font-weight: 800; letter-spacing: -.03em; margin-bottom: 14px; line-height: 1.15; }
    .hero .sub { font-size: 16px; opacity: .80; max-width: 600px; }
    .category-cards { display: grid; grid-template-columns: repeat(6, 1fr); gap: 16px; margin-bottom: 32px; }
    .cat-card { position: relative; border-radius: var(--radius); padding: 24px 20px; cursor: pointer; transition: all .25s cubic-bezier(.4,0,.2,1); border: 1px solid transparent; overflow: hidden; text-decoration: none; display: block; color: inherit; }
    .cat-card::before { content: ''; position: absolute; inset: 0; opacity: 0; transition: opacity .25s; }
    .cat-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-xl); }
    .cat-card:hover::before { opacity: 1; }
    .cat-card .cat-icon { font-size: 32px; margin-bottom: 10px; display: block; position: relative; z-index: 1; }
    .cat-card .cat-count { font-size: 38px; font-weight: 800; letter-spacing: -.03em; line-height: 1; margin-bottom: 6px; position: relative; z-index: 1; }
    .cat-card .cat-label { font-size: 14px; font-weight: 600; position: relative; z-index: 1; }
    .cat-card .cat-sub { font-size: 11px; color: var(--text-3); margin-top: 4px; position: relative; z-index: 1; }
    .cat-card.total { background: var(--surface); border: 2px solid var(--accent-2); cursor: default; }
    .cat-card.total:hover { transform: none; box-shadow: none; color: inherit; }
    .cat-card.total::before { display: none; }
    .cat-card.total .cat-count { color: var(--accent); }
    .cat-card.total .cat-label { color: var(--accent); }
    .cat-card.drug { background: var(--cat-drug-bg); border-color: rgba(29,78,216,.20); }
    .cat-card.drug::before { background: var(--cat-drug-grad); }
    .cat-card.drug:hover { color: #fff; border-color: var(--cat-drug); }
    .cat-card.drug:hover .cat-sub { color: rgba(255,255,255,.7); }
    .cat-card.drug .cat-count { color: var(--cat-drug); }
    .cat-card.reg { background: var(--cat-reg-bg); border-color: rgba(217,119,6,.20); }
    .cat-card.reg::before { background: var(--cat-reg-grad); }
    .cat-card.reg:hover { color: #fff; border-color: var(--cat-reg); }
    .cat-card.reg:hover .cat-sub { color: rgba(255,255,255,.7); }
    .cat-card.reg .cat-count { color: var(--cat-reg); }
    .cat-card.research { background: var(--cat-research-bg); border-color: rgba(14,159,110,.20); }
    .cat-card.research::before { background: var(--cat-research-grad); }
    .cat-card.research:hover { color: #fff; border-color: var(--cat-research); }
    .cat-card.research:hover .cat-sub { color: rgba(255,255,255,.7); }
    .cat-card.research .cat-count { color: var(--cat-research); }
    .cat-card.ai { background: var(--cat-ai-bg); border-color: rgba(124,58,237,.20); }
    .cat-card.ai::before { background: var(--cat-ai-grad); }
    .cat-card.ai:hover { color: #fff; border-color: var(--cat-ai); }
    .cat-card.ai:hover .cat-sub { color: rgba(255,255,255,.7); }
    .cat-card.ai .cat-count { color: var(--cat-ai); }
    .cat-card.biz { background: var(--cat-biz-bg); border-color: rgba(180,83,9,.20); }
    .cat-card.biz::before { background: var(--cat-biz-grad); }
    .cat-card.biz:hover { color: #fff; border-color: var(--cat-biz); }
    .cat-card.biz:hover .cat-sub { color: rgba(255,255,255,.7); }
    .cat-card.biz .cat-count { color: var(--cat-biz); }
    .highlights-section { margin-bottom: 32px; }
    .section-title { font-size: 24px; font-weight: 700; margin-bottom: 20px; color: var(--text-1); display: flex; align-items: center; gap: 10px; }
    .section-title .icon { font-size: 28px; }
    .section-title .divider { flex: 1; height: 1px; background: var(--border); }
    .highlights-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }
    .highlight-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 28px; transition: all .25s; position: relative; overflow: hidden; }
    .highlight-card::before { content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 4px; background: linear-gradient(180deg,#dc2626,#e53e3e); border-radius: var(--radius-lg) 0 0 var(--radius-lg); }
    .highlight-card:hover { box-shadow: var(--shadow-lg); transform: translateY(-2px); }
    .highlight-card .hl-tag { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; margin-bottom: 10px; letter-spacing: .03em; }
    .highlight-card .hl-tag.breakthrough { background: #fef2f2; color: #dc2626; }
    .highlight-card .hl-tag.major { background: #eff6ff; color: #1d4ed8; }
    .highlight-card .hl-tag.important { background: #fffbeb; color: #d97706; }
    .highlight-card h3 { font-size: 17px; font-weight: 700; margin-bottom: 8px; color: var(--text-1); line-height: 1.4; }
    .highlight-card .hl-desc { font-size: 14px; color: var(--text-2); line-height: 1.6; margin-bottom: 12px; }
    .highlight-card .hl-meta { display: flex; align-items: center; gap: 12px; font-size: 12px; color: var(--text-3); }
    .highlight-card .hl-meta a { color: var(--accent-2); text-decoration: none; font-weight: 500; }
    .highlight-card .hl-meta a:hover { text-decoration: underline; }
    .highlight-card .hl-meta .hl-date { font-family: 'JetBrains Mono', monospace; }
    .filters { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 24px; align-items: center; }
    .filters .filter-label { font-size: 13px; color: var(--text-3); font-weight: 500; margin-right: 4px; }
    .filter-btn { padding: 7px 20px; border-radius: 22px; border: 1.5px solid var(--border); background: var(--surface); font-size: 13px; cursor: pointer; font-family: inherit; transition: all .15s; font-weight: 500; color: var(--text-2); }
    .filter-btn:hover { border-color: var(--accent-2); color: var(--accent-2); }
    .filter-btn.active { background: var(--accent-2); color: #fff; border-color: var(--accent-2); }
    .section { margin-bottom: 28px; display: none; }
    .section.visible { display: block; }
    .section-header { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; }
    .section-header h2 { font-size: 22px; font-weight: 700; }
    .section-header .count { font-size: 13px; color: var(--text-3); font-weight: 400; }
    .cat-badge { padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .06em; color: #fff; display: inline-block; }
    .cat-drug { background: var(--cat-drug); } .cat-reg { background: var(--cat-reg); }
    .cat-research { background: var(--cat-research); } .cat-ai { background: var(--cat-ai); }
    .cat-biz { background: var(--cat-biz); }
    .news-item { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 18px 22px; margin-bottom: 10px; transition: box-shadow .2s; position: relative; }
    .news-item:hover { box-shadow: var(--shadow); }
    .news-item .item-head { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 6px; }
    .news-item .item-title { font-size: 15px; font-weight: 600; flex: 1; }
    .news-item .item-summary { font-size: 13px; color: var(--text-2); line-height: 1.55; margin-bottom: 8px; }
    .news-item .item-meta { display: flex; align-items: center; gap: 12px; font-size: 12px; color: var(--text-3); }
    .news-item .item-source { font-weight: 500; }
    .news-item .item-source a { color: var(--accent-2); text-decoration: none; }
    .news-item .item-source a:hover { text-decoration: underline; }
    .news-item .item-date { font-family: 'JetBrains Mono', monospace; }
    footer { text-align: center; padding: 40px 24px; color: var(--text-3); font-size: 12px; border-top: 1px solid var(--border); margin-top: 20px; }
    footer a { color: var(--accent-2); text-decoration: none; }
    .sources { margin-top: 8px; opacity: .7; font-size: 11px; max-width: 600px; margin-left: auto; margin-right: auto; }
    @media (max-width: 900px) { .category-cards { grid-template-columns: repeat(3, 1fr); } .highlights-grid { grid-template-columns: 1fr; } }
    @media (max-width: 768px) { .hero h1 { font-size: 28px; } .hero { padding: 36px 28px; } .container { padding: 12px; } }
    @media (max-width: 560px) { .category-cards { grid-template-columns: repeat(2, 1fr); } .cat-card { padding: 18px 14px; } .cat-card .cat-count { font-size: 32px; } }'''

html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>医药研发周报 | 2026年第33周</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Sans+SC:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
{css}
  </style>
</head>
<body>
  <div class="container">
    <div class="hero">
      <div class="week">🦞 第33周 · 8月3日 — 8月9日</div>
      <h1>医药研发周报<br>Pharma R&D Weekly Report</h1>
      <p class="sub">新药研发 · 监管资讯 · 科研进展 · AI 发展 · 商业布局 — 一站式掌握全球医药动态</p>
    </div>

    <div class="category-cards" id="catCards">
      <div class="cat-card total">
        <span class="cat-icon">📊</span>
        <div class="cat-count">{total}</div>
        <div class="cat-label">本周总计</div>
        <div class="cat-sub">条医药研发资讯</div>
      </div>
      <div class="cat-card drug" data-cat="drug">
        <span class="cat-icon">🆕</span>
        <div class="cat-count">{counts.get('新药研发', 0)}</div>
        <div class="cat-label">新药研发</div>
        <div class="cat-sub">获批 · 临床 · 管线</div>
      </div>
      <div class="cat-card reg" data-cat="reg">
        <span class="cat-icon">📋</span>
        <div class="cat-count">{counts.get('监管资讯', 0)}</div>
        <div class="cat-label">监管资讯</div>
        <div class="cat-sub">FDA · NMPA · CDE</div>
      </div>
      <div class="cat-card research" data-cat="research">
        <span class="cat-icon">🔬</span>
        <div class="cat-count">{counts.get('科研进展', 0)}</div>
        <div class="cat-label">科研进展</div>
        <div class="cat-sub">论文 · 学术突破</div>
      </div>
      <div class="cat-card ai" data-cat="ai">
        <span class="cat-icon">🤖</span>
        <div class="cat-count">{counts.get('AI 发展', 0)}</div>
        <div class="cat-label">AI 发展</div>
        <div class="cat-sub">AI 制药 · 数字医疗</div>
      </div>
      <div class="cat-card biz" data-cat="biz">
        <span class="cat-icon">💰</span>
        <div class="cat-count">{counts.get('商业布局', 0)}</div>
        <div class="cat-label">商业布局</div>
        <div class="cat-sub">并购 · 融资 · 市场</div>
      </div>
    </div>

    <div class="highlights-section">
      <div class="section-title">
        <span class="icon">🏆</span>
        本周重磅
        <span class="divider"></span>
      </div>
      <div class="highlights-grid">
        {chr(10).join(highlight_html(h) for h in highlights)}
      </div>
    </div>

    <div class="filters">
      <span class="filter-label">筛选分类：</span>
      <button class="filter-btn active" data-cat="all">全部</button>
      <button class="filter-btn" data-cat="drug">🆕 新药研发</button>
      <button class="filter-btn" data-cat="reg">📋 监管资讯</button>
      <button class="filter-btn" data-cat="research">🔬 科研进展</button>
      <button class="filter-btn" data-cat="ai">🤖 AI 发展</button>
      <button class="filter-btn" data-cat="biz">💰 商业布局</button>
    </div>

{all_sections_html}

    <footer>
      <p>🦞 自动生成 by 小壮 · 每周一 10:00 更新 · <a href="https://kevinget-svg.github.io" target="_blank">在线浏览</a></p>
      <p class="sources">信息源：FDA · NMPA · CDE · EMA · ICH · PubMed · FiercePharma · Endpoints News · STAT · 医药魔方 · 药明康德 · 药融云 · 药融圈</p>
    </footer>
  </div>

  <script>
    document.querySelectorAll('.cat-card[data-cat]').forEach(card => {{
      card.addEventListener('click', () => {{
        const cat = card.dataset.cat;
        document.querySelectorAll('.filter-btn').forEach(b => {{
          b.classList.remove('active');
          if (b.dataset.cat === cat) b.classList.add('active');
        }});
        document.querySelectorAll('.section').forEach(s => {{
          s.classList.toggle('visible', cat === s.dataset.cat);
        }});
        document.querySelector('.filters').scrollIntoView({{ behavior: 'smooth', block: 'start' }});
      }});
    }});
    document.querySelectorAll('.filter-btn').forEach(btn => {{
      btn.addEventListener('click', () => {{
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const cat = btn.dataset.cat;
        document.querySelectorAll('.section').forEach(s => {{
          s.classList.toggle('visible', cat === 'all' || cat === s.dataset.cat);
        }});
      }});
    }});
    document.querySelectorAll('.section').forEach(s => s.classList.add('visible'));
  </script>
</body>
</html>'''

# Write HTML
html_dir = md_path.parent
html_dir.mkdir(parents=True, exist_ok=True)
html_path = html_dir / 'index.html'
html_path.write_text(html)
print(f"HTML written: {html_path} ({len(html)} bytes)")

# ── Update archives.json ──
repo_root = Path('/Users/wangyafei/projects/pharma-weekly')
archives_path = repo_root / 'archives.json'
archives = json.loads(archives_path.read_text())
archives.append({
    "date": "2026-08-10",
    "label": "第33周",
    "range": "2026年8月3日 — 8月9日",
    "path": "reports/2026/08-10/",
    "summary": f"本周共收录 {total} 条资讯：新药研发 {counts.get('新药研发',0)} 条（OX2R激动剂中美双批、首个mRNA流感疫苗、恒瑞HER2 ADC新适应症等），监管资讯 {counts.get('监管资讯',0)} 条（EMA 12款推荐、avacopan撤销、ICH E6(R3)实施），科研进展 {counts.get('科研进展',0)} 条（柳叶刀PSMA靶向核素、IgA肾病eGFR恢复），AI 发展 {counts.get('AI 发展',0)} 条（BMS超算、89亿零批准反思、AI诊断入医保），商业布局 {counts.get('商业布局',0)} 条（Curium 80亿并购、AZ-BMS合并传闻、四家同周IPO）"
})
archives_path.write_text(json.dumps(archives, ensure_ascii=False, indent=2))
print(f"Archives updated: {archives_path}")

# ── Sync to Obsidian ──
obsidian_dir = Path('/Users/wangyafei/Documents/Myobs/医药研发周报/2026')
obsidian_dir.mkdir(parents=True, exist_ok=True)
obsidian_path = obsidian_dir / '08-10.md'
shutil.copy(md_path, obsidian_path)
print(f"Synced to Obsidian: {obsidian_path}")

# ── Copy index.html to repo root for GitHub Pages ──
root_html = repo_root / 'index.html'
shutil.copy(html_path, root_html)
print(f"Copied to repo root: {root_html}")
