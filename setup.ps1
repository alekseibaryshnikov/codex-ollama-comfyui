<#
WINSETUP-1: One Windows PowerShell 5.1 entry installs prerequisites, checks out
the repository, configures an owned Comfy environment, restores skills/plugins,
provisions models, starts local services and verifies the installation. Preview
is read-only; native failures stop dependent work and survive in JSON/HTML reports.
WINSETUP-2: Reruns revalidate live state. Preserve existing repositories, foreign
listeners and edited activation evidence. Never invent successful smoke evidence.
Reports for a refused checkout go to a new sibling directory, never inside it.
Validate ignored work/report/log/evidence paths before writing through them.
Comfy must pass an actual CUDA operation before model downloads. A failed Ollama
version/ownership check blocks all subsequent model-alias changes.
WINSETUP-3: Use one selected Codex profile and ChatGPT login. Account access may
need human action; unattended mode reports it instead of waiting for input.
Long-running services don't inherit access tokens. Never restart unrelated work.
Resolve an explicitly supplied evidence path against the caller's directory,
before entering the checkout. Unattended mode without approval exits 2 read-only.
WINSETUP-4: Accept only the owned supervisor's direct managed Python child or
its measured Windows venv redirector/base-interpreter chain, with exact argv,
interpreter paths and creation ordering. Refuse all unrelated listener shapes.
Windows path arguments compare without case; app flags and values compare exactly.
Evidence: tests/test_windows_setup.py and tests/windows_setup_cases.ps1 exercise
real PowerShell and temporary files with software/network boundaries replaced.
They do not prove a clean OS install or model inference.
#>
[CmdletBinding()]
param(
    [string]$InstallRoot = (Join-Path $env:USERPROFILE 'Documents\Codex\codex-ollama-comfyui'),
    [string]$ComfyRoot = (Join-Path $env:USERPROFILE 'AI\ComfyUI'),
    [string]$CodexHome = $(if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }),
    [switch]$Plan,
    [switch]$Approved,
    [switch]$NonInteractive,
    [string]$Evidence
)

