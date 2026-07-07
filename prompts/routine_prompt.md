# 阿卡夏圖書館・每日館報 Routine Prompt

本 prompt 由 Claude Code Routine 每日 05:00（Asia/Taipei）載入。
對應規格 §14（每日排程流程）。

---

## 你的任務

現在是台灣早上 05:00。請執行今日的館報生成流程，並在完成後回報摘要。

執行環境：雲端 clone。**不寫死任何本機路徑。**所有路徑均以 repo 根目錄為基準。

館報需求依據：`akashic-daily-report-final-spec-v1.1.md`
專案結構與規則：`AI_CONTEXT.md`

---

## 確切指令序列（依序執行，不得跳步）

### ⚠️ 前置最高優先 — 鎖定今天日期（Asia/Taipei），不准用系統時鐘判斷

**不准用沙盒系統時鐘、`date`、或憑印象判斷「今天」。** 沙盒時鐘是 UTC；台北早上
05:00 觸發時，UTC 還停在「昨天」的 21:00。若直接讀系統時間，日期會算成昨天，
於是看到昨天的館報已存在、就誤判「今天已完成、無事可做」而收工——
**這正是 2026-07-07 當天整份館報漏產、沒寫進 GitHub 的事故原因。**

先用台北時區實算今天日期，之後所有 `{date}` / `YYYYMMDD` 一律代入這個值：

```bash
DATE=$(python -c "from datetime import datetime, timezone, timedelta; print(datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d'))")
echo "今天（Asia/Taipei）= $DATE"
```

（`src/pipeline.py` 未給 `--date` 時預設即用 `datetime.now(TAIPEI)`，本來就會算對——
但**唯一安全的做法是實際把 pipeline 跑起來**，不要在跑之前自己先用系統時鐘推斷日期。）

**⛔ 嚴禁「看起來做過就跳過」。** 不准因為 git log 有近期 commit、或 `output/`
已有某天的檔案，就判定「今天已完成」而不跑流程。**每天都必須實際跑完下列 Step，
產出 `$DATE` 當天的館報。** 同日重跑是安全的（idempotent，formatter 覆寫）。
判斷「今天做了沒」的唯一依據，是 `output/daily_<今天YYYYMMDD>.json` 是否為
**這次流程新產生的**——不是 git log 上有沒有近期報告。

### Step 0 — 同步最新程式碼

```bash
git pull origin main
```

### Step 1 — 執行 pipeline（跳過 fetch，到 select 截止）

```bash
python -m src.pipeline --skip-fetch --until select
```

**`--skip-fetch`**：跳過 RSS 抓取步驟，直接使用 `data/raw/{date}/` 的預抓取資料。
原因：約半數 RSS 來源封鎖雲端 IP，由本地排程 `scripts/local_fetch.py` 提前抓取並推送至 git。

若 `data/raw/{date}/` 不存在或沒有 XML 檔，pipeline 自動回退執行線上 fetch（預期僅 ~12 個來源能通）。

**`--until select`**：pipeline 跑到 Step 7（選題）後停止，不進入 Step 8（Claude 改寫）。

此階段依序執行：

| # | 步驟 | 對應模組 | 資料目錄 |
|---|------|---------|---------|
| 1 | RSS 抓取（--skip-fetch 時跳過） | `src/fetch_rss.py` | `data/raw/{date}/` |
| 2 | 正規化 | `src/normalize.py` | `data/articles/{date}/` |
| 3 | Beat 分類 | `src/classifier.py` | 就地更新 articles |
| 4 | 台灣焦點 | `src/tw_highlight.py` | 就地更新 articles |
| 5 | 文章去重 | `src/dedup.py` | 刪除重複 articles |
| 6 | 事件聚合 | `src/event_cluster.py` | `data/events/{date}/` |
| 7 | 選題 | `src/selector.py` | `_selection_manifest.json` |

### Step 2（Step 8）— agent 執行改寫

載入 `prompts/rewrite_prompt.md`，**嚴格遵循其全部規則**，對 `_selection_manifest.json` 中所有已選取的 events，逐一執行改寫，並將結果**寫回** `data/events/{date}/` 對應事件 JSON 的下列欄位：

- `headline`
- `context`
- `thread_text`
- `threads_text`
- `voice_text`
- `confidence`
- `opinion_level`
- `claim_trace`

**禁止動結構欄位**（`event_id`、`beat`、`sources`、`tw_highlight`、`tw_highlight_reason`、`published_at` 等）。

### Step 3 — 格式化輸出

```bash
python -m src.formatter --date {date}
```

此步驟從 `data/events/{date}/` 讀取改寫結果，產出六件套輸出至 `output/`。

### Step 4 — 驗證輸出

```bash
python scripts/verify_output.py --date {date}
```

---

## 鐵則

**以下規則不得違反。違反任何一條即視為流程錯誤，須中止並回報。**

