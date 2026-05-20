# 整合設計稿：akasha-rss-news → akasha-library

> 版本：v1.0（2026-05-19）
> 對應規格：akashic-daily-report-final-spec-v1.1.md §11–§17
> 前置依賴：Phase 4 formatter 完成後方可實作

---

## 1. 概覽

akasha-rss-news（本專案）每天 05:00 自動產出六種檔案。
akasha-library（PWA）有一個 `modules/daily-report/` 模組，目前靠**人工貼文字 → AI 整理**。

本設計稿定義：如何讓 akasha-rss-news 的產出**自動流入** akasha-library，取代手動貼文字，同時保留手動模式作為 fallback。

```
akasha-rss-news                         akasha-library
┌──────────────┐                        ┌──────────────────────┐
│ daily_*.json │──── bridge.js ────────▶│ daily-report module  │
│ voice_*.txt  │──── voice adapter ───▶│ report-voice.js      │
│ x_*.json     │──── platform panel ──▶│ (new) publish panel  │
│ threads_*.json│                       │                      │
│ daily_*.md   │──── 靜態下載 ─────────▶│ export 按鈕          │
│ run_*.json   │──── (不進 PWA) ───────▶│ (dev-only log)       │
└──────────────┘                        └──────────────────────┘
```

---

## 2. 資料格式對照

### 2.1 現有格式差異

| 欄位         | akasha-rss-news (report.schema.json)      | akasha-library (daily-report) |
|-------------|-------------------------------------------|-------------------------------|
| 頂層 ID     | `reportId: "daily_20260519"`               | `reportId` (自訂字串)          |
| 日期         | `date: "2026-05-19"`                      | `date` (同格式)               |
| 時區         | `timezone: "Asia/Taipei"`                 | (無)                          |
| 產出時間     | `generated_at` (ISO datetime)              | (無)                          |
| 狀態         | `status: "ok" / "partial" / "failed"`     | (無)                          |
| 警告         | `warnings: [{type, message, source_id}]`  | (無)                          |
| 統計         | `stats: {total_feeds_checked, ...}`        | (無)                          |
| sections    | `[{beat, title, emoji, items}]`            | `[{title, items}]`            |
| item 結構   | 完整 platform_output（見 §2.2）            | `{source, title, summary, url}` |

### 2.2 item 欄位映射

akasha-rss-news 的每個 item 有 20+ 個欄位（event_id, headline, context, beat, thread_text, threads_text, voice_text, platform_outputs, sources, source_count, confidence, claim_trace, tw_highlight...）。

akasha-library 的 renderReport() 只讀四個欄位：`title`, `summary`, `source`, `url`。

**映射規則（bridge 層負責）：**

```javascript
// akasha-rss-news item → akasha-library item
function bridgeItem(rssItem) {
  return {
    // 必填：直接映射
    title:   rssItem.headline,
    summary: rssItem.context,

    // 來源：取第一來源的 publisher
    source:  rssItem.sources?.[0]?.publisher ?? '',
    url:     rssItem.sources?.[0]?.url ?? '',

    // 擴充欄位：akasha-library 不會壞，但可漸進使用
    _event_id:       rssItem.event_id,
    _beat:           rssItem.beat,
    _confidence:     rssItem.confidence,
    _source_count:   rssItem.source_count,
    _tw_highlight:   rssItem.tw_highlight,
    _voice_text:     rssItem.voice_text,
    _claim_trace:    rssItem.claim_trace,
    _selection_score: rssItem.selection_score,
    _all_sources:    rssItem.sources,
    _platform_outputs: rssItem.platform_outputs,
    _single_source_warning: rssItem.single_source_warning ?? false,
    _opinion_level:  rssItem.opinion_level,
  };
}
```

**設計原則：**
- 核心四欄位（title / summary / source / url）直接映射，**不改 akasha-library 現有程式碼**
- 擴充欄位用 `_` 前綴，akasha-library 的 renderReport() 會自動忽略
- 日後 akasha-library 升級 UI 時，可逐步讀取 `_` 欄位顯示信心度、來源數量、台灣焦點標記等

