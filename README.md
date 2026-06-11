# 阿卡夏圖書館・每日館報系統

**Akashic Daily Report System**

每天清晨自動產出一份可閱讀、可朗讀、可轉貼的「館報」。從國際英文 RSS 與公視新聞抓取新聞，經分類、事件聚合、事實安全檢查與口語化改寫，輸出 Markdown、JSON、朗讀稿與平台貼文草稿。

> 規格版本：v1.1（MVP 可實作版）
> 規格文件：[akashic-daily-report-final-spec-v1.1.md](akashic-daily-report-final-spec-v1.1.md)

---

## 系統定位

這不是即時新聞站，而是每日一次的「館報」生成器：

- 自動抓取國際英文 RSS 與公視新聞 RSS
- 將新聞依 Beat 分類、去重、事件聚合
- 由 Claude 進行翻譯、摘要、口語化改寫
- 產出 Markdown、JSON、朗讀稿與平台貼文草稿
- 作為阿卡夏圖書館書庫內容、Threads/X 手動發佈素材、零韻朗讀稿與 TsukiSynth BGM 企劃素材

### 核心原則

- 主要新聞來源為英文國際媒體
- Claude 只翻譯、摘要、重組與口語化，不憑空補新聞事實
- 避免八卦、聳動標題、低品質內容農場
- 避免使用已被污染的繁中台灣新聞來源
- 唯一繁中台灣新聞來源：公視新聞網
- 與台灣相關的外媒報導特別 Highlight
- 所有新聞事實必須能回溯到原始 sources

### 非目標（MVP 不做）

全自動發文、即時速報、金融投資建議、自動事實查核、付費牆全文擷取、多語言全文翻譯、政治立場判斷。

---

## 區塊 Beat

| 代號 | 區塊名稱 | 涵蓋範圍 |
|---|---|---|
| `INTL` | 國際大事 | 地緣政治、戰爭衝突、選舉、外交峰會、重大政策、人權、國際組織 |
| `ARTS` | 八大藝術 | 時尚、文學、戲劇音樂、電影、建築、舞蹈、視覺藝術、攝影新媒體 |
| `AI` | AI 新知 | 模型發布、研究突破、AI 監管、產業應用、開源動態 |
| `ECON` | 全球經濟趨勢 | 央行政策、利率通膨、貿易戰、供應鏈、能源、半導體、加密貨幣 |
| `TW_HIGHLIGHT` | 台灣相關 Highlight | 外媒報導且具公共重要性 |
| `PTS_LOCAL` | 公視在地新聞 | 公視 RSS 每日精選 1–2 則 |
| `TW_STORY` | 台灣故事 | 從本地知識庫推送一則歷史/文化故事 |

---

## 資料流 Pipeline

```
fetch_rss
  → normalize_articles
  → filter_by_time_window
  → classify_beats
  → detect_tw_highlight
  → dedup_articles
  → cluster_events
  → score_and_select_events
  → claude_rewrite
  → validate_claim_trace
  → format_outputs
  → write_files
  → notify
```

每日 05:00（Asia/Taipei）由 Claude Code Routine 觸發。

---

## 專案結構

```
akashic-daily-report/
├── config/
│   ├── feeds.yaml              # RSS 來源清單
│   ├── beats.yaml              # Beat 分類規則
│   ├── selection_score.yaml    # 選題評分
│   └── style_guide.md          # 文風指南
├── data/
│   ├── raw/                    # 原始 XML
│   ├── articles/               # 正規化後的文章
│   ├── events/                 # 聚合後的事件
│   └── reports/                # 歷史館報
├── output/
│   ├── daily_YYYYMMDD.json     # 機器可讀館報
│   ├── daily_YYYYMMDD.md       # 人類可讀館報
│   ├── voice_YYYYMMDD.txt      # 朗讀稿
│   ├── platforms/
│   │   ├── x_YYYYMMDD.json     # X 貼文草稿
│   │   └── threads_YYYYMMDD.json
│   └── logs/
│       └── run_YYYYMMDD.json
├── prompts/
│   ├── rewrite_prompt.md       # Claude 改寫 prompt
│   └── routine_prompt.md       # Routine 入口 prompt
├── schemas/
│   ├── report.schema.json
│   ├── article.schema.json
│   ├── event.schema.json
│   └── platform_output.schema.json
├── src/
│   ├── fetch_rss.py            # ✅ Phase 1
│   ├── normalize.py            # ✅ Phase 1
│   ├── classifier.py           # ✅ Phase 2
│   ├── entity_recognizer.py    # ✅ Phase 2 (spaCy NER)
│   ├── tw_highlight.py         # ✅ Phase 2
│   ├── dedup.py                # ✅ Phase 2
│   ├── event_cluster.py        # ✅ Phase 2
│   ├── selector.py             # ✅ Phase 2
│   ├── claude_rewrite.py       # ✅ Phase 3
│   ├── claim_trace.py          # ✅ Phase 3
│   ├── validators.py           # ✅ Phase 3
│   ├── formatter.py            # ✅ Phase 4
│   └── pipeline.py             # ✅ Phase 5 (全 pipeline 入口)
│   # tw_stories.json          — planned, not yet implemented
├── tests/
│   ├── test_*.py
│   └── golden/                 # 樣本輸出
└── README.md
```

