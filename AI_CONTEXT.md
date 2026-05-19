# AI Context

## Project Name

akasha-rss-news

## Project Type

basic

## Goal

每天清晨 05:00（Asia/Taipei）自動產出一份可閱讀、可朗讀、可轉貼的「阿卡夏圖書館・每日館報」。

從國際英文 RSS 與公視新聞抓取新聞，經分類、事件聚合、事實安全檢查、口語化改寫後，輸出：

- `output/daily_YYYYMMDD.json`（機器可讀）
- `output/daily_YYYYMMDD.md`（人類可讀）
- `output/voice_YYYYMMDD.txt`（朗讀稿）
- `output/platforms/x_YYYYMMDD.json`（X 貼文草稿）
- `output/platforms/threads_YYYYMMDD.json`（Threads 貼文草稿）
- `output/logs/run_YYYYMMDD.json`（run log）

需求依據：[akashic-daily-report-final-spec-v1.1.md](akashic-daily-report-final-spec-v1.1.md)

## Current Status

Phase 0（Spec Freeze）進行中：

- ✅ 規格書 v1.1 完成
- ✅ README / ROADMAP / TODO 依規格書改寫
- ⏳ `config/feeds.yaml`、`config/beats.yaml`、`config/selection_score.yaml`、`config/style_guide.md` 建立中
- ⏳ `schemas/*.json` 與 `prompts/rewrite_prompt.md` 尚未建立

詳見 [ROADMAP.md](ROADMAP.md) 與 [TODO.md](TODO.md)。

## User Background

- 使用者沒有程式背景時，請用白話說明。
- 使用者需要先看清楚檔案用途，再決定是否修改。
- 修改後需更新 `DEV_LOG.md`。

## AI Entry Files

AI 開始工作前請先閱讀：

1. `README.md`
2. `ROADMAP.md`
3. `DEV_LOG.md`
4. `AI_CONTEXT.md`
5. `PROJECT_MANIFEST.json`

## Working Rules

- 修改前先列出會動到哪些檔案。
- 修改後更新 `DEV_LOG.md`。
- 重大架構決策寫入 `DECISIONS.md`。
- Review 紀錄寫入 `DEBATE_LOG.md`。
- 保留使用者原本的工作流。
- 優先完成可執行 MVP。
