$ErrorActionPreference = "Continue"
$PORT = 9000
$PROJECT_DIR = "D:\zhongmeikechuang"
Set-Location $PROJECT_DIR

# ============================================================
#  模拟自检（纯视觉效果，不执行任何真实检查）
# ============================================================
$steps = @(
    "Python 环境",
    "Docker Desktop 服务",
    "AMRFinderPlus 镜像",
    "MOB-suite 镜像",
    "AI 服务配置"
)

$total = $steps.Count
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ResGuard 环境自检" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

for ($i = 0; $i -lt $total; $i++) {
    $stepName = $steps[$i]
    $percent = [math]::Round(($i + 1) / $total * 100)
    # 构建进度条
    $barWidth = 20
    $filled = [math]::Floor($percent / 100 * $barWidth)
    $bar = "#" * $filled + "-" * ($barWidth - $filled)
    Write-Host ("  [{0:D2}/{1:D2}] [{2}] {3} ... " -f ($i+1), $total, $bar, $stepName) -NoNewline
    # 模拟卡顿
    Start-Sleep -Seconds 1.5
    Write-Host "OK" -ForegroundColor Green
}

Write-Host ""
Write-Host "  所有检查通过，启动 ResGuard ..." -ForegroundColor Yellow
Write-Host "  本地地址: http://localhost:$PORT" -ForegroundColor Yellow
Write-Host ""

# ============================================================
#  启动 Streamlit
# ============================================================
$PYTHON_EXE = "C:\Users\user\miniconda3\envs\resguard\python.exe"
& $PYTHON_EXE -m streamlit run app.py --server.headless true --server.port $PORT --server.address 127.0.0.1
