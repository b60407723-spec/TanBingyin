<#
.SYNOPSIS
    一键重启 tbyAgenticBaseWeb 开发服务（Tornado，端口 10086）。

.DESCRIPTION
    依次执行：
    1、结束本项目中运行 app.py 的旧实例（仅匹配本项目 python.exe，不影响其它项目）；
    2、等待 10086 端口释放；
    3、用 .venv 解释器重新启动 app.py（前台运行，Ctrl + C 停止）。

    默认窗口可能禁止运行脚本，可用下面任一方式执行：
        powershell -ExecutionPolicy Bypass -File .\restart.ps1
        或在当前会话先执行：Set-ExecutionPolicy -Scope Process Bypass -Force

.EXAMPLE
    .\restart.ps1
#>

$ErrorActionPreference = 'Stop'

# 项目根目录 = 脚本所在目录
$ProjectRoot = $PSScriptRoot
Set-Location $ProjectRoot

$Port       = 10086
$ProjectName = Split-Path $ProjectRoot -Leaf
$Python     = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
$Entry      = Join-Path $ProjectRoot 'app.py'

# 1、结束旧实例（只命中本项目的 python.exe 进程）
$procs = Get-CimInstance Win32_Process |
    Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -like "*$ProjectName*app.py*" }
if ($procs) {
    foreach ($p in $procs) {
        Write-Host "停止旧实例 PID $($p.ProcessId) ..."
        Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
    }
} else {
    Write-Host "未发现运行中的旧实例。"
}

# 2、等待端口释放（最多 10 秒）
$waited = 0
while ((Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) -and $waited -lt 20) {
    Start-Sleep -Milliseconds 500
    $waited++
}
$still = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($still) {
    Write-Host "端口 $Port 仍被占用（PID $(@($still.OwningProcess) -join ',')），请手动处理后重试。"
    exit 1
}

# 3、启动服务
if (-not (Test-Path $Python)) {
    Write-Host "未找到虚拟环境解释器：$Python"
    Write-Host "请先创建虚拟环境并安装依赖后再运行本脚本。"
    exit 1
}

Write-Host "启动服务：$Python $Entry"
& $Python $Entry
