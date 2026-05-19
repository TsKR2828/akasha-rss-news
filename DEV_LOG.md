# Dev Log

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
