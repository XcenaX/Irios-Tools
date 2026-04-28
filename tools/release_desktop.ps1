param(
    [Parameter(Mandatory = $true)]
    [string]$Version,

    [string]$Repo = "XcenaX/Irios-Tools",
    [string]$ReleaseAssetName = "Irios.Tools.exe",
    [switch]$SkipTests,
    [switch]$SkipPush
)

$ErrorActionPreference = "Stop"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent $ScriptRoot
Set-Location $Root

$Tag = "v$Version"
$AppInfoPath = Join-Path $Root "desktop_app\config\app_info.py"
$ManifestPath = Join-Path $Root "releases\latest.json"
$EntryPath = Join-Path $Root ".tmp\irios_desktop_entry.py"
$DistPath = Join-Path $Root ".tmp\package_onefile"
$BuildPath = Join-Path $Root ".tmp\package_build_onefile"
$BuiltExePath = Join-Path $DistPath "Irios Tools.exe"
$ReleaseAssetPath = Join-Path $DistPath $ReleaseAssetName

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $EntryPath), (Split-Path -Parent $ManifestPath) | Out-Null

$appInfo = Get-Content -Path $AppInfoPath -Raw -Encoding UTF8
$appInfo = $appInfo -replace 'APP_VERSION = "[^"]+"', "APP_VERSION = `"$Version`""
Set-Content -Path $AppInfoPath -Value $appInfo -Encoding UTF8

@'
from desktop_app.app.main import run


if __name__ == "__main__":
    run()
'@ | Set-Content -Path $EntryPath -Encoding UTF8

if (-not $SkipTests) {
    python -m pytest `
        tests/test_license_config.py `
        tests/test_update_service.py `
        tests/test_hr_documents_desktop.py `
        tests/test_materials_writeoff_desktop.py `
        tests/test_hr_organization_cards.py `
        tests/test_missing_originals_comment_groups.py `
        tests/test_missing_originals_columns.py
}

python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --onefile `
    --name "Irios Tools" `
    --icon "$Root\assets\icon.ico" `
    --distpath $DistPath `
    --workpath $BuildPath `
    --specpath "$Root\.tmp" `
    --add-data "$Root\assets;assets" `
    --add-data "$Root\data;data" `
    --add-data "$Root\templates;templates" `
    --add-data "$Root\shared;shared" `
    --add-data "$Root\desktop_app;desktop_app" `
    --hidden-import desktop_app.modules.hr_documents.page `
    --hidden-import desktop_app.modules.materials_writeoff.page `
    --hidden-import pymorphy3_dicts_ru `
    --collect-data pymorphy3_dicts_ru `
    $EntryPath

Copy-Item -LiteralPath $BuiltExePath -Destination $ReleaseAssetPath -Force

$Hash = (Get-FileHash -LiteralPath $ReleaseAssetPath -Algorithm SHA256).Hash.ToLowerInvariant()
$Size = (Get-Item -LiteralPath $ReleaseAssetPath).Length
$DownloadUrl = "https://github.com/$Repo/releases/download/$Tag/$ReleaseAssetName"

$releaseExists = $true
cmd.exe /c "gh release view $Tag --repo $Repo >NUL 2>NUL"
if ($LASTEXITCODE -ne 0) {
    $releaseExists = $false
}

if ($releaseExists) {
    gh release upload $Tag $ReleaseAssetPath --repo $Repo --clobber
} else {
    gh release create $Tag $ReleaseAssetPath `
        --repo $Repo `
        --title "Irios Tools $Version" `
        --notes "Desktop update $Version"
}

$Manifest = [ordered]@{
    version = $Version
    mandatory = $true
    min_supported_version = "3.0.0"
    url = $DownloadUrl
    sha256 = $Hash
    size = $Size
    published_at = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    message = "Подождите, программа обновляется"
}

$Manifest | ConvertTo-Json -Depth 5 | Set-Content -Path $ManifestPath -Encoding UTF8

if (-not $SkipPush) {
    git add desktop_app/config/app_info.py releases/latest.json
    git diff --cached --quiet
    if ($LASTEXITCODE -ne 0) {
        git commit -m "Release desktop $Version"
    } else {
        Write-Host "No manifest/version changes to commit."
    }
    git push
}

Write-Host "Release ready: $Tag"
Write-Host "Asset: $ReleaseAssetPath"
Write-Host "SHA256: $Hash"
