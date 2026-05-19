# Roadmap

對應規格：[akashic-daily-report-final-spec-v1.1.md](akashic-daily-report-final-spec-v1.1.md)

---

## 北極星

每天早上 05:00（Asia/Taipei），系統自動產出當日館報六種輸出：

```
output/daily_YYYYMMDD.json
output/daily_YYYYMMDD.md
output/voice_YYYYMMDD.txt
output/platforms/x_YYYYMMDD.json
output/platforms/threads_YYYYMMDD.json
output/logs/run_YYYYMMDD.json
```

並滿足：能抓 → 能分類 → 能去重 → 能合併 → 能選題 → 能改寫 → 能追來源 → 能輸出 → 能驗證 → 能在來源失敗時留下可讀錯誤。

---

## Phase 0 | Spec Freeze 與專案骨架

把規格翻譯成可被程式引用的設定檔與 Schema。

- [x] 建立專案骨架
- [x] 初始化 Git
- [x] 建立 GitHub repo（https://github.com/TsKR2828/akasha-rss-news）
- [x] `config/feeds.yaml`（規格 §3.1 全部 29 個 source）
- [x] `config/beats.yaml`（規格 §2.1、§6.1）
- [x] `config/selection_score.yaml`（規格 §8.2）
- [x] `config/style_guide.md`（規格 §13）
- [x] `schemas/report.schema.json`
- [x] `schemas/article.schema.json`
- [x] `schemas/event.schema.json`
- [x] `schemas/platform_output.schema.json`
- [x] `prompts/rewrite_prompt.md`（含規格 §10.1 injection 防護）
- [x] `prompts/routine_prompt.md`
- [x] `tests/test_schemas.py`（37 條測試，全綠）

**驗收：** ✅ Schema 自我驗證通過、✅ 每個 source 有穩定 `source_id`、✅ prompt 明列 Claude 可做/不可做。

**Phase 0 狀態：** ✅ 全數完成（含 GitHub remote `TsKR2828/akasha-rss-news`、branch: main）。可進 Phase 1。

---

## Phase 1 | RSS 抓取與正規化

任何單一來源掛掉，不能讓今天的館報整個失敗。

- [ ] `src/fetch_rss.py`（讀 feeds.yaml、併發抓取、記錄 feed health）
- [ ] `src/normalize.py`（RSS → normalized article，規格 §5.3）
- [ ] `data/raw/YYYY-MM-DD/` 保留原始 XML
- [ ] `data/articles/` 輸出正規化 JSON
- [ ] feed health log（規格 §4.3）
- [ ] timeout 10s + 2 retries + exponential backoff
- [ ] 時間窗口：`report_date 05:00 - 24h - 3h grace`
- [ ] `tests/test_fetch_rss.py`

**驗收：**
- 單一 source 失敗 → `continue_with_warning`，`warnings[]` 有條目
- 全部 source 失敗 → `abort_report`，**不產出假成功報告**
- 連續失敗 3 次的 source 觸發告警
- `article_id = sha256(source_id + canonical_url)` 重跑得到相同 ID

---

## Phase 2 | 分類、去重、事件聚合

一篇文章能走到「被選或被丟」並完整寫進 events JSON。

- [ ] `src/classifier.py`（Beat 分類，規格 §6.1）
- [ ] `src/tw_highlight.py`（Taiwan Highlight 偵測，規格 §6.3）
- [ ] `src/dedup.py`（文章去重）
- [ ] `src/event_cluster.py`（同事件聚合，規格 §7）
- [ ] `src/selector.py`（selection_score 計算與選題，規格 §8）
- [ ] `data/events/` 事件 JSON 輸出
- [ ] `tests/test_classifier.py`, `test_dedup.py`, `test_selector.py`

**驗收：**
- 分類權重：source 0.6 + keyword 0.3 + entity 0.1，min_score 0.45
- AI beat 例外（The Verge / BBC Tech / Ars Technica 需二次過濾）
- TW_HIGHLIGHT 必有 `tw_highlight_reason` 與 `tw_highlight_keywords`
- MVP 不用 embedding：標題正規化相似度 0.88 + 共同關鍵詞 ≥ 3 + 共同實體 ≥ 2
- 每個 beat 符合 `daily_limits` min/max
- 未選入事件記錄 `drop_reason`

