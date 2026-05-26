# GitHub Pages 初回セットアップ補助スクリプト
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

Write-Host "=== GitHub Pages セットアップ補助 ===" -ForegroundColor Cyan
Write-Host "作業フォルダ: $Root`n"

$git = Get-Command git -ErrorAction SilentlyContinue
if (-not $git) {
    Write-Host "Git が見つかりません。" -ForegroundColor Yellow
    Write-Host "https://git-scm.com/download/win からインストール後、PowerShell を開き直してください。"
    Write-Host "手順の詳細: GitHubPages-セットアップ.html をブラウザで開いてください。"
    exit 1
}

Write-Host "1) 掲示HTMLを再生成します..."
python (Join-Path $Root "scripts\generate.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$defaultRepo = "shisetsu-keiji-2026"
$ghUser = Read-Host "2) GitHubのユーザー名（例: yamada-taro）"
$ghRepo = Read-Host "3) リポジトリ名（Enterで $defaultRepo）"
if ([string]::IsNullOrWhiteSpace($ghRepo)) { $ghRepo = $defaultRepo }

$hostingPath = Join-Path $Root "data\hosting.yaml"
@"
# GitHub Pages 常設公開
github_user: $ghUser
github_repo: $ghRepo
public_base: ""
"@ | Set-Content -Path $hostingPath -Encoding UTF8

python (Join-Path $Root "scripts\generate.py")

Write-Host "`n4) Git リポジトリを初期化してコミットします..."
if (-not (Test-Path (Join-Path $Root ".git"))) {
    git init
    git branch -M main
}
git add .
git status

$doCommit = Read-Host "`nコミットしますか？ (Y/n)"
if ($doCommit -ne "n" -and $doCommit -ne "N") {
    git commit -m "施設基準掲示 令和8年度改定（GitHub Pages）"
}

$remoteUrl = "https://github.com/$ghUser/$ghRepo.git"
Write-Host "`n=== 次に実行してください ===" -ForegroundColor Green
Write-Host @"

# リモート追加（初回のみ）
git remote add origin $remoteUrl
# すでに origin がある場合は:
# git remote set-url origin $remoteUrl

git push -u origin main

"@

Write-Host "GitHub でリポジトリ '$ghRepo' を先に作成してください（Public推奨）。"
Write-Host "Settings → Pages → Source: GitHub Actions を選択。"
Write-Host ""
Write-Host "push 成功後（2〜3分）の公開URL:" -ForegroundColor Cyan
Write-Host "  https://$ghUser.github.io/$ghRepo/"
Write-Host ""
Write-Host "各院:" -ForegroundColor Cyan
@("kohokudai", "nogata", "ikebukuro", "yuzawa") | ForEach-Object {
    Write-Host "  https://$ghUser.github.io/$ghRepo/$_/"
}
Write-Host "`n詳細: GitHubPages-セットアップ.html / GitHubPages-公開URL.txt"
