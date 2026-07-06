# Dev Log

目前階段：Phase 5 進行中（pipeline + routine 已設定，2026-06-11 健檢後 16 卡修復波；2026-06-16 voice 拼貼感修復：formatter 半邊 + v2 prompt 上線）
測試合計：441 條全綠（2026-07-06 實測）
Enabled sources：27 / 0 failed（2026-07-06：雲端自抓 27/27 全 200 OK）

---

## 2026-07-06 — 0706 健檢修復波（FIX-A~E；Fable 建圖 / Sonnet 施工 / Opus 驗證）

依 `review-protocol-v1` 全量健檢（結論 PASS WITH ISSUES）→ 5 項修復 + 1 項資料救援。工作流：Fable 建地圖、Sonnet 照圖施工、Opus 三路並行驗證；其中 FIX-A 被 Opus 驗證打回，由 Opus 主模型重做。

- **舊館報救回（S1-1a，已推 daily-reports commit `e6067a7`）**：6/30 生成 commit `28669e6` 以 main 快照覆蓋工作樹後 commit，一次抹除 daily-reports 上 5/21~6/29 全部 output/ 館報（4622 檔、-43 萬行）。自其父 `b1ba9dd` 撿回 234 檔（純新增，未動 6/30~7/6）。daily-reports 現有 5/21~7/6 連續 46 份館報。
- **FIX-A 公視在地過濾**：`classifier.py` 新增雙閘門 `_is_foreign_pts_news`——「有外國訊號（外國地名 or INTL 關鍵字）且無台灣訊號」才判外國、改歸 INTL。Sonnet 初版只比對 INTL 關鍵字，Opus 驗證抓到兩向缺陷（漏殺純中文外國新聞；誤殺含選舉/外交/峰會字樣的台灣政治新聞並因落不到 beat 整篇丟棄），主模型重做為雙閘門並補回歸測試。關鍵字放 `config/beats.yaml` 的 `pts_local`。
- **FIX-B voice 來源標注 lint**：`validators.py` `VOICE_FORBIDDEN_PATTERNS` 新增中文 pattern，攔截 rewrite_prompt「零來源規則」明令禁止但舊 lint 擋不住的「只有一個來源」「本則整理自」「根據○○報導」等句型。Opus 拿 6/30、7/6 真檔實測命中、乾淨句不誤殺。
- **FIX-C run log 忠實**：`pipeline.py` 在 `--until` 提前停止時把 steps/start 落地 `_pipeline_run_state.json`，`formatter.py` 讀回合併，run log 不再 steps=[]、duration=0.01；無 state 檔時向後相容。
- **FIX-D routine 分支保護**：`routine_prompt.md`「產出與 push」新增分支保護鐵則（禁 force push/reset/整批覆蓋、push 前核對 git status 無既有檔被刪），防 6/30 抹除重演。
- **FIX-E 文件數字**：CLAUDE.md 422→441、review-protocol 366→441。
- **附帶**：`claude_rewrite.py` MODEL `claude-sonnet-4-6`→`claude-sonnet-5`（僅影響本地/API 路徑；雲端 Routine 改寫由 claude.ai session 模型執行、不呼叫此 API）。

| 檔案 | 變更 |
|------|------|
| `src/classifier.py` / `config/beats.yaml` | FIX-A 雙閘門在地過濾 + `pts_local` 關鍵字 |
| `src/validators.py` | FIX-B voice 來源標注 pattern |
| `src/pipeline.py` / `src/formatter.py` | FIX-C run log 銜接（run state 中間檔）|
| `prompts/routine_prompt.md` | FIX-D 分支保護鐵則 |
| `src/claude_rewrite.py` | MODEL → claude-sonnet-5 |
| `CLAUDE.md` / `review-protocol-v1-...md` | FIX-E 測試數字 → 441 |
| `tests/test_{classifier,validators,pipeline,formatter}.py` | 各修復對應新測試 |

測試：423 → 441 全綠。

