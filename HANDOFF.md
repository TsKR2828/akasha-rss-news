# 交接文件 — 2026-06-11

給下一個 Claude Code 視窗的工作摘要。

---

## 專案一句話

**akasha-rss-news**：每天 05:00 自動抓 RSS → 分類 → 聚合 → Claude 改寫 → 輸出六種格式的中文每日新聞館報。

---

## 目前在哪

**Phase 5（Routine 自動化）— 2026-06-11 全量健檢完成（結論 BLOCKED），16 卡修復波執行中/完成。**

2026-06-11 由 Opus 進行全量健檢，發現多處「宣告正確、執行缺席」失效模式：
- fetch 失敗告警未落地到 warnings[]（CARD-1 修復）
- pipeline exit code 邏輯不完整（CARD-2 修復）
- voice 確定性缺失（CARD-3 修復）
- split_posts 窗口上限實際未被 verify（CARD-4 修復）
- 其他共計 16 張修復卡，Opus 設計、Sonnet 執行

422 條測試全綠（修復波後實測）。

---

## Git 狀態

- **Branch**：`main`（目前 checkout）
- **Remote**：`https://github.com/TsKR2828/akasha-rss-news`（private）
- **Latest commit**：16 卡修復波提交（主控統一處理，2026-06-11）
- **Tests**：422 passed, 0 failed（~5.0 秒）
- **Working tree**：16 卡修復波完成後待主控 push

### 雙分支策略

| Branch | 用途 | 最新 commit |
|--------|------|-------------|
| `main` | 程式碼 | `7f2b136` — ops: fix broken RSS sources + add idempotent tests |
| `daily-reports` | 每日產出（routine push） | `963326e` — daily-report: 2026-06-01 |

---

## 這個視窗做了什麼

### 2026-06-11：全量健檢（Opus）+ 16 卡修復波（Sonnet）

**健檢結論**：BLOCKED — 多處宣告正確但執行缺席。

**流程說明**：Opus 擔任驗證角色，閱讀全部 src/ 模組與 tests/，制定 16 張 FIX-CARD；Sonnet 擔任執行角色，逐卡實作並在每卡結束前確認 pytest 全綠。

**16 張修復卡摘要**：

| 卡號 | 一句話 | 主要動到的檔案 |
|------|--------|----------------|
| CARD-1 | fetch 失敗 warnings 落地修復 | `src/fetch_rss.py`, `src/pipeline.py` |
| CARD-2 | pipeline exit code 完整性修復 | `src/pipeline.py` |
| CARD-3 | voice 確定性（transition pool seed 固定） | `src/formatter.py` |
| CARD-4 | split_posts 上限 verify 修復 | `src/formatter.py`, `scripts/verify_output.py` |
| CARD-5 | fetch_warnings 欄位正式落地 | `src/fetch_rss.py`, `src/pipeline.py` |
| CARD-6 | --until step-stop flag 實作（pipeline.py）；窗口上限 fetch_window_end 在 normalize.py | `src/pipeline.py`（--until flag）, `src/normalize.py`（fetch_window_end / in_window） |
| CARD-7 | requirements.lock 生成與鎖定 | `requirements.lock` |
| CARD-8 | verify_output.py push 前強制驗證腳本 | `scripts/verify_output.py` |
| CARD-9 | fetch abort → pipeline 明確 exit 2 | `src/pipeline.py` |
| CARD-10 | 告警鏈：consecutive_failures 觸發路徑修復 | `src/fetch_rss.py` |
| CARD-11 | voice lint N/N regex 與 schema 同步 | `schemas/platform_output.schema.json`（N/N regex 收窄；validators.py git diff 0 行，未改動） |
| CARD-12 | claim_trace fallback 覆蓋率補測 | `tests/test_claim_trace.py`（git diff 0 行，此項未落地；覆蓋率缺口仍存在） |
| CARD-13 | 文件同步：修正失真宣稱 + DEV_LOG/CHANGELOG | `README.md`, `ROADMAP.md`, `AI_CONTEXT.md`, `HANDOFF.md`, `DEV_LOG.md`, `CHANGELOG.md` |
| CARD-14 | routine_prompt.md 重寫（反映雙層抓取現況） | `prompts/routine_prompt.md` |
| CARD-15 | selector total_events.max advisory 升格 hard | `src/selector.py`（git diff 0 行，此項未落地；hard enforce 仍為 advisory） |
| CARD-16 | pipeline --dry-run 覆蓋率補強 | `tests/test_pipeline.py` |
| *(unattributed)* | classifier ECON 例外 + tests | `src/classifier.py`, `tests/test_classifier.py` |
| *(unattributed)* | event_cluster 同 beat title_sim 門檻 + tests | `src/event_cluster.py`, `tests/test_event_cluster.py` |
| *(unattributed)* | tw_highlight 中文關鍵詞 + PTS_LOCAL stats + tests | `src/tw_highlight.py`, `tests/test_tw_highlight.py` |

