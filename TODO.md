# TODO

最新更新：2026-05-20
目前階段：Phase 5 進行中（pipeline + routine prompt 完成）

整體規劃見 [ROADMAP.md](ROADMAP.md)。本檔案只列「現在做」與「下一個做」。

---

## Done — Phase 0 ✅

- [x] `config/feeds.yaml`（31 sources，26 enabled）
- [x] `config/beats.yaml`（4 大 beat 關鍵字 + entity 設定 + TW Highlight）
- [x] `config/selection_score.yaml`
- [x] `config/style_guide.md`
- [x] 4 個 JSON Schema（article / event / platform_output / report）
- [x] 2 個 Prompt（rewrite_prompt / routine_prompt）
- [x] `requirements.txt`（含 spaCy）
- [x] `tests/test_schemas.py`（37 條）
- [x] GitHub remote（https://github.com/TsKR2828/akasha-rss-news, branch: main）

## Done — Phase 1 ✅

- [x] `src/fetch_rss.py` — concurrent fetch + timeout/retry/backoff + consecutive_failures state
- [x] `src/normalize.py` — feedparser + canonicalize_url + sha256 article_id + fetch window
- [x] `tests/test_fetch_rss.py`（12 條）+ `tests/test_normalize.py`（20 條）
- [x] 實機驗證：BBC World 抓 32/36 articles，schema 全過

## Done — Phase 2 ✅

- [x] `src/classifier.py` — Beat 分類（source 0.6 + keyword 0.3 + entity 0.1）+ AI 例外
- [x] `src/entity_recognizer.py` — spaCy NER 封裝（extract_entities + entity_match_score）
- [x] `src/tw_highlight.py` — positive + context + FP review
- [x] `src/dedup.py` — canonical_url + 同源相似標題（rapidfuzz ≥0.92）
- [x] `src/event_cluster.py` — 24h 窗口 + 標題 0.88 + 共同關鍵詞 ≥ 3
- [x] `src/selector.py` — selection_score + daily_limits + drop_reason + same_topic 罰分
- [x] `tests/test_classifier.py`(20) + `test_entity_recognizer.py`(19) + `test_tw_highlight.py`(10) + `test_dedup.py`(9) + `test_event_cluster.py`(16) + `test_selector.py`(13) — 87 條全綠
- [x] Feed sweep 全 28 sources → 關 4 死源（the_verge / venturebeat / ap_rsshub / bloomberg_proxy）
- [x] 新增 2 AI 來源（techcrunch_ai / wired_ai）
- [x] 實機驗證：26 sources → 461 articles → pipeline end-to-end 跑通

**測試合計：156 條全綠（37 schema + 32 Phase 1 + 87 Phase 2）**

## Done — Phase 3 ✅

- [x] `src/html_cleaner.py` — strip HTML / script / style + 追蹤參數清理 + entity decode
- [x] `src/claude_rewrite.py` — Anthropic SDK 呼叫 + retry + JSON parse + merge + dry-run
- [x] `src/claim_trace.py` — verify + fix + fallback claim + single_source_warning
- [x] `src/validators.py` — banned_phrases(8) + voice_text lint(6 patterns) + confidence / opinion_level / claim_trace / platform lengths
- [x] `tests/test_html_cleaner.py`(18) + `test_validators.py`(27) + `test_claim_trace.py`(19) + `test_claude_rewrite.py`(16) — 80 條全綠（mocked SDK）
- [x] `docs/INTEGRATION_DESIGN.md` — akasha-rss-news ↔ akasha-library 整合設計稿

**測試合計：250 條全綠（37 schema + 32 Phase 1 + 87 Phase 2 + 80 Phase 3 + 14 entity）**

## Done — Phase 4 ✅

- [x] `src/formatter.py` — 多格式輸出（JSON / Markdown / Voice / X / Threads + run log）
- [x] `tests/test_formatter.py`(56) — split_posts / platform_output / report / markdown / voice / drafts / validation / integration
- [x] 驗收：voice_text lint + X ≤280 + Threads ≤500 + 朗讀版獨立生成 + Markdown 多 beat 排版

**測試合計：306 條全綠（37 schema + 32 Phase 1 + 87 Phase 2 + 80 Phase 3 + 14 entity + 56 Phase 4）**

---

## Now — Phase 5 進行中

Routine 自動化 + 7 天穩定性。

- [x] 寫 `src/pipeline.py`（串接 Phase 1–4 所有模組的 main 入口）+ 19 條測試
- [x] 更新 `prompts/routine_prompt.md` 為正式版（指令：`python -m src.pipeline`）
- [x] Claude Code Routine 設定（每日 05:00 Asia/Taipei → `0 21 * * *` UTC，ID: trig_01YZgdnxrvUsTLDh6YQKaDY4）
- [ ] 通知管道設定（月月決定先不做，之後再加）
- [ ] 同日重跑 idempotent 測試（同一 reportId 覆寫）
- [ ] 連跑 7 天穩定性測試

---

## 待確認的決策

下列項目規格沒寫死，需要月月決定後寫入 [DECISIONS.md](DECISIONS.md)：

- [ ] Routine 通知管道：Telegram、Discord、Email 三選一？
- [x] RSSHub 用公共實例還是自架？→ **公共實例已確認 403，需自架**（2026-05-19 sweep）
- [ ] Google News proxy 失效時的 fallback 策略（Reuters proxy 目前正常但規格警告 unstable）
- [ ] `tw_stories.json` 初始故事數量（5? 30? 100?）
- [ ] Phase 0 各設定檔由誰人工填，由誰機器產

---

## 不在這份 TODO 裡

以下屬於 Post-MVP，等 MVP 連跑 7 天穩定再回來看：

- 零韻 TTS、TsukiSynth BGM、Web UI、週/月報、Threads/X API 自動發文、Grok 追蹤報自動化

詳見 [ROADMAP.md](ROADMAP.md) 的 Post-MVP 區段。
