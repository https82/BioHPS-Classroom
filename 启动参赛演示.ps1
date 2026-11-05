param([switch]$Sample)
$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
if (-not $projectRoot.StartsWith('F:\ai\', [System.StringComparison]::OrdinalIgnoreCase)) {
    throw '请先将源码解压到 F:\ai 下的文件夹，再启动，避免依赖和缓存占用C盘。'
}
Set-Location -LiteralPath $projectRoot
$tempRoot = Join-Path $projectRoot '.cache\temp'
$pipRoot = Join-Path $projectRoot '.cache\pip'
New-Item -ItemType Directory -Path $tempRoot,$pipRoot -Force | Out-Null
$env:TEMP = $tempRoot
$env:TMP = $tempRoot
$env:PIP_CACHE_DIR = $pipRoot
$env:PYTHONPYCACHEPREFIX = Join-Path $projectRoot '.cache\pycache'
$pythonExe = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 -m venv (Join-Path $projectRoot '.venv')
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python -m venv (Join-Path $projectRoot '.venv')
    } else { throw '本机未找到Python，请先安装Python 3.10或更新版本。安装目录可选择F盘。' }
    if ($LASTEXITCODE -ne 0) { throw 'Python环境创建失败' }
}
$stamp = Join-Path $projectRoot '.venv\biohps_requirements.sha256'
$requiredHash = (Get-FileHash -LiteralPath (Join-Path $projectRoot 'requirements.txt') -Algorithm SHA256).Hash
$installedHash = if (Test-Path -LiteralPath $stamp) { (Get-Content -LiteralPath $stamp -Raw).Trim() } else { '' }
if ($requiredHash -ne $installedHash) {
    & $pythonExe -m pip install -r (Join-Path $projectRoot 'requirements.txt')
    if ($LASTEXITCODE -ne 0) { throw '依赖安装未完成，请检查网络后重试' }
    Set-Content -LiteralPath $stamp -Value $requiredHash -Encoding ASCII
}
if ($Sample) {
    $sampleDb = Join-Path $projectRoot 'demo_data\contest_sample.sqlite'
    if (-not (Test-Path -LiteralPath $sampleDb)) {
        & $pythonExe (Join-Path $projectRoot '生成演示记录.py')
        if ($LASTEXITCODE -ne 0) { throw '演示样例创建失败' }
    }
    $env:BIOHPS_DEMO_DB = $sampleDb
} else {
    $env:BIOHPS_DEMO_DB = Join-Path $projectRoot 'demo_data\class_demo.sqlite'
}
& $pythonExe -m streamlit run (Join-Path $projectRoot 'app.py') --browser.gatherUsageStats false
