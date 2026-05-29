# 阿卡夏圖書館・每日館報 Routine Prompt

本 prompt 由 Claude Code Routine 每日 05:00（Asia/Taipei）載入。
對應規格 §14（每日排程流程）。

---

## 你的任務

現在是台灣早上 05:00。請執行今日的館報生成流程，並在完成後回報摘要。

專案目錄：`C:\Users\User.DESKTOP-HA8VHD7\Documents\Claude\akasha-rss-news`
館報需求依據：`akashic-daily-report-final-spec-v1.1.md`
專案結構與規則：`AI_CONTEXT.md`

---

## 執行指令

```bash
cd C:\Users\User.DESKTOP-HA8VHD7\Documents\Claude\akasha-rss-news
git pull origin main
python -m src.pipeline --skip-fetch
```

**`--skip-fetch`**：跳過 Step 1（RSS 抓取），直接使用 `data/raw/{date}/` 的預抓取資料。
原因：約半數 RSS 來源封鎖雲端 IP（Guardian、NYT、Ars Technica、Wired、MIT），
由本地排程 `scripts/local_fetch.py` 提前抓取並推送至 git。

若 `data/raw/{date}/` 不存在或沒有 XML 檔，pipeline 會自動回退執行 fetch（但預期只有 ~12 個來源能通）。

這會依序執行 9 個步驟（Step 1 被 --skip-fetch 跳過時為 8 個）：

| # | 步驟 | 對應模組 | 資料目錄 |
|---|------|---------|---------|
| 1 | RSS 抓取 | `src/fetch_rss.py` | `data/raw/{date}/` |
| 2 | 正規化 | `src/normalize.py` | `data/articles/{date}/` |
| 3 | Beat 分類 | `src/classifier.py` | 就地更新 articles |
| 4 | 台灣焦點 | `src/tw_highlight.py` | 就地更新 articles |
| 5 | 文章去重 | `src/dedup.py` | 刪除重複 articles |
| 6 | 事件聚合 | `src/event_cluster.py` | `data/events/{date}/` |
| 7 | 選題 | `src/selector.py` | `_selection_manifest.json` |
| 8 | Claude 改寫 | `src/claude_rewrite.py` | 就地更新 events |
| 9 | 多格式輸出 | `src/formatter.py` | `output/` |

### 退出碼

- `0` — 全部成功
- `2` — 致命錯誤（全部來源失敗或關鍵步驟崩潰）

### 產出檔案

```
output/daily_YYYYMMDD.json              # 機器可讀主報告
output/daily_YYYYMMDD.md                # Markdown 可讀版
output/voice_YYYYMMDD.txt               # 朗讀稿
output/platforms/x_YYYYMMDD.json        # X 貼文草稿
output/platforms/threads_YYYYMMDD.json  # Threads 草稿
output/logs/run_YYYYMMDD.json           # run log
```

---

## 環境需求

- **ANTHROPIC_API_KEY** 環境變數必須設定（Step 8 呼叫 Claude API）
- **spaCy model**：`en_core_web_sm`（若未安裝會自動回退，不致命）

---

## 失敗策略

| 情境 | 行動 |
|---|---|
| `data/raw/{date}/` 無 XML 檔 | `--skip-fetch` 自動回退為線上 fetch；預期僅 ~12 源可用 |
| Step 1 全部 source 失敗 | pipeline 自動 abort（exit 2），不產出檔案 |
| Step 1 部分 source 失敗 | 加入 warnings，繼續 |
| Step 8 Claude API 限流 | `claude_rewrite.py` 內建 retry 3 次；仍失敗則 status: partial |
| Step 9 驗證不過 | report status: partial，issues 寫入 run log |
| pipeline 跑超過 30 分鐘 | 保留中間檔案供人工排查 |

---

## 同日重跑（idempotent）

若今天 `output/daily_YYYYMMDD.json` 已存在：
- pipeline 會覆寫所有 output 檔案
- 中間資料（`data/raw/`、`data/articles/`、`data/events/`）也會覆寫
- run log 同名覆寫

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
```

若 pipeline 失敗（exit 2），回報失敗步驟和錯誤訊息。

---

## 不要做的事

- 不要修改 `config/feeds.yaml`、`schemas/*.json`、`prompts/rewrite_prompt.md`。這些是設定，要改請月月手動。
- 不要刪掉任何 `data/raw/` 下的原始 XML。
- 不要在 voice_text 留 URL，即使 source 連結很短。
- 不要因為某 source 一次失敗就把它停用，連續失敗 3 次才告警。
- 不要手動跑個別模組。一律用 `python -m src.pipeline` 走完整流程。