### 2.3 section 映射

```javascript
function bridgeSection(rssSection) {
  return {
    title: `${rssSection.emoji} ${rssSection.title}`,
    items: rssSection.items.map(bridgeItem),

    // 擴充
    _beat:  rssSection.beat,
    _emoji: rssSection.emoji,
  };
}
```

### 2.4 report 頂層映射

```javascript
function bridgeReport(rssReport) {
  return {
    reportId: rssReport.reportId,          // "daily_20260519"
    date:     rssReport.date,              // "2026-05-19"
    sections: rssReport.sections.map(bridgeSection),

    // 擴充：不影響現有功能
    _generated_at: rssReport.generated_at,
    _status:       rssReport.status,
    _warnings:     rssReport.warnings,
    _stats:        rssReport.stats,
    _source:       'akasha-rss-news',      // 標記來源為自動系統
  };
}
```

---

## 3. 傳輸機制

### 3.1 方案比較

| 方案 | 說明 | 優點 | 缺點 |
|------|------|------|------|
| A. 本地檔案讀取 | PWA 用 File API 讀取 output/ 資料夾 | 零伺服器成本 | 需使用者手動選檔、不自動 |
| B. GitHub Pages | output/ 推到 GitHub → PWA fetch | 免費、自動、可追溯 | 公開 repo、延遲 ~2min |
| C. Google Drive 同步 | output/ 上傳到 Drive → PWA 已有 Drive 同步 | 沿用既有架構 | 需要 Drive API 授權 |
| D. PostMessage 注入 | 外部腳本 fetch JSON → postMessage 進 iframe | 最彈性 | 需要 app shell 改造 |

**建議：B + A 雙軌**
- **主路線 (B)**：Routine 每天 push output/ 到 GitHub → PWA 用 fetch 抓最新 JSON
- **備援 (A)**：保留手動匯入按鈕，使用者可拖入本地 JSON 檔

### 3.2 主路線實作（GitHub Pages fetch）

```
akasha-rss-news Routine (05:00)
  ↓ git push output/ → GitHub
  ↓
GitHub Pages (自動部署)
  ↓ https://tskr2828.github.io/akasha-rss-news/output/daily_20260519.json
  ↓
akasha-library daily-report module
  ↓ fetch → bridgeReport() → renderReport()
```

**PWA 端 fetch 邏輯（新增到 daily-report/index.html）：**

```javascript
const RSS_BASE = 'https://tskr2828.github.io/akasha-rss-news/output';

async function fetchTodayReport() {
  const today = new Date().toISOString().slice(0, 10).replace(/-/g, '');
  const url = `${RSS_BASE}/daily_${today}.json`;

  try {
    const res = await fetch(url, { cache: 'no-cache' });
    if (!res.ok) return null;
    const rssReport = await res.json();
    return bridgeReport(rssReport);
  } catch {
    return null;
  }
}
```

### 3.3 備援：手動匯入

新增一個「匯入 JSON」按鈕在左側面板，讓使用者拖入或選擇 `daily_*.json`：

```javascript
async function importLocalReport(file) {
  const text = await file.text();
  const rssReport = JSON.parse(text);

  // 驗證基本結構
  if (!rssReport.reportId || !rssReport.sections) {
    throw new Error('不是有效的館報 JSON');
  }

  return bridgeReport(rssReport);
}
```

---

## 4. akasha-library 模組改動

### 4.1 daily-report/index.html 變更範圍

改動原則：**最小侵入，向後相容**。手動貼文字模式保留不動。

```
現有流程：
  使用者貼文字 → [整理成館報] → AI 整理 → renderReport()

新增流程（二選一）：
  (A) 自動載入：頁面開啟 → fetchTodayReport() → renderReport()
  (B) 手動匯入：使用者選 JSON → importLocalReport() → renderReport()
```

**具體新增 UI 元素：**

