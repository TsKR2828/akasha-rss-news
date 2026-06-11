# Changelog

## [2026-06-11] — 全量健檢修復波

### Fixed

- **重跑崩潰**：pipeline 在 fetch 步驟 abort 後未正確 exit 2，導致後續步驟繼續空跑並產出假成功報告（CARD-2、CARD-9）
- **告警鏈斷路**：fetch_rss.py 的 consecutive_failures 觸發路徑從未實際觸發，告警完全失效（CARD-10）；fetch 失敗警告未落地到 pipeline warnings[]（CARD-1）
- **窗口上限未驗**：split_posts 超過 X 280 / Threads 500 字元上限時 verify_output 未攔截（CARD-4）
- **exit code 不完整**：非 abort 步驟失敗時 pipeline 靜默繼續而非記錄 warning（CARD-2）
- **voice 確定性缺失**：transition pool 每次重跑選不同句，同一份 raw data 重跑得到不同 voice.txt（CARD-3）

### Added

- **`scripts/verify_output.py`**：push 前強制驗證腳本，檢查 warnings[] 落地、split_posts 上限、schema 合規（CARD-4、CARD-8）；AI_CONTEXT.md 決策 6（fail mode）與決策 8（split_posts）補充「2026-06-11 起由此腳本強制驗證」
- **`--until` flag**（`src/pipeline.py`）：pipeline step-stop 旗標，執行到指定 STEP 即停止，語意為「執行到哪一步」而非窗口截止時間（CARD-6）；真正的窗口上限 `fetch_window_end` / `in_window` 在 `src/normalize.py`（行 138/152/281），與 fetch_rss.py 無關
- **`requirements.lock`**：精確版本鎖定，避免「上週能跑、這週不能跑」（CARD-7）
- **`fetch_warnings` 欄位**：fetch_rss 的逐來源警告正式落地到 run log，可追蹤每日哪些來源有異常（CARD-5）

### 工作樹實際異動（未被 16 張卡認領）

- **`src/classifier.py`**：ECON 例外機制（`_has_econ_keyword` + `econ_exception_sources`），防止商業 RSS 來源的非經濟新聞因 source_default 0.6 自動入選 ECON beat
- **`tests/test_classifier.py`**：+4 條 ECON 例外測試 + entity integration group
- **`src/event_cluster.py`**：同 beat 關鍵詞匹配新增 title_sim ≥ 50% 門檻；停用詞擴充至 30 個，防止 transitive chain 誤合併
- **`tests/test_event_cluster.py`**：+3 條 same-beat title-sim 隔離測試
- **`src/tw_highlight.py`**：中文關鍵詞新增；PTS_LOCAL 在統計中正確計入
- **`tests/test_tw_highlight.py`**：+1 條中文關鍵詞測試

### 未落地項目（卡號已列但 git diff 0 行）

- **CARD-11**（validators.py）：`src/validators.py` 未實際修改；N/N regex 收窄僅在 `schemas/platform_output.schema.json` 落地
- **CARD-12**（test_claim_trace.py）：`tests/test_claim_trace.py` 未實際修改；claim_trace fallback 覆蓋率缺口仍存在
- **CARD-15**（selector.py）：`src/selector.py` 未實際修改；total_events.max hard enforce 仍為 advisory

### Docs

- **`prompts/routine_prompt.md` 重寫**（CARD-14）：反映雙層抓取現況（本地 04:30 fetch + 遠端 05:00 --skip-fetch）、明確 abort 判斷條件、local_fetch push 分支決策 placeholder
- **ROADMAP.md**：Phase 1 驗收「單一 source 失敗 → warnings[] 有條目」註記「2026-06-11 修復後成立」；Phase 5 連跑紀錄旁標示「6/1 為人工補回日，連續計數已重置」
- **AI_CONTEXT.md**：測試數更新（422 條實測），Recent Commits 補充修復波說明
- **README.md**：來源狀態日期更新至 2026-06-11，Phase 5 狀態補充修復波完成說明
- **HANDOFF.md**：「目前在哪」改寫為全量健檢 BLOCKED 結論 + 16 卡修復波摘要；已知待處理補充人工待處理項目（Routine prompt、schtasks、local_fetch 分支歸屬、通知管道）；測試命令更新為實測值 422 passed
- **DEV_LOG.md**：新增 2026-06-11 條目，列出全部 16 張卡（含未落地項目與未認領實際改動）、流程說明、測試結果
