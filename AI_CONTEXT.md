# AI Context

## Project Name

akasha-rss-news — 阿卡夏圖書館・每日館報系統

## Goal

每天清晨 05:00（Asia/Taipei）自動產出一份可閱讀、可朗讀、可轉貼的每日館報。

從國際英文 RSS 與公視新聞抓取新聞，經分類、事件聚合、事實安全檢查、口語化改寫後，輸出六種檔案：

```
output/daily_YYYYMMDD.json        # 機器可讀主報告
output/daily_YYYYMMDD.md          # 人類可讀 Markdown
output/voice_YYYYMMDD.txt         # 朗讀稿（無 URL / emoji / Markdown）
output/platforms/x_YYYYMMDD.json  # X 貼文草稿（≤280 字/則）
output/platforms/threads_YYYYMMDD.json  # Threads 草稿（≤500 字/則）
output/logs/run_YYYYMMDD.json     # run log
```

需求依據：`akashic-daily-report-final-spec-v1.1.md`（根目錄，1554 行）

---

## Current Status

**Phase 0–4 完成，Phase 5 進行中（pipeline + routine prompt 完成）。**

| Phase | 狀態 | 說明 |
|---|---|---|
| 0 Spec Freeze | ✅ 完成 | config / schema / prompt / requirements 全數到位 |
| 1 RSS 抓取 | ✅ 完成 | fetch_rss + normalize，含 feed health / retry / time window |
| 2 分類聚合 | ✅ 完成 | classifier + tw_highlight + dedup + event_cluster + selector |
| 3 Claude 改寫 | ✅ 完成 | html_cleaner + claude_rewrite + claim_trace + validators |
| 4 多格式輸出 | ✅ 完成 | formatter（JSON / MD / voice / X / Threads + run log + 驗證） |
| **5 Routine** | 🔧 **進行中** | pipeline.py + routine 已設定，待穩定性驗證 |

**數據快照（2026-06-09）**：
- 27 enabled sources（含 CNA 中央社）/ 14 remote_blocked / 461+ articles
- 14 個 source modules，0 個 pending
- 366 條測試全綠（~4.5 秒）

---

## File Inventory

### Config（Phase 0）

| 檔案 | 用途 | 對應規格 |
|---|---|---|
| `config/feeds.yaml` | 32 個 RSS 來源（27 enabled，含 CNA 中央社） | §3.1 |
| `config/beats.yaml` | 4 大 beat 關鍵字 + entity 設定 + TW Highlight + AI/ECON 例外 | §2.1, §6 |
| `config/selection_score.yaml` | 評分表 + daily_limits + dedup 閾值 | §8.2 |
| `config/style_guide.md` | 文風、禁用詞、轉場語、事實紅線 | §13 |

### Schema（Phase 0）

| 檔案 | 用途 |
|---|---|
| `schemas/article.schema.json` | normalized article（§5.3） |
| `schemas/event.schema.json` | clustered event（§7.3），含 conditional rules |
| `schemas/platform_output.schema.json` | 平台輸出 item（voice_text lint / char limits） |
| `schemas/report.schema.json` | 最終報告（$ref → platform_output） |

### Prompt（Phase 0）

| 檔案 | 用途 |
|---|---|
| `prompts/rewrite_prompt.md` | Claude 改寫指令（含 injection 防護、可做/不可做、voice_style_guide、checklist） |
| `prompts/routine_prompt.md` | 正式版 — 呼叫 `python -m src.pipeline` 的 9-step 流程 |

### Source Code（Phase 1–4，全部完成）

| 檔案 | 功能 | 測試 |
|---|---|---|
| `src/fetch_rss.py` | 併發抓取 + retry/backoff + consecutive_failures state | 12 條 |
| `src/normalize.py` | feedparser 解析 + canonicalize URL + sha256 article_id + time window | 26 條 |
| `src/classifier.py` | Beat 分類：source 0.6 + keyword 0.3 + entity 0.1（spaCy NER）+ AI/ECON exception | 22 條 |
| `src/entity_recognizer.py` | spaCy NER 封裝：extract_entities + entity_match_score | 19 條 |
| `src/tw_highlight.py` | Taiwan Highlight：positive + context + FP review | 10 條 |
| `src/dedup.py` | 文章去重：canonical URL + 同源相似標題（rapidfuzz ≥0.92） | 11 條 |
| `src/event_cluster.py` | 事件聚合：title sim 0.88 + 共同關鍵詞 ≥5（同beat+title≥50%） + 24h window + 停用詞 | 24 條 |
| `src/selector.py` | 選題：selection_score + daily_limits + drop_reason | 18 條 |
| `src/html_cleaner.py` | strip HTML/script/style + 追蹤參數清理 + entity decode | 21 條 |
| `src/claude_rewrite.py` | Anthropic SDK 呼叫 + retry + JSON parse + merge + lint | 23 條 |
| `src/claim_trace.py` | verify + fix + fallback claim + single_source_warning | 18 條 |
| `src/validators.py` | banned_phrases(8) + voice_text lint(6) + confidence/opinion/claim/platform | 37 條 |
| `src/formatter.py` | 六種輸出 + split_posts + 驗證 + CLI（stats 讀取 + transition pool + 7-event voice limit） | 66 條 |
| `src/pipeline.py` | 全 pipeline 入口（串接 9 步）+ stats 收集 + 摘要 + idempotent | 21 條 |