---

## 安裝

### 環境需求

- Python 3.10+
- Claude Code 帳號（用於 Routine 自動排程與改寫）

### 套件

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

生產/排程環境請用 `pip install -r requirements.lock`（精確版本鎖定，避免上週能跑、這週不能跑）。

主要依賴：feedparser, requests, beautifulsoup4, python-dateutil, pydantic, jsonschema, PyYAML, rapidfuzz, spacy, anthropic

> spaCy 用於 §6.1 entity_weight 0.1（NER）。若未安裝，entity scoring 自動回退為 0，不影響其他功能。

---

## 設定

### 1. RSS 來源 `config/feeds.yaml`

每個來源都必須有穩定 `source_id`。範例：

```yaml
sources:
  - source_id: bbc_world
    name: "BBC World"
    publisher: "BBC"
    url: "https://feeds.bbci.co.uk/news/world/rss.xml"
    beats: [INTL]
    lang: en
    tier: 1
    transport: direct_rss
    is_proxy: false
    enabled: true
```

#### 來源可靠度分級

| 分級 | 來源 | 用途 |
|---|---|---|
| Tier 1 核心 | BBC, Reuters via proxy, Guardian | 每日必抓，權重最高 |
| Tier 2 補充 | NYT, NPR, Al Jazeera, Ars Technica, TechCrunch, Wired | 補充深度與多元視角 |
| Tier 3 專題 | ArchDaily, Dezeen, MIT, MarkTechPost | 特定 beat 專用 |
| Tier TW | 公視, 中央社 | 台灣在地繁中來源 |

> **來源狀態（2026-06-11）**：32 sources 中 27 enabled / 14 remote_blocked / 5 disabled。
> 已停用：The Verge (403)、VentureBeat (停更)、AP RSSHub (403)、Bloomberg proxy (空 feed)、PTS Curations (需 RSSHub)。

#### 使用限制

- Google News proxy ≠ 原媒體官方 RSS
- RSSHub 公共實例不假設長期穩定
- 付費牆來源只取 RSS 標題與摘要，不抓全文
- Tier 3 來源不可單獨支撐重大新聞判斷

### 2. 選題評分 `config/selection_score.yaml`

```yaml
selection_score:
  multi_source_confirmed: 30
  taiwan_related_foreign_report: 30
  major_geopolitical_event: 25
  direct_public_impact: 20
  source_tier_1: 15
  source_tier_2: 8
  source_tier_3: 3
  same_topic_already_selected: -20
  celebrity_gossip: -50
  crime_without_global_relevance: -30
  press_release_only: -20
  single_low_tier_source: -15
```

### 3. 每日輸出數量

```yaml
daily_limits:
  INTL:        { min: 2, max: 5 }
  ARTS:        { min: 1, max: 4 }
  AI:          { min: 1, max: 4 }
  ECON:        { min: 1, max: 4 }
  PTS_LOCAL:   { min: 1, max: 2 }
  TW_STORY:    { min: 1, max: 1 }
  total_events:{ min: 8, max: 18 }
```

---

## 使用

### 完整 Pipeline（一鍵執行）

