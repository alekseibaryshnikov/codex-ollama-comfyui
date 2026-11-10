param([string]$Scenario, [string]$Scratch)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\setup.ps1')
function Assert($condition, $message) { if (-not $condition) { throw $message } }
$root = Join-Path $Scratch 'Harness With Spaces'
$comfy = Join-Path $Scratch 'Comfy With Spaces'
$homePath = Join-Path $Scratch 'Profile\.codex'

if ($Scenario -in @('preview','approval')) {
    if ($Scenario -eq 'approval') {
        $result = Invoke-WindowsSetup -Root $root -Comfy $comfy -ProfileHome $homePath -Unattended
        Assert ($result.state -eq 'approval_required' -and $result.exit_code -eq 2) 'Unapproved unattended invocation reported success'
        Assert (-not (Test-Path $root)) 'Unapproved invocation wrote to disk'
        exit 0
    }
    $result = Invoke-WindowsSetup -Root $root -Comfy $comfy -ProfileHome $homePath -Preview
    Assert ($result.state -eq 'preview') 'Expected preview'
    Assert (-not (Test-Path $root)) 'Preview wrote to disk'
    Assert ($result.components -contains 'plugins') 'Plan omitted plugin restore'
    Assert ($result.components -contains 'native coder/reviewer') 'Plan omitted native roles'
    Assert (($result.components -join ' ') -notmatch 'Ollama|Qwen' -and $result.notes -notmatch '18 GB|Qwen') 'Plan requires local coding model'
    exit 0
}
if ($Scenario -eq 'native') {
    $child = Join-Path $Scratch 'fail.ps1'
    'Write-Output "Known child failure"; exit 7' | Set-Content -LiteralPath $child
    $failed = $false
    try { Invoke-SetupCommand -File 'powershell.exe' -Arguments @('-NoProfile', '-File', $child) | Out-Null }
    catch { $failed = $_.Exception.Message -match '7|Known child failure' }
    Assert $failed 'Native failure was hidden'
    $global:LASTEXITCODE = 0
    $failed = $false
    try { Invoke-SetupCommand -File 'missing-harness-test-command.exe' -Arguments @() | Out-Null }
    catch { $failed = $true }
    Assert $failed 'Missing executable inherited a successful exit status'
    $success = Join-Path $Scratch 'success.ps1'
    'Write-Output "Visible login fixture"; exit 0' | Set-Content -LiteralPath $success
    $nativeResult = @(Invoke-SetupCommand -File 'powershell.exe' -Arguments @('-NoProfile','-File',$success) -Interactive)
    Assert ($nativeResult.Count -eq 1 -and $nativeResult[0].Code -eq 0) 'Interactive output contaminated command result'
    exit 0
}
if ($Scenario -eq 'python-base') {
    $env:LOCALAPPDATA = $Scratch
    $candidate = Join-Path $Scratch 'Programs\Python\Python312\python.exe'
    $baseInterpreter = Join-Path $Scratch 'Base\python.exe'
    $null = New-Item -ItemType Directory -Path (Split-Path $candidate) -Force
    $null = New-Item -ItemType Directory -Path (Split-Path $baseInterpreter) -Force
    '' | Set-Content -LiteralPath $candidate; '' | Set-Content -LiteralPath $baseInterpreter
    function Get-Command { return $null }
    function Invoke-SetupCommand {
        param($File, $Arguments, [switch]$AllowFailure, [switch]$Capture)
        return [pscustomobject]@{ Code = 0; Output = $baseInterpreter }
    }
    Assert ((Find-SetupPython) -eq $baseInterpreter) 'Supervisor would launch through an unverified venv redirector'
    exit 0
}
if ($Scenario -eq 'ownership') {
    $managedPython = Join-Path $comfy 'python\Scripts\python.exe'
    $basePython = Join-Path $Scratch 'Base Python\python.exe'
    $mainFile = Join-Path $comfy 'app\main.py'
    $argv = '"' + $managedPython + '" -B "' + $mainFile + '" --listen 127.0.0.1 --port 8189 --reserve-vram 3.5 --offline'
    $owned = [pscustomobject]@{ pid = 100 }
    $supervisor = [pscustomobject]@{ StartTime = [DateTime]::UtcNow.AddSeconds(-10) }
    $listener = [pscustomobject]@{ OwningProcess = 300; LocalAddress = '127.0.0.1' }
    $script:worker = [pscustomobject]@{ ProcessId = 300; ParentProcessId = 200; ExecutablePath = $basePython; CommandLine = $argv.Replace($managedPython,$basePython); CreationDate = [DateTime]::UtcNow }
    $script:shim = [pscustomobject]@{ ProcessId = 200; ParentProcessId = 100; ExecutablePath = $managedPython; CommandLine = $argv; CreationDate = [DateTime]::UtcNow.AddSeconds(-1) }
    function Get-CimInstance { param($ClassName, $Filter); if ($Filter -eq 'ProcessId=300') { return $script:worker }; if ($Filter -eq 'ProcessId=200') { return $script:shim }; throw 'Unexpected process lookup' }
    Assert-SetupComfyListener $listener $owned $supervisor $comfy $basePython
    $script:worker.CommandLine = $script:worker.CommandLine.Replace($mainFile,$mainFile.ToLowerInvariant())
    Assert-SetupComfyListener $listener $owned $supervisor $comfy $basePython
    $script:worker.ParentProcessId = 100; $script:worker.ExecutablePath = $managedPython; $script:worker.CommandLine = $argv
    Assert-SetupComfyListener $listener $owned $supervisor $comfy $basePython
    $script:worker.CommandLine += ' --extra-unsafe-argument'
    $failed = $false
    try { Assert-SetupComfyListener $listener $owned $supervisor $comfy $basePython } catch { $failed = $true }
    Assert $failed 'Extra app arguments accepted'
    $script:worker.CommandLine = $argv.Replace($managedPython,$basePython); $script:worker.ParentProcessId = 200; $script:worker.ExecutablePath = $basePython
    $script:shim.ParentProcessId = 999
    $failed = $false
    try { Assert-SetupComfyListener $listener $owned $supervisor $comfy $basePython } catch { $failed = $true }
    Assert $failed 'Unrelated redirector ancestor accepted'
    exit 0
}
if ($Scenario -eq 'foreign') {
    function Get-SetupJson { return @{ system = @{ os = 'fixture' } } }
    function Get-SetupListeners { return @([pscustomobject]@{ OwningProcess = 999999; LocalAddress = '127.0.0.1' }) }
    $failed = $false
    try { Start-SetupComfy -Root $root -Python 'python.exe' -Comfy $comfy | Out-Null }
    catch { $failed = $_.Exception.Message -match 'unrelated|foreign|owned' }
    Assert $failed 'Foreign listener was accepted or interrupted'
    $failed = $false
    try { Assert-SetupPath -Path (Join-Path $Scratch '..\escape') }
    catch { $failed = $true }
    Assert $failed 'Parent path segment accepted'
    exit 0
}

