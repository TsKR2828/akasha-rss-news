# Dev Log

目前階段：Phase 4 完成 → Phase 5 起手
測試合計：306 條全綠（37 schema + 32 Phase 1 + 87 Phase 2 + 80 Phase 3 + 14 entity + 56 Phase 4）
Enabled sources：26 / 0 failed / 461 articles（2026-05-19 sweep）

---

## 2026-05-20 — Phase 4: Multi-format output

### Added

- `src/formatter.py` — 多格式輸出模組（Phase 4 全部功能）
  - `split_posts()`: 把長文切成 ≤ max_chars 的 posts（X 280 字 / Threads 500 字），依序嘗試句號→逗號→強制截斷
  - `build_platform_output_item()`: event → platform_output.schema.json 格式，含 platform_outputs.x/threads/voice
  - `build_report()`: 組裝完整 report.schema.json（sections by beat order, stats, warnings, dropped_events）
  - `format_markdown()`: Markdown 可讀版（beat 標題 + emoji + 來源摺疊 + 統計表）
  - `format_voice_script()`: 朗讀稿（§13.3 開場 + §13.4 轉場語 + §13.5 來源宣告 + 結語），獨立生成非刪 emoji
  - `format_x_draft()` / `format_threads_draft()`: 平台貼文草稿 JSON
  - `build_run_log()`: pipeline run log
  - `validate_report_output()`: P0 驗收驗證（voice_text lint + X/Threads 字數 + 必填欄位 + single_source_warning）
  - `generate_all_outputs()`: 一次產出六種輸出檔 + 驗證
  - CLI: `python -m src.formatter --date YYYY-MM-DD [--dry-run]`

- `tests/test_formatter.py` — 56 條測試
  - TestSplitPosts (7): 短文 / 空文 / 精確上限 / 句號切 / 逗號切 / 強制截斷 / 中文
  - TestForceSplit (3): 整除 / 餘數 / 限內
  - TestSplitLongSentence (2): 逗號切 / 限內
  - TestBuildPlatformOutputItem (6): 基本結構 / platform_outputs / sources / tw_highlight / single_source / X 切分
  - TestBuildReport (8): 結構 / beat 排序 / title+emoji / partial / failed / dropped / stats / 空 beat
  - TestFormatMarkdown (5): header / beat headings / headlines / stats / tw mark
  - TestFormatVoiceScript (6): 開場 / 轉場語 / voice_text / 來源宣告 / 結語 / 非刪 emoji
  - TestBuildSourceAttribution (3): 單源 / 多源 / 空
  - TestFormatXDraft (2) / TestFormatThreadsDraft (1)
  - TestBuildRunLog (2): 結構 / steps
  - TestValidateReportOutput (4): 乾淨 / URL / X 超長 / claim_trace
  - TestLoadBeatMeta (2): 正常 / fallback
  - TestGenerateAllOutputs (5): dry-run / 六檔寫入 / JSON 驗證 / 多 beat / 警告

### Verification

- 306 條測試全綠（~5.7 秒）
- 六種輸出檔格式：
  - `output/daily_YYYYMMDD.json` — report.schema.json 格式
  - `output/daily_YYYYMMDD.md` — Markdown 可讀版
  - `output/voice_YYYYMMDD.txt` — 朗讀稿
  - `output/platforms/x_YYYYMMDD.json` — X 草稿
  - `output/platforms/threads_YYYYMMDD.json` — Threads 草稿
  - `output/logs/run_YYYYMMDD.json` — run log

### Notes

- 朗讀稿遵守規格 §12.3：從 voice_text 獨立生成，不是拿 thread_text 刪 emoji
- 區塊轉場語來自規格 §13.4，每個 beat 用第一句
- 來源宣告格式來自規格 §13.5，單源/多源兩種模板
- split_posts 三級退讓：句號→逗號→強制截斷，確保不超字數
- validate_report_output 做 P0 驗收：voice lint + X/Threads 長度 + 必填欄位

---

## 2026-05-19

### Changed

- 建立專案骨架。
- 依規格書 v1.1 改寫 `README.md`（先前已完成）。
- 依規格書 v1.1 改寫 `ROADMAP.md`：補入 Phase 0–5 各階段交付與驗收，新增 Post-MVP 四級優先區段與「砍範圍時的保留順序」。
- 依規格書 v1.1 改寫 `TODO.md`：分為 Now（Phase 0 收尾）、Next（Phase 1 起手）、待確認決策、Post-MVP 範圍外四區。