**維運者待辦（程式改不到）**：口語稿品質根因是雲端 Routine 改寫模型不穩定遵循 prompt。FIX-B 讓 `verify_output` 能擋下違規（治本）；若要把每日產稿模型換成 Sonnet 5，需在 **claude.ai Routine 設定頁**手動切換（雲端改寫不呼叫程式碼的 API）。

---

## 2026-06-16 — voice 拼貼感修復（formatter 半邊，FIX-1 / FIX-2）

維運者診斷「館報朗讀像拼貼、像在唸目錄」。根因一半在 prompt、一半在 formatter 寫死組裝。本波先處理 formatter 半邊。

- **FIX-1 換場語去模板**：`BEAT_TRANSITION_POOL` 移除 5 句模板標籤式換場語——「換個節奏，看建築。」「然後是 AI 的部分。」「財經面。」（rewrite_prompt v2 明列禁止）＋同毛病的「科技那邊。」「換到經濟。」，改為自然過渡句。
- **FIX-2 全則完整朗讀**：`format_voice_script` 移除 7 則展開上限（`VOICE_MAX_FULL_EVENTS`）與「另外還有：A、B、C。」頓號串列拼接，改為每則完整唸出；缺 voice_text 時退回 headline 補一句完整語句。voice_text 本就由改寫階段為每則生成，不增加 API 成本，僅音檔變長（維運者決策：完整 > 簡短）。
- **關鍵矛盾**：formatter 原本寫死產生 rewrite_prompt 明令禁止的頓號串列——LLM 寫得再自然都被程式重新貼回。本波修掉。CARD-3 的轉場確定性（同日同輸出）維持不變。

| 檔案 | 變更 |
|------|------|
| `src/formatter.py` | 換場語 pool 去模板；移除 VOICE_MAX_FULL_EVENTS 與「另外還有」拼貼，全則完整朗讀 |
| `tests/test_formatter.py` | `test_voice_7_event_limit`→`test_voice_reads_all_events_fully`；新增 `test_no_banned_template_transitions` 防呆 |

測試：422 → 423 全綠（替換 1 + 新增 1）。

**FIX-3（prompt 半邊，v2 上線，同日完成）**：依維運者澄清「已公開過的內容無妨，只需保護 V10 原始素材」，捨棄原規劃的私有文風通道（過度設計、且會多一道手動貼後台的維運負擔），改採最簡路徑——

- v2 文風**直接寫進公開** `prompts/rewrite_prompt.md`（新增：零醬具名人格、聲音貫穿全文、情緒基調、禁止外漏、去重規則、換場語規則、禁用詞擴充）。雲端 Routine 讀公開檔，pull 後**自動套用、無需手動貼後台**；本地一致。
- `.gitignore` 僅保留 `文風指南*.md`（保護 V10 原始素材；去掉不穩的前導 `/`）。`rewrite_prompt_v2.md` 草稿內容已成正式 prompt，草稿與一度建立的私有檔／注入測試全部移除。
- ⚠️ CLAUDE.md 要求「改 rewrite_prompt.md 須做修改前後輸出比對」：本次採用維運者自審的 v2 草稿、且 formatter 已與其對齊；**未跑線上 API 實測比對**（環境無金鑰），建議維運者留意次日雲端館報並由 watchdog 兜底。

### 本地抓取（local fetch）排程修復 + 跨機遷移工具

- **修好啟動失敗**：`akasha-local-fetch`（桌機，04:30）原 `0x800710E0`，因 WakeToRun=False（睡眠不喚醒）+ DisallowStartIfOnBatteries=True。已設 WakeToRun / StartWhenAvailable=True、解除電池限制；AC 喚醒計時器本就啟用。手動觸發實測通過：27/27 源、`fetch_warnings=[]`、3.7MB 自動 push（`9db3021`）。前提：夜間睡眠非關機、維持登入；待次日驗證「從睡眠自動喚醒」。
- **新增 `scripts/setup_local_fetch_task.ps1`**：新家用 Windows 機一鍵建立此排程（含喚醒設定），供維運者把本機腿從公司電腦遷到家用電腦。`local_fetch.py` 只做 fetch RSS + git push、**不需任何 API 金鑰**；遷移僅需 Python + clone repo + GitHub 推送認證 + 家用（residential）IP。