# Remaining cases exercise actual orchestration, with all external boundaries replaced.
$script:calls = @()
function Install-SetupTools { $script:calls += 'tools'; return @{ Python = 'fixture-python'; Codex = 'fixture-codex' } }
function Get-SetupRepository { param($Root); if ($Scenario -eq 'refused-root') { throw 'Preserving unrelated repository' }; $null = New-Item -ItemType Directory -Path $Root -Force; return $Root }
function Test-SetupHardware { $script:calls += 'hardware' }
function Ensure-SetupCodexLogin { param($Codex, $Unattended); if ($Scenario -eq 'accounts') { throw 'ChatGPT sign-in needed' }; $script:calls += 'codex-login' }
function Ensure-SetupHuggingFaceLogin { param($Comfy, $Unattended); if ($Scenario -eq 'accounts') { throw 'Hugging Face sign-in needed' }; $script:calls += 'hf-login' }
function Start-SetupOllama { $script:calls += 'ollama-service' }
function Start-SetupComfy { $script:calls += 'comfy-service' }
function Invoke-SetupCommand {
    param($File, $Arguments, [switch]$AllowFailure, [switch]$Capture, [switch]$Interactive)
    $script:calls += ($Arguments -join ' ')
    if (($Arguments -contains 'comfy') -and $Scenario -eq 'failure') { throw 'Preserving unrelated environment' }
    if (($Arguments -contains '--plugins') -and $Scenario -eq 'accounts') {
        throw 'plugins incomplete: Missing catalog'
    }
    return [pscustomobject]@{ Code = 0; Output = '{"ready":true}' }
}