| 元素 | 位置 | 說明 |
|------|------|------|
| 「今日館報」按鈕 | header 右側 | 點擊 → fetch 最新自動館報 |
| 「匯入 JSON」按鈕 | 左側面板 input-actions | 備援匯入 |
| 來源標記 | report-header | 顯示「🤖 自動生成」或「✍️ 手動整理」|
| 信心度徽章 | report-item（未來） | 讀取 `_confidence` 顯示 high/medium/low |
| 台灣焦點標記 | report-item（未來） | 讀取 `_tw_highlight` 顯示 🇹🇼 |

### 4.2 新增檔案

```
akasha-library/
  modules/daily-report/
    index.html          ← 修改（加 fetch + import + UI）
    rss-bridge.js       ← 新增（bridgeReport / bridgeSection / bridgeItem）
  core/
    report-voice.js     ← 不動（已相容）
    voice.js            ← 不動
```

**rss-bridge.js 完整介面：**

```javascript
// rss-bridge.js — akasha-rss-news ↔ akasha-library 格式轉換

export function bridgeReport(rssReport)  { /* §2.4 */ }
export function bridgeSection(rssSection) { /* §2.3 */ }
export function bridgeItem(rssItem)       { /* §2.2 */ }
export function isRssReport(obj)          { /* 驗證是否為 rss-news 格式 */ }
export function extractVoiceText(rssReport) { /* 提取 voice_text → 組裝朗讀稿 */ }
export function extractPlatformDrafts(rssReport) { /* 提取 X / Threads 草稿 */ }
```

### 4.3 不需要改的部分

以下 akasha-library 功能**不需改動**，因為 bridge 後的格式完全相容：

- ✅ `renderReport()` — 只讀 sections[].title 和 items[].{title, summary, source, url}
- ✅ `callParentMemory('save', ...)` — 存的是 JSON.stringify(report)，格式無關
- ✅ `exportReport('md')` 和 `exportReport('json')` — 讀同樣的欄位
- ✅ `loadHistory()` / `renderHistory()` — 靠 IndexedDB，不管 report 內容
- ✅ 主題切換 (dark/light) — PostMessage 驅動，與資料無關

---

## 5. 語音整合

> **決定（2026-05-19）：朗讀由獨立專案處理，本整合不實作 PWA 端 TTS 播放。**

### 5.1 akasha-rss-news 提供的語音資料

akasha-rss-news 產出兩種語音相關資料，供外部朗讀專案使用：

| 資料 | 位置 | 格式 |
|------|------|------|
| `voice_text` | 每個 item 的欄位 | 單段中文朗讀稿（不含 URL、emoji、Markdown） |
| `voice_YYYYMMDD.txt` | `output/` 檔案 | 完整朗讀稿純文字（Phase 4 formatter 產出） |

### 5.2 本整合的責任範圍

- ✅ bridge 後的 JSON 保留 `_voice_text` 欄位 → 朗讀專案可從 IndexedDB 讀取
- ✅ `voice_YYYYMMDD.txt` 隨 output/ 一起 push → 朗讀專案可直接 fetch
- ❌ 不在 daily-report 模組加「朗讀」按鈕
- ❌ 不新增 `akasha-voice-play-tasks` PostMessage type
- ❌ 不改動 akasha-library 的 `report-voice.js` 或 `voice.js`

akasha-library 現有的朗讀按鈕（手動模式）不動，繼續使用 `reportToVoiceTasks()`。
自動館報的語音播放由朗讀專案獨立處理。

---

## 6. 平台輸出整合（X / Threads 草稿）

### 6.1 現狀

akasha-library 目前**沒有** X 或 Threads 發文功能。
akasha-rss-news 產出的 `x_*.json` 和 `threads_*.json` 目前是給人類複製貼上用的。

### 6.2 設計：發文預覽面板

在 daily-report 模組新增一個 tab 或 panel，顯示平台草稿：

```
┌─────────────────────────────────────────┐
│  館報  │  𝕏 草稿  │  Threads 草稿  │    │ ← 三個 tab
├─────────────────────────────────────────┤
│  [1/3]  🌍 俄烏停火協議第三輪談判破裂    │
│  ─────────────────────────────────────  │
│  俄烏停火協議第三輪談判在日內瓦破裂，     │
│  雙方在領土讓步問題上分歧擴大...          │
│                                         │
│  [📋 複製] [📋 全部複製]                 │
└─────────────────────────────────────────┘
```