---

## 2026-06-11 — 全量健檢（Opus）+ 16 卡修復波（Sonnet）

### 流程說明

採「Opus 驗證、Sonnet 執行」分工：
- **Opus（驗證角色）**：閱讀全部 src/ 14 模組、prompts/、tests/，對照 spec v1.1 逐條回歸，發現多處「宣告正確、執行缺席」失效模式，制定 16 張 FIX-CARD。
- **Sonnet（執行角色）**：逐卡實作，每卡結束前確認 pytest 全綠，不多做不少做。

**健檢結論**：全量 BLOCKED（告警鏈斷路、exit code 邏輯不完整、voice 確定性缺失、verify 缺席）。

### 16 張修復卡詳情

| 卡號 | 一句話說明 | 動到的主要檔案 |
|------|------------|----------------|
| CARD-1 | fetch 失敗 warnings 未落地到 pipeline 報告 | `src/fetch_rss.py`, `src/pipeline.py` |
| CARD-2 | pipeline exit code 邏輯不完整（非 abort 步驟應 warning 不 abort） | `src/pipeline.py` |
| CARD-3 | voice transition pool 每次重跑選不同句，確定性缺失 | `src/formatter.py` |
| CARD-4 | split_posts 超限沒有被 verify_output 攔截 | `src/formatter.py`, `scripts/verify_output.py` |
| CARD-5 | fetch_warnings 欄位正式落地到 run log | `src/fetch_rss.py`, `src/pipeline.py` |
| CARD-6 | --until step-stop flag 實作（`pipeline.py`）；窗口上限 `fetch_window_end` / `in_window` 在 `normalize.py`（與 fetch_rss.py 無關） | `src/pipeline.py`（argparse + step-stop 邏輯）, `src/normalize.py`（fetch_window_end / in_window） |
| CARD-7 | requirements.lock 生成，鎖定生產依賴版本 | `requirements.lock` |
| CARD-8 | verify_output.py 新增 push 前強制驗證腳本 | `scripts/verify_output.py` |
| CARD-9 | fetch abort → pipeline 明確 exit 2，而非靜默繼續 | `src/pipeline.py` |
| CARD-10 | consecutive_failures 告警觸發路徑修復（從未實際觸發） | `src/fetch_rss.py` |
| CARD-11 | voice lint N/N regex 與 platform_output.schema.json 同步 | `schemas/platform_output.schema.json`（N/N regex 收窄）；`src/validators.py` git diff 0 行，未改動，不應列入此卡 |
| CARD-12 | claim_trace fallback 覆蓋率補測（原有測試不足） | `tests/test_claim_trace.py` git diff 0 行，未改動，此卡未落地；覆蓋率缺口仍存在 |
| CARD-13 | 文件同步：修正失真宣稱 + 更新 DEV_LOG/CHANGELOG | `README.md`, `ROADMAP.md`, `AI_CONTEXT.md`, `HANDOFF.md`, `DEV_LOG.md`, `CHANGELOG.md` |
| CARD-14 | routine_prompt.md 重寫，反映雙層抓取現況與 --skip-fetch 流程 | `prompts/routine_prompt.md` |
| CARD-15 | selector total_events.max advisory warning 升格為 hard enforce | `src/selector.py` git diff 0 行，未改動，此卡未落地；total_events.max 仍為 advisory |
| CARD-16 | pipeline --dry-run 覆蓋率補強，補測缺失路徑 | `tests/test_pipeline.py` |

**工作樹 ground truth — 未被任何卡號認領的實際改動：**

| 檔案 | 實際變更摘要 |
|------|------------|
| `src/classifier.py` | ECON 例外機制（`_has_econ_keyword` + `econ_exception_sources`） |
| `tests/test_classifier.py` | +4 條 ECON 例外測試（+1 entity integration group） |
| `src/event_cluster.py` | 同 beat 關鍵詞匹配新增 title_sim ≥ 50% 門檻；停用詞擴充 |
| `tests/test_event_cluster.py` | +3 條 same-beat title-sim 隔離測試 |
| `src/tw_highlight.py` | 中文關鍵詞新增；PTS_LOCAL 在統計中正確計入 |
| `tests/test_tw_highlight.py` | +1 條中文關鍵詞測試 |