---

## Phase 3 | Claude 改寫與事實安全

每一句改寫的內容都能回溯到原始來源。

- [ ] `prompts/rewrite_prompt.md` 正式版（含 injection 防護）
- [ ] `src/claude_rewrite.py`
- [ ] `src/claim_trace.py`（驗證 claim 對應 source）
- [ ] `src/validators.py`（banned_phrases lint、confidence 標記）
- [ ] RSS 進入模型前清理 HTML / script / 追蹤參數

**驗收：**
- Claude 不會新增來源沒提到的數字、動機、責任歸屬
- 每個 selected item 至少 1 條 `claim_trace`
- `source_count = 1` 時自動標記 `single_source_warning: true`
- `confidence` 三級分類正確（high / medium / low）
- `opinion_level` 三級分類正確
- banned_phrases lint 抓到「據悉、引發關注、值得一提的是」等八股

---

## Phase 4 | 多格式輸出與驗證

五種輸出檔同時產出，全部通過 schema 與 lint。

- [ ] `src/formatter.py`（Markdown / Voice / X / Threads）
- [ ] `output/daily_YYYYMMDD.json` 主館報
- [ ] `output/daily_YYYYMMDD.md` 人類可讀版
- [ ] `output/voice_YYYYMMDD.txt` 朗讀稿
- [ ] `output/platforms/x_YYYYMMDD.json` X 草稿
- [ ] `output/platforms/threads_YYYYMMDD.json` Threads 草稿
- [ ] `output/logs/run_YYYYMMDD.json` run log
- [ ] `tests/golden/sample_report.{json,md,voice.txt}`
- [ ] `tests/test_formatter.py`, `test_report_schema.py`

**驗收（P0）：**
- 所有 JSON 通過對應 schema
- `voice_text` 不含 `http://`, `https://`, `🧵`, `📌`, `📎`, `1/N`, `[text](url)`
- X 每則 ≤ 280 字、Threads 每則 ≤ 500 字
- 朗讀版**重新生成**，不是拿 X 版刪 emoji
- Markdown 在 ≥ 3 個 beat 有內容時排版正常

---

## Phase 5 | Routine 與半自動工作流

Claude Code Routine 連跑 7 天無人工介入。

- [ ] `prompts/routine_prompt.md` 正式版
- [ ] Claude Code Routine 設定（每日 05:00 Asia/Taipei）
- [ ] 通知管道（Telegram / Discord / Email 擇一）
- [ ] 同日重跑 idempotent 測試
- [ ] 連跑 7 天穩定性測試

**驗收：**
- 相同 `report_id` 覆寫檔案、通知只發一次
- run log 完整記錄每個 step 的 duration 與 status
- 連跑 7 天無人工介入仍可產出可讀報告

---

## Post-MVP

待 MVP 連跑 7 天穩定後啟動，優先順序待月月決定。

### 優先級 1（讓館報變好聽 / 變好看）

- [ ] 零韻 TTS 朗讀自動生成
- [ ] TsukiSynth BGM 自動配樂
- [ ] 歷史館報書庫頁 Web UI

### 優先級 2（讓內容變深）

- [ ] 週報 / 月報自動彙整
- [ ] 台灣故事庫擴展（從 `src/tw_stories.json` 升格為獨立來源）
- [ ] 國家文化記憶庫 API 接入

### 優先級 3（讓下午報半自動）

- [ ] Grok 下午追蹤報半自動化（規格 §15）
- [ ] afternoon_update 併入同日 report

### 優先級 4（讓發布變自動）

- [ ] Threads API 發布（需 Meta app 審核）
- [ ] X API 發布（需重查 Developer Console 報價）
- [ ] Discord / Telegram bot 查詢館報
- [ ] Akasha Library App Shell 內建館報面板

> ⚠️ 自動發文評估項：每日平均貼文數、是否含 URL、排程需求、回覆讀取、API 成本、App 審核成本、帳號風險。

---

## 砍範圍時的保留順序（規格 §24）

資源有限時按這個順序保留：

1. feed health
2. normalized articles
3. event clustering
4. selection score
5. claim trace
6. schema validation
7. voice / platform formatter
8. idempotent rerun

這些是「每天自動跑不壞」的骨架。文風、BGM、TTS、Web UI 都可以等資料流穩定後再接。
