[CmdletBinding()]
param(
    [string]$TaskName = "WechatMidlifeDailyRetro",
    [datetime]$At = [datetime]::Today.AddHours(8).AddMinutes(15)
)

$projectRoot = Split-Path -Parent $PSScriptRoot
$python = (Get-Command python -ErrorAction Stop).Source
$runner = Join-Path $PSScriptRoot "run_daily_retro.py"

$action = New-ScheduledTaskAction -Execute $python -Argument "`"$runner`""
$trigger = New-ScheduledTaskTrigger -Daily -At $At
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 5)

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Description "Fetch yesterday's WeChat metrics and generate the daily retro." -Force | Out-Null

Write-Output "Registered $TaskName at $($At.ToString('HH:mm')) every day."
Write-Output "Project: $projectRoot"
