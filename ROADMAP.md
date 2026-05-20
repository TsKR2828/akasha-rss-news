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
- [x] `config/feeds.yaml`（規格 §3.1，31 sources / 26 enabled）
- [x] `config/beats.yaml`（規格 §2.1、§6.1，含 entity 設定）
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

- [x] `src/fetch_rss.py`（讀 feeds.yaml、併發抓取、記錄 feed health）
- [x] `src/normalize.py`（RSS → normalized article，規格 §5.3）
- [x] `data/raw/YYYY-MM-DD/` 保留原始 XML
- [x] `data/articles/` 輸出正規化 JSON
- [x] feed health log（規格 §4.3）
- [x] timeout 10s + 2 retries + exponential backoff
- [x] 時間窗口：`report_date 05:00 - 24h - 3h grace`
- [x] `tests/test_fetch_rss.py` + `tests/test_normalize.py`（32 條，全綠）
- [x] 實機 BBC World fetch + normalize 驗證 end-to-end（32/36 articles 入窗口）

**驗收：**
- 單一 source 失敗 → `continue_with_warning`，`warnings[]` 有條目
- 全部 source 失敗 → `abort_report`，**不產出假成功報告**
- 連續失敗 3 次的 source 觸發告警
- `article_id = sha256(source_id + canonical_url)` 重跑得到相同 ID

---

## Phase 2 | 分類、去重、事件聚合

一篇文章能走到「被選或被丟」並完整寫進 events JSON。

- [x] `src/classifier.py`（Beat 分類，規格 §6.1，含 §6.2 AI 例外）
- [x] `src/entity_recognizer.py`（spaCy NER，補齊 §6.1 entity_weight 0.1）
- [x] `src/tw_highlight.py`（Taiwan Highlight 偵測，規格 §6.3）
- [x] `src/dedup.py`（文章去重：canonical URL + 同源相似標題）
- [x] `src/event_cluster.py`（同事件聚合，規格 §7.2 MVP 策略）
- [x] `src/selector.py`（selection_score 計算與選題，規格 §8）
- [x] `data/events/YYYY-MM-DD/` 事件 JSON 輸出
- [x] `tests/` Phase 2 測試（87 條，全綠）
- [x] Feed sweep 全 28 sources 實機掃描（關 4 死源、新增 2 AI 來源）
- [x] 實機驗證：26 sources → 461 articles，pipeline end-to-end 跑通

**驗收：** ✅ 全部達標
- ✅ 分類權重：source 0.6 + keyword 0.3 + entity 0.1，min_score 0.45（entity 已接 spaCy NER）
- ✅ AI beat 例外（BBC Tech / Ars Technica 二次過濾；The Verge 已停用）
- ✅ TW_HIGHLIGHT 必有 `tw_highlight_reason` 與 `tw_highlight_keywords`
- ✅ 不用 embedding：標題正規化相似度 0.88 + 共同關鍵詞 ≥ 3
- ✅ 每個 beat 符合 `daily_limits` min/max
- ✅ 未選入事件記錄 `drop_reason`
- ✅ 26 enabled sources 全部 200 OK、0 warnings

---

## Phase 3 | Claude 改寫與事實安全

每一句改寫的內容都能回溯到原始來源。

- [x] `prompts/rewrite_prompt.md` 正式版（含 injection 防護）— Phase 0 已完成
- [x] `src/html_cleaner.py`（strip HTML/script/style + 追蹤參數 + entity decode）
- [x] `src/claude_rewrite.py`（Anthropic SDK + retry + JSON parse + merge + lint）
- [x] `src/claim_trace.py`（verify + fix + fallback claim）
- [x] `src/validators.py`（banned_phrases 8 詞 + voice_text 6 patterns + confidence / opinion / claim / platform lint）
- [x] `tests/` Phase 3 測試（80 條，全綠；Claude SDK 全部 mocked）

