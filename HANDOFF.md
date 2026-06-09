# 交接文件 — 2026-06-09

給下一個 Claude Code 視窗的工作摘要。

---

## 專案一句話

**akasha-rss-news**：每天 05:00 自動抓 RSS → 分類 → 聚合 → Claude 改寫 → 輸出六種格式的中文每日新聞館報。

---

## 目前在哪

**Phase 5（Routine 自動化）— pipeline live 運作中，報告序列 05-21 起連續產出。**

Pipeline + Routine 已 live，每天 05:00 Asia/Taipei 自動執行。
最近兩個視窗做了：
1. tw_highlight 中文關鍵字修復 + PTS_LOCAL 計入台灣相關統計
2. 四項品質改進（CNA 來源、選材去重、remote_blocked 統計分離、rewrite prompt 強化）
3. 6/1 報告手動補回（routine 當天 limit hit 未執行）

360 條測試全綠。

---

## Git 狀態

- **Branch**：`main`（目前 checkout）
- **Remote**：`https://github.com/TsKR2828/akasha-rss-news`（private）
- **Latest commit**：`66c151a` improve: add CNA source, tune selection dedup, separate remote_blocked stats, strengthen rewrite prompt
- **Tests**：360 passed, 0 failed（~4.5 秒）
- **Working tree**：clean

### 雙分支策略

| Branch | 用途 | 最新 commit |
|--------|------|-------------|
| `main` | 程式碼 | `66c151a` — CNA + dedup tuning + remote_blocked stats + prompt |
| `daily-reports` | 每日產出（routine push） | `963326e` — daily-report: 2026-06-01 |

---

## 這個視窗做了什麼

### Session 1：tw_highlight 修復 + 6/1 報告補回

| 問題 | 修法 |
|------|------|
| 台灣相關統計 = 0（公視文章存在但沒偵測到） | `beats.yaml` 加中文關鍵字（11 positive + 16 context + 3 FP）；`pipeline.py` + `formatter.py` 把 PTS_LOCAL beat 也計入 tw_highlights_count |
| 6/1 報告缺失（routine limit hit） | 從 6/2 remote raw data + 本地 fetch blocked sources → 跑完整 pipeline → 手動改寫 18 則 → push 到 daily-reports |
| 6/2 報告被覆蓋 | 確認 merge 保留了更完整的版本（155 vs 141 articles），無需修復 |

**Commit**：`1829402` fix: tw_highlight Chinese keywords + count PTS_LOCAL in stats

### Session 2：四項品質改進

來自月月的改進方向分析，逐一回應後挑出 4 項可行改動一口氣做完：

| # | 改動 | 影響 |
|---|------|------|
| 1 | **加中央社 CNA RSS 源** `cna_all`（`feeds.yaml`）+ `selector.py` TAIWAN_SOURCE_PREFIXES 加 `cna_` | 台灣新聞覆蓋量翻倍 |
| 2 | **same_topic_already_selected** 罰分 -20 → **-45**（`selection_score.yaml`） | 減少 WWDC 類重複選材 |
| 4 | **remote_blocked 統計分離**：`pipeline.py` + `formatter.py` 新增 `total_feeds_failed_remote_blocked` 欄位，Markdown 顯示「失敗來源 13（遠端封鎖 13、實際失敗 0）」 | 報表不再看起來「50% 失敗」 |
| 5 | **rewrite prompt 加具體事實規則**：每則 context 至少包含一個具體事實（數字/人名/時間點/地點） | 防止空泛趨勢描述 |

**也更新了**：`report.schema.json`（加 `total_feeds_failed_remote_blocked`）、3 個 test fixtures。

**Commit**：`66c151a` improve: add CNA source, tune selection dedup, separate remote_blocked stats, strengthen rewrite prompt

---

## 月月提出但未實作的改進

以下是月月同一次分析中提到、但這次未做的項目（供下個視窗參考）：

| 項目 | 原因 | 難度 |
|------|------|------|
| ECON 分類太鬆（印度空難、機場擴建歸 ECON） | 需加 `econ_exception_sources` 或調降 source_default_weight 0.6→0.45 | 中 |
| 加報導者 RSS | 需確認 RSS URL，更新頻率較低（週更） | 低 |
| 加農業部新聞 RSS | 需寫 3 個 adapter（truncation + 去公文腔 + 濾宣傳稿），ROI 低 | 高 |
| event_cluster 二次合併（同事件主體 + 24hr 窗口） | 長期改善選材重複的根本方案 | 中 |