### 測試結果

修復波完成後全量跑測：**422 passed, 0 failed（~5.0 秒）**（較修復前 366 條增加 56 條）

---

## 2026-06-09 — 程式碼修復 + 來源健康稽核

### 程式碼修復（2 項）

**#1 claude_rewrite.py MODEL 過期修復**

- 問題：MODEL = `claude-sonnet-4-20250514`（EOL 2026-06-15）
- 修法：改為 `claude-sonnet-4-6`

**#2 ECON 分類例外機制**

- 問題：商業類 RSS（BBC/Reuters/NYT/Guardian Business）的非經濟新聞（空難、機場擴建）被自動歸類 ECON，因 source_default 0.6 > min_score 0.45
- 修法：鏡像 AI §6.2 例外模式——`beats.yaml` 新增 `econ_exception_sources`；`classifier.py` 新增 `_has_econ_keyword()` + 例外檢查
- 效果：例外來源須 title/summary 命中 ECON 關鍵字才歸類 ECON
- 新增測試 4 條（無關鍵字降權 / 有關鍵字保留 / 非例外不受影響 / 中文關鍵字通過）

### CNA RSS 修復 + 驗證（#4）

- 問題：`feeds.cna.com.tw` 域名不存在，CNA 無全類別 RSS feed
- 修法：`cna_all` → `cna_intworld`，URL 改為 `https://feeds.feedburner.com/rsscna/intworld`，beats 改為 `[INTL]`
- 驗證：fetch 20 篇 → normalize 20/20 → classify 全部 INTL → 中文 title/summary 正常保留 → tw_highlight 偵測到 2 篇台灣相關

### Idempotent 測試（#5）

- 新增 `test_idempotent_rerun_same_output`：同日重跑 pipeline 產出相同 summary
- 新增 `test_idempotent_output_files_overwritten`：重跑覆寫檔案而非產生重複

### 來源健康稽核（#7–#9）

**Reuters Google News proxy 修復**

- 問題：原 `allinurl:reuters.com` 語法返回 302 redirect + 0 entries
- 修法：改用 `site:reuters.com/world` 及 `site:reuters.com/business` 語法
- 驗證：world 99 entries / business 96 entries

**marktechpost**

- 稽核結果：200 OK，10 entries — 健康正常，先前 items=0 為暫時性問題

**RSSHub（AP World）**

- 稽核結果：仍 403，確認需自架 RSSHub — 此為基礎設施工作，非程式碼可解決

### 動到的檔案

| 檔案 | 變更 |
|---|---|
| `src/claude_rewrite.py` | MODEL → `claude-sonnet-4-6` |
| `src/classifier.py` | `_has_econ_keyword()` + ECON 例外檢查 |
| `config/beats.yaml` | `econ_exception_sources` 4 個來源 |
| `config/feeds.yaml` | CNA URL 修復 + Reuters proxy 語法修復 |
| `tests/test_classifier.py` | +4 條 ECON 例外測試 |
| `tests/test_pipeline.py` | +2 條 idempotent 測試 |
| `ROADMAP.md` | Phase 5 idempotent 勾選 |

測試：366 條全綠（+6 條：4 ECON exception + 2 idempotent）

---

## 2026-05-29 — 雙層來源策略（Dual-layer Source Strategy）

約 14/26 個 RSS 來源從雲端 IP 抓不到（Guardian 8 個、NYT 3 個、Ars Technica、Wired、MIT），
導致 remote routine 報告品質受限（尤其 ARTS 只剩 ArchDaily + Dezeen）。

**策略：本地抓取 + 遠端處理**

1. `config/feeds.yaml`：14 個來源標記 `remote_blocked: true`（不影響本地抓取行為）
2. `src/pipeline.py`：新增 `--skip-fetch` flag，若 `data/raw/{date}/` 已有 XML 則跳過 fetch_rss
3. `scripts/local_fetch.py`：本地排程腳本，抓取 → git commit → push
4. `.gitignore`：`data/raw/` 不再被 ignore（articles/ 和 events/ 仍 ignore）
5. `prompts/routine_prompt.md`：routine 改用 `git pull` + `--skip-fetch`

