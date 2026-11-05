# 仅在自己的电脑上运行；不会显示、上传或记录API密钥。
$ErrorActionPreference = "Stop"
$dest = Join-Path $PSScriptRoot '.streamlit\secrets.toml'
if (Test-Path -LiteralPath $dest) {
  Write-Host '当前项目已有 Secrets，未做覆盖。'
  exit 0
}
$parent = Split-Path -Parent $PSScriptRoot
$folders = Get-ChildItem -LiteralPath $parent -Directory -ErrorAction SilentlyContinue |
  Where-Object { $_.FullName -ne $PSScriptRoot -and $_.Name -like 'BioHPS*' }
$candidates = @($folders | ForEach-Object {
  $file = Join-Path $_.FullName '.streamlit\secrets.toml'
  if (Test-Path -LiteralPath $file) { $file }
})
if ($candidates.Count -eq 0) {
  Write-Host '未在相邻旧版本中找到本地 Secrets。'
  Write-Host '请打开 .streamlit\secrets.example.toml，根据说明建立 secrets.toml 并填入自己的API配置。'
  Write-Host '不要把密钥发给任何人，也不要上传到GitHub。'
  exit 1
}
Write-Host '找到以下旧版本地配置文件（不会显示文件内容）：'
for ($i=0; $i -lt $candidates.Count; $i++) {
  Write-Host ("{0}. {1}" -f ($i+1), (Split-Path -Parent (Split-Path -Parent $candidates[$i])))
}
$selected = Read-Host '请输入要迁移的编号（直接回车取消）'
$num = 0
if (-not [int]::TryParse($selected, [ref]$num) -or $num -lt 1 -or $num -gt $candidates.Count) {
  Write-Host '操作取消。'; exit 0
}
$confirm = Read-Host '仅复制到当前项目的本地Secrets，不会提交到GitHub。确认复制请输入 Y'
if ($confirm -ne 'Y') { Write-Host '操作取消。'; exit 0 }
New-Item -ItemType Directory -Path (Split-Path -Parent $dest) -Force | Out-Null
Copy-Item -LiteralPath $candidates[$num-1] -Destination $dest -ErrorAction Stop
Write-Host '本地 Secrets 已复制。可重新启动Streamlit并在教师端运行“在线AI连接检查”。'