function Invoke-WindowsSetup {
    param([string]$Root, [string]$Comfy, [string]$ProfileHome, [switch]$Preview,
          [switch]$Consent, [switch]$Unattended, [string]$EvidenceFile)
    $components = @('Git', 'Python 3.12 x64', 'Codex desktop', 'Codex CLI', 'Ollama',
                    'ComfyUI', 'models', 'skills', 'plugins', 'Astra/Terra', 'verification')
    if ($Preview -or (-not $Consent -and $Unattended)) {
        return [pscustomobject]@{ state = $(if ($Preview) { 'preview' } else { 'approval_required' }); exit_code = $(if ($Preview) { 0 } else { 2 }); components = $components;
            install_root = $Root; comfy_root = $Comfy; codex_home = $ProfileHome;
            notes = 'About 88 GB media weights plus 18 GB Qwen, Python/CUDA and temporary files. Allow 200 GB free. App Installer, NVIDIA driver, sign-in and model access are required.' }
    }
    if (-not $Consent) {
        Write-Host 'Install Git, Python, Codex desktop/CLI, Ollama, ComfyUI, models, skills and plugins.'
        Write-Host 'About 88 GB media weights plus 18 GB Qwen and dependencies. Allow 200 GB free.'
        Write-Host 'WinGet package/source terms will be accepted. Model terms and account sign-in remain yours.'
        if ((Read-Host 'Continue? [y/N]') -notmatch '^(y|yes)$') {
            return [pscustomobject]@{ state = 'cancelled'; exit_code = 2 }
        }
    }
    $ErrorActionPreference = 'Stop'
    $script:SetupSteps = @(); $script:SetupPending = @(); $script:SetupLog = $null
    $oldProfile = $env:CODEX_HOME
    $location = Get-Location
    $state = 'failed'; $code = 1; $pathsValid = $false; $reportDirectory = $null
    try {
        Assert-SetupPath $Root; Assert-SetupPath $Comfy; Assert-SetupPath $ProfileHome
        $Root = [IO.Path]::GetFullPath($Root); $Comfy = [IO.Path]::GetFullPath($Comfy); $ProfileHome = [IO.Path]::GetFullPath($ProfileHome)
        if ($EvidenceFile) { $EvidenceFile = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($EvidenceFile) }
        $pathsValid = $true
        $env:CODEX_HOME = $ProfileHome
        Invoke-SetupStep 'hardware' { Test-SetupHardware }
        $tools = Install-SetupTools
        $Root = Get-SetupRepository $Root
        Set-Location -LiteralPath $Root
        $reportDir = Join-Path $Root 'work\windows-setup'
        Assert-SetupPath $reportDir
        foreach ($file in @('commands.log','report.json','report.html')) { Assert-SetupPath (Join-Path $reportDir $file) }
        $reportDirectory = $reportDir
        $null = New-Item -ItemType Directory -Path $reportDir -Force
        $script:SetupLog = Join-Path $reportDir 'commands.log'
        Invoke-SetupStep 'configuration' { Invoke-SetupCommand $tools.Python @('-E','-s','-B','bootstrap.py','configure','--comfy-root',$Comfy) }
        # A refused environment must never reach login, provision or run-comfy.
        Invoke-SetupStep 'ComfyUI environment' { Invoke-SetupCommand $tools.Python @('-E','-s','-B','bootstrap.py','comfy','--approved') }
        Invoke-SetupStep 'CUDA runtime' { Invoke-SetupCommand (Join-Path $Comfy 'python\Scripts\python.exe') @('-I','-c','import torch;assert torch.cuda.is_available();print(torch.ones(1).cuda().sum().item())') }
        Invoke-SetupStep 'skills' { Invoke-SetupCommand $tools.Python @('-E','-s','-B','restore_skills.py','--approved','--codex-home',$ProfileHome) }
        Invoke-SetupStep 'native agents' { Invoke-SetupCommand $tools.Python @('-E','-s','-B','install.py','stage','--codex-home',$ProfileHome) }
        $privateEvidence = Join-Path $Root 'work\activation-evidence.json'
        Assert-SetupPath $privateEvidence
        if (-not (Test-Path -LiteralPath $privateEvidence)) {
            Copy-Item -LiteralPath (Join-Path $Root 'examples\activation-evidence.json') -Destination $privateEvidence
        }
        Invoke-SetupStep 'ChatGPT sign-in' { Ensure-SetupCodexLogin $tools.Codex $Unattended } -Optional
        Invoke-SetupStep 'plugins' { Invoke-SetupCommand $tools.Python @('-E','-s','-B','restore_skills.py','--plugins','--approved','--codex-home',$ProfileHome) } -Optional
        Invoke-SetupStep 'Hugging Face sign-in' { Ensure-SetupHuggingFaceLogin $Comfy $Unattended } -Optional
        if ($script:SetupSteps[-1].state -eq 'passed') {
            Invoke-SetupStep 'models' { Invoke-SetupCommand $tools.Python @('-E','-s','-B','bootstrap.py','models','--approved') } -Optional
        }
        Invoke-SetupStep 'Ollama service' { Start-SetupOllama $tools.Ollama $Root } -Optional
        if ($script:SetupSteps[-1].state -eq 'passed') {
            Invoke-SetupStep 'Qwen' { Invoke-SetupCommand $tools.Python @('-E','-s','-B','bootstrap.py','ollama','--approved') } -Optional
        }
        Invoke-SetupStep 'ComfyUI service' { Start-SetupComfy $Root $tools.Python $Comfy } -Optional
        Invoke-SetupStep 'service verification' { Invoke-SetupCommand $tools.Python @('-E','-s','-B','bootstrap.py','verify') } -Optional
        if ($EvidenceFile -and $script:SetupPending.Count -eq 0) {
            Invoke-SetupStep 'routing activation' { Invoke-SetupCommand $tools.Python @('-E','-s','-B','install.py','activate','--codex-home',$ProfileHome,'--evidence',[IO.Path]::GetFullPath($EvidenceFile)) }
            $state = 'complete'; $code = 0
        } else {
            $script:SetupPending += 'Run destination smoke checks in docs/verification.md, then rerun this script with -Evidence work\activation-evidence.json to enable global routing.'
            $state = 'needs_verification'; $code = 2
        }
    } catch {
        $script:SetupPending += $_.Exception.Message
        Write-Host $_.Exception.Message
    } finally {
        $env:CODEX_HOME = $oldProfile
        Set-Location -LiteralPath $location.Path
    }
    if (-not $reportDirectory -and $pathsValid) {
        $reportDirectory = Join-Path (Split-Path -Parent $Root) ('codex-setup-report-' + [Guid]::NewGuid().ToString('N'))
    }
    $result = [pscustomobject]@{ state = $state; exit_code = $code; install_root = $Root; report_directory = $reportDirectory;
        comfy_root = $Comfy; codex_home = $ProfileHome; steps = @($script:SetupSteps);
        pending = @($script:SetupPending); note = 'Installation checks do not prove inference, artistic quality, native agent availability or fresh-account skill discovery.' }
    if ($reportDirectory) { Write-SetupReport $reportDirectory $result }
    return $result
}

