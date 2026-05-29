# 交接文件 — 2026-05-25（Data Layer Audit 完成後）

給下一個 Claude Code 視窗的工作摘要。

---

## 專案一句話

**akasha-rss-news**：每天 05:00 自動抓 RSS → 分類 → 聚合 → Claude 改寫 → 輸出六種格式的中文每日新聞館報。

---

## 目前在哪

**Phase 5（Routine 自動化）— 資料層審查完成，等穩定性測試。**

Pipeline + Routine 已 live，每天 05:00 Asia/Taipei 自動執行。
月月從 05-21 開始每天 review 產出，經歷三輪品質修復 + 一輪資料層審查。
所有已知問題已修完，359 條測試全綠。

---

## Git 狀態

- **Branch**：`main`
- **Remote**：`https://github.com/TsKR2828/akasha-rss-news`（private）
- **Latest commit**：`5f0bdc4` fix: data layer audit — dirty data + rule consistency
- **Tests**：359 passed, 0 failed（~4 秒）
- **Untracked**：`HANDOFF.md` + 4 個 review 暫存檔（`daily_20260521_review.*`），不需 commit

---

## 這個視窗做了什麼（Data Layer Audit）

系統性審查整個 pipeline 的資料流，從 normalize → classifier → cluster → selector → rewrite → formatter 逐層檢查欄位是否正確傳遞、規則是否一致。修了 10 項問題，新增 18 條測試。

### 髒數據修復（5 項）

| # | 嚴重度 | 模組 | 問題 | 修法 |
|---|---|---|---|---|
| 1 | HIGH | dedup.py | `_selection_manifest.json` 被 glob 撈入當 article | 過濾 `_` 前綴檔 |
| 2 | HIGH | normalize.py | BBC `at_medium` 等追蹤參數未清除 | TRACKING_PARAMS 10→27 項 |
| 3 | HIGH | claude_rewrite.py | source summary 取了 `name`（publisher）而非 `summary` | 修正取值 + event_cluster 帶入 summary |
| 4 | MEDIUM | normalize.py | RSS summary 含原始 HTML 流入下游 | 新增 `_strip_html()`（避免循環 import） |
| 5 | MEDIUM | event_cluster.py | source name 用 `sid.replace("_"," ").title()` 合成 | 改用 `article["publisher"]` |

### 規則一致性修復（5 項）

| # | 模組 | 問題 | 修法 |
|---|---|---|---|
| 6 | validators.py | confidence 預期 single T3="low" 但 derive 不產 low | 移除 low 分支（schema enum 保留） |
| 7 | selector.py | `total_events.max` 定義了但未讀取 | hard enforce + beat min advisory warning |
| 8 | event.schema.json | 缺 `single_source_warning: true` const 約束 | 補齊 allOf 規則，與 platform_output 對齊 |
| 11 | validators.py + schema | `\d+/\d+` regex 誤殺日期/比例/法條 | 收窄為 word-boundary + 1-2 digit |
| 12 | config + README | TW_STORY min=1 但 tw_stories.json 不存在 | min=0 + README 標 planned |

### 月月給的 5 個明確決策

1. **confidence enum**：保留 "low" 在 schema，pipeline 不主動產生，但 Claude/人工可回傳
2. **total_events.min**：advisory only（log warning），不自動塞低分事件
3. **platform_output sourceRef**：同步加 optional summary，供 trace/debug
4. **TW_STORY**：維持未啟用，min=0，tw_stories.json 標 planned
5. **N/N regex**：只用於 voice_text lint，不套用到 article/source summary

---

## 關鍵檔案快速參照

| 檔案 | 作用 |
|---|---|
| `AI_CONTEXT.md` | **新視窗先讀這個** — 全貌速覽 |
| `DEV_LOG.md` | 每次改了什麼、為什麼（最新 2026-05-25 audit 記錄） |
| `ROADMAP.md` | 全 phase 進度 + Data Layer Audit 段落 |
| `DECISIONS.md` | 所有架構決策紀錄 |
| `prompts/rewrite_prompt.md` | Claude 改寫指令（含所有文風規則） |
| `src/pipeline.py` | 全 pipeline 入口（9 步串接） |
| `src/event_cluster.py` | 事件聚合（title sim + keyword + stopwords） |
| `src/formatter.py` | 多格式輸出（transition pool + 7-event limit） |
| `src/validators.py` | banned phrases + voice lint + confidence + claim trace |
| `src/selector.py` | selection_score 計算 + daily_limits + total_events.max |

---

## Routine 資訊

- **Routine ID**：`trig_01YZgdnxrvUsTLDh6YQKaDY4`
- **排程**：`0 21 * * *` UTC = 每日 05:00 Asia/Taipei
- **模型**：claude-sonnet-4-6
- **管理**：https://claude.ai/code/routines/trig_01YZgdnxrvUsTLDh6YQKaDY4
- **產出**：push 到 `daily-reports` branch
- **Step 8 改寫**：遠端 Sonnet agent 自己做（不需 ANTHROPIC_API_KEY）

---

## 下一步

### 立即可做
- [ ] 看 05-23 ~ 05-26 的自動產出，確認資料層修復有效
- [ ] 如果品質 OK → 開始 5 天穩定性測試

### TODO 清單（Phase 5 剩餘）
- [ ] 同日重跑 idempotent 測試
- [ ] 連跑 5~7 天穩定性測試
- [ ] 通知管道（月月說先不做，之後再加）

### 待決策
- [ ] Routine 通知管道：Telegram / Discord / Email？
- [ ] RSSHub 自架（公共實例 403）
- [ ] Google News proxy fallback 策略
- [ ] TW_STORY 何時啟用（需建立 tw_stories.json）

---

## 月月的工作風格備註

- 使用者沒有程式背景，用白話說明
- 她會每天看產出、列問題、一次丟 3-5 個修復項目
- commit 慣例：她會說「commit+push」，意思是 stage + commit + push 一步到位
- Sonnet prompt 要寫得很硬——「Sonnet 有時候會自作主張，prompt 要寫得夠硬才壓得住」
- 她在意朗讀體驗（voice.txt），會實際唸出來測
- 「先調再跑」= 先把品質調到位，再跑穩定性測試

---

## 測試命令

```bash
cd C:\Users\User.DESKTOP-HA8VHD7\Documents\Claude\akasha-rss-news
python -m pytest tests/ -q          # 359 passed, ~4 秒
python -m src.pipeline --dry-run    # 跑全 pipeline（跳過 Claude API）
python -m src.formatter --date 2026-05-22  # 單獨跑格式化
```