**從 report JSON 提取草稿：**

```javascript
// rss-bridge.js
export function extractPlatformDrafts(rssReport) {
  const x = [];
  const threads = [];

  for (const section of rssReport.sections) {
    for (const item of section.items) {
      if (item.platform_outputs?.x?.posts) {
        x.push({
          event_id: item.event_id,
          headline: item.headline,
          beat: item.beat,
          posts: item.platform_outputs.x.posts,
        });
      }
      if (item.platform_outputs?.threads?.posts) {
        threads.push({
          event_id: item.event_id,
          headline: item.headline,
          beat: item.beat,
          posts: item.platform_outputs.threads.posts,
        });
      }
    }
  }

  return { x, threads };
}
```

### 6.3 優先級

發文面板是 **Post-MVP** 功能（ROADMAP 優先級 4）。MVP 階段只需確保 bridge 正確保留 `_platform_outputs` 欄位即可。

---

## 7. IndexedDB 儲存

### 7.1 現有機制

akasha-library 的 IndexedDB 儲存由 app shell 的 memory 模組管理。
daily-report 透過 PostMessage 呼叫 `callParentMemory('save', {...})`：

```javascript
callParentMemory('save', {
  id: state.currentReportId || undefined,
  module: 'daily-report',
  scope: 'report',
  title: `館報 ${report.date}（${sectionCount} 主題）`,
  content: JSON.stringify(report),
  tags: ['館報', report.date],
  source: 'daily-report',
});
```

### 7.2 整合策略

自動館報存入 IndexedDB 時，**保留完整 bridge 後的 JSON**（含 `_` 前綴欄位）：

```javascript
async function saveAutoReport(bridgedReport, rawRssReport) {
  const sectionCount = bridgedReport.sections?.length || 0;
  const title = `🤖 館報 ${bridgedReport.date}（${sectionCount} 主題）`;

  await callParentMemory('save', {
    module: 'daily-report',
    scope: 'report',
    title,
    content: JSON.stringify(bridgedReport),
    tags: ['館報', bridgedReport.date, '自動'],
    source: 'akasha-rss-news',
  });
}
```

**差異標記：**
- 自動館報：title 前綴 `🤖`，tags 含 `'自動'`，source = `'akasha-rss-news'`
- 手動館報：title 無前綴，tags 不含 `'自動'`，source = `'daily-report'`

歷史列表可以靠 tags 或 source 欄位區分顯示。

### 7.3 同日覆寫

規格要求「相同 report_id 覆寫檔案」。

在 IndexedDB 中，用 `reportId` 作為去重鍵：

```javascript
async function upsertReport(bridgedReport) {
  // 找是否已有同日報告
  const all = await callParentMemory('getAll', 'daily-report');
  const existing = all.find(r => {
    try {
      const stored = JSON.parse(r.content);
      return stored.reportId === bridgedReport.reportId;
    } catch { return false; }
  });

  if (existing) {
    // 覆寫
    await callParentMemory('save', {
      id: existing.id,
      module: 'daily-report',
      scope: 'report',
      title: `🤖 館報 ${bridgedReport.date}（${bridgedReport.sections.length} 主題）`,
      content: JSON.stringify(bridgedReport),
      tags: ['館報', bridgedReport.date, '自動'],
      source: 'akasha-rss-news',
    });
  } else {
    await saveAutoReport(bridgedReport);
  }
}
```

---

## 8. Google Drive 同步

### 8.1 現有機制

akasha-library 的 Google Drive 同步是 app shell 層級的功能，會定期把 IndexedDB 資料同步到 Drive。

### 8.2 整合策略

**不需要額外做事。** 自動館報存入 IndexedDB 後，app shell 的 Drive 同步會自動上傳。