### Files

- `README.md`
- `ROADMAP.md`
- `TODO.md`
- `AI_CONTEXT.md`
- `PROJECT_MANIFEST.json`

### Notes

- 規格書（`akashic-daily-report-final-spec-v1.1.md`）正式作為 Phase 0–5 的需求依據。
- ROADMAP 與 TODO 採分工：ROADMAP 看全貌、TODO 只列「現在做 / 下一個做」。
- `AI_CONTEXT.md` 的 Goal 欄位仍為「尚未填寫」，建議下一步同步更新。
- TODO 已標出待月月決定的 5 個 open question（通知管道、RSSHub 部署、Google News fallback、tw_stories 初始量、設定檔填寫責任），決定後請記入 `DECISIONS.md`。

### Added（同日，Phase 0 設定檔）

- `AI_CONTEXT.md`：填入 Goal（每天清晨自動產出館報）與 Current Status（Phase 0 進行中）。
- `config/feeds.yaml`：依規格 §3.1 建立全部 29 個 RSS 來源，含 feed_health、fail_mode、fetch_window 設定。
- `config/beats.yaml`：四大 beat 的關鍵字、AI 例外規則、TW_HIGHLIGHT 判定。
- `config/selection_score.yaml`：daily_limits、selection_score、dedup_mvp、tw_story_policy。
- `config/style_guide.md`：基調、禁用詞、每日開場、區塊轉場、來源宣告、事實安全紅線、朗讀版規則。
- 同步勾掉 `ROADMAP.md` Phase 0 與 `TODO.md` Now 區段對應項目。

### Next

- `schemas/*.json`（report / article / event / platform_output 四個 schema）
- `prompts/rewrite_prompt.md`（含規格 §10.1 injection 防護）
- `prompts/routine_prompt.md`
- `requirements.txt`

### Added（同日續，Schema + Prompt + 環境）

- `schemas/article.schema.json`：規格 §5.3 normalized article，含 article_id sha256 pattern。
- `schemas/event.schema.json`：規格 §7.3 clustered event，含 conditional rules（tw_highlight=true 需 reason、source_count=1 需 single_source_warning）。
- `schemas/platform_output.schema.json`：規格 §11.3 item with platform outputs，voice_text 用 JSON Schema `not` 直接擋掉 URL / emoji / 1/N / Markdown link，X ≤ 280、Threads ≤ 500 用 maxLength 強制。
- `schemas/report.schema.json`：規格 §11.2 + §17.1，sections.items 透過 `$ref` 指向 platform_output.schema.json。
- `prompts/rewrite_prompt.md`：含規格 §10.1 injection 防護段落、§9.1 可做/不可做清單、§13 文風與禁用詞、完成檢查 checklist。
- `prompts/routine_prompt.md`：Routine 入口，列出 7 個 step、idempotent 規則、異常處理表。
- `requirements.txt`：規格 §16.2 全部套件 + anthropic SDK + pytest。

### 完成狀態

Phase 0 設定/Schema/Prompt 全數完成，剩下兩件：

1. `tests/test_schemas.py`（4 條 self-validation 測試）
2. 建立 GitHub repo 並 push

### Notes

- platform_output.schema.json 的 voice_text lint 用 JSON Schema `not + pattern` 實作，但 jsonschema 套件對 `not` 的錯誤訊息不友善，正式 lint 仍由 `src/validators.py` 補充人類可讀錯誤。
- routine_prompt.md 假設所有 `src/*.py` 已實作，這些尚未存在；Phase 1 開始建立。

### Added（同日續，Phase 0 收尾）

- `tests/__init__.py`：使 tests 成為 Python package。
- `tests/conftest.py`：提供 4 個 schema fixtures 與樣本 article / source / claim / event / item / report fixtures。
- `tests/test_schemas.py`：37 條測試分 8 組：
  1. `TestSchemasAreValid`（4 條）— Draft 7 meta-schema 自我驗證。
  2. `TestSamplesPass`（4 條）— 規格樣本通過對應 schema。
  3. `TestVoiceTextLint`（7 條）— voice_text 含 URL / 🧵 📌 📎 / 1/N / Markdown link 必擋。
  4. `TestPlatformCharLimits`（4 條）— X 281 字必擋、280 字 OK；Threads 501 字必擋、500 字 OK。
  5. `TestSourceRequirement`（4 條）— event / item 沒 sources 或 claim_trace 必擋。
  6. `TestConditionalRules`（3 條）— tw_highlight=true 沒 reason 必擋、source_count=1 沒 warning 必擋。
  7. `TestSourceFieldsRequired`（5 條）— 每個 source 缺 source_id/publisher/title/url/published_at 任一必擋。
  8. `TestStatusEnum` + `TestArticleIdHash`（6 條）— 邊角案例。