**流程**

```
[本地 04:30] local_fetch.py → 26 源 → data/raw/{date}/ → git push
[遠端 05:00] routine → git pull → pipeline --skip-fetch → 處理+輸出
```

若本地 fetch 未跑，`--skip-fetch` 自動回退為線上 fetch（~12 源可通）。

檔案異動：`config/feeds.yaml`、`src/pipeline.py`、`prompts/routine_prompt.md`、`.gitignore`、`scripts/local_fetch.py`（新）
測試：360 條全綠

---

## 2026-05-26 — PTS_LOCAL 選題修復

05-23 ~ 05-26 報告中台灣新聞缺失或不穩定。根因：`selector.py` 有兩個問題。

**問題 1：tier "TW" 不被計分**

- `feeds.yaml` 中公視的 tier 設為 `"TW"`（字串），但 `score_event()` 只判 `tier == 1/2/3`（整數）
- PTS_LOCAL 事件永遠得 0 分，其他 beat 事件至少 3~15 分
- 修法：`tier == "TW"` 視同 tier 1（+15 分）

**問題 2：total_events.max 裁切不保護 beat min**

- INTL 5 + ARTS 4 + AI 4 + ECON 4 + PTS_LOCAL 2 = 19 > max 18
- 裁切砍最低分 → PTS_LOCAL（score=0）被砍，05-24 甚至全砍光
- 修法：裁切時跳過會讓 beat 低於 min 的事件

**附帶修正：排序 tier 混合型別**

- `source_tiers` 含 `"TW"` 字串時，`min()` 比較 str/int 報 TypeError
- 修法：排序 key 中把非整數 tier 轉為 1

檔案異動：`src/selector.py`、`tests/test_selector.py`（+1 新測試）
測試：360 條全綠（~4.4 秒）

---

## 2026-05-25 — 資料層髒數據審查（Data Layer Audit）

跨 Phase 1–4 系統性審查，修復 5 項髒數據問題 + 5 項規則一致性問題。測試 341 → 359 條。

### 髒數據修復

**HIGH #1 dedup.py — 過濾 `_` 前綴中繼檔**

- 問題：`data/events/` 下的 `_selection_manifest.json`、`_selection_stats.json` 被 dedup `main()` 的 glob 撈入
- 修法：`main()` glob 結果過濾掉 `_` 開頭的檔案

**HIGH #2 normalize.py — TRACKING_PARAMS 擴充**

- 問題：BBC `at_medium`/`at_campaign`、Reddit `ref`、Yahoo `soc_src` 等追蹤參數未被清除，影響 canonical URL 穩定性
- 修法：TRACKING_PARAMS 從 10 項擴充至 27 項；`html_cleaner.py` 改為 `from src.normalize import TRACKING_PARAMS` 消除重複

**HIGH #3 claude_rewrite.py — source summary 取值錯誤**

- 問題：`prepare_event_payload()` 把 `source["name"]`（publisher 名稱）當成 summary 傳給 Claude
- 修法：改為 `source["summary"]`；同步在 `event_cluster.py` 將 article summary 帶入 source dict

**MEDIUM #4 normalize.py — summary HTML 清洗**

- 問題：RSS feed summary 含原始 HTML（`<p>`、`<img>`、entity），流入 classifier/cluster 造成髒數據
- 修法：在 normalize 階段加入 `_strip_html()` 清洗（獨立實作，避免與 html_cleaner.py 循環 import）

**MEDIUM #5 event_cluster.py — source name 合成名問題**

- 問題：`source["name"]` 用 `sid.replace("_", " ").title()` 產生，如 `bbc_world` → `Bbc World`
- 修法：改用 `article["publisher"]`，保留 sid 作為 fallback

### 規則一致性修復

**#6 validators.py — confidence 驗證邏輯不一致**

