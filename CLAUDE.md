# CLAUDE.md — akasha-rss-news

阿卡夏圖書館・每日館報系統。每日 05:00（Asia/Taipei）自動產出可閱讀、可朗讀、可轉貼的新聞館報。

入口文件順序：`AI_CONTEXT.md` → `ROADMAP.md` → `TODO.md` → `DEV_LOG.md` → 規格書 `akashic-daily-report-final-spec-v1.1.md`。

---

## 任務模式判定（先讀這段）

- **審查任務**（健檢、audit、review）：載入根目錄 `review-protocol-v1-akasha-rss-news.md` **全文**並嚴格依其執行（Part A 核心協議 + Part B 專案附錄）。審查者只報告、不改碼。
- **開發任務**（修 bug、加功能、改文件）：Part A 的「審查者身分」**不適用**，但本檔以下所有規則適用。

---

## 凍結與半活躍區（所有模式適用）

| 區域 | 規則 |
|---|---|
| `schemas/`、spec v1.1 的 P0 驗收標準 | **凍結**。改動需月月明文同意；不得為了讓測試通過而放寬標準 |
| `src/` 各模組 | 半活躍：可修 bug，**任何行為變更必附新測試** |
| `prompts/` | 生產程式碼，與 src/ 同等對待；改 `rewrite_prompt.md` 須做修改前後輸出比對 |
| `config/feeds.yaml` | 新增/修改來源必須**實際 fetch 驗證** feed 存在且有 entries |

- **測試基準：441 條全綠**（2026-07-06 起）。每次修改後全跑，全綠才算完成。
- **禁止手寫/手改 `output/` 下任何檔案**——輸出只能由 `src/formatter.py` 產生，push 前必跑 `python scripts/verify_output.py --date {date}`。

## 生產架構現實（2026-06-11 起）

- **雲端 Routine** 每日 05:00：`git pull origin main` → `pipeline --skip-fetch --until select` → agent 依 `rewrite_prompt.md` 改寫 events → `formatter` → `verify_output` 守門 → push `daily-reports`。詳見 `prompts/routine_prompt.md`。
- **本機排程** `akasha-local-fetch`（Windows 工作排程器，04:30）跑 `scripts/local_fetch.py` 抓全部 26+ 源、push raw data 到 main（14 個來源雲端 IP 被擋，靠這條腿補齊）。
- **監工** GitHub Actions `daily-report-watchdog` 每日 06:00 檢查當日館報：缺報、缺檔、verify 不過 → 自動開 GitHub issue。
- `data/raw/` 有 git 追蹤（雙層策略的資料通道），repo 體積每日增長，定期關注 retention。

## 已豁免事項（審查時不要重複回報）

- **X「280 字」= Python code-point 語義**（`DECISIONS.md` 2026-06-11）。X 平台加權計數（CJK=2）下超長**不是缺陷**，月月貼文時人工處理；自動發文功能上線前必須重新評估此決策。

## 工作慣例

- 修改前列出會動到哪些檔案；修改後更新 `DEV_LOG.md`；重大決策寫 `DECISIONS.md`。
- 使用者（月月）沒有程式背景：說明用白話、行為語言，修復指令要可直接複製。
- commit 慣例：她說「commit+push」= stage + commit + push 一步到位。