- `.gitignore`：補上 `.pytest_cache/` `.mypy_cache/` `.ruff_cache/` `.coverage` `htmlcov/`。
- 安裝 jsonschema 4.26.0（測試已驗證可跑）。
- `git init` + 首次 commit（branch: master，user: 月月 / dr1090a@gmail.com）。

### Phase 0 完成檢查

- ✅ 4 個 config YAML / MD
- ✅ 4 個 JSON Schema
- ✅ 2 個 Prompt
- ✅ requirements.txt
- ✅ tests/test_schemas.py（37/37 PASSED）
- ✅ 本機 git 初始化 + 首次 commit
- ✅ GitHub remote 建立與 push（origin: https://github.com/TsKR2828/akasha-rss-news, branch: main，commit 22233c4）

### Notes（Phase 0 收尾）

- `RefResolver` 在 jsonschema 4.18+ 已 deprecated，目前測試仍可跑，未來可遷移到 `referencing` library。
- 測試使用 `RefResolver` 是為了讓 report.schema.json 能解析其對 platform_output.schema.json 的 `$ref`。
- 建立 GitHub repo 的建議指令：`gh repo create akasha-rss-news --private --source=. --push --description "阿卡夏圖書館・每日館報系統"`。
- `docs/spec.md` 是 scaffold 留下的 stub，內容與專案無關；真正的規格是根目錄的 `akashic-daily-report-final-spec-v1.1.md`。可考慮刪除或改寫。

### Added（同日續，Phase 1 — RSS 抓取與正規化）

新增程式碼：

- `src/__init__.py`、`src/fetch_rss.py`、`src/normalize.py`
- `conftest.py`（project root）— 讓 pytest 找得到 `src` package
- `tests/test_fetch_rss.py`（12 條）
- `tests/test_normalize.py`（20 條）
- `.gitignore`：新增 `data/`（pipeline 中繼資料不入 git）

`src/fetch_rss.py`：
- 從 `config/feeds.yaml` 讀來源、`ThreadPoolExecutor` 併發抓取
- 每個 source: timeout 10s + 2 retries + exponential backoff
- `data/feed_health_state.json` 跨次累計 `consecutive_failures`
- `decide_overall_status` 實作規格 §4.2 三種 fail_mode：
  - `single_source_failed` → `partial` + warning
  - `all_sources_failed` → `failed` + abort（退出碼 2）
  - `consecutive_failures >= 3` → 額外告警
- CLI: `python -m src.fetch_rss [--only X] [--date YYYY-MM-DD]`

`src/normalize.py`：
- `canonicalize_url`: 去除 utm_*, fbclid, gclid 等 10 種追蹤參數 + lowercase scheme/host
- `compute_article_id = sha256(source_id|canonical_url)` — 重跑必同 ID
- `parse_published`: 多欄位 fallback（published / updated / created）+ 統一 +08:00 ISO
- `fetch_window_start`: 規格 §5.2 公式（report 05:00 - 24h - 3h grace）
- 輸出符合 `schemas/article.schema.json` 的 JSON 到 `data/articles/YYYY-MM-DD/`
- CLI: `python -m src.normalize [--date YYYY-MM-DD]`

測試：69 條全綠（37 schemas + 12 fetch_rss + 20 normalize），0.53s。

實機驗證（2026-05-19 12:31）：
- `python -m src.fetch_rss --only bbc_world` → 抓 27 KB BBC RSS，feed_health.json 寫入正確
- `python -m src.normalize` → 36 entries 進 parser，32 個落在 24h+3h 窗口內，4 個太舊被濾掉
- 抽樣檔案內容通過 schema：article_id 64 hex、source/publisher/tier 對齊 feeds.yaml

### Notes（Phase 1）