- 問題：`validate_confidence` 預期 single Tier 3 = "low"，但 `derive_confidence` 設計上不產生 "low"
- 修法：移除 `validate_confidence` 的 low 分支；schema enum 保留 "low"（供 Claude/人工使用）

**#7 selector.py — total_events.max 未實作**

- 問題：`selection_score.yaml` 定義了 `total_events.max` 但 selector 未讀取
- 修法：新增 total_events.max hard enforce（超出者 `drop_reason="total_limit_reached"`）+ beat min 不足 advisory warning

**#8 event.schema.json — single_source_warning 約束不完整**

- 問題：`platform_output.schema.json` 有 `source_count=1 → single_source_warning: true` 但 event.schema.json 缺少
- 修法：event.schema.json allOf 補齊相同規則

**#11 validators.py — N/N regex 過寬**

- 問題：`\d+/\d+` 會誤殺日期（5/18）、比例（2/3）、法條（14/2）
- 修法：收窄為 `(?:^|\s)\d{1,2}/\d{1,2}(?=\s|$)`；同步更新 platform_output.schema.json

**#12 TW_STORY phantom dependency**

- 問題：`selection_score.yaml` 設 `TW_STORY.min: 1` 但 `tw_stories.json` 從未建立
- 修法：min 改 0 + README 標為 planned

### 動到的檔案

| 檔案 | 變更 |
|---|---|
| `src/normalize.py` | TRACKING_PARAMS 27 項 + `_strip_html()` |
| `src/html_cleaner.py` | TRACKING_PARAMS 改為 import |
| `src/dedup.py` | main() 過濾 `_` 前綴檔 |
| `src/event_cluster.py` | source name 用 publisher + 帶入 summary |
| `src/claude_rewrite.py` | summary 取值修正 |
| `src/validators.py` | confidence 去 low 分支 + N/N regex 收窄 |
| `src/selector.py` | total_events.max enforce + min advisory |
| `schemas/event.schema.json` | sourceRef summary + single_source_warning const |
| `schemas/platform_output.schema.json` | sourceRef summary + N/N regex 收窄 |
| `config/selection_score.yaml` | TW_STORY min 0 |
| `README.md` | tw_stories.json 標為 planned |
| `tests/` | +18 條測試覆蓋本次修復 |

---

## 2026-05-22 — voice_style_guide 整合進 rewrite_prompt

月月提供 `docs/voice_style_guide.md`，把所有 voice 文風規則合併進 `prompts/rewrite_prompt.md`。

### 合併進 rewrite_prompt.md 的規則

- **句式節奏**：短句 60% / 中句 30% / 長句 10%（取代原本的「15–30 字」）
- **每則結構**：第一句是 takeaway（≤30 字），不是背景
- **數字人話翻譯**：大金額附新台幣換算（voice_text 限定）
- **擴充禁用句型**：視角類（值得注意的是、後續仍需關注）+ 結構類（首先其次最後、排比收尾）
- **來源禁止句型擴充**：「讓圖書館員翻譯給你聽」（開場已含）、「目前來源提供的細節有限」等
- **資料邊界**：寧可留白不可捏造、原文語意模糊用「據報導」帶過
- **checklist** 新增 2 項：takeaway 檢查 + 短句比例檢查

### formatter.py 系統級變更

- **過場句 pool**：每個 beat 3-4 句備選，同一期隨機選用不重複（取代固定一句）
- **voice 7-event 限制**：最多展開 7 則完整 voice_text，其餘用 headline 一句帶過（「另外還有：XXX、YYY。」）
- 新增 `BEAT_TRANSITION_POOL`、`VOICE_MAX_FULL_EVENTS` 常數

### 動到的檔案

| 檔案 | 變更 |
|---|---|
| `prompts/rewrite_prompt.md` | 全面合併 voice_style_guide 規則 |
| `src/formatter.py` | 過場句 pool + 7-event voice limit + import random |
| `tests/test_formatter.py` | 改 1 條（transition pool）+ 新增 1 條（7-event limit） |

---

## 2026-05-22 — 品質修復第三輪（聚合收緊 + 數字格式 + stats 修正）