### Docs

| 檔案 | 用途 |
|---|---|
| `docs/INTEGRATION_DESIGN.md` | akasha-rss-news ↔ akasha-library PWA 整合設計稿 |

### Tests

```
tests/test_schemas.py           38 條（schema meta-validation + samples + lint）
tests/test_fetch_rss.py         12 條
tests/test_normalize.py         26 條
tests/test_classifier.py        22 條（含 entity integration + AI/ECON exception）
tests/test_entity_recognizer.py 19 條
tests/test_tw_highlight.py      10 條
tests/test_dedup.py             11 條
tests/test_event_cluster.py     24 條
tests/test_selector.py          18 條
tests/test_html_cleaner.py      21 條
tests/test_claude_rewrite.py    23 條（mocked SDK）
tests/test_claim_trace.py       18 條
tests/test_validators.py        37 條
tests/test_formatter.py         66 條
tests/test_pipeline.py          21 條（含 2 條 idempotent）
───────────────────────────────────
合計                            366 條，全綠，~4.5 秒
```

---

## Key Architecture Decisions

1. **分類公式**：`score = 0.6 × source_default + 0.3 × keyword + 0.1 × entity`，min_score 0.45。source_default 單獨就能過閾（0.6 > 0.45），代表 feeds.yaml 裡的 beat 配置是主要分類依據。

2. **Entity weight**：spaCy `en_core_web_sm` NER，各 beat 在 beats.yaml 定義 `entity_names`（具名組織/機構）和 `entity_types`（spaCy label 通配）。若 spaCy 未安裝自動回退為 0。

3. **AI 例外**：`ai_exception_sources`（原 The Verge / BBC Tech / Ars Technica）的文章必須 title/summary 命中 AI 關鍵字才算 AI beat。TechCrunch AI / Wired AI 不在例外名單，因為它們的 feed 已是 AI category。

3b. **ECON 例外**：鏡像 AI 例外機制。`econ_exception_sources`（bbc_business / reuters_business / nyt_business / guardian_business）的文章必須命中 ECON 關鍵字才歸 ECON beat，防止非經濟新聞因 source_default 0.6 自動入選。

4. **去重兩層**：dedup（文章層，同源）→ event_cluster（事件層，跨源）。跨源同題不在 dedup 處理。

5. **article_id**：`sha256(source_id | canonical_url)`，重跑必得同 ID。

6. **Fail mode**：單源失敗 → continue_with_warning；全源失敗 → abort（exit code 2）。連續 3 次失敗 → 額外告警。

7. **Claude 改寫安全**：rewrite_prompt.md 含 injection 防護；claim_trace verify → fix → fallback 確保至少 1 條；banned_phrases 8 詞 + voice_text 6 patterns lint。

8. **文字切分**：split_posts 三級退讓（句號 → 逗號 → 強制截斷），確保 X ≤280 / Threads ≤500。

9. **朗讀稿獨立生成**：用 voice_text 欄位加上 §13.3 開場 + §13.4 轉場語 + §13.5 來源宣告，不是拿 thread_text 刪 emoji。

10. **整合設計**：akasha-library PWA 用 bridge pattern（headline→title, context→summary），擴展欄位用 `_` prefix，IndexedDB 15 年保留。

---

## Feed Health Snapshot（2026-06-09）

**27 enabled / 14 remote_blocked（雲端 403 預期行為）**

| Beat | 活源數 | 備註 |
|---|---|---|
| INTL | 5 | bbc_world / reuters×2 / aljazeera / npr / cna_intworld |
| ARTS | 11 | guardian×7 / nyt×2 / archdaily / dezeen |
| ECON | 4 | bbc_biz / reuters_biz / guardian_biz / nyt_biz |
| AI | 4+2 低頻 | bbc_tech / marktechpost / techcrunch / wired + ars/mit |
| PTS_LOCAL / TW | 1+1 | pts_news（PTS_LOCAL）+ cna_intworld（INTL beat，TW tier） |