- **禁止直接建立、編輯、覆寫 `output/` 下任何檔案。** 輸出只能由 `formatter` 產生。
- **`verify_output` 不過 → 修 `data/events/{date}/` 中的事件欄位 → 重跑 `python -m src.formatter --date {date}` → 重跑 `python scripts/verify_output.py --date {date}`；絕不准手改輸出檔讓它「看起來過」。**
- **`verify_output` 仍不過時才准 commit，且 commit message 必須以 `[FAILED]` 開頭並逐條列出未過項。**
- **`thread_text` 寫純文字，不加 emoji 標頭、不加手動 1/N 編號。** 貼文切分由 `src/formatter.py` 的 `split_posts` 處理。
- **不需要也不准要求 `ANTHROPIC_API_KEY`。** Step 2 由 agent 自己執行改寫，不呼叫外部 API。
- 不要修改 `config/feeds.yaml`、`schemas/*.json`、`prompts/rewrite_prompt.md`。這些是設定，要改請手動。
- 不要刪掉任何 `data/raw/` 下的原始 XML。
- 不要在 `voice_text` 留 URL，即使 source 連結很短。
- 不要因為某 source 一次失敗就把它停用，連續失敗 3 次才告警。

---

## 失敗策略

| 情境 | 行動 |
|---|---|
| `data/raw/{date}/` 無 XML 檔 | `--skip-fetch` 自動回退為線上 fetch；預期僅 ~12 源可用 |
| Step 1 fetch 全部 source 失敗（exit 2） | **中止流程，回報錯誤，不繼續後續步驟** |
| Step 1 部分 source 失敗 | 加入 warnings，繼續 |
| pipeline status = failed | **中止流程，回報失敗步驟與錯誤訊息** |
| Step 2 改寫某 event 失敗 | 跳過該 event，記入 warnings，繼續其餘 events |
| `python -m src.formatter` exit 1（partial） | 照常 commit，但回報 partial 原因 |
| `verify_output` 不過 | 修 events → 重跑 formatter → 重 verify；仍不過才 commit（commit message 以 `[FAILED]` 開頭） |
| pipeline 跑超過 30 分鐘 | 保留中間檔案供人工排查 |

---

## 同日重跑（idempotent）

若今天 `output/daily_YYYYMMDD.json` 已存在：
- formatter 會覆寫所有 output 檔案
- 中間資料（`data/raw/`、`data/articles/`、`data/events/`）也會覆寫
- run log 同名覆寫

→ 因此「今天好像已經有報告」**不是**跳過的理由；idempotent 的用意就是讓你可以放心
一律重跑。唯一要小心的是別動到**其他日期**的檔案（見下方分支保護鐵則）。

---

## 產出與 push

完成後 push 以下內容至 `daily-reports` 分支：

- 六件套：
  - `output/daily_YYYYMMDD.json`
  - `output/daily_YYYYMMDD.md`
  - `output/voice_YYYYMMDD.txt`
  - `output/platforms/x_YYYYMMDD.json`
  - `output/platforms/threads_YYYYMMDD.json`
  - `output/logs/run_YYYYMMDD.json`
- 當日中間資料：
  - `data/raw/{date}/`（所有 XML）
  - `data/events/{date}/`（改寫後的 event JSON）

### ⛔ 分支保護鐵則（FIX-D 0706 健檢——最高優先）

`daily-reports` 分支保存的是**每日累積的歷史館報**，不是單日快照。push 前務必：

- **絕對禁止** `git push --force`、`git reset --hard`、或任何會讓 `daily-reports`
  分支歷史檔案消失的操作。
- **絕對禁止**先 `checkout`/`clean` 清空 `daily-reports` 工作目錄再整批複製今天的檔案——
  這樣會抹掉先前所有日期的館報。
- 正確流程：在 `daily-reports` 分支**既有的工作目錄基礎上**，只新增/覆寫「今天日期」對應的檔案
  （`daily_YYYYMMDD.*`、`run_YYYYMMDD.json` 等），不觸碰其他日期的檔案。
- commit 前先確認：`git status` 顯示的異動只包含今天日期的檔案，
  沒有任何既有日期的檔案被刪除或修改。若看到非當日檔案被刪除，**立即停止，不要 commit**，
  回報異常等待人工檢查。
- 2026-06-30 曾發生一次 commit 抹掉 40 天歷史館報的事故，此規則即為預防重演而加入。

---

## 完成時請回報

```
阿卡夏圖書館・YYYY-MM-DD 館報已生成

狀態：{ok | partial | failed}
事件數：{N}
- INTL: {n}
- ARTS: {n}
- AI: {n}
- ECON: {n}
- PTS_LOCAL: {n}
- TW_STORY: {n}

警告：{N} 則
{若有 warnings 逐條列出}

輸出檔案：output/daily_YYYYMMDD.{json,md} 等 6 個檔

verify_output 結果：{PASS | FAILED（{N} 條）}
{若 FAILED 逐條列出未過項}
```

若 pipeline 失敗（exit 2）或 status = failed，回報失敗步驟和錯誤訊息。

### ⛔ 完成的唯一標準

本 Routine 的產物是「`$DATE` 當天的六件套館報，已 push 到 `daily-reports` 分支」。

- **不准**把本任務當成「檢查工作分支有沒有程式要 commit / 要不要開 PR」。工作分支
  （`claude/*`）乾不乾淨、有沒有 PR，**與本任務無關**——本 Routine 不開 PR，
  產物直接進 `daily-reports`。
- 只要 `$DATE` 當天的館報還沒 push 到 `daily-reports`，任務就**尚未完成**，
  即使工作分支是乾淨的。回報「無事可做」之前，先確認 `daily-reports` 上確實有
  `output/daily_<今天YYYYMMDD>.md`。
