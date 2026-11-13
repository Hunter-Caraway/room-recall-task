# Sets up a private Python for the task in runtime\ next to Run Task.bat.
# Run once, automatically, by Run Task.bat. Needs internet; no admin rights; changes
# nothing outside this folder. Every download is checked against a fixed SHA-256.
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$root = Split-Path -Parent $PSScriptRoot
$runtime = Join-Path $root "runtime"
$python = Join-Path $runtime "python"
$downloads = Join-Path $runtime "downloads"

function Get-Checked($url, $name, $sha256) {
    $out = Join-Path $downloads $name
    Write-Host "  downloading $name"
    Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $out
    $hash = (Get-FileHash -Algorithm SHA256 $out).Hash
    if ($hash -ne $sha256.ToUpper()) {
        Remove-Item $out
        throw "$name did not match its expected checksum; not using it."
    }
    return $out
}

if (Test-Path $runtime) { Remove-Item -Recurse -Force $runtime }
New-Item -ItemType Directory -Force $python, $downloads | Out-Null

$zip = Get-Checked "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip" `
    "python-3.11.9-embed-amd64.zip" "009d6bf7e3b2ddca3d784fa09f90fe54336d5b60f0e0f305c37f400bf83cfd3b"
Expand-Archive -Path $zip -DestinationPath $python
# The portable Python ignores installed packages until "import site" is switched on.
$pth = Join-Path $python "python311._pth"
(Get-Content $pth) -replace "^#\s*import site", "import site" | Set-Content -Encoding ascii $pth

$pip = Get-Checked "https://files.pythonhosted.org/packages/b7/3f/945ef7ab14dc4f9d7f40288d2df998d1837ee0888ec3659c813487572faa/pip-25.2-py3-none-any.whl" `
    "pip-25.2-py3-none-any.whl" "6d67a2b4e7f14d8b31b8b52648866fa717f45a1eb70e83002f4331d07e953717"
Write-Host "  installing pygame and Pillow"
& (Join-Path $python "python.exe") "$pip/pip" install --disable-pip-version-check --no-warn-script-location `
    --only-binary ":all:" --require-hashes -r (Join-Path $PSScriptRoot "requirements-windows.txt")
if ($LASTEXITCODE -ne 0) { throw "Installing pygame and Pillow failed." }

Remove-Item -Recurse -Force $downloads
Set-Content -Encoding ascii (Join-Path $runtime "ready.txt") "python 3.11.9, pygame-ce 2.5.8, pillow 13.0.0"
Write-Host "  done"