- BBC 在 URL 上加自家的 `at_medium=RSS&at_campaign=rss`，不在我的 TRACKING_PARAMS 預設清單；目前不影響 dedup（同源同 URL 都會帶這兩個），但 Phase 2 跨源比對 canonical_url 時若發現誤判，可擴充 TRACKING_PARAMS。
- `RefResolver` deprecation warning 仍在；未來可遷移到 `referencing` library。
- 還沒測過 Reuters / RSSHub proxy 來源的可用性；建議 Phase 2 開始前實機 sweep 一次全部 enabled sources，把實際掛掉的 mark `enabled: false`。
- `data/` 已加入 .gitignore；歷史 raw XML 與 normalized JSON 不入 git，可靠 `fetch_rss` 重跑重建。

### Phase 1 完成狀態

- ✅ `src/fetch_rss.py` + `src/normalize.py`
- ✅ feed health log + consecutive_failures state
- ✅ timeout / retry / backoff
- ✅ 時間窗口
- ✅ 32 條 Phase 1 測試
- ✅ 實機 BBC fetch + normalize end-to-end

下一步：Phase 2 — classifier / tw_highlight / dedup / event_cluster / selector。

### Added（同日續，Phase 2 — 分類、去重、事件聚合）

新增程式碼：

- `src/classifier.py`、`src/tw_highlight.py`、`src/dedup.py`、`src/event_cluster.py`、`src/selector.py`
- `tests/test_classifier.py` (11)、`test_tw_highlight.py` (10)、`test_dedup.py` (9)、`test_event_cluster.py` (16)、`test_selector.py` (13)

**classifier.py**：
- 規格 §6.1 加權公式：`0.6 * source_default + 0.3 * keyword + 0.1 * entity`（MVP entity = 0）
- 規格 §6.2 AI 例外：The Verge / BBC Tech / Ars Technica AI 沒命中 AI 關鍵字 → AI 候選降為 0
- PTS_LOCAL 直接歸類，不與其他 beat 競爭

**tw_highlight.py**：
- positive_keyword 命中 → 第一道
- false_positive_review 命中 + 無 context → 排除
- 無 context_keyword → 排除（只是順帶提一句）
- 同時有 positive 與 context → highlight=true，組合 reason

**dedup.py**：
- 規則 1：canonical_url 完全相同 → drop（rule="exact_canonical_url"）
- 規則 2：同源 + 標題正規化相似度 ≥ 0.92 → drop（rule="same_source_similar_title"）
- 跨源同題不在本層處理，留給 event_cluster

**event_cluster.py**：
- 規格 §7.2 MVP 策略：canonical URL / 標題 token_set_ratio ≥ 0.88 / 共同關鍵詞 ≥ 3 / 24h 窗口
- PTS_LOCAL 與其他 beat 隔離
- `derive_confidence`: ≥2 Tier 1/2 source → high；單 Tier 3 → low；其他 → medium
- `merge_tw_highlight`: 任一篇 highlight 即傳遞到 event
- `build_event`: 產出符合 `event.schema.json` 的結構，含 claim_trace 占位（Phase 3 Claude 會重寫）

**selector.py**：
- 規格 §8.2 selection_score 全部正/負分項；§8.3 drop_reason
- Beat-specific bonus 用關鍵字啟發式（INTL: war/summit; ARTS: pulitzer/cannes; AI: gpt/foundation model; ECON: fed/inflation）
- `same_topic_already_selected` 用「已選事件 keyword set 與當前事件交集 ≥ 3」判斷
- `daily_limits` max 強制；輸出按 beat 順序 INTL → ARTS → AI → ECON → PTS_LOCAL → TW_STORY

**測試**：128 條全綠（37 schemas + 32 Phase 1 + 59 Phase 2），0.54s。

**實機驗證（2026-05-19 12:44）**：
- classifier: 32 BBC articles → 32 INTL
- tw_highlight: 1 highlight 命中（"Trump told Taiwan not to 'go independent'"）
- dedup: 0 drops（BBC 本身無重複）
- event_cluster: 32 articles → 29 events（3 篇被合進既有 cluster）
- selector: 29 events → 5 selected
  - 第一名 score=70：Taiwan-China 主題（30 taiwan_foreign + 15 tier_1 + 25 major_geopolitical）
  - 第二到第五名 score=40：Ukraine kill-zone / 政治處決 / Everest / Iran-Trump
  - 被丟事件記入 `_selection_manifest.json` 與 `drop_reason`

### Notes（Phase 2）