如果未來需要**獨立備份完整 report JSON**（含 claim_trace、dropped_events 等 bridge 時省略的資料），可以在 akasha-rss-news Routine 裡直接上傳到 Drive 的特定資料夾，但這不在 MVP 範圍。

---

## 9. 自動載入流程（完整 sequence）

```
使用者開啟 akasha-library → 切到「每日館報」模組
  ↓
daily-report/index.html 載入
  ↓
loadHistory()                    ← 現有：載入 IndexedDB 歷史
  ↓
checkAutoReport()                ← 新增：檢查今日自動館報
  ↓
fetchTodayReport()
  ├─ 成功 → bridgeReport()
  │         → upsertReport()     ← 存入 IndexedDB
  │         → renderReport()     ← 顯示
  │         → 顯示「🤖 今日館報已自動載入」
  │
  └─ 失敗 → (靜默，不影響使用)
            → 使用者可手動貼文字或匯入 JSON
```

**新增函式：**

```javascript
async function checkAutoReport() {
  const report = await fetchTodayReport();
  if (!report) return;

  // 檢查 IndexedDB 是否已有同日自動報告
  const existing = state.history.find(h =>
    h.tags?.includes(report.date) && h.source === 'akasha-rss-news'
  );

  if (existing) {
    // 已有 → 比較 generated_at，如果 fetch 的比較新才覆寫
    try {
      const stored = JSON.parse(existing.content);
      if (stored._generated_at >= report._generated_at) return;
    } catch {}
  }

  await upsertReport(report);
  state.currentReport = report;
  renderReport(report);
  showToast('🤖 今日館報已自動載入');
  await loadHistory();
}
```

---

## 10. UI 變更一覽

### 10.1 Phase 1（MVP 整合，隨 akasha-rss-news Phase 4 同步）

| 變更 | 位置 | 說明 |
|------|------|------|
| 自動載入 | init 區塊 | 頁面開啟時 fetch 今日報告 |
| 「匯入 JSON」按鈕 | input-actions | `<input type="file" accept=".json">` |
| 來源標記 | report-header | 「🤖 自動」 vs 「✍️ 手動」 |
| rss-bridge.js 引入 | `<script>` 或 ES module | 格式轉換邏輯 |

### 10.2 Phase 2（UI 增強，Post-MVP）

| 變更 | 位置 | 說明 |
|------|------|------|
| 信心度徽章 | report-item | 🟢 high / 🟡 medium / 🔴 low |
| 來源數量 | report-item-source | 「3 個來源」+展開列表 |
| 台灣焦點 | report-item | 🇹🇼 標記 + 原因 tooltip |
| claim trace 展開 | report-item | 可展開查看每個聲明的來源對應 |
| 統計摘要 | report-header | 「抓取 461 篇 → 選入 12 則」 |

### 10.3 Phase 3（發文面板，Post-MVP 優先級 4）

| 變更 | 位置 | 說明 |
|------|------|------|
| 𝕏 草稿 tab | report-panel 頂部 | 顯示 X 版文字 + 複製按鈕 |
| Threads 草稿 tab | report-panel 頂部 | 顯示 Threads 版文字 + 複製按鈕 |
| 一鍵複製全部 | 面板底部 | 複製完整 thread 到剪貼簿 |

---

## 11. 跨專案檔案對照

```
akasha-rss-news 產出              用途                    akasha-library 消費方式
─────────────────────────────────────────────────────────────────────────────
output/daily_YYYYMMDD.json    主館報 JSON               fetch → bridge → render
output/daily_YYYYMMDD.md      人類可讀 Markdown          匯出下載（不進 PWA 渲染）
output/voice_YYYYMMDD.txt     純文字朗讀稿              朗讀專案使用（不進 PWA）
output/platforms/x_*.json     X 草稿                    (Post-MVP) 發文面板
output/platforms/threads_*.json  Threads 草稿            (Post-MVP) 發文面板
output/logs/run_*.json        執行日誌                  不進 PWA（開發除錯用）
```

---

## 12. PostMessage 協議擴充

現有 PostMessage types（akasha-library app shell 已支援）：

