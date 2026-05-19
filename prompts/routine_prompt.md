# 阿卡夏圖書館・每日館報 Routine Prompt

本 prompt 由 Claude Code Routine 每日 05:00（Asia/Taipei）載入。
對應規格 §14（每日排程流程）。

---

## 你的任務

現在是台灣早上 05:00。請執行今日的館報生成流程，並在完成後產出可推播的摘要。

館報的需求依據：`akashic-daily-report-final-spec-v1.1.md`。
專案結構與規則：`README.md`、`AI_CONTEXT.md`。

---

## Pipeline

按順序執行，每步遇錯遵循 §14 的失敗策略：

### Step 1 — fetch_rss
```bash
python src/fetch_rss.py
```
- 讀 `config/feeds.yaml`，併發抓取所有 `enabled: true` 的 source。
- 記錄 feed health 到 `data/raw/YYYY-MM-DD/feed_health.json`。
- 儲存原始 XML 至 `data/raw/YYYY-MM-DD/`。

**失敗策略：**
- 單一 source 失敗 → 加入 `warnings[]`，**繼續**。
- 全部 source 失敗 → `abort_report`，**停止** 並推送錯誤通知。

### Step 2 — normalize + classify
```bash
python src/normalize.py
python src/classifier.py
python src/tw_highlight.py
python src/dedup.py
```
- 輸出 `data/articles/YYYY-MM-DD/*.json`，每篇都通過 `schemas/article.schema.json`。

### Step 3 — event cluster + selection
```bash
python src/event_cluster.py
python src/selector.py
```
- 輸出 `data/events/YYYY-MM-DD/*.json`，每個事件通過 `schemas/event.schema.json`。
- 未選入的事件記錄 `drop_reason`。
- 檢查每個 beat 是否符合 `daily_limits`。

### Step 4 — Claude 改寫
```bash
python src/claude_rewrite.py
```
- 對每個 selected event 呼叫 Claude，使用 `prompts/rewrite_prompt.md`。
- 產出 headline、context、thread_text、threads_text、voice_text、claim_trace、confidence、opinion_level。
- 跑 `src/claim_trace.py` 驗證每條 claim 對應 source。

### Step 5 — 格式化輸出
```bash
python src/formatter.py
```
- 產出六個檔：
  - `output/daily_YYYYMMDD.json`
  - `output/daily_YYYYMMDD.md`
  - `output/voice_YYYYMMDD.txt`
  - `output/platforms/x_YYYYMMDD.json`
  - `output/platforms/threads_YYYYMMDD.json`
  - `output/logs/run_YYYYMMDD.json`

### Step 6 — 驗證
```bash
python src/validators.py
```
必須通過：
- 所有 JSON 過對應 schema。
- voice_text 不含 URL / emoji / 1/N / Markdown link。
- X 每則 ≤ 280 字、Threads 每則 ≤ 500 字。
- 每個 item 至少 1 個 source、1 條 claim_trace。
- `source_count = 1` 必標 `single_source_warning`。
- `tw_highlight = true` 必有 `tw_highlight_reason`。
- banned_phrases lint 通過。

### Step 7 — 通知
- 推送一則摘要訊息（標題 + 各 beat 件數 + warnings 數）。
- 同日重跑：相同 `report_id` 已通知過則**不重複通知**（規格 §14.3）。

---

## 同日重跑（idempotent）

若今天 `daily_YYYYMMDD.json` 已存在：
- 覆寫所有 output 檔案。
- 若上次已成功通知，**這次不發第二則通知**。
- run log 寫成 `run_YYYYMMDD_NNN.json`（NNN 流水號）。

---

## 完成時請回報

```
📚 阿卡夏圖書館・YYYY-MM-DD 館報已生成

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

---

## 異常處理

| 情境 | 行動 |
|---|---|
| Step 1 全部 source 失敗 | `abort_report`，推錯誤通知，不寫成功檔案 |
| Step 4 Claude API 限流 | 退避重試 3 次，仍失敗則改 `status: partial`，問題事件加入 warnings |
| Step 6 schema 不過 | **不可** 覆寫昨天的成功檔案；報告 status: failed |
| Routine 跑超過 30 分鐘 | 推送「執行超時」通知，保留中間檔案供人工排查 |

---

## 不要做的事

- 不要修改 `config/feeds.yaml`、`schemas/*.json`、`prompts/rewrite_prompt.md`。這些是設定，要改請月月手動。
- 不要刪掉任何 `data/raw/` 下的原始 XML。
- 不要在 voice_text 留 URL，即使 source 連結很短。
- 不要因為某 source 一次失敗就把它停用，連續失敗 3 次才告警。