- entity weight (0.1) 在 MVP 是 0；未來接 spaCy NER 或外部服務後再上線。
- selector 的 beat signal keywords 是寫死在 src/selector.py，不是 config——未來可移到 yaml。
- `same_topic_already_selected` 判定用 keyword 交集 ≥ 3，可能太嚴或太鬆；待實機跑全部 28 個 sources 後再校準。
- 因為今天只跑了 BBC World 一個 source，ARTS / AI / ECON / PTS_LOCAL 都是 0 件——驗證 pipeline 邏輯沒問題，但無法測 daily_limits min。

### Phase 2 完成狀態

- ✅ 5 個 src 模組
- ✅ 59 條 Phase 2 測試
- ✅ events JSON 通過 event.schema.json
- ✅ 實機 BBC pipeline end-to-end 跑通
- ✅ selection_manifest.json 含 drop_reason

下一步：Phase 3 — `claude_rewrite.py` + `claim_trace.py` + `validators.py`。

### Added（同日續，Entity Weight — spaCy NER）

補齊規格 §6.1 公式中 entity_weight 0.1，原本 MVP 為 0。

新增程式碼：

- `src/entity_recognizer.py`：spaCy NER 封裝
  - `extract_entities(text)` → list of `{text, label}` dicts（lazy-load `en_core_web_sm`）
  - `entity_match_score(entities, beat_entity_config)` → 0.0 / 0.5 / 1.0（同 keyword 量表）
  - Graceful degradation：spaCy 或模型未安裝時自動回退為 0（行為等同 MVP）
- `tests/test_entity_recognizer.py`（19 條）：
  1. `TestEntityMatchScore`（13 條）— 純邏輯，合成 entity list，不需 spaCy
  2. `TestExtractEntities`（5 條）— 需 spaCy + en_core_web_sm；模型不在則 skip
  3. `TestFallback`（1 條）— mock spaCy unavailable

修改程式碼：

- `src/classifier.py`：
  - import `entity_recognizer`
  - `classify()` 內提取一次 entities，每個 beat 呼叫 `entity_match_score`
  - 移除 `entity_score = 0.0` 占位
- `config/beats.yaml`：四大 beat 各加 `entities:` 區段
  - INTL：entity_names（UN / NATO / EU / G7 …）+ entity_types（GPE）
  - ARTS：entity_names（MoMA / Grammy / Oscar …）+ entity_types（WORK_OF_ART）
  - AI：entity_names（OpenAI / Anthropic / DeepMind …）+ entity_types 空（靠具名命中）
  - ECON：entity_names（Fed / ECB / IMF …）+ entity_types（MONEY / PERCENT）
- `tests/test_classifier.py`：
  - 新增 autouse `_mock_ner` fixture 確保既有測試 entity=0 不變
  - 新增 `TestEntityIntegration`（9 條）驗證 entity 分數正確疊加
- `requirements.txt`：新增 `spacy>=3.7,<4.0`（需另跑 `python -m spacy download en_core_web_sm`）

測試：156 條全綠（37 schemas + 32 Phase 1 + 59 Phase 2 + 28 entity），3.94s。

### Notes（Entity Weight）

- entity_match_score 只比對 spaCy 提取出的實體，不做原文搜尋——避免與 keyword 訊號重複。
- 0.1 權重是 tiebreaker 性質：source(0.6) + keyword(0.3) 仍為主要分類依據。
- INTL 使用 GPE（國家/城市）作為通配 entity type，因為國際新聞天然大量提及地名。
- AI beat 不設通配 entity type（ORG 太廣），只靠具名公司（OpenAI / Anthropic / …）。
- ECON 的 MONEY + PERCENT entity type 能捕捉「$2 trillion」「0.25%」等財經數據，是關鍵字難以覆蓋的訊號。
- spaCy `en_core_web_sm`（~13 MB）首次載入 ~1-2 秒，後續每篇 article ~5-50 ms，29 sources 不構成瓶頸。
- `reset()` 函式僅供測試用，正式 pipeline 中 NLP 模型只 load 一次。

### Changed（同日續，Feed Sweep — 全 28 enabled sources 實機掃描）

**掃描時間**：2026-05-19 15:26 Taipei

**結果**：26 ok / 2 failed → 修正後 26 ok / 0 failed

**關掉 4 個死源**（enabled: false）：