| type | 方向 | 用途 |
|------|------|------|
| `akasha-report-generate` | iframe → parent | 請 AI 整理文字 |
| `akasha-report-response` | parent → iframe | AI 整理結果 |
| `akasha-voice-play-report` | iframe → parent | 朗讀報告 |
| `akasha-voice-pause/resume/stop` | iframe → parent | 語音控制 |
| `akasha-reading-room-memory` | iframe → parent | IndexedDB 操作 |

**新增 PostMessage type：無。**

朗讀由獨立專案處理（§5），不需要新的 PostMessage type。
所有功能（儲存、匯出、歷史、fetch）全部沿用現有協議。

---

## 13. 安全考量

### 13.1 fetch 安全

- GitHub Pages 是 HTTPS，PWA 也是 HTTPS → 無 mixed content 問題
- CORS：GitHub Pages 預設允許跨域 fetch
- 驗證：fetch 後要驗證 JSON 結構（`isRssReport()`），拒絕不明格式

### 13.2 content 安全

- akasha-rss-news 的 output 已經過 validators.py 的 banned_phrases lint
- voice_text 已保證不含 URL、emoji、Markdown link
- bridge 層不做 innerHTML，akasha-library 的 renderReport() 已用 escapeHtml()

### 13.3 離線模式

- IndexedDB 存了歷史報告（保留 15 年）→ 離線時仍可閱讀
- fetch 失敗 → 靜默降級為手動模式
- 不強制要求連線

---

## 14. 實作順序

```
                     akasha-rss-news                akasha-library
                     ═══════════════                ══════════════

Phase 3 (現在做)     claude_rewrite.py              (不動)
                     claim_trace.py
                     validators.py

Phase 4              formatter.py                   (不動)
                     → 產出 6 種檔案

Phase 4.5 (整合)     (不動)                          ① rss-bridge.js
                                                    ② index.html 改動
                                                    ③ fetch + import
                                                    ④ 測試

Phase 5              Routine 設定                    (不動)
                     → 每天自動 push output/

Post-MVP             (不動)                          信心度 / TW 焦點 / 發文面板
```

**Phase 4.5 預計工時：**

| 工項 | 預估時間 | 說明 |
|------|---------|------|
| rss-bridge.js | 1h | 純函式，好寫好測 |
| index.html 修改 | 2h | fetch + import UI + 來源標記 |
| 測試驗證 | 1h | 用 Phase 4 的 golden test JSON 測 |
| **合計** | **4h** | |

---

## 15. 開放問題（已決定 2026-05-19）

| # | 問題 | 決定 | 備註 |
|---|------|------|------|
| 1 | GitHub Pages 是否要公開 output/ | **延後** | 等 Phase 4 做完再看 |
| 2 | 自動載入頻率 | **頁面開啟時** | 每天一份報告，不需輪詢 |
| 3 | 手動模式保留程度 | **保留** | 完整手動流程作為 fallback |
| 4 | 歷史報告保留天數 | **15 年** | 比照圖書館典藏精神，不設自動清理 |
| 5 | 朗讀機制 | **另案處理** | 朗讀由獨立專案負責，本設計不實作 TTS 播放 |

> 決策記錄於 `DECISIONS.md`（2026-05-19）

---

## 16. 驗收條件

### MVP 整合驗收（Phase 4.5）

- [ ] `fetchTodayReport()` 能抓到今日 JSON（傳輸方式待 Phase 4 後決定）
- [ ] `bridgeReport()` 轉換後，renderReport() 正常顯示
- [ ] bridge 後的 JSON 保留 `_voice_text` 欄位供朗讀專案使用
- [ ] 「儲存」到 IndexedDB 成功，歷史列表有新條目
- [ ] 歷史報告無 TTL（保留 15 年）
- [ ] 「匯出 MD」和「匯出 JSON」正常下載
- [ ] 手動模式仍然可用（貼文字 → AI 整理 → 顯示）
- [ ] 同日重跑：第二次 fetch 覆寫 IndexedDB 中的同日報告
- [ ] fetch 失敗時靜默降級，不影響手動模式
- [ ] 離線時可從 IndexedDB 讀取已存報告