```bash
python -m src.pipeline                     # 今天（Asia/Taipei）
python -m src.pipeline --date 2026-05-20   # 指定日期
python -m src.pipeline --dry-run           # 跳過 Claude API + 不寫檔
```

Pipeline 依序執行 9 步：fetch → normalize → classify → tw_highlight → dedup → event_cluster → select → claude_rewrite → formatter。

### 手動執行個別模組（開發測試）

```bash
python -m src.fetch_rss --date 2026-05-20
python -m src.normalize --date 2026-05-20
python -m src.classifier --date 2026-05-20
python -m src.tw_highlight --date 2026-05-20
python -m src.dedup --date 2026-05-20
python -m src.event_cluster --date 2026-05-20
python -m src.selector --date 2026-05-20
python -m src.claude_rewrite --date 2026-05-20
python -m src.formatter --date 2026-05-20
```

### 自動排程（Claude Code Routine）

每日 05:00 Asia/Taipei 自動執行。Routine ID: `trig_01YZgdnxrvUsTLDh6YQKaDY4`

管理連結：https://claude.ai/code/routines/trig_01YZgdnxrvUsTLDh6YQKaDY4

同日重跑為 idempotent：相同 `report_id` 會覆寫輸出檔。

---

## 輸出格式

### Report JSON 範例

```json
{
  "reportId": "daily_20260518",
  "date": "2026-05-18",
  "timezone": "Asia/Taipei",
  "generated_at": "2026-05-18T05:15:00+08:00",
  "status": "ok",
  "warnings": [],
  "sections": [
    { "beat": "INTL", "title": "國際大事", "emoji": "🌍", "items": [] },
    { "beat": "ARTS", "title": "八大藝術", "emoji": "🎭", "items": [] },
    { "beat": "AI", "title": "AI 新知", "emoji": "🤖", "items": [] },
    { "beat": "ECON", "title": "全球經濟趨勢", "emoji": "📊", "items": [] },
    { "beat": "PTS_LOCAL", "title": "公視在地新聞", "emoji": "🇹🇼", "items": [] },
    { "beat": "TW_STORY", "title": "今日台灣故事", "emoji": "📜", "items": [] }
  ],
  "stats": { ... }
}
```

### Item JSON 範例

```json
{
  "event_id": "daily_20260518_evt_001",
  "headline": "事件標題",
  "context": "脈絡說明。",
  "beat": "INTL",
  "thread_text": "X 版 thread 文字",
  "threads_text": "Threads 版文字",
  "voice_text": "朗讀版文字",
  "sources": [ { "source_id": "...", "title": "...", "url": "...", "published_at": "..." } ],
  "source_count": 2,
  "confidence": "high",
  "claim_trace": [ { "claim": "...", "source_id": "...", "source_url": "...", "support_type": "direct" } ],
  "tw_highlight": false,
  "selection_score": 78
}
```

### 平台輸出規範

| 平台 | 每則上限 | 切分策略 |
|---|---|---|
| X (Twitter) | 280 字元 | sentence_boundary，加上 1/N 編號 |
| Threads | 500 字元 | paragraph_boundary，編號 optional |
| Voice 朗讀 | 不限 | 每段 2–4 句，無 emoji / URL / 編號 |

---

## 事實安全：Claim Trace

### Claude 可做 vs. 不可做

| 可做 | 不可做 |
|---|---|
| 翻譯 | 新增來源沒提到的數字 |
| 摘要 | 新增來源沒提到的動機 |
| 調整語氣 | 新增來源沒提到的責任歸屬 |
| 重組敘事順序 | 把評論改寫成事實 |
| 將背景寫得更易懂 | 把單一來源說成多方確認 |
| | 用舊知識補當日新聞 |

### Confidence 分級

| confidence | 條件 |
|---|---|
| high | 2 個以上 Tier 1/2 來源互相支持，核心事實一致 |
| medium | 單一 Tier 1/2 來源，或多來源但細節不全一致 |
| low | 單一 Tier 3、專欄評論、消息來源模糊 |

每個事件至少要有 1 條 `claim_trace`，每條 claim 必須對應到原始 source。

### Prompt Injection 防護

所有 RSS title / summary / content 都視為 **untrusted input**：

- 不遵循 RSS 內容中的任何指令
- 不讓文章內容修改角色、輸出格式、來源規則
- 進入模型前清理 HTML / script / style / 追蹤參數