| source_id | 原因 |
|---|---|
| `the_verge` | 403 X-Forbidden，The Verge 主動封鎖 RSS（RSSHub route 也 403） |
| `venturebeat_ai` | 最後一篇 2026-01-22，停更 4 個月 |
| `ap_world_rsshub` | 403 Forbidden，RSSHub 公共實例封鎖 |
| `bloomberg_tech_google_news` | Google News proxy 回傳 0 entries |

**新增 2 個 AI 來源**（補救 AI beat）：

| source_id | publisher | Tier | 窗口內文章 |
|---|---|---|---|
| `techcrunch_ai` | TechCrunch | 2 | 7 |
| `wired_ai` | Wired | 2 | 2 |

**修正後 Beat 分佈**（461 篇）：

| Beat | sources | 文章數 |
|---|---|---|
| INTL | bbc_world + reuters_world + aljazeera + npr | 165 |
| ARTS | guardian×7 + nyt×2 + archdaily + dezeen | 128 |
| ECON | bbc_biz + reuters_biz + guardian_biz + nyt_biz | 124 |
| AI | bbc_tech + marktechpost + techcrunch_ai + wired_ai | 19 |
| PTS_LOCAL | pts_news | 25 |

**低頻但仍 enabled**（不關，部分日期會有料）：

- `ars_technica_ai`：最新 5/14，Technology Lab feed 更新頻率低
- `mit_ai_news`：最新 5/14，學術性質，一週數篇

### Notes（Feed Sweep）

- `config/feeds.yaml` sources 總數不變（29 + 2 新增 = 31），enabled 數 = 26。
- AI beat 從 2 個活源（10 篇）→ 4 個活源（19 篇），daily_limits.AI.min=1 有餘裕。
- TechCrunch 與 Wired 都是 AI exception 候選（同 The Verge 性質），如有需要可加入 `ai_exception_sources`。目前不加，因為它們的 feed 已篩到 AI category，比 The Verge 全站 feed 乾淨。
- 被 disabled 的 4 個 source 若未來條件改變（自架 RSSHub、The Verge 開放、VB 恢復更新），把 enabled 改回 true 即可。
- Google News proxy 路線（reuters_world/reuters_business）目前正常但規格 §3.1 已警告 unstable；長期建議找穩定替代。

### Added（同日續，整合設計稿）

- `docs/INTEGRATION_DESIGN.md`：akasha-rss-news ↔ akasha-library 整合設計稿 v1.0

設計稿涵蓋：

1. **資料格式 Bridge**：akasha-rss-news 的 report.schema.json → akasha-library daily-report 格式
   - 核心四欄位（title / summary / source / url）直接映射
   - 擴充欄位用 `_` 前綴保留（confidence / claim_trace / tw_highlight / platform_outputs 等）
   - akasha-library 的 renderReport() 不需改動即可渲染
2. **傳輸機制**：GitHub Pages fetch（主） + 本地匯入（備援）
3. **語音整合**：優先使用 akasha-rss-news 的 voice_text（Claude 生成朗讀稿），fallback 到 reportToVoiceTasks()
4. **平台草稿**：X / Threads 草稿面板（Post-MVP）
5. **IndexedDB 同日覆寫**：用 reportId 去重，自動 vs 手動標記分離
6. **PostMessage 擴充**：只新增一個 `akasha-voice-play-tasks` type
7. **UI 三階段**：MVP 整合 → UI 增強 → 發文面板

### Notes（整合設計稿）

- akasha-library 端改動極小：新增 `rss-bridge.js`（~50 行）+ `index.html` 加 fetch/import UI
- 不改 akasha-library 現有 renderReport() / 存檔 / 匯出 / 語音任何一行
- Phase 4.5 預估工時 ~4h（rss-bridge.js 1h + index.html 修改 2h + 測試 1h）
- 5 個開放問題已決定（記入 DECISIONS.md）：
  1. GitHub Pages 公開性 → **延後**（等 Phase 4 做完再看）
  2. 自動載入頻率 → **頁面開啟時**
  3. 手動模式 → **保留**
  4. 歷史保留天數 → **15 年**（比照圖書館典藏）
  5. 朗讀機制 → **另案處理**（獨立專案負責，設計稿 §5 不實作 TTS 播放）

## 2026-05-20

### Added（Phase 3 — Claude 改寫與事實安全）

新增程式碼：

