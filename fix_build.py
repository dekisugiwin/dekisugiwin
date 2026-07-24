import io

content = r'''$ErrorActionPreference = 'Stop'

$origDashboard = "C:\Users\tobise-claw8\.gemini\antigravity\brain\64bc2adc-500d-4c9e-9ddf-1607686f3a8a\scratch\Dashboard_orig.ps1"
$newDashboard = "C:\Users\tobise-claw8\.gemini\antigravity\brain\64bc2adc-500d-4c9e-9ddf-1607686f3a8a\scratch\Dashboard_Final.ps1"

# 1. Generate the unified Dashboard.ps1
$psCode = @"
param(
    [switch]`$Start,
    [switch]`$Stop,
    [switch]`$Startup,
    [switch]`$UwpExempt,
    [switch]`$UwpReset,
    [switch]`$AutoStart,
    [switch]`$NoAutoStart,
    [switch]`$Native
)

`$ExePath = [System.Diagnostics.Process]::GetCurrentProcess().MainModule.FileName
`$BaseDir = [System.AppDomain]::CurrentDomain.BaseDirectory.TrimEnd('\')
`$ConfigPath = Join-Path `$BaseDir "config\config.yaml"
`$SettingsPath = Join-Path `$BaseDir "config\settings.xml"
`$ClashPath = Join-Path `$BaseDir "bin\clash-amd64.exe"
`$ConfigDir = Join-Path `$BaseDir "config"

function Start-Core {
    `$isNative = `$false
    if (Test-Path `$SettingsPath) {
        try {
            [xml]`$xml = Get-Content `$SettingsPath -Encoding UTF8
            if (`$xml.DekisugiConfig.RunMode.Trim().ToLower() -eq "native") {
                `$isNative = `$true
            }
        } catch {}
    }
    if (-not (Test-Path `$ClashPath)) {
        [System.Windows.Forms.MessageBox]::Show("Error: clash-amd64.exe not found in `n`$ClashPath", "dekisugi Start Error", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error)
        return
    }

    # Check if running
    `$running = Get-Process -Name "clash-amd64" -ErrorAction SilentlyContinue
    if (`$running) {
        return
    }

    # Check essential databases
    `$geoipPath = Join-Path `$ConfigDir "geoip.metadb"
    `$geositePath = Join-Path `$ConfigDir "GeoSite.dat"
    if ((-not (Test-Path `$geoipPath)) -or (-not (Test-Path `$geositePath))) {
        [System.Windows.Forms.MessageBox]::Show("核心运行所需的数据库文件 (geoip.metadb 或 GeoSite.dat) 缺失！ 请补全后重试。", "错误", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error)
        return
    }

    `$logFile = Join-Path `$BaseDir "config\log\clash_`$(Get-Date -f 'yyyyMMddHHmm').log"
    if (-not (Test-Path (Join-Path `$BaseDir "config\log"))) { New-Item -ItemType Directory -Path (Join-Path `$BaseDir "config\log") -Force | Out-Null }

    `$startInfo = New-Object System.Diagnostics.ProcessStartInfo
    `$startInfo.FileName = "cmd.exe"
    if (`$isNative) {
        if (-not (Test-Path (Join-Path `$ConfigDir "original.yaml"))) {
            [System.Windows.Forms.MessageBox]::Show("当前未找到原生配置文件 (original.yaml)！`n请先在面板控制中心点击【拉取原生配置】后再启动服务。", "错误", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error)
            return
        }
        `$startInfo.Arguments = '/c ""' + `$ClashPath + '" -d "' + `$ConfigDir + '" -f "' + `$ConfigDir + '\original.yaml" > "' + `$logFile + '" 2>&1"'
    } else {
        `$startInfo.Arguments = '/c ""' + `$ClashPath + '" -d "' + `$ConfigDir + '" > "' + `$logFile + '" 2>&1"'
    }
    `$startInfo.WorkingDirectory = `$BaseDir
    `$startInfo.UseShellExecute = `$true
    `$startInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
    `$startInfo.Verb = "runas"
    
    try {
        [System.Diagnostics.Process]::Start(`$startInfo) | Out-Null
    } catch {
        [System.Windows.Forms.MessageBox]::Show("启动核心需要管理员权限，已被取消。`n`n`$($_)", "错误", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error)
        return
    }

    # Wait for UI port to be available
    `$isReady = `$false
    for (`$i=0; `$i -lt 15; `$i++) {
        Start-Sleep -Seconds 1
        try {
            `$resp = Invoke-WebRequest -Uri "http://127.0.0.1:9090/ui" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
            `$isReady = `$true
            break
        } catch { }
    }

    `$running = Get-Process -Name "clash-amd64" -ErrorAction SilentlyContinue
    if (-not `$running) {
        [System.Windows.Forms.MessageBox]::Show("启动失败！请检查日志", "dekisugi Start Error", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error)
        return
    }

    # Set proxy
    `$tunEnabled = `$false
    `$confPathToRead = `$ConfigPath
    if (`$isNative) {
        `$confPathToRead = Join-Path `$BaseDir "config\original.yaml"
    }

    if (Test-Path `$confPathToRead) {
        `$conf = Get-Content `$confPathToRead -Encoding UTF8 -Raw
        if (`$conf -match '(?im)^tun:\s*\n\s*enable:\s*true') {
            `$tunEnabled = `$true
        }
    }

    `$regPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings"
    if (`$tunEnabled) {
        Set-ItemProperty -Path `$regPath -Name ProxyEnable -Value 0
    } else {
        Set-ItemProperty -Path `$regPath -Name ProxyServer -Value "127.0.0.1:7890"
        Set-ItemProperty -Path `$regPath -Name ProxyEnable -Value 1
    }

    # Open UI
    if (`$isReady) {
        Start-Process "http://localhost:9090/ui"
    }
}

function Stop-Core {
    # Clear proxy
    `$regPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings"
    Set-ItemProperty -Path `$regPath -Name ProxyEnable -Value 0 -ErrorAction SilentlyContinue

    # Kill core
    `$startInfo = New-Object System.Diagnostics.ProcessStartInfo
    `$startInfo.FileName = "cmd.exe"
    `$startInfo.Arguments = "/c taskkill /f /im clash-amd64.exe"
    `$startInfo.Verb = "runas"
    `$startInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
    try { [System.Diagnostics.Process]::Start(`$startInfo).WaitForExit() } catch { }
    Start-Sleep -Milliseconds 500
}

if (`$Stop) {
    Stop-Core
    exit
}

if (`$Startup) {
    Start-Sleep -Seconds 15
    Start-Core
    `$global:StartMinimized = `$true
    # Fall through to UI - don't exit
}

if (`$AutoStart) {
    function Show-TopMostMsg(`$text, `$title, `$icon) {
        [System.Windows.Forms.MessageBox]::Show(`$text, `$title, 0, `$icon, 0, [System.Windows.Forms.MessageBoxOptions]::ServiceNotification) | Out-Null
    }
    `$taskExists = `$null -ne (Get-ScheduledTask -TaskName "DekisugiAutoStart" -ErrorAction SilentlyContinue)
    if (`$taskExists) {
        Show-TopMostMsg "已经设置过开机自启，无需重复设置！" "提示" 64
        exit
    }
    try {
        `$action = New-ScheduledTaskAction -Execute `"`$ExePath`" -Argument `"-Startup`"
        `$trigger = New-ScheduledTaskTrigger -AtLogOn
        `$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Days 0)
        `$principal = New-ScheduledTaskPrincipal -GroupId `"BUILTIN\Administrators`" -RunLevel Highest
        `$task = New-ScheduledTask -Action `$action -Trigger `$trigger -Settings `$settings -Principal `$principal
        Register-ScheduledTask -TaskName `"DekisugiAutoStart`" -InputObject `$task -Force | Out-Null
        Show-TopMostMsg "开机自启设置成功！`n`n由于需要后台运行核心，建议保留面板所在的文件夹不要随意移动。" "成功" 64
    } catch {
        Show-TopMostMsg "设置开机自启失败！`n`$($_)" "错误" 16
    }
    exit
}

if (`$NoAutoStart) {
    function Show-TopMostMsg(`$text, `$title, `$icon) {
        [System.Windows.Forms.MessageBox]::Show(`$text, `$title, 0, `$icon, 0, [System.Windows.Forms.MessageBoxOptions]::ServiceNotification) | Out-Null
    }
    `$taskExists = `$null -ne (Get-ScheduledTask -TaskName "DekisugiAutoStart" -ErrorAction SilentlyContinue)
    if (-not `$taskExists) {
        Show-TopMostMsg "当前并未设置开机自启，无需关闭。" "提示" 64
        exit
    }
    try {
        Unregister-ScheduledTask -TaskName `"DekisugiAutoStart`" -Confirm:`$false -ErrorAction Stop
        Show-TopMostMsg "开机自启已成功关闭！" "成功" 64
    } catch {
        Show-TopMostMsg "关闭自启失败！`n`$($_)" "错误" 16
    }
    exit
}

if (`$UwpExempt) {
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing
    `$frm = New-Object System.Windows.Forms.Form
    `$frm.Text = "UWP 解除限制"
    `$frm.Size = New-Object System.Drawing.Size(420, 160)
    `$frm.StartPosition = "CenterScreen"
    `$frm.FormBorderStyle = "FixedDialog"
    `$frm.MaximizeBox = `$false
    `$frm.MinimizeBox = `$false
    `$frm.ControlBox = `$false
    `$frm.TopMost = `$true

    `$lbl = New-Object System.Windows.Forms.Label
    `$lbl.Text = "正在扫描并解除系统中的 UWP 应用网络隔离...`n这可能需要几十秒时间，请耐心等待。"
    `$lbl.AutoSize = `$false
    `$lbl.Size = New-Object System.Drawing.Size(380, 40)
    `$lbl.Location = New-Object System.Drawing.Point(20, 15)
    `$frm.Controls.Add(`$lbl)

    `$pb = New-Object System.Windows.Forms.ProgressBar
    `$pb.Size = New-Object System.Drawing.Size(360, 20)
    `$pb.Location = New-Object System.Drawing.Point(20, 65)
    `$pb.Style = [System.Windows.Forms.ProgressBarStyle]::Marquee
    `$frm.Controls.Add(`$pb)

    `$frm.Show()
    [System.Windows.Forms.Application]::DoEvents()

    `$packages = Get-AppxPackage -AllUsers
    `$total = `$packages.Count
    `$count = 0
    
    `$pb.Style = [System.Windows.Forms.ProgressBarStyle]::Blocks
    `$pb.Maximum = `$total
    `$pb.Value = 0

    foreach (`$pkg in `$packages) {
        `$count++
        `$pb.Value = `$count
        if (`$count % 2 -eq 0 -or `$count -eq `$total) {
            `$lbl.Text = "正在处理 (`$count / `$total) : `$`(`$pkg.Name)"
            [System.Windows.Forms.Application]::DoEvents()
        }
        CheckNetIsolation.exe LoopbackExempt -a -n="`$`(`$pkg.PackageFamilyName)" | Out-Null
    }

    `$frm.Close()
    [System.Windows.Forms.MessageBox]::Show("解除成功！共处理 `$total 个应用。", "成功", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)
    exit
}

if (`$UwpReset) {
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing
    `$frm = New-Object System.Windows.Forms.Form
    `$frm.Text = "UWP 恢复限制"
    `$frm.Size = New-Object System.Drawing.Size(420, 140)
    `$frm.StartPosition = "CenterScreen"
    `$frm.FormBorderStyle = "FixedDialog"
    `$frm.MaximizeBox = `$false
    `$frm.MinimizeBox = `$false
    `$frm.ControlBox = `$false
    `$frm.TopMost = `$true

    `$lbl = New-Object System.Windows.Forms.Label
    `$lbl.Text = "正在清空 UWP 应用的网络隔离白名单...`n系统处理需要一定时间，请耐心等待。"
    `$lbl.AutoSize = `$false
    `$lbl.Size = New-Object System.Drawing.Size(380, 40)
    `$lbl.Location = New-Object System.Drawing.Point(20, 15)
    `$frm.Controls.Add(`$lbl)

    `$pb = New-Object System.Windows.Forms.ProgressBar
    `$pb.Size = New-Object System.Drawing.Size(360, 20)
    `$pb.Location = New-Object System.Drawing.Point(20, 60)
    `$pb.Style = [System.Windows.Forms.ProgressBarStyle]::Marquee
    `$frm.Controls.Add(`$pb)

    `$frm.Show()
    [System.Windows.Forms.Application]::DoEvents()

    CheckNetIsolation.exe LoopbackExempt -c | Out-Null

    `$frm.Close()
    [System.Windows.Forms.MessageBox]::Show("UWP 隔离白名单已清空并恢复默认设置！", "成功", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)
    exit
}

if (`$Start) {
    Start-Core
    exit
}

"@

$origContent = Get-Content $origDashboard -Encoding UTF8 -Raw

# Replace AvalonEdit path explicitly with Join-Path to avoid string interpolation bugs
$origContent = $origContent -replace '(?i)Add-Type -Path "\$PSScriptRoot[\\/]\.\.[\\/]bin[\\/]ICSharpCode\.AvalonEdit\.dll"', 'Add-Type -Path (Join-Path $BaseDir "bin\ICSharpCode.AvalonEdit.dll")'

# Inject single instance event listener
$eventListener = @"
`$global:showEvent = New-Object System.Threading.EventWaitHandle(`$false, [System.Threading.EventResetMode]::AutoReset, "DekisugiwinShowEvent")
`$checkEventTimer = New-Object System.Windows.Forms.Timer
`$checkEventTimer.Interval = 500
`$checkEventTimer.Add_Tick({
    if (`$global:showEvent.WaitOne(0)) {
        `$Form.Show()
        `$Form.WindowState = [System.Windows.Forms.FormWindowState]::Normal
        `$Form.Activate()
    }
})
`$checkEventTimer.Start()
"@
$origContent = $origContent -replace '(?m)^\$global:AllowExit = \$false$', "`$global:AllowExit = `$false`n$eventListener"

# Replace $BaseDir definition
$origContent = $origContent -replace '(?m)^\$BaseDir = .*$', ""
$origContent = $origContent -replace '(?m)^\$ConfigPath = .*$', ""
$origContent = $origContent -replace '(?m)^\$SettingsPath = .*$', ""

# Replace UI Start button
$origContent = $origContent -replace '(?sm)\$BtnGlobalStart\.Add_Click\(\{.*?\n\}\)', "`$BtnGlobalStart.Add_Click({ 
    `$running = Get-Process -Name `"clash-amd64`" -ErrorAction SilentlyContinue
    if (`$running) {
        [System.Windows.Forms.MessageBox]::Show(`"已有一个代理实例正在运行！`", `"提示`", 0, 64)
        return
    }
    `$BtnGlobalStart.Enabled = `$false
    `$BtnGlobalStart.Text = `"启动中...`"
    [System.Windows.Forms.Application]::DoEvents()
    try { Start-Process `"`$ExePath`" -ArgumentList `"-Start`" } catch {} 
    Start-Sleep -Milliseconds 500
    `$BtnGlobalStart.Enabled = `$true
    `$BtnGlobalStart.Text = `"全局启动`"
})"

# Replace UI Restart button
$origContent = $origContent -replace '(?sm)\$BtnGlobalRestart\.Add_Click\(\{.*?\n\}\)', "`$BtnGlobalRestart.Add_Click({ 
    `$BtnGlobalRestart.Enabled = `$false
    `$BtnGlobalRestart.Text = `"重启中...`"
    [System.Windows.Forms.Application]::DoEvents()
    try { Start-Process `"`$ExePath`" -ArgumentList `"-Stop`" -Wait } catch {}
    Start-Sleep -Seconds 1
    try { Start-Process `"`$ExePath`" -ArgumentList `"-Start`" } catch {} 
    Start-Sleep -Milliseconds 500
    `$BtnGlobalRestart.Enabled = `$true
    `$BtnGlobalRestart.Text = `"重启服务`"
})"

# Replace UI Stop button
$origContent = $origContent -replace '(?m)\$BtnGlobalStop\.Add_Click\(\{.*?\}\)', "`$BtnGlobalStop.Add_Click({ 
    `$running = Get-Process -Name `"clash-amd64`" -ErrorAction SilentlyContinue
    if (-not `$running) {
        [System.Windows.Forms.MessageBox]::Show(`"当前没有正在运行的服务实例！`", `"提示`", 0, 48)
        return
    }
    `$BtnGlobalStop.Enabled = `$false
    `$BtnGlobalStop.Text = `"停止中...`"
    [System.Windows.Forms.Application]::DoEvents()
    try { Start-Process `"`$ExePath`" -ArgumentList `"-Stop`" -Wait } catch {}
    [System.Windows.Forms.MessageBox]::Show(`"服务已成功停止！`", `"提示`", 0, 64)
    `$BtnGlobalStop.Enabled = `$true
    `$BtnGlobalStop.Text = `"关闭服务`"
})"

# Replace UI Auto Start
$origContent = $origContent -replace '(?m)\$BtnGlobalAuto\.Add_Click\(\{.*?\}\)', "`$BtnGlobalAuto.Add_Click({
    `$BtnGlobalAuto.Enabled = `$false
    `$BtnGlobalAuto.Text = `"处理中...`"
    [System.Windows.Forms.Application]::DoEvents()
    `$startInfo = New-Object System.Diagnostics.ProcessStartInfo
    `$startInfo.FileName = `"`$ExePath`"
    `$startInfo.Arguments = `"-AutoStart`"
    `$startInfo.Verb = `"runas`"
    try { 
        `$p = [System.Diagnostics.Process]::Start(`$startInfo)
        if (`$p) { `$p.WaitForExit() }
    } catch {}
    `$BtnGlobalAuto.Text = `"开启自启`"
    `$BtnGlobalAuto.Enabled = `$true
})"

# Replace UI Auto Stop
$origContent = $origContent -replace '(?m)\$BtnGlobalNoAuto\.Add_Click\(\{.*?\}\)', "`$BtnGlobalNoAuto.Add_Click({
    `$BtnGlobalNoAuto.Enabled = `$false
    `$BtnGlobalNoAuto.Text = `"处理中...`"
    [System.Windows.Forms.Application]::DoEvents()
    `$startInfo = New-Object System.Diagnostics.ProcessStartInfo
    `$startInfo.FileName = `"`$ExePath`"
    `$startInfo.Arguments = `"-NoAutoStart`"
    `$startInfo.Verb = `"runas`"
    try { 
        `$p = [System.Diagnostics.Process]::Start(`$startInfo)
        if (`$p) { `$p.WaitForExit() }
    } catch {}
    `$BtnGlobalNoAuto.Text = `"关闭自启`"
    `$BtnGlobalNoAuto.Enabled = `$true
})"

# Replace UI UWP Exempt
$origContent = $origContent -replace '(?m)\$BtnUwpEnable\.Add_Click\(\{.*?\}\)', "`$BtnUwpEnable.Add_Click({
    `$startInfo = New-Object System.Diagnostics.ProcessStartInfo
    `$startInfo.FileName = `"`$ExePath`"
    `$startInfo.Arguments = `"-UwpExempt`"
    `$startInfo.Verb = `"runas`"
    try { [System.Diagnostics.Process]::Start(`$startInfo) | Out-Null } catch {}
})"

# Replace UI UWP Reset
$origContent = $origContent -replace '(?m)\$BtnUwpDisable\.Add_Click\(\{.*?\}\)', "`$BtnUwpDisable.Add_Click({
    `$startInfo = New-Object System.Diagnostics.ProcessStartInfo
    `$startInfo.FileName = `"`$ExePath`"
    `$startInfo.Arguments = `"-UwpReset`"
    `$startInfo.Verb = `"runas`"
    try { [System.Diagnostics.Process]::Start(`$startInfo) | Out-Null } catch {}
})"

$finalCode = $psCode + "`n`n" + $origContent

# 1.5 Minify PS code (remove comments and empty lines)
$finalCode = $finalCode -replace '(?m)^\s*#.*$', ''
$finalCode = $finalCode -replace '(?m)\r?\n\s*\r?\n', "`n"

$finalCode | Out-File -FilePath $newDashboard -Encoding UTF8

# 2. Compress
$bytes = [System.Text.Encoding]::UTF8.GetBytes($finalCode)
$memoryStream = New-Object System.IO.MemoryStream
$gzipStream = New-Object System.IO.Compression.GZipStream($memoryStream, [System.IO.Compression.CompressionMode]::Compress)
$gzipStream.Write($bytes, 0, $bytes.Length)
$gzipStream.Close()
$compressedBytes = $memoryStream.ToArray()

# 2.5 AES Encrypt
$aes = [System.Security.Cryptography.Aes]::Create()
$aes.KeySize = 256
$aes.GenerateKey()
$aes.GenerateIV()
$encryptor = $aes.CreateEncryptor()
$cipherStream = New-Object System.IO.MemoryStream
$cryptoStream = New-Object System.Security.Cryptography.CryptoStream($cipherStream, $encryptor, [System.Security.Cryptography.CryptoStreamMode]::Write)
$cryptoStream.Write($compressedBytes, 0, $compressedBytes.Length)
$cryptoStream.FlushFinalBlock()
$cipherBytes = $cipherStream.ToArray()

$base64 = [Convert]::ToBase64String($cipherBytes)
$keyBase64 = [Convert]::ToBase64String($aes.Key)
$ivBase64 = [Convert]::ToBase64String($aes.IV)

# 3. Generate C# Wrapper
$csCode = @"
using System;
using System.IO;
using System.IO.Compression;
using System.Security.Cryptography;
using System.Management.Automation;
using System.Management.Automation.Runspaces;
using System.Text;
using System.Diagnostics;
using System.Threading;
using System.Windows.Forms;

class AppLoader {
    static Mutex singleMutex;

    [STAThread]
    static void Main(string[] args) {
        if (args.Length == 0) {
            bool createdNew;
            singleMutex = new Mutex(true, "DekisugiwinSingleInstance", out createdNew);
            if (!createdNew) {
                try {
                    using (var evt = EventWaitHandle.OpenExisting("DekisugiwinShowEvent")) {
                        evt.Set();
                    }
                } catch {}
                return;
            }
        }

        try {
            byte[] cipher = Convert.FromBase64String(`"$base64`");
            byte[] key = Convert.FromBase64String(`"$keyBase64`");
            byte[] iv = Convert.FromBase64String(`"$ivBase64`");

            byte[] compressed = null;
            using (Aes aes = Aes.Create()) {
                aes.Key = key;
                aes.IV = iv;
                using (var msIn = new MemoryStream(cipher))
                using (var cs = new CryptoStream(msIn, aes.CreateDecryptor(), CryptoStreamMode.Read))
                using (var msOut = new MemoryStream()) {
                    cs.CopyTo(msOut);
                    compressed = msOut.ToArray();
                }
            }

            string script = "";
            using (var ms = new MemoryStream(compressed))
            using (var gzip = new GZipStream(ms, CompressionMode.Decompress))
            using (var reader = new StreamReader(gzip, Encoding.UTF8)) {
                script = reader.ReadToEnd();
            }

            var iss = InitialSessionState.CreateDefault();
            iss.ExecutionPolicy = Microsoft.PowerShell.ExecutionPolicy.Bypass;
            iss.ApartmentState = System.Threading.ApartmentState.STA;
            iss.ThreadOptions = PSThreadOptions.UseCurrentThread;
            using (var runspace = RunspaceFactory.CreateRunspace(iss)) {
                runspace.Open();
                runspace.SessionStateProxy.SetVariable("ExePath", System.Reflection.Assembly.GetExecutingAssembly().Location);
                runspace.SessionStateProxy.SetVariable("args", args);
                
                using (var ps = PowerShell.Create()) {
                    ps.Runspace = runspace;
                    ps.AddScript(script);
                    
                    if (args.Length > 0) {
                        if(args[0] == "-Start") ps.AddParameter("Start", true);
                        else if(args[0] == "-Stop") ps.AddParameter("Stop", true);
                        else if(args[0] == "-Startup") ps.AddParameter("Startup", true);
                        else if(args[0] == "-UwpExempt") ps.AddParameter("UwpExempt", true);
                        else if(args[0] == "-UwpReset") ps.AddParameter("UwpReset", true);
                        else if(args[0] == "-AutoStart") ps.AddParameter("AutoStart", true);
                        else if(args[0] == "-NoAutoStart") ps.AddParameter("NoAutoStart", true);
                        
                        if (args.Length > 1 && args[1] == "-Native") {
                            ps.AddParameter("Native", true);
                        }
                    }
                    
                    ps.Invoke();
                    
                    if (ps.HadErrors) {
                        var errs = new StringBuilder();
                        foreach (var err in ps.Streams.Error) {
                            errs.AppendLine(err.ToString());
                        }
                        string errText = errs.ToString().Trim();
                        if(args.Length == 0 && errText.Length > 0) MessageBox.Show(errText, "Runtime Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    }
                }
            }
        } catch (Exception ex) {
            if(args.Length == 0) MessageBox.Show(ex.ToString(), "Fatal Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }
}
"@

$csPath = "C:\Users\tobise-claw8\.gemini\antigravity\brain\64bc2adc-500d-4c9e-9ddf-1607686f3a8a\scratch\Wrapper.cs"
$csCode | Out-File -FilePath $csPath -Encoding UTF8

# Compile C#
$compiler = "C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
$sma = "C:\Windows\Microsoft.Net\assembly\GAC_MSIL\System.Management.Automation\v4.0_3.0.0.0__31bf3856ad364e35\System.Management.Automation.dll"
$outExe = "C:\Users\tobise-claw8\Documents\test\dekisugiwin\dekisugiwin.exe"

& $compiler /target:winexe /out:"$outExe" /reference:"$sma" "$csPath"
if ($LASTEXITCODE -ne 0) {
    throw "C# compilation failed"
}

Write-Output "Compilation Successful!"
'''

with open(r'C:\Users\tobise-claw8\.gemini\antigravity\brain\64bc2adc-500d-4c9e-9ddf-1607686f3a8a\scratch\build.ps1', 'w', encoding='utf-8-sig') as f:
    f.write(content)