2026-05-22 館報 review 發現 4 個問題，全部修復。

### 修了什麼

**#1 event_cluster.py — 同 beat 關鍵詞匹配加標題相似度門檻**

- 問題：ARTS beat 內兩篇完全不相關的建築文章（圍牆住宅 vs 木門）因共享領域關鍵詞（architecture, residential, courtyard, design）被合併
- 根因：同 beat 內的關鍵詞匹配沒有標題相似度要求，只要 ≥5 個共同詞就合併
- 修法：關鍵詞分支新增 `title_sim ≥ 50%` 門檻——同 beat 必須標題也有中度相似才走關鍵詞合併
- 新增測試 3 條：`test_same_beat_low_title_sim_keywords_only_no_match`、`test_same_beat_moderate_title_sim_plus_keywords_matches`、`test_same_beat_unrelated_articles_separate_clusters`
- 修改測試 1 條：`test_shared_keywords_matches` 標題改為有中度相似度的版本

**#2 rewrite_prompt.md — 數字格式規則（中文萬/億）**

- 問題：「一個人如何欠下26千磅債」——「26千磅」是 £26k 直譯，中文應寫「2.6 萬英鎊」
- 修法：新增「⛔ 數字格式規則」段落，含 k/M/B → 萬/億 換算表 + 規則 + checklist 項目
- 範例：£26k → 2.6 萬英鎊、$1.5M → 150 萬美元、$3.2B → 32 億美元

**#3 formatter.py CLI — 統計數據從磁碟讀取**

- 問題：統計區塊顯示「抓取文章: 0」「過濾後文章: 0」但選了 19 則事件
- 根因：formatter CLI 的 `main()` 硬編碼 `total_articles_fetched: 0`，沒從 feed_health.json 讀
- 修法：仿 `pipeline._collect_stats()` 邏輯，從 `data/raw/{date}/feed_health.json` 和 `data/articles/{date}/` 讀取實際計數
- 新增測試 1 條：`TestCLIStatsReading::test_stats_from_feed_health`

### 動到的檔案

| 檔案 | 變更 |
|---|---|
| `src/event_cluster.py` | 關鍵詞分支加 title_sim ≥ 50% 門檻 |
| `prompts/rewrite_prompt.md` | 新增數字格式規則（⛔ 段落 + 換算表 + checklist） |
| `src/formatter.py` | CLI main() 從 feed_health.json + articles 目錄讀取實際統計 |
| `tests/test_event_cluster.py` | +3 條（same-beat title-sim 隔離）+ 改 1 條 |
| `tests/test_formatter.py` | +1 條（CLI stats 讀取） |

---

## 2026-05-21 — 首日館報品質修復（#1 事件聚合 + #2 朗讀稿重複）

首日自動產出的 2026-05-21 館報品質檢討後，優先修復兩個嚴重問題。

### 修了什麼

**#1 event_cluster.py — 跨 beat 關鍵詞合併限制**

- 問題：「中國確認購入200架波音客機」事件被標記有 7 個來源，混入完全無關的文章（Dezeen 建築設計、ArchDaily 車站、NPR 人道援助等）
- 根因：`matches_cluster()` 的「共同關鍵詞 ≥ 3」太鬆散，不同 beat 的文章因通用英文詞（china, trade, summit 等）被 transitive chain 合併
- 修法：共同關鍵詞匹配限制為**同 beat 才能觸發**；標題高相似度（≥ 88%）仍允許跨 beat 合併（真正相同事件）
- 新增測試 3 條：`test_cross_beat_keyword_does_not_match`、`test_cross_beat_title_sim_still_matches`、`test_cross_beat_keyword_only_separate_clusters`

**#2 formatter.py — 移除朗讀稿重複來源宣告**

- 問題：每則新聞出現兩段來源宣告——Claude voice_text 自帶一句（「本則來自 BBC...」）+ formatter 再追加一句（「本館報來自 BBC 新聞...讓圖書館員翻譯給你聽」）
- 根因：`format_voice_script()` 的 `_build_source_attribution()` 與 Claude 改寫的 voice_text 重複
- 修法：移除 formatter 端的額外來源宣告，由 Claude voice_text 自帶的版本作為唯一來源
- 更新測試 1 條：`test_has_source_attribution` → `test_no_duplicate_attribution`