---

## 月月提出但未實作的改進

以下是月月分析中提到、尚未做的項目（供下個視窗參考）：

| 項目 | 原因 | 難度 |
|------|------|------|
| 加報導者 RSS | 需確認 RSS URL，更新頻率較低（週更） | 低 |
| 加農業部新聞 RSS | 需寫 3 個 adapter（truncation + 去公文腔 + 濾宣傳稿），ROI 低 | 高 |

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
| `config/feeds.yaml` | RSS 來源清單（27 enabled，含 CNA intworld） |
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

**每日雲端執行固定 14/27 失敗，全部是 `remote_blocked: true` 來源（預期行為）：**

- Guardian ×8（art, books, film, culture, music, stage, fashion, business）
- NYT ×3（books, arts, business）
- Ars Technica, MIT AI News, Wired

這些來源在雲端 IP 會被 403，需要月月本機先跑 `python -m src.fetch_rss --date YYYY-MM-DD`，push raw data 到 daily-reports branch，routine 再 `--skip-fetch` 使用。

**之前回報的 3 個異常已全部解決：**
- Reuters ×2：Google News proxy URL 已修復（`site:` 語法，99+96 entries）
- marktechpost：確認健康，之前是暫時性問題（10 entries OK）

---

## 已知待處理項目

### 程式碼層面（2026-06-11 修復波後）
- [x] ~~MODEL 更新~~ → `claude-sonnet-4-6`
- [x] ~~ECON 分類例外~~ → `econ_exception_sources` 機制
- [x] ~~Reuters proxy 修復~~ → `site:` 語法
- [x] ~~CNA URL 修復~~ → feedburner
- [x] ~~fetch 失敗 warnings 未落地~~ → CARD-1/5 修復
- [x] ~~pipeline exit code 不完整~~ → CARD-2/9 修復
- [x] ~~voice 確定性缺失~~ → CARD-3 修復
- [x] ~~split_posts 上限 verify 缺失~~ → CARD-4/8 修復
- [ ] Reuters Google News proxy 需定期 audit（語法曾變更一次）

### 人工待處理項目（程式碼無法替代）
- [ ] **claude.ai Routine prompt 更新**：`prompts/routine_prompt.md` 已重寫（CARD-14），但 claude.ai 介面上的 Routine 設定需月月手動貼入新版 prompt
- [ ] **本地 04:30 schtasks 設定**：`scripts/local_fetch.py` 需月月在 Windows 本機設定 schtasks 排程（`schtasks /create ...`），目前仍為手動
- [ ] **local_fetch push 分支歸屬決策**：local_fetch.py 抓的 raw data 應 push 到 `main` 還是 `daily-reports` 分支，尚未決定
- [ ] **通知管道決策**：Telegram / Discord / Email？月月決定後實作

### 資料/營運層面
- [ ] RSSHub 自架（公共實例 403，AP World 無法使用）
- [ ] TW_STORY 功能啟用（需建立 tw_stories.json）
- [ ] 7 天穩定性驗證（6/1 人工補回日已標記，連續計數重置中）

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
python -m pytest tests/ -q          # 422 passed, ~5.0 秒
python -m src.pipeline --dry-run    # 跑全 pipeline（跳過 Claude API）
python -m src.formatter --date 2026-06-04  # 單獨跑格式化
```