function Invoke-SetupStep {
    param([string]$Name, [scriptblock]$Action, [switch]$Optional)
    Write-Host "`n[$Name]"
    try {
        $null = & $Action
        $script:SetupSteps += [pscustomobject]@{ name = $Name; state = 'passed' }
    } catch {
        $message = $Name + ': ' + $_.Exception.Message
        $script:SetupSteps += [pscustomobject]@{ name = $Name; state = 'failed'; error = $_.Exception.Message }
        if (-not $Optional) { throw }
        $script:SetupPending += $message
        Write-Host $message
    }
}

function Write-SetupReport {
    param([string]$Directory, $Result)
    Assert-SetupPath $directory
    foreach ($file in @('report.json','report.html')) { Assert-SetupPath (Join-Path $directory $file) }
    $null = New-Item -ItemType Directory -Path $directory -Force
    $encoding = New-Object Text.UTF8Encoding($false)
    [IO.File]::WriteAllText((Join-Path $directory 'report.json'), ($Result | ConvertTo-Json -Depth 12), $encoding)
    $rows = ($Result.steps | ForEach-Object { '<tr><td>' + [Net.WebUtility]::HtmlEncode($_.name) + '</td><td>' + $_.state + '</td></tr>' }) -join ''
    $pending = ($Result.pending | ForEach-Object { '<li>' + [Net.WebUtility]::HtmlEncode($_) + '</li>' }) -join ''
    $html = '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Windows setup report</title><style>body{font:16px system-ui;max-width:950px;margin:40px auto;padding:20px;background:#f3f6f2;color:#193b35}table{width:100%;border-collapse:collapse}td{border-bottom:1px solid #cddad2;padding:12px}li{margin:12px 0;overflow-wrap:anywhere}</style><h1>Windows setup</h1><p>' + $Result.state + '</p><table>' + $rows + '</table><h2>Next steps</h2><ul>' + $pending + '</ul><p>' + $Result.note + '</p></html>'
    [IO.File]::WriteAllText((Join-Path $directory 'report.html'), $html, $encoding)
    Write-Host ('Report: ' + (Join-Path $directory 'report.html'))
}

function Invoke-SetupCommand {
    param([string]$File, [string[]]$Arguments, [switch]$AllowFailure, [switch]$Capture, [switch]$Interactive)
    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $lines = New-Object 'Collections.Generic.List[string]'
    try {
        if ($Interactive) {
            & $File @Arguments | Out-Host
        } else {
            & $File @Arguments 2>&1 | ForEach-Object {
                $line = $_.ToString(); $lines.Add($line)
                if (-not $Capture) { Write-Host $line }
                if ($script:SetupLog) { Add-Content -LiteralPath $script:SetupLog -Value $line -Encoding UTF8 }
            }
        }
        $nativeCode = $LASTEXITCODE
    } finally { $ErrorActionPreference = $previousPreference }
    $text = $lines -join "`n"
    if ($nativeCode -ne 0 -and -not $AllowFailure) {
        throw ('Command failed (' + $nativeCode + '): ' + [IO.Path]::GetFileName($File) + ' ' + ($Arguments -join ' ') + "`n" + (($lines | Select-Object -Last 8) -join "`n"))
    }
    return [pscustomobject]@{ Code = $nativeCode; Output = $text }
}