**第二輪（月月 review 後追加）**

**A. 可信度分級修正 — 單一 Tier 3 不再自動標低**

- 問題：ArchDaily 報建築（自身領域權威）卻被標 🔴 低可信度
- 根因：`derive_confidence()` 把所有單一 Tier 3 一律標 low
- 修法：移除 single-T3=low 規則，單一來源一律 medium；語氣保留由 `single_source_warning` 控制

**B. ECON 同 beat 內三件不相關事件合併**

- 問題：波音訂單 + 歐美貿易協議 + 三星罷工被合成一則
- 根因：`shared_kw_min=3` 太低，新聞通用詞（trade, deal, summit）觸發 transitive chain
- 修法：
  - `SHARED_KEYWORDS_MIN` 3 → 5
  - 新增 30 個新聞通用停用詞（government, president, global, billion 等）
  - `selection_score.yaml` 同步更新

**C. 朗讀稿「讓圖書館員翻譯給你聽」出現頻率過高**

- 問題：每則新聞結尾都跟一句，朗讀起來很重複
- 修法：
  - 開場白加入「讓圖書館員翻譯給你聽」（只出現一次）
  - `rewrite_prompt.md` 告知 Claude voice_text 不加尾部來源宣告
  - 系統在報告結尾統一彙整來源

**D. 參考連結集中底部**

- 問題：想貼推特時沒有方便的連結區塊
- 修法：
  - voice.txt 底部加「參考來源」區塊（來源名 + URL）
  - markdown 底部加「📎 參考來源」區塊（可點擊連結）
  - 新增 `_collect_all_sources()` helper（URL 去重）

### 動到的檔案

| 檔案 | 變更 |
|---|---|
| `src/event_cluster.py` | beat 限制 + shared_kw 5 + 停用詞 + confidence 修正 |
| `src/formatter.py` | 開場白 + 移除重複 attribution + 參考來源區塊 |
| `prompts/rewrite_prompt.md` | voice_text 不加尾部來源宣告 |
| `config/selection_score.yaml` | shared_keywords_min 3→5 |
| `tests/test_event_cluster.py` | +3 條（跨 beat 隔離）+ 改 1 條（confidence）|
| `tests/test_formatter.py` | +2 條（參考連結）+ 改 2 條（opening / attribution）|

---

## 2026-05-20 — Phase 5: Pipeline orchestrator + routine prompt

### 新增檔案

- `src/pipeline.py` — 全 pipeline 入口，串接 9 個步驟（fetch → normalize → classify → tw_highlight → dedup → event_cluster → select → claude_rewrite → formatter）
- `tests/test_pipeline.py`（19 條）— 單步執行、stats 收集、事件讀取、全流程 mock 整合

### 修改檔案

- `prompts/routine_prompt.md` — 從 Phase 0 草稿改為正式版，指令改為 `python -m src.pipeline`

### pipeline.py 設計

- 呼叫各模組的 `main(argv=[...])` 依序執行，不修改現有模組
- fetch_rss exit 2 → 立即 abort，不跑後續步驟
- 其他步驟 exit non-0 → 記錄 warning，繼續執行
- formatter 步驟直接呼叫 `generate_all_outputs()` 帶入從檔案系統收集的真實 stats
- 支援 `--dry-run`（跳過 Claude API + 檔案寫入）
- 支援 `--date YYYY-MM-DD` 指定日期
- 捕獲 SystemExit 和 Exception，不會因單步崩潰整個中斷

### 測試覆蓋

| 區塊 | 測試數 |
|------|-------|
| _run_module_step | 6 條（正常、dry-run 傳遞、例外處理、SystemExit） |
| _collect_stats | 4 條（空目錄、health log、article 計數、manifest） |
| _read_selected_events | 3 條（無 manifest、正常讀取、missing event） |
| run_pipeline 整合 | 6 條（全成功、fetch abort、部分失敗、beat 統計、formatter 例外、計時） |

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
