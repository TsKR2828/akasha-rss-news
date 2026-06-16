<#
  setup_local_fetch_task.ps1
  在新的「家用」Windows 電腦上，一鍵建立 akasha 凌晨抓取排程（含自動喚醒設定）。

  前置（先做好，再跑這支）：
    1. 安裝 Python 3.12，安裝時勾「Add Python to PATH」
    2. git clone https://github.com/TsKR2828/akasha-rss-news
    3. cd 進 repo，執行 pip install -r requirements.txt
    4. gh auth login（或設好 git 推送認證），確認能 git push
  然後在 repo 根目錄執行：
    powershell -ExecutionPolicy Bypass -File scripts\setup_local_fetch_task.ps1

  夜間請讓電腦「睡眠」（不要關機）、維持登入；04:30 會自動喚醒抓取後再睡回去。
#>
$ErrorActionPreference = "Stop"

# repo 根目錄 = 本腳本所在 scripts/ 的上一層
$repo  = Split-Path -Parent $PSScriptRoot
$fetch = Join-Path $repo "scripts\local_fetch.py"
if (-not (Test-Path $fetch)) {
  Write-Error "找不到 $fetch；請在 git clone 好的 repo 內執行此腳本。"
  exit 1
}

# 找 python（優先 python，再退而求其次 py launcher）
$py = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $py) { $py = (Get-Command py -ErrorAction SilentlyContinue).Source }
if (-not $py) {
  Write-Error "找不到 python，請先安裝 Python 並勾選 Add to PATH。"
  exit 1
}

Write-Host "Python : $py"
Write-Host "Repo   : $repo"
Write-Host "Script : $fetch"

$action  = New-ScheduledTaskAction -Execute $py -Argument "`"$fetch`"" -WorkingDirectory $repo
$trigger = New-ScheduledTaskTrigger -Daily -At ([datetime]"04:30")
$principal = New-ScheduledTaskPrincipal -UserId ("{0}\{1}" -f $env:USERDOMAIN, $env:USERNAME) -LogonType Interactive -RunLevel Limited

# 關鍵：自動喚醒 + 錯過補跑 + 不被電池限制（桌機無電池也無妨）
$settings = New-ScheduledTaskSettingsSet -WakeToRun -StartWhenAvailable
$settings.DisallowStartIfOnBatteries = $false
$settings.StopIfGoingOnBatteries     = $false

Register-ScheduledTask -TaskName "akasha-local-fetch" -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null
Write-Host "`n[OK] 排程 akasha-local-fetch 已建立（每日 04:30、自動喚醒）。" -ForegroundColor Green

# 檢查電源計畫「允許喚醒計時器（插電）」是否啟用；沒開就提示（設定需系統管理員）
try {
  $q = powercfg /query SCHEME_CURRENT SUB_SLEEP RTCWAKE
  $ac = ($q | Select-String "AC").ToString()
  if ($ac -notmatch "0x00000001") {
    Write-Host "[!] 插電時的『允許喚醒計時器』似乎沒開。請開『系統管理員』身分的 PowerShell 執行：" -ForegroundColor Yellow
    Write-Host "      powercfg /setacvalueindex SCHEME_CURRENT SUB_SLEEP RTCWAKE 1" -ForegroundColor Yellow
    Write-Host "      powercfg /setactive SCHEME_CURRENT" -ForegroundColor Yellow
  } else {
    Write-Host "[OK] 插電喚醒計時器已啟用。" -ForegroundColor Green
  }
} catch { }

Write-Host "`n下一步：先測一次抓取（不上傳）" -ForegroundColor Cyan
Write-Host "    python `"$fetch`" --no-push"
Write-Host "成功後測真正上傳：python `"$fetch`"   （或直接等明早 04:30 自動跑）"
Write-Host "提醒：夜間讓電腦『睡眠』非關機、維持登入。"