**remote_blocked（14 個）**：Guardian ×8 / NYT ×3 / Ars Technica / MIT AI News / Wired
→ 雲端 IP 被封，需本機先 fetch、push raw data

**Disabled sources**（5 個）：
- `the_verge`：403 封鎖
- `venturebeat_ai`：停更 4 個月
- `ap_world_rsshub`：RSSHub 公共實例 403
- `bloomberg_tech_google_news`：Google News proxy 空 feed
- `pts_curations_rsshub`：MVP 先關

---

## Recent Commits

- `8b9a340` docs: sync HANDOFF.md with completed audit items
- `7f2b136` ops: fix broken RSS sources + add idempotent tests
- `1462591` fix: update deprecated MODEL + add ECON classification exception
- `dee18c5` docs: update HANDOFF.md and AI_CONTEXT.md for 2026-06-09 session
- `66c151a` improve: add CNA source, tune selection dedup, separate remote_blocked stats, strengthen rewrite prompt

---

## Next Step — Phase 5 剩餘

已完成：`src/pipeline.py`（19 條測試）+ `prompts/routine_prompt.md` 正式版 + Routine 已設定。

- Routine ID: `trig_01YZgdnxrvUsTLDh6YQKaDY4`
- 排程: `0 21 * * *` UTC = 每日 05:00 Asia/Taipei
- 模型: claude-sonnet-4-6
- 管理: https://claude.ai/code/routines/trig_01YZgdnxrvUsTLDh6YQKaDY4
- 遠端 agent 自己做 Step 8 改寫（不需要 ANTHROPIC_API_KEY）
- 產出 push 到 `daily-reports` branch

TODO 清單（`TODO.md`）：

- [ ] 通知管道（月月決定先不做，之後再加）
- [x] 同日重跑 idempotent 測試（2 條測試通過）
- [ ] 連跑 7 天穩定性測試（6 天連續 OK，待第 7 天）

---

## Pending Decisions

下列項目規格沒寫死，需要月月決定後寫入 `DECISIONS.md`：

- [ ] Routine 通知管道：Telegram、Discord、Email 三選一？
- [x] RSSHub 用公共實例還是自架？→ **公共實例已確認 403，需自架**（2026-05-19 sweep）
- [ ] Google News proxy 失效時的 fallback 策略（Reuters proxy 目前正常但規格警告 unstable）
- [ ] `tw_stories.json` 初始故事數量（5? 30? 100?）
- [x] GitHub Pages 部署？→ **等 Phase 4 做完再看**（2026-05-19）
- [x] 自動載入頻率？→ **頁面開啟時**（2026-05-19）
- [x] 手動模式？→ **保留作為 fallback**（2026-05-19）
- [x] 歷史報告保留天數？→ **15 年（圖書館精神）**（2026-05-19）
- [x] 朗讀/TTS？→ **另案處理，本專案只提供 voice_text 欄位**（2026-05-19）

---

## Git

- **Remote**：`https://github.com/TsKR2828/akasha-rss-news`（private）
- **Branch**：main
- **Latest commit**：`8b9a340` docs: sync HANDOFF.md with completed audit items
- **User**：月月 / dr1090a@gmail.com

---

## User Background

- 使用者沒有程式背景時，請用白話說明。
- 使用者需要先看清楚檔案用途，再決定是否修改。
- 修改後需更新 `DEV_LOG.md`。

## Working Rules

- 修改前先列出會動到哪些檔案。
- 修改後更新 `DEV_LOG.md`。
- 重大架構決策寫入 `DECISIONS.md`。
- Review 紀錄寫入 `DEBATE_LOG.md`。
- 保留使用者原本的工作流。
- 優先完成可執行 MVP。
- 每個 Phase 跑完測試全綠才算完成。
- 不要刪除現有檔案除非使用者明確要求。
- 每次修改後跑全部測試，全綠才算通過。

## AI Entry Files

AI 開始工作前請先閱讀：

1. `AI_CONTEXT.md`（本檔案 — 全貌速覽）
2. `ROADMAP.md`（Phase 0–5 + Post-MVP）
3. `TODO.md`（現在做 / 下一個做）
4. `DEV_LOG.md`（每次改了什麼、為什麼、踩了什麼坑）
5. `akashic-daily-report-final-spec-v1.1.md`（需求規格書，1554 行）