---

## 關鍵檔案快速參照

| 檔案 | 作用 |
|------|------|
| `AI_CONTEXT.md` | **新視窗先讀這個** — 全貌速覽 |
| `DEV_LOG.md` | 每次改了什麼、為什麼 |
| `ROADMAP.md` | 全 phase 進度 |
| `DECISIONS.md` | 所有架構決策紀錄 |
| `prompts/rewrite_prompt.md` | Claude 改寫指令（含文風規則 + 具體事實規則） |
| `src/pipeline.py` | 全 pipeline 入口（9 步串接） |
| `src/classifier.py` | Beat 分類（source 0.6 + keyword 0.3 + entity 0.1） |
| `src/selector.py` | selection_score + same_topic 罰分 + daily_limits |
| `src/formatter.py` | 多格式輸出（含 remote_blocked 統計分離） |
| `config/feeds.yaml` | RSS 來源清單（27 enabled，含新增 CNA） |
| `config/beats.yaml` | Beat 關鍵字 + tw_highlight 設定（含中文） |
| `config/selection_score.yaml` | 選題評分（same_topic -45） |

---

## Routine 資訊

- **Routine ID**：`trig_01YZgdnxrvUsTLDh6YQKaDY4`
- **排程**：`0 21 * * *` UTC = 每日 05:00 Asia/Taipei
- **模型**：claude-sonnet-4-6
- **管理**：https://claude.ai/code/routines/trig_01YZgdnxrvUsTLDh6YQKaDY4
- **產出**：push 到 `daily-reports` branch
- **Step 8 改寫**：遠端 Sonnet agent 自己做（不需 ANTHROPIC_API_KEY）
- **重要**：routine 用的是 remote clone，code fix 推到 main 後 routine 下次跑就會用新程式碼

---

## 來源失敗狀況

**每日雲端執行固定 13/26 失敗，全部是 `remote_blocked: true` 來源（預期行為）：**

- Guardian ×8（art, books, film, culture, music, stage, fashion, business）
- NYT ×3（books, arts, business）
- Ars Technica, Wired

這些來源在雲端 IP 會被 403，需要月月本機先跑 `python -m src.fetch_rss --date YYYY-MM-DD`，push raw data 到 daily-reports branch，routine 再 `--skip-fetch` 使用。

**另有 3 個實際異常（OK 但 items=0）：**
- `reuters_world_google_news`：Google News proxy query 可能失效
- `reuters_business_google_news`：同上
- `marktechpost`：可能停更

---

## 已知待處理項目

### 程式碼層面
- [ ] `claude_rewrite.py` MODEL 仍為 `claude-sonnet-4-20250514`（EOL 2026-06-15）→ 需更新為新模型名
- [ ] ECON 分類太鬆 → 加 exception 機制或調權重
- [ ] Reuters Google News proxy 需定期 audit query 語法

### 資料/營運層面
- [ ] CNA RSS 加入後，首次跑 pipeline 需確認 normalize + classify 正常處理中文內容
- [ ] RSSHub 自架（公共實例 403，AP World 無法使用）
- [ ] TW_STORY 功能啟用（需建立 tw_stories.json）

### 待決策
- [ ] Routine 通知管道：Telegram / Discord / Email？
- [ ] 報導者 RSS 是否加入？
- [ ] Google News proxy 長期 fallback 策略

---

## 月月的工作風格備註

- 使用者沒有程式背景，用白話說明
- 她會每天看產出、列問題、一次丟 3-5 個修復項目
- commit 慣例：她會說「commit+push」，意思是 stage + commit + push 一步到位
- Sonnet prompt 要寫得很硬——「Sonnet 有時候會自作主張，prompt 要寫得夠硬才壓得住」
- 她在意朗讀體驗（voice.txt），會實際唸出來測
- 「先調再跑」= 先把品質調到位，再跑穩定性測試
- 她也會做產品級分析（這次的 5 點改進方向就是她自己分析的）

---

## 測試命令

```bash
cd C:\Users\User.DESKTOP-HA8VHD7\Documents\Claude\akasha-rss-news
python -m pytest tests/ -q          # 360 passed, ~4.5 秒
python -m src.pipeline --dry-run    # 跑全 pipeline（跳過 Claude API）
python -m src.formatter --date 2026-06-04  # 單獨跑格式化
```
