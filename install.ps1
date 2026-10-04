<#
.SYNOPSIS
Install the QSWATMOD2 plugin into a QGIS 3 profile (Windows PowerShell 5.1 or PowerShell 7).

.DESCRIPTION
Downloads the plugin ZIP of a GitHub release (or uses one you already have), checks it, and
unpacks it into the QGIS plugins folder of the current user. No administrator rights needed.
Close QGIS first, then restart it and tick QSWATMOD2 in
Plugins > Manage and Install Plugins > Installed.

.PARAMETER Version
Release tag, for example v2.11.0. Default: the latest release.

.PARAMETER Zip
A QSWATMOD2.<version>.zip you already downloaded.

.PARAMETER Url
Download the ZIP from this URL instead of a GitHub release.

.PARAMETER Profile
QGIS profile name (default: default).

.PARAMETER PluginsDir
Any plugins folder, instead of %APPDATA%\QGIS\QGIS3\profiles\<Profile>\python\plugins.

.PARAMETER Uninstall
Remove the installed plugin.

.PARAMETER Force
Replace or remove a plugin folder that is a link (a development install).

.EXAMPLE
powershell -ExecutionPolicy Bypass -c "irm https://raw.githubusercontent.com/spark-hydro/QSWATMOD2-plugin/main/install.ps1 | iex"

.EXAMPLE
.\install.ps1 -Version v2.11.0

.EXAMPLE
.\install.ps1 -Zip .\QSWATMOD2.2.11.0.zip

.EXAMPLE
.\install.ps1 -Uninstall
#>
[CmdletBinding()]
param(
    [string]$Version = "",
    [string]$Zip = "",
    [string]$Url = "",
    [string]$Profile = "default",
    [string]$PluginsDir = "",
    [switch]$Uninstall,
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"   # the progress bar makes downloads very slow in 5.1
$repo = "spark-hydro/QSWATMOD2-plugin"
$name = "QSWATMOD2"

# throw, not exit: this script can be run with "irm ... | iex" inside the user's own shell
function Fail($message) { throw "install.ps1: $message" }

if (-not $PluginsDir) {
    if (-not $env:APPDATA) { Fail "APPDATA is not set; use -PluginsDir" }
    $PluginsDir = Join-Path $env:APPDATA "QGIS\QGIS3\profiles\$Profile\python\plugins"
}
$target = Join-Path $PluginsDir $name

function Test-IsLink($path) {
    $item = Get-Item -LiteralPath $path -Force -ErrorAction SilentlyContinue
    return [bool]($item -and $item.LinkType)
}

function Remove-Target {
    if (Test-IsLink $target) {
        [System.IO.Directory]::Delete($target)   # removes the link only, never its content
    } else {
        Remove-Item -LiteralPath $target -Recurse -Force
    }
}

if ($Uninstall) {
    if (-not (Test-Path -LiteralPath $target)) { Fail "nothing to remove: $target does not exist" }
    if ((Test-IsLink $target) -and -not $Force) {
        Fail "$target is a link (a development install); use -Force to remove the link"
    }
    Remove-Target
    Write-Host "Removed $target"
    return
}

$tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("qswatmod2-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $tmp | Out-Null
try {
    if (-not $Zip) {
        # Windows gets the full ZIP: it holds the Windows SWAT-MODFLOW programs
        if (-not $Url) {
            if (-not $Version) {
                Write-Host "Looking for the latest release of $repo"
                $release = Invoke-RestMethod -UseBasicParsing -Headers @{ "User-Agent" = "install.ps1" } `
                    -Uri "https://api.github.com/repos/$repo/releases/latest"
                $Version = $release.tag_name
                if (-not $Version) { Fail "could not find the latest release" }
            }
            if (-not $Version.StartsWith("v")) { $Version = "v$Version" }
            $file = "$name.$($Version.Substring(1)).zip"
            $Url = "https://github.com/$repo/releases/download/$Version/$file"
        } else {
            $file = [System.IO.Path]::GetFileName(($Url -split "\?")[0])
        }
        $Zip = Join-Path $tmp $file
        Write-Host "Downloading $Url"
        try {
            Invoke-WebRequest -UseBasicParsing -Uri $Url -OutFile $Zip
        } catch {
            Fail "download failed (is there a release with ${file}?): $($_.Exception.Message)"
        }
        # verify with SHA256SUMS when the release has one
        $sums = Join-Path $tmp "SHA256SUMS"
        $sumsUrl = $Url.Substring(0, $Url.LastIndexOf("/")) + "/SHA256SUMS"
        $haveSums = $true
        try { Invoke-WebRequest -UseBasicParsing -Uri $sumsUrl -OutFile $sums } catch { $haveSums = $false }
        if ($haveSums) {
            $line = Get-Content $sums | Where-Object { $_ -match "\s\*?$([regex]::Escape($file))$" } | Select-Object -First 1
            if (-not $line) { Fail "$file is not listed in SHA256SUMS" }
            $expected = ($line -split "\s+")[0].ToLower()
            $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $Zip).Hash.ToLower()
            if ($expected -ne $actual) { Fail "checksum does not match" }
            Write-Host "SHA256 OK"
        } else {
            Write-Host "No SHA256SUMS next to the file: not verified"
        }
    }
    if (-not (Test-Path -LiteralPath $Zip -PathType Leaf)) { Fail "$Zip not found" }

    # the ZIP must hold one folder, QSWATMOD2/, with metadata.txt inside
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive = [System.IO.Compression.ZipFile]::OpenRead((Resolve-Path -LiteralPath $Zip).Path)
    try {
        $entries = $archive.Entries | ForEach-Object { $_.FullName }
    } finally {
        $archive.Dispose()
    }
    $tops = $entries | ForEach-Object { ($_ -split "/")[0] } | Sort-Object -Unique
    if (@($tops).Count -ne 1 -or $tops -ne $name -or -not ($entries -contains "$name/metadata.txt")) {
        Fail "$Zip is not a $name plugin ZIP (top-level: $(@($tops | Select-Object -First 3) -join ', '))"
    }

    if ((Test-Path -LiteralPath $target) -and (Test-IsLink $target) -and -not $Force) {
        Fail "$target is a link (a development install); use -Force to replace it"
    }
    New-Item -ItemType Directory -Force -Path $PluginsDir | Out-Null
    $unzipped = Join-Path $tmp "unzipped"
    Expand-Archive -LiteralPath $Zip -DestinationPath $unzipped -Force
    if (Test-Path -LiteralPath $target) { Remove-Target }
    Move-Item -LiteralPath (Join-Path $unzipped $name) -Destination $target

    $installed = (Get-Content (Join-Path $target "metadata.txt") | Where-Object { $_ -match "^version=" } |
        Select-Object -First 1) -replace "^version=", ""
    Write-Host "Installed $name $($installed.Trim()) in $target"
    Write-Host "Restart QGIS, then tick $name in Plugins > Manage and Install Plugins > Installed."
} finally {
    Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
}
