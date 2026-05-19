# TODO

最新更新：2026-05-19
目前階段：Phase 0（Spec Freeze）

整體規劃見 [ROADMAP.md](ROADMAP.md)。本檔案只列「現在做」與「下一個做」。

---

## Now — Phase 0 收尾

把規格書翻成程式碼吃得到的設定檔。完成後才開始寫 fetch_rss。

### 設定檔（規格 §3, §6, §8, §13）

- [x] `config/feeds.yaml` — 規格 §3.1 的 29 個 source 全部填入
- [x] `config/beats.yaml` — INTL / ARTS / AI / ECON 關鍵字（規格 §2.1）
- [x] `config/selection_score.yaml` — 規格 §8.2 的評分表
- [x] `config/style_guide.md` — 文風、禁用詞、區塊轉場語（規格 §13）

### JSON Schema（規格 §17）

- [x] `schemas/report.schema.json`
- [x] `schemas/article.schema.json`
- [x] `schemas/event.schema.json`
- [x] `schemas/platform_output.schema.json`
- [x] 寫 schema 自我驗證測試（`tests/test_schemas.py`，37 條，全綠）

### Prompt（規格 §9.1, §10.1）

- [x] `prompts/rewrite_prompt.md`
  - 明列 Claude 可做（翻譯、摘要、調整語氣、重組敘事）
  - 明列 Claude 不可做（補數字、補動機、補責任、評論變事實、單一來源說成多方）
  - 包含規格 §10.1 的 prompt injection 防護段落
- [x] `prompts/routine_prompt.md`（Routine 入口）

### 環境

- [x] `requirements.txt` 加入：feedparser, requests, beautifulsoup4, python-dateutil, pydantic, jsonschema, PyYAML, rapidfuzz, anthropic, pytest
- [x] 本機 `git init` + 首次 commit 完成
- [x] 建立 GitHub remote 並 push（origin: https://github.com/TsKR2828/akasha-rss-news, branch: main）

---

## Now — Phase 1 收尾 / Phase 2 起手

### Phase 1 完成（2026-05-19）

- [x] `src/fetch_rss.py` — concurrent fetch + timeout/retry/backoff + consecutive_failures state
- [x] `src/normalize.py` — feedparser + canonicalize_url + sha256 article_id + fetch window
- [x] `tests/test_fetch_rss.py`（12 條）+ `tests/test_normalize.py`（20 條）
- [x] 實機驗證：BBC World 抓 32/36 articles，schema 全過

### Phase 2 完成（2026-05-19）

- [x] `src/classifier.py` — Beat 分類 + AI 例外二次過濾
- [x] `src/tw_highlight.py` — positive + context + FP review
- [x] `src/dedup.py` — canonical_url + 同源相似標題（rapidfuzz）
- [x] `src/event_cluster.py` — 24h 窗口 + 標題 0.88 + 共同關鍵詞 ≥ 3
- [x] `src/selector.py` — selection_score + daily_limits + drop_reason + same_topic 罰分
- [x] `tests/test_classifier.py` (11) + `test_tw_highlight.py` (10) + `test_dedup.py` (9) + `test_event_cluster.py` (16) + `test_selector.py` (13) — 59 條全綠
- [x] events JSON 通過 `schemas/event.schema.json`（test_event_cluster::TestEventSchemaConformance）
- [x] 實機驗證：BBC 32 articles → 29 events → 5 selected（Trump-Taiwan 70 分排第一）

### Next — Phase 3 起手

Claude 改寫 + Claim trace + 文風 lint。

- [ ] `src/claude_rewrite.py` — 呼叫 Anthropic SDK，套用 `prompts/rewrite_prompt.md`
- [ ] `src/claim_trace.py` — 驗證每條 claim 對應某 source_id
- [ ] `src/validators.py` — banned_phrases lint + voice_text URL/emoji lint + confidence 標記
- [ ] HTML / script / 追蹤參數清理（送 Claude 之前）
- [ ] `tests/test_claude_rewrite.py`（mocked SDK） + `test_validators.py`
- [ ] 驗收：跑完一輪後，所有 selected event 的 `claim_trace` 都有 source 對應

---

## 待確認的決策

下列項目規格沒寫死，需要月月決定後寫入 [DECISIONS.md](DECISIONS.md)：

- [ ] Routine 通知管道：Telegram、Discord、Email 三選一？
- [ ] RSSHub 用公共實例還是自架？
- [ ] Google News proxy 失效時的 fallback 策略
- [ ] `tw_stories.json` 初始故事數量（5? 30? 100?）
- [ ] Phase 0 各設定檔由誰人工填，由誰機器產

---

## 不在這份 TODO 裡

以下屬於 Post-MVP，等 MVP 連跑 7 天穩定再回來看：

- 零韻 TTS、TsukiSynth BGM、Web UI、週/月報、Threads/X API 自動發文、Grok 追蹤報自動化

詳見 [ROADMAP.md](ROADMAP.md) 的 Post-MVP 區段。