function Assert-SetupPath {
    param([string]$Path)
    if (-not [IO.Path]::IsPathRooted($Path) -or $Path -match '(^|[\\/])\.\.([\\/]|$)' -or $Path.StartsWith('\\')) {
        throw ('Use an absolute local path without parent segments: ' + $Path)
    }
    $item = [IO.Path]::GetFullPath($Path)
    while ($item) {
        if (Test-Path -LiteralPath $item) {
            if (((Get-Item -LiteralPath $item -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw ('Preserving redirected setup path: ' + $item)
            }
        }
        $item = Split-Path -Parent $item
    }
}

function Update-SetupPath {
    $env:PATH = (($env:PATH + ';' + [Environment]::GetEnvironmentVariable('PATH','User') + ';' + [Environment]::GetEnvironmentVariable('PATH','Machine')).Split(';') | Select-Object -Unique) -join ';'
}

function Find-SetupPython {
    $candidates = @((Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'))
    if (Get-Command py.exe -ErrorAction SilentlyContinue) {
        $result = Invoke-SetupCommand 'py.exe' @('-3.12','-E','-s','-c','import sys;print(sys.executable)') -AllowFailure -Capture
        if ($result.Code -eq 0) { $candidates += $result.Output.Trim() }
    }
    $command = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($command -and $command.Source -notmatch 'WindowsApps') { $candidates += $command.Source }
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            $result = Invoke-SetupCommand $candidate @('-E','-s','-c',"import sys,struct;sys.exit(0 if sys.version_info[:2]==(3,12) and struct.calcsize('P')==8 else 1)") -AllowFailure -Capture
            if ($result.Code -eq 0) {
                $base = Invoke-SetupCommand $candidate @('-E','-s','-c','import sys;print(sys._base_executable)') -Capture
                $basePath = $base.Output.Trim()
                if (Test-Path -LiteralPath $basePath -PathType Leaf) {
                    $check = Invoke-SetupCommand $basePath @('-E','-s','-c',"import sys,struct;sys.exit(0 if sys.version_info[:2]==(3,12) and struct.calcsize('P')==8 else 1)") -AllowFailure -Capture
                    if ($check.Code -eq 0) { return $basePath }
                }
            }
        }
    }
    return $null
}

function Install-SetupPackage {
    param([string]$Id, [string]$Source = 'winget', [string]$Version)
    $arguments = @('install','--id',$Id,'--exact','--source',$Source,'--accept-package-agreements','--accept-source-agreements','--disable-interactivity','--no-upgrade')
    if ($Source -eq 'winget') { $arguments += @('--architecture','x64','--scope','user','--silent') }
    if ($Version) { $arguments += @('--version',$Version) }
    $result = Invoke-SetupCommand 'winget.exe' $arguments -AllowFailure
    # WinGet's already-installed code is accepted only with later tool checks.
    if ($result.Code -notin @(0,-1978335189)) { throw ('WinGet failed for ' + $Id + ' (' + $result.Code + '). Inspect its output, complete any reboot, then rerun.') }
    Update-SetupPath
}

function Test-SetupHardware {
    if ($env:OS -ne 'Windows_NT' -or $env:PROCESSOR_ARCHITECTURE -ne 'AMD64' -or [IntPtr]::Size -ne 8) {
        throw 'Run 64-bit Windows PowerShell on Windows x86-64.'
    }
    $gpu = Get-Command nvidia-smi.exe -ErrorAction SilentlyContinue
    if (-not $gpu) { throw 'Install the compatible NVIDIA driver, reboot, then rerun. This CUDA 13 setup was calibrated on an RTX 5080 with 16 GB VRAM and about 64 GB RAM.' }
    $null = Invoke-SetupCommand $gpu.Source @('--query-gpu=name,memory.total,driver_version','--format=csv,noheader')
}

function Install-SetupTools {
    if (-not (Get-Command winget.exe -ErrorAction SilentlyContinue)) {
        throw 'Install/update App Installer from Microsoft Store, open a new terminal and rerun: https://apps.microsoft.com/detail/9nblggh4nns1'
    }
    if (-not (Get-Command git.exe -ErrorAction SilentlyContinue)) { Install-SetupPackage 'Git.Git' }
    if (-not (Find-SetupPython)) { Install-SetupPackage 'Python.Python.3.12' }
    if (-not (Get-Command codex.exe -ErrorAction SilentlyContinue)) { Install-SetupPackage 'OpenAI.Codex' }
    if (-not (Get-AppxPackage -Name OpenAI.Codex -ErrorAction SilentlyContinue)) { Install-SetupPackage '9PLM9XGG6VKS' 'msstore' }
    if (-not (Get-Command ollama.exe -ErrorAction SilentlyContinue)) { Install-SetupPackage 'Ollama.Ollama' 'winget' '0.40.16' }
    $python = Find-SetupPython
    $codex = Get-Command codex.exe -ErrorAction SilentlyContinue
    $ollama = Get-Command ollama.exe -ErrorAction SilentlyContinue
    if (-not $python -or -not $codex -or -not $ollama -or -not (Get-Command git.exe -ErrorAction SilentlyContinue)) {
        throw 'A prerequisite is not available after installation. Open a new 64-bit PowerShell terminal and rerun.'
    }
    if (-not (Get-AppxPackage -Name OpenAI.Codex -ErrorAction SilentlyContinue)) { throw 'Codex desktop installation is not registered for this Windows account.' }
    return @{ Python = $python; Codex = $codex.Source; Ollama = $ollama.Source }
}

function Get-SetupRepository {
    param([string]$Root)
    $remote = 'https://github.com/alekseibaryshnikov/codex-ollama-comfyui.git'
    if (-not (Test-Path -LiteralPath $Root)) {
        $null = Invoke-SetupCommand 'git.exe' @('clone','--branch','main',$remote,$Root)
    } else {
        $origin = Invoke-SetupCommand 'git.exe' @('-C',$Root,'remote','get-url','origin') -Capture
        if ($origin.Output.Trim() -notin @($remote,'git@github.com:alekseibaryshnikov/codex-ollama-comfyui.git')) { throw 'Preserving unrelated installation directory: unexpected Git origin.' }
        $dirty = Invoke-SetupCommand 'git.exe' @('-C',$Root,'status','--porcelain','--untracked-files=normal') -Capture
        if ($dirty.Output.Trim()) { throw 'Preserving repository edits. Commit or move them before rerunning setup.' }
    }
    foreach ($file in @('bootstrap.py','restore_skills.py','install.py','locks\runtime.json','setup.ps1')) {
        if (-not (Test-Path -LiteralPath (Join-Path $Root $file) -PathType Leaf)) { throw ('Installation checkout is incomplete: ' + $file) }
    }
    return $Root
}

function Ensure-SetupCodexLogin {
    param([string]$Codex, [bool]$Unattended)
    $null = New-Item -ItemType Directory -Path $env:CODEX_HOME -Force
    $savedLog = $script:SetupLog; $script:SetupLog = $null
    try {
        $status = Invoke-SetupCommand $Codex @('login','status') -AllowFailure -Capture
        if ($status.Code -eq 0 -and $status.Output -match 'ChatGPT') { return }
        if ($Unattended) { throw 'ChatGPT sign-in needed: run codex login with the selected CODEX_HOME, then rerun.' }
        Write-Host 'Sign into Codex with ChatGPT in the browser. API-key access is not used by this harness.'
        $null = Invoke-SetupCommand $Codex @('login') -Interactive
        $status = Invoke-SetupCommand $Codex @('login','status') -Capture
        if ($status.Output -notmatch 'ChatGPT') { throw 'Codex login is not signed-in ChatGPT access.' }
    } finally { $script:SetupLog = $savedLog }
}

function Ensure-SetupHuggingFaceLogin {
    param([string]$Comfy, [bool]$Unattended)
    $hf = Join-Path $Comfy 'python\Scripts\hf.exe'
    $savedLog = $script:SetupLog; $script:SetupLog = $null
    try {
        $status = Invoke-SetupCommand $hf @('auth','whoami') -AllowFailure -Capture
        if ($status.Code -eq 0) { return }
        if ($Unattended) { throw 'Hugging Face sign-in needed. Use the installed environment hf auth login, or provide HF_TOKEN locally.' }
        Write-Host 'Accept the model terms on your Hugging Face account, then log in locally.'
        Write-Host 'https://huggingface.co/Lightricks/LTX-2.5'
        Write-Host 'https://huggingface.co/stabilityai/stable-audio-open-1.0'
        $null = Invoke-SetupCommand $hf @('auth','login') -Interactive
    } finally { $script:SetupLog = $savedLog }
}

function Get-SetupJson {
    param([string]$Url)
    $request = [Net.HttpWebRequest]::Create($Url); $request.Proxy = $null
    $request.Timeout = 2000
    $response = $request.GetResponse()
    try {
        $reader = New-Object IO.StreamReader($response.GetResponseStream())
        try { return ($reader.ReadToEnd() | ConvertFrom-Json) } finally { $reader.Dispose() }
    } finally { $response.Dispose() }
}

function Get-SetupListeners {
    param([int]$Port)
    return @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

function Start-SetupProcess {
    param([string]$File, [string[]]$Arguments, [string]$Root, [string]$Name)
    foreach ($stream in @('stdout','stderr')) { Assert-SetupPath (Join-Path $Root ('work\windows-setup\' + $Name + '.' + $stream + '.log')) }
    $saved = @{}
    foreach ($key in @('HF_TOKEN','HUGGING_FACE_HUB_TOKEN','OPENAI_API_KEY','ANTHROPIC_API_KEY','GH_TOKEN','GITHUB_TOKEN','OLLAMA_API_KEY','PYTHONHOME','PYTHONPATH','VIRTUAL_ENV','OLLAMA_HOST')) {
        $saved[$key] = [Environment]::GetEnvironmentVariable($key,'Process')
        [Environment]::SetEnvironmentVariable($key,$null,'Process')
    }
    try {
        $env:OLLAMA_HOST = '127.0.0.1:11434'
        return Start-Process -FilePath $File -ArgumentList $Arguments -WorkingDirectory $Root -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $Root ('work\windows-setup\' + $Name + '.stdout.log')) -RedirectStandardError (Join-Path $Root ('work\windows-setup\' + $Name + '.stderr.log'))
    } finally {
        foreach ($key in $saved.Keys) { [Environment]::SetEnvironmentVariable($key,$saved[$key],'Process') }
    }
}

function Start-SetupOllama {
    param([string]$Ollama, [string]$Root)
    $expected = (Get-Content -LiteralPath (Join-Path $Root 'locks\runtime.json') -Raw | ConvertFrom-Json).ollama.version
    $version = $null
    try { $version = Get-SetupJson 'http://127.0.0.1:11434/api/version' } catch {}
    if (-not $version) {
        if (@(Get-SetupListeners 11434).Count -ne 0) { throw 'Port 11434 belongs to an unrelated or unready service; preserving it.' }
        $null = Start-SetupProcess $Ollama @('serve') $Root 'ollama'
        $deadline = [DateTime]::UtcNow.AddSeconds(120)
        do {
            try { $version = Get-SetupJson 'http://127.0.0.1:11434/api/version' } catch {}
            if (-not $version) { Start-Sleep -Milliseconds 500 }
        } until ($version -or [DateTime]::UtcNow -gt $deadline)
    }
    if (-not $version -or $version.version -ne $expected) { throw ('Expected Ollama ' + $expected + ' on loopback 11434. Preserve an existing different version; reconcile it explicitly before rerunning.') }
}

function Start-SetupComfy {
    param([string]$Root, [string]$Python, [string]$Comfy)
    $receipt = Join-Path $Root 'work\windows-setup\comfy-service.json'
    Assert-SetupPath $receipt
    $listeners = @(Get-SetupListeners 8189)
    if ($listeners.Count -eq 0) {
        $process = Start-SetupProcess $Python @('-E','-s','-B','bootstrap.py','run-comfy') $Root 'comfy'
        @{ pid = $process.Id; started = $process.StartTime.ToUniversalTime().Ticks.ToString() } | ConvertTo-Json | Set-Content -LiteralPath $receipt -Encoding UTF8
        $deadline = [DateTime]::UtcNow.AddSeconds(120)
        do {
            $listeners = @(Get-SetupListeners 8189)
            if ($listeners.Count -eq 0) { Start-Sleep -Milliseconds 500 }
            if ($process.HasExited) { throw 'Owned ComfyUI launcher exited; inspect work/windows-setup/comfy.stderr.log.' }
        } until ($listeners.Count -gt 0 -or [DateTime]::UtcNow -gt $deadline)
    }
    if (-not (Test-Path -LiteralPath $receipt)) { throw 'Port 8189 belongs to an unrelated service; no owned ComfyUI receipt.' }
    $owned = Get-Content -LiteralPath $receipt -Raw | ConvertFrom-Json
    $supervisor = Get-Process -Id $owned.pid -ErrorAction SilentlyContinue
    if (-not $supervisor -or $supervisor.StartTime.ToUniversalTime().Ticks.ToString() -ne $owned.started) { throw 'ComfyUI listener is not owned by this setup process receipt.' }
    if ($listeners.Count -eq 0) { throw 'Owned ComfyUI startup timed out. Inspect the service logs; no unrelated service was stopped.' }
    $base = Invoke-SetupCommand (Join-Path $Comfy 'python\Scripts\python.exe') @('-I','-c','import sys;print(sys._base_executable)') -Capture
    foreach ($listener in $listeners) { Assert-SetupComfyListener $listener $owned $supervisor $Comfy $base.Output.Trim() }
    $null = Get-SetupJson 'http://127.0.0.1:8189/system_stats'
}

function Assert-SetupComfyListener {
    param($Listener, $Owned, $Supervisor, [string]$Comfy, [string]$BasePython)
    $managed = Join-Path $Comfy 'python\Scripts\python.exe'
    $worker = Get-CimInstance Win32_Process -Filter ('ProcessId=' + $Listener.OwningProcess)
    if ($Listener.LocalAddress -notin @('127.0.0.1','::1') -or -not $worker) { throw 'Preserving an unrelated ComfyUI listener.' }
    $chain = @($worker)
    if ($worker.ParentProcessId -eq $Owned.pid) {
        if ($worker.ExecutablePath -ne $managed) { throw 'Unexpected direct ComfyUI interpreter.' }
    } else {
        $shim = Get-CimInstance Win32_Process -Filter ('ProcessId=' + $worker.ParentProcessId)
        if (-not $shim -or $shim.ParentProcessId -ne $Owned.pid -or $shim.ExecutablePath -ne $managed -or $worker.ExecutablePath -ne $BasePython) {
            throw 'Preserving an unrelated ComfyUI redirector chain.'
        }
        $chain = @($shim, $worker)
    }
    $earliest = $Supervisor.StartTime.ToUniversalTime()
    $expected = @('-B',(Join-Path $Comfy 'app\main.py'),'--listen','127.0.0.1','--port','8189','--reserve-vram','3.5','--offline')
    foreach ($processInfo in $chain) {
        if ($processInfo.CreationDate.ToUniversalTime() -lt $earliest) { throw 'ComfyUI process predates its owned parent.' }
        $earliest = $processInfo.CreationDate.ToUniversalTime()
        $argv = @(Split-SetupCommandLine $processInfo.CommandLine)
        if ($argv.Count -ne 10 -or $argv[0] -ne $processInfo.ExecutablePath) { throw 'Unexpected ComfyUI executable or arguments.' }
        for ($index = 0; $index -lt $expected.Count; $index++) {
            $matches = if ($index -eq 1) { [string]::Equals([IO.Path]::GetFullPath($argv[$index+1]),[IO.Path]::GetFullPath($expected[$index]),[StringComparison]::OrdinalIgnoreCase) } else { $argv[$index+1] -ceq $expected[$index] }
            if (-not $matches) { throw 'Unexpected ComfyUI arguments; preserving the listener.' }
        }
    }
}

function Split-SetupCommandLine {
    param([string]$CommandLine)
    if (-not ('CodexHarnessSetupArgv' -as [type])) {
        Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class CodexHarnessSetupArgv {
    [DllImport("shell32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    static extern IntPtr CommandLineToArgvW(string command, out int count);
    [DllImport("kernel32.dll")] static extern IntPtr LocalFree(IntPtr memory);
    public static string[] Split(string command) {
        int count; var memory = CommandLineToArgvW(command, out count);
        if (memory == IntPtr.Zero) throw new System.ComponentModel.Win32Exception();
        try {
            var result = new string[count];
            for (int i=0; i<count; i++) result[i] = Marshal.PtrToStringUni(Marshal.ReadIntPtr(memory, i*IntPtr.Size));
            return result;
        } finally { LocalFree(memory); }
    }
}
'@
    }
    return [CodexHarnessSetupArgv]::Split($CommandLine)
}

if ($MyInvocation.InvocationName -ne '.') {
    $result = Invoke-WindowsSetup -Root $InstallRoot -Comfy $ComfyRoot -ProfileHome $CodexHome -Preview:$Plan -Consent:$Approved -Unattended:$NonInteractive -EvidenceFile $Evidence
    $result | ConvertTo-Json -Depth 12
    exit $result.exit_code
}