- `src/html_cleaner.py`：
  - `clean_html()`: strip `<script>` / `<style>` 整塊 → 移除 HTML 標籤 → 解碼 entities（named + numeric） → 清理文中 URL 追蹤參數 → 壓縮空白
  - `strip_tracking_params()`: 移除 URL 的 utm_*, fbclid, gclid 等 20+ 種追蹤參數 + fragment
  - `clean_article_for_rewrite()`: 清理 article dict 的 title / summary / content / url

- `src/claude_rewrite.py`：
  - `prepare_event_payload()`: event → rewrite_prompt.md 定義的輸入 JSON（含 HTML 清理）
  - `parse_claude_response()`: 支援純 JSON 和 ```json code block 兩種格式
  - `call_claude()`: Anthropic SDK 呼叫，2 次重試 + exponential backoff
  - `merge_rewrite_into_event()`: 改寫結果合併回 event（保留結構欄位，覆蓋內容欄位）
  - `rewrite_event()`: 單一 event 改寫 pipeline（prepare → call → lint → merge）
  - `rewrite_selected_events()`: 批次改寫所有 selected events
  - CLI: `python -m src.claude_rewrite --date YYYY-MM-DD [--dry-run] [--model MODEL]`

- `src/claim_trace.py`：
  - `verify_claim_trace()`: 驗證每條 claim 的 source_id、claim 文字、support_type
  - `fix_claim_trace()`: 自動修正 source_url / source_title，移除無效 claim，修正 support_type
  - `verify_and_fix_claim_trace()`: 驗證 + 修正，若全部無效則建立 fallback claim
  - `derive_single_source_warning()`: source_count=1 → True

- `src/validators.py`：
  - `validate_banned_phrases()`: 8 個禁用詞掃描
  - `validate_voice_text()`: 6 patterns（URL / 🧵 / 📌 / 📎 / N/N / Markdown link）
  - `validate_confidence()`: 三級 vs 來源推斷比對
  - `validate_claim_trace()`: claim 合法性（空文字 / 無 source_id / 不存在 source / 無效 support_type）
  - `validate_opinion_level()`: enum 驗證
  - `validate_platform_lengths()`: X / Threads 長度 sanity check
  - `lint_rewrite_output()`: 整合 lint（一次跑完所有檢查）

新增測試：

- `tests/test_html_cleaner.py`（18 條）：tracking params / HTML strip / entity decode / article cleaning
- `tests/test_validators.py`（27 條）：banned phrases / voice lint / confidence / claim trace / opinion / platform / integration
- `tests/test_claim_trace.py`（19 條）：verify / fix / verify_and_fix / single_source_warning
- `tests/test_claude_rewrite.py`（16 條）：payload prep / response parse / call retry / merge / rewrite event / batch / lint

測試：250 條全綠（37 schema + 32 Phase 1 + 87 Phase 2 + 14 entity + 80 Phase 3），7.66s。

### Phase 3 完成狀態

- ✅ 4 個 src 模組（html_cleaner / claude_rewrite / claim_trace / validators）
- ✅ 80 條 Phase 3 測試（Claude SDK 全部 mocked，不需 API key）
- ✅ banned_phrases 8 詞 + voice_text 6 patterns + confidence 3 級
- ✅ claim_trace 自動修正 + fallback（保證至少 1 條 claim）
- ✅ HTML 清理含 script/style 移除、entity decode、追蹤參數清除
- ✅ dry-run 模式可跑完 pipeline 不呼叫 API

### Notes（Phase 3）

- Claude SDK 呼叫用 `claude-sonnet-4-20250514` 預設，可透過 `--model` CLI 參數覆蓋。
- retry 策略：最多 2 次重試（共 3 次嘗試），每次 delay 3 秒 × attempt 數。
- `parse_claude_response()` 同時支援純 JSON 和 markdown code block，因為 Claude 有時會加 ```json wrapper。
- `lint_rewrite_output()` 不做硬性阻擋（不 raise），只回傳 warning list；pipeline 繼續跑。硬性阻擋留給 Phase 4 的 schema validation。
- `claim_trace` 的 fallback 機制：若 Claude 回傳的所有 claim 都參照了不存在的 source_id，自動建立一條以第一個 source 為基礎的 fallback claim，確保 event.schema.json 的 minItems: 1 約束不會被違反。
- `validate_confidence()` 比對 Claude 回傳的 confidence 與基於來源數量/tier 的推斷值，不一致時產出 warning 但不覆寫——Claude 可能基於內容判斷有更好的 confidence 評估。

下一步：Phase 4 — `src/formatter.py`（多格式輸出 + schema validation）。