$null = New-Item -ItemType Directory -Path (Join-Path $root 'examples') -Force
$template = '{"tests":false,"terra_coder":false,"terra":false,"astra":false,"image":false,"image_edit":false,"video":false,"video_edit":false,"music":false,"sfx":false,"speech":false}'
$template | Set-Content -LiteralPath (Join-Path $root 'examples\activation-evidence.json')
$evidenceFile = Join-Path $root 'work\activation-evidence.json'
if ($Scenario -eq 'redirected-work') {
    $outside = Join-Path $Scratch 'Unrelated Files'
    $null = New-Item -ItemType Directory -Path $outside -Force
    try { $null = New-Item -ItemType Junction -Path (Join-Path $root 'work') -Value $outside }
    catch { Write-Host 'Host does not permit the junction fixture'; exit 77 }
    $result = Invoke-WindowsSetup -Root $root -Comfy $comfy -ProfileHome $homePath -Consent -Unattended
    Assert ($result.state -eq 'failed') 'Redirected work folder accepted'
    Assert (@(Get-ChildItem -LiteralPath $outside -Force).Count -eq 0) 'Wrote through ignored work junction'
    exit 0
}
if ($Scenario -eq 'refused-root') {
    $oldReports = Join-Path $root 'work\windows-setup'
    $null = New-Item -ItemType Directory -Path $oldReports -Force
    'Operator JSON report' | Set-Content -LiteralPath (Join-Path $oldReports 'report.json')
    'Operator HTML report' | Set-Content -LiteralPath (Join-Path $oldReports 'report.html')
    $result = Invoke-WindowsSetup -Root $root -Comfy $comfy -ProfileHome $homePath -Consent -Unattended
    Assert ($result.state -eq 'failed') 'Refused checkout reported success'
    Assert ((Get-Content -LiteralPath (Join-Path $oldReports 'report.json') -Raw).Trim() -eq 'Operator JSON report') 'Unrelated JSON overwritten'
    Assert ((Get-Content -LiteralPath (Join-Path $oldReports 'report.html') -Raw).Trim() -eq 'Operator HTML report') 'Unrelated HTML overwritten'
    exit 0
}
if ($Scenario -eq 'evidence') {
    $null = New-Item -ItemType Directory -Path (Split-Path $evidenceFile) -Force
    '{"tests":true,"custom":"keep me"}' | Set-Content -LiteralPath $evidenceFile
    $original = [IO.File]::ReadAllBytes($evidenceFile)
    Set-Location -LiteralPath $Scratch
    $result = Invoke-WindowsSetup -Root $root -Comfy $comfy -ProfileHome $homePath -Consent -Unattended -EvidenceFile 'Harness With Spaces\work\activation-evidence.json'
    Assert ([Convert]::ToBase64String($original) -eq [Convert]::ToBase64String([IO.File]::ReadAllBytes($evidenceFile))) 'Operator evidence overwritten'
    Assert (@($script:calls | Where-Object { $_ -match 'install.py activate' }).Count -eq 1) 'Explicit activation not delegated to the real evidence gate'
    Assert (@($script:calls | Where-Object { $_.EndsWith($evidenceFile) }).Count -eq 1) 'Evidence path was rebased to checkout instead of caller'
    exit 0
}
$result = Invoke-WindowsSetup -Root $root -Comfy $comfy -ProfileHome $homePath -Consent -Unattended
if ($Scenario -eq 'failure') {
    Assert ($result.state -eq 'failed') 'Critical failure hidden'
    Assert (@($script:calls | Where-Object { $_ -match 'models|hf-login|comfy-service' }).Count -eq 0) 'Executed refused Comfy environment'
    Assert (Test-Path (Join-Path $root 'work\windows-setup\report.html')) 'Failure report absent'
    exit 0
}
Assert (Test-Path (Join-Path $root 'work\windows-setup\report.json')) 'JSON report absent'
Assert (Test-Path (Join-Path $root 'work\windows-setup\report.html')) 'HTML report absent'
Assert ($env:CODEX_HOME -ne $homePath) 'Selected profile leaked to caller'
if ($Scenario -eq 'accounts') {
    Assert ($result.exit_code -eq 2) 'Partial install reported complete'
    Assert (@($result.pending | Where-Object { $_ -match 'ChatGPT|Hugging Face|plugins' }).Count -ge 3) 'Account/plugin failures hidden'
    Assert ($script:calls -notcontains 'ollama-service') 'Touched Ollama during account failure'
    exit 0
}
Assert ($script:calls -notcontains 'ollama-service') 'Started existing Ollama'
Assert (@($script:calls | Where-Object { $_ -match 'bootstrap.py ollama' }).Count -eq 0) 'Modified Ollama models'
Assert ($result.state -eq 'needs_verification') 'Installation invented smoke success'
Assert ((Get-Content -LiteralPath $evidenceFile -Raw | ConvertFrom-Json).tests -eq $false) 'Synthetic verification evidence'
Assert (@($script:calls | Where-Object { $_ -match 'restore_skills.py.*--plugins' }).Count -eq 1) 'Plugins omitted'
Assert (@($script:calls | Where-Object { $_ -match 'restore_skills.py' }).Count -eq 2) 'Standalone skills omitted'
Assert (@($script:calls | Where-Object { $_ -match 'install.py stage.*--codex-home' }).Count -eq 1) 'Native agents/profile omitted'
Assert (@($script:calls | Where-Object { $_ -match 'install.py activate' }).Count -eq 0) 'Ungated activation'
$comfyIndex = -1; $modelsIndex = -1
for ($i=0; $i -lt $script:calls.Count; $i++) {
    if ($script:calls[$i] -match 'bootstrap.py comfy ') { $comfyIndex=$i }
    if ($script:calls[$i] -match 'bootstrap.py models ') { $modelsIndex=$i }
}
Assert ($comfyIndex -ge 0 -and $modelsIndex -gt $comfyIndex) 'Provisioning preceded managed environment validation'
Assert (@($script:calls | Where-Object { $_ -match 'torch.cuda.is_available' }).Count -eq 1) 'CUDA runtime not checked before model download'