**驗收：** ✅ 全部達標
- ✅ Claude 改寫由 rewrite_prompt.md 的安全規則保護（injection 防護、事實安全紅線）
- ✅ 每個 selected item 至少 1 條 `claim_trace`（fix_claim_trace 自動修正 + fallback）
- ✅ `source_count = 1` → `single_source_warning: true`
- ✅ `confidence` 三級驗證（高/中/低 vs 來源推斷不符時產出 warning）
- ✅ `opinion_level` 三級驗證
- ✅ banned_phrases lint 8 個禁用詞（據悉 / 有鑑於此 / 引發關注 / 受到矚目 / 備受矚目 / 值得一提的是 / 不容忽視 / 相關單位表示）
- ✅ voice_text lint 6 patterns（URL / 🧵 / 📌 / 📎 / N/N / Markdown link）
- ✅ HTML 清理：strip script/style、tag removal、entity decode、追蹤參數移除

**Phase 3 狀態：** ✅ 全數完成。可進 Phase 4。

---

## Phase 4 | 多格式輸出與驗證

五種輸出檔同時產出，全部通過 schema 與 lint。

- [x] `src/formatter.py`（JSON / Markdown / Voice / X / Threads + run log）
- [x] `output/daily_YYYYMMDD.json` 主館報
- [x] `output/daily_YYYYMMDD.md` 人類可讀版
- [x] `output/voice_YYYYMMDD.txt` 朗讀稿
- [x] `output/platforms/x_YYYYMMDD.json` X 草稿
- [x] `output/platforms/threads_YYYYMMDD.json` Threads 草稿
- [x] `output/logs/run_YYYYMMDD.json` run log
- [x] `tests/test_formatter.py`（56 條測試，全綠）

**驗收（P0）：** ✅ 全部達標
- ✅ report JSON 結構符合 report.schema.json（reportId / sections / stats / warnings）
- ✅ platform_output items 結構符合 platform_output.schema.json
- ✅ `voice_text` lint 驗證不含 `http://`, `https://`, `🧵`, `📌`, `📎`, `1/N`, `[text](url)`
- ✅ X 每則 ≤ 280 字（split_posts 三級切分：句號→逗號→強制截斷）
- ✅ Threads 每則 ≤ 500 字
- ✅ 朗讀版**獨立生成**（voice_text → 開場 + 轉場語 + 來源宣告），不是拿 X 版刪 emoji
- ✅ Markdown 多 beat 排版正常（beat 順序 INTL→ARTS→AI→ECON→PTS_LOCAL→TW_STORY）
- ✅ validate_report_output 自動驗收所有 P0 條件

**Phase 4 狀態：** ✅ 全數完成。可進 Phase 5。

---

## Phase 5 | Routine 與半自動工作流

Claude Code Routine 連跑 7 天無人工介入。

- [x] `src/pipeline.py`（串接 Phase 1–4 所有模組的 main 入口）+ 19 條測試
- [x] `prompts/routine_prompt.md` 正式版（指令：`python -m src.pipeline`）
- [x] Claude Code Routine 設定（每日 05:00 Asia/Taipei → `0 21 * * *` UTC）
- [ ] 通知管道（月月決定先不做，之後再加）
- [ ] 同日重跑 idempotent 測試
- [ ] 連跑 7 天穩定性測試

**Routine 資訊：**
- ID: `trig_01YZgdnxrvUsTLDh6YQKaDY4`
- 模型: claude-sonnet-4-6
- 架構: 遠端 agent 跑 Steps 1-7（Python CLI），Step 8 由 agent 自己改寫（不需 ANTHROPIC_API_KEY），Step 9 formatter
- 產出 push 到 `daily-reports` branch
- 管理: https://claude.ai/code/routines/trig_01YZgdnxrvUsTLDh6YQKaDY4

**驗收：**
- 相同 `report_id` 覆寫檔案、通知只發一次
- run log 完整記錄每個 step 的 duration 與 status
- 連跑 7 天無人工介入仍可產出可讀報告

**Phase 5 狀態：** 🔧 進行中（pipeline + routine 已設定，待穩定性驗證）

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