---

## 附錄 A：完整 bridgeReport 範例

**輸入（akasha-rss-news output，截取）：**

```json
{
  "reportId": "daily_20260519",
  "date": "2026-05-19",
  "timezone": "Asia/Taipei",
  "generated_at": "2026-05-19T05:12:34+08:00",
  "status": "ok",
  "warnings": [],
  "sections": [
    {
      "beat": "INTL",
      "title": "國際脈動",
      "emoji": "🌍",
      "items": [
        {
          "event_id": "daily_20260519_evt_001",
          "headline": "俄烏停火協議第三輪談判在日內瓦破裂",
          "context": "俄羅斯與烏克蘭在日內瓦舉行的第三輪停火談判宣告破裂...",
          "beat": "INTL",
          "voice_text": "俄烏第三輪停火談判在日內瓦宣告破裂，雙方在領土讓步問題上分歧持續擴大。",
          "sources": [
            {
              "source_id": "bbc_world",
              "publisher": "BBC News",
              "title": "Russia-Ukraine Geneva talks collapse",
              "url": "https://www.bbc.com/news/...",
              "published_at": "2026-05-18T22:30:00Z"
            }
          ],
          "source_count": 1,
          "confidence": "high",
          "single_source_warning": true,
          "claim_trace": [{"claim": "...", "source_id": "bbc_world", "source_url": "...", "support_type": "direct"}],
          "tw_highlight": false,
          "selection_score": 8.2,
          "platform_outputs": {
            "x": {"max_chars": 280, "posts": ["🌍 俄烏停火第三輪談判破裂..."]},
            "threads": {"max_chars": 500, "posts": ["俄烏停火協議第三輪談判..."]},
            "voice": {"text": "俄烏第三輪停火談判在日內瓦宣告破裂..."}
          }
        }
      ]
    }
  ],
  "stats": {
    "total_feeds_checked": 26,
    "total_feeds_failed": 0,
    "total_articles_fetched": 461,
    "total_articles_after_filter": 389,
    "total_events_merged": 127,
    "total_events_selected": 12,
    "tw_highlights_count": 2
  }
}
```

**輸出（bridge 後，akasha-library 可直接使用）：**

```json
{
  "reportId": "daily_20260519",
  "date": "2026-05-19",
  "sections": [
    {
      "title": "🌍 國際脈動",
      "items": [
        {
          "title": "俄烏停火協議第三輪談判在日內瓦破裂",
          "summary": "俄羅斯與烏克蘭在日內瓦舉行的第三輪停火談判宣告破裂...",
          "source": "BBC News",
          "url": "https://www.bbc.com/news/...",
          "_event_id": "daily_20260519_evt_001",
          "_beat": "INTL",
          "_confidence": "high",
          "_source_count": 1,
          "_tw_highlight": false,
          "_voice_text": "俄烏第三輪停火談判在日內瓦宣告破裂，雙方在領土讓步問題上分歧持續擴大。",
          "_claim_trace": [{"claim": "...", "source_id": "bbc_world", "source_url": "...", "support_type": "direct"}],
          "_selection_score": 8.2,
          "_all_sources": [{"source_id": "bbc_world", "publisher": "BBC News", "...": "..."}],
          "_platform_outputs": {"x": {"...": "..."}, "threads": {"...": "..."}, "voice": {"...": "..."}},
          "_single_source_warning": true,
          "_opinion_level": null
        }
      ],
      "_beat": "INTL",
      "_emoji": "🌍"
    }
  ],
  "_generated_at": "2026-05-19T05:12:34+08:00",
  "_status": "ok",
  "_warnings": [],
  "_stats": {"total_feeds_checked": 26, "...": "..."},
  "_source": "akasha-rss-news"
}
```

akasha-library 的 `renderReport()` 只會讀到 `title`, `summary`, `source`, `url`，所有 `_` 前綴欄位被安全忽略。未來 UI 升級時，逐步啟用這些欄位即可。
