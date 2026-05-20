# Decisions

## 2026-05-19 | Initial Scaffold

### Decision

使用固定 AI 協作骨架初始化專案。

### Reason

讓後續人類與 AI 都能快速理解專案狀態、入口文件與工作規則。

### Impact

專案會維護 `README.md`、`ROADMAP.md`、`DEV_LOG.md`、`AI_CONTEXT.md` 與 `PROJECT_MANIFEST.json`。

---

## 2026-05-19 | 整合設計稿 — 開放問題決策

對應文件：`docs/INTEGRATION_DESIGN.md` §15

### Decision 1 — GitHub Pages 公開性

**延後決定。** 等 Phase 4 formatter 完成、output/ 實際產出後再評估。

### Decision 2 — 自動載入頻率

**頁面開啟時 fetch 一次。** 每天只有一份報告，不需輪詢或 Service Worker。

### Decision 3 — 手動模式

**保留。** 手動貼文字 → AI 整理的流程不刪，作為自動系統故障時的 fallback。

### Decision 4 — 歷史報告保留天數

**15 年（5,475 天）。** 比照圖書館的典藏精神，IndexedDB 容量足夠。不設自動清理。

### Decision 5 — 朗讀機制

**另案處理。** 朗讀由獨立專案負責，本整合設計不涉入語音合成細節。akasha-rss-news 仍產出 `voice_text` 欄位供朗讀專案使用，但 PWA 端不實作 TTS 播放按鈕。

### Reason

月月 2026-05-19 口頭指示。

### Impact

- 設計稿 §5（語音整合）降級為「提供資料供外部朗讀專案使用」，不做 PWA 內朗讀
- 設計稿 §12 的 `akasha-voice-play-tasks` PostMessage type 不需實作
- IndexedDB 不設 TTL，長期保留所有歷史館報
- GitHub Pages 決策留到 Phase 4 後再談

---

## 2026-05-20 | Routine 架構 — 遠端 agent 自行改寫

### Decision

Claude Code Routine 使用遠端 Sonnet agent，Step 8（改寫）由 agent 自己完成，不透過 Anthropic Python SDK 呼叫 API。

### Reason

遠端 Routine agent 跑在 Anthropic 雲端，無法存取本機環境變數（ANTHROPIC_API_KEY）。但 agent 本身就是 Claude，可以直接讀取 `prompts/rewrite_prompt.md` 並依照規則改寫事件。

### Impact

- 不需要在遠端環境設定 ANTHROPIC_API_KEY
- Step 8 的改寫品質取決於 Sonnet 模型能力（vs 本機 pipeline 用的是 SDK 呼叫，可指定任意模型）
- `src/pipeline.py` 和 `src/claude_rewrite.py` 仍保留完整的本機 SDK 呼叫路徑，供本機手動執行使用
- Routine 產出 push 到 `daily-reports` branch（不汙染 main）
- 通知管道先不設定，之後再加

---

## 2026-05-20 | 通知管道延後

### Decision

Phase 5 先不設定通知管道，後續再加。

### Reason

月月 2026-05-20 決定。先確保 pipeline + routine 穩定運行，通知是錦上添花。

### Impact

- Routine 完成後不會主動推送通知，需要手動到 GitHub 或 claude.ai/code/routines 查看結果
- 之後可選 Telegram / Discord / Email 任一管道
