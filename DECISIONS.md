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

---

## 2026-05-21 | 可信度分級修訂 — 取消單一 Tier 3 自動標低

### Decision

`derive_confidence()` 不再把單一 Tier 3 來源自動標為 "low"。所有單一來源事件一律 "medium"。

### Reason

月月 2026-05-21 review 首日館報時指出：ArchDaily 報建築是領域權威，不該標 🔴 低可信度。原規格 §9.2 的「單一 Tier 3 = low」對專業媒體報導自身領域過於嚴苛。語氣保留機制已有 `single_source_warning` 覆蓋。

### Impact

- 單一 Tier 3 來源事件的 confidence 從 "low" 改為 "medium"
- Markdown 顯示從 🔴 低 改為 🟡 中
- `single_source_warning` 仍維持，Claude 改寫時仍會用保留語氣

---

## 2026-05-21 | 事件聚合門檻提高 — shared_kw_min 3→5 + 停用詞

### Decision

共同關鍵詞門檻從 3 提高到 5，並新增 30 個新聞通用停用詞。

### Reason

首日館報的 ECON 區塊把三件不相關事件合併（波音訂單 + 歐美貿易 + 三星罷工），因為 trade, deal, summit 等通用詞觸發 transitive chain。

### Impact

- 同 beat 內的事件合併更嚴格，需要 5 個非通用共同詞才會合
- 標題高相似度（≥ 88%）的跨源合併不受影響
- `config/selection_score.yaml` 同步更新

---

## 2026-05-21 | 朗讀稿來源格式 — 開場一次 + 底部彙整

### Decision

「讓圖書館員翻譯給你聽」只在開場白出現一次。改寫 prompt 告知 Claude voice_text 不加尾部來源。所有參考連結集中在 voice / markdown 底部。

### Reason

月月 2026-05-21 review 指出每則重複唸來源太冗，且貼推特時沒有方便的連結區塊。

### Impact

- voice.txt 開場：「以下是今日的紀錄檔案，讓圖書館員翻譯給你聽。」
- voice.txt / markdown 底部新增「參考來源」區塊，URL 集中一處
- 貼推特時可在留言區一次貼連結
- `rewrite_prompt.md` 更新，Claude 不再在 voice_text 結尾加來源行

---

## 2026-05-22 | 同 beat 關鍵詞匹配加標題相似度門檻

### Decision

關鍵詞匹配分支（弱信號）新增 `title_sim ≥ 50%` 門檻。同 beat 內的文章必須標題也有中度相似度，才能透過共同關鍵詞合併。

### Reason

月月 2026-05-22 review 指出 ARTS beat 內兩篇完全不同的建築文章（圍牆住宅 vs 木門文章）因共享領域關鍵詞（architecture, residential, courtyard, design）被合併。同領域不同報導共享領域詞彙是正常現象，不代表是同一事件。

### Impact

- 關鍵詞合併三重條件：同 beat + title_sim ≥ 50% + shared_kw ≥ 5
- 標題高相似度（≥ 88%）的跨源合併不受影響
- canonical URL 完全相同的合併不受影響
- 同領域（ARTS 建築、ECON 金融）的不相關文章不再被黏在一起

---

## 2026-05-22 | 數字翻譯規則 — k/M/B → 萬/億

### Decision

rewrite_prompt.md 新增「⛔ 數字格式規則」，要求 Claude 將英文數字縮寫（k/M/B）轉換為中文萬/億單位。

### Reason

月月 2026-05-22 review 指出「26千磅」是 £26k 的直譯，中文應寫「2.6 萬英鎊」。

### Impact

- 新增換算表 + 規則 + checklist 項目
- Sonnet 改寫時必須做數字單位轉換，不得直譯英文 k/M/B

---

## 2026-06-11 | X 貼文「280 字」計數語義 — 維持 code-point

### Decision

P0「X 每則 ≤ 280 字」維持 Python code-point 計數（producer split_posts、schema maxLength、verify_output 守門三者現狀一致）。**不**改用 X 平台的加權計數（CJK=2）。

### Reason

2026-06-11 全量健檢終驗發現：生產 X 草稿以 code-point 計全數合規（150–234），但以 X 平台加權規則計有 14/18 則達 269–372 單位，直接貼出會被拒。三個選項（加權自動切串文 / prompt 要求縮短 / 維持現狀）由月月決策：**維持現狀**，貼文時人工刪減。

### Impact

- 守門腳本 scripts/verify_output.py 維持 code-point 計數，X 加權超長**不視為缺陷**
- 未來審查不應將「加權計數超長」列為 P0 違規（本決策明文豁免）
- 若日後要自動發文（Post-MVP 優先級 4），此決策必須重新評估