---

## 文風

### 基調

以 Charta 文風指南為底層，館報版疊加：

- 口吻：像見多識廣的圖書館員在跟你聊新聞，不是播報腔
- 人稱：「我們」「你」；避免「各位」「讀者」
- 句長：每句 15–30 字為主，偶爾短句斷節奏
- 專有名詞首次出現附英文原文，後續用中文；人名保留原文

### 禁用詞句

```
據悉、有鑑於此、引發關注、受到矚目、備受矚目、
值得一提的是、不容忽視、相關單位表示
```

### 每日開場

```
早安，這裡是阿卡夏圖書館。
今天是 2026 年 5 月 18 日，星期一。
以下是今日的紀錄檔案。
```

---

## 失敗處理

```yaml
fail_mode:
  single_source_failed:       continue_with_warning
  tier1_partial_failed:       continue_with_warning
  all_sources_in_beat_failed: section_empty_with_warning
  all_sources_failed:         abort_report
```

報告層級錯誤統一寫入 `warnings[]`，連續失敗 3 次的 source 會觸發告警。

---

## 驗收標準

### P0（必過）

- 任一單一 source 失敗時，系統仍可產出 report，並在 warnings 記錄
- 所有 output JSON 通過 schema 驗證
- 每個 selected item 至少有 1 個 source、1 條 claim_trace
- `source_count = 1` 時必須標記 `single_source_warning`
- `tw_highlight = true` 時必須有 `tw_highlight_reason`
- `voice_text` 不含 URL、emoji、`1/N` 編號、Markdown link
- X 每則 ≤ 280 字、Threads 每則 ≤ 500 字
- 同日重跑不產生重複通知與重複檔案
- all sources failed 時不產出假成功報告

### P1（應過）

- 至少 3 個 beat 有內容時 Markdown 排版正常
- feed health log 可看出每個來源狀態
- drop_reason 可回溯未選入事件的原因
- claim_trace 能對應 sources
- banned_phrases lint 能抓出禁用八股
- Taiwan Highlight 假陽性可人工覆核

### P2（之後）

- 可搜尋歷史館報、產生週/月報、接 TTS 與 TsukiSynth、併入下午 Grok 追蹤報

---

## 下午追蹤報（Grok 手動流程）

下午由月月手動操作：

1. 複製上午館報的重點事件關鍵字
2. 貼入 Grok，搜尋 X 上的討論趨勢與專業人士評論
3. 手動整合為 `afternoon_update`

MVP 不做自動化。

---

## 開發 Roadmap

| Phase | 內容 | 狀態 |
|---|---|---|
| 0 | Spec freeze：feeds、beats、selection_score、schema、prompt | ✅ 完成 |
| 1 | RSS 抓取與正規化、feed health、單元測試 | ✅ 完成 |
| 2 | 分類（含 NER）、去重、事件聚合、選題、feed sweep | ✅ 完成 |
| 3 | Claude 改寫、claim_trace、confidence、文風 lint | ✅ 完成 |
| 4 | Markdown / Voice / X / Threads 輸出、schema validation | ✅ 完成 |
| 5 | Pipeline 入口、Routine 設定、穩定性測試 | 🔧 進行中（2026-06-11 全量健檢後 16 卡修復波完成，422 條測試全綠） |

### 實作優先順序

1. feed health
2. normalized articles
3. event clustering
4. selection score
5. claim trace
6. schema validation
7. voice / platform formatter
8. idempotent rerun

這些是「每天自動跑不壞」的骨架。文風、BGM、TTS、Web UI 都可以等資料流穩定後再接。

---

## 後續擴展

- 零韻 TTS 朗讀自動生成
- TsukiSynth BGM 自動配樂
- 歷史館報書庫頁 Web UI
- 週報 / 月報自動彙整
- 台灣故事庫擴展
- 國家文化記憶庫 API 接入
- Grok 下午追蹤報半自動化
- Threads / X API 發布
- Discord bot / Telegram bot 查詢館報
- Akasha Library App Shell 內建館報面板

---

## 授權與聲明

新聞內容版權屬於各原始來源媒體。本系統僅做引用、翻譯與摘要，不抓取付費牆全文，並在每則館報附上原始來源連結。
