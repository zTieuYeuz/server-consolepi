# Console System - (c) 2026 zTieuYeuz. All rights reserved.
# Duoc ConsoleSystemAgent.msi goi sau khi dat file: ghi danh may voi Console System (ghim chung chi may chu) roi cai dich vu agent.
#   cs-install.ps1 -Server 192.168.1.10:8443 -Pin <SHA-256 cua CA Console System> -Code <ma ghi danh>
# (Kiem tra passkey va go cai dat do cs-agent.exe lam: --check-passkey / --check-local / --teardown)
param([string]$Server = '', [string]$Pin = '', [string]$Code = '')
$ErrorActionPreference = 'Stop'
$log = Join-Path $env:windir 'Temp\cs-agent-msi.log'
function L($m) { try { Add-Content -LiteralPath $log -Value ((Get-Date -Format s) + ' ' + $m) } catch {} }
try {
    $Pin = $Pin.Trim().ToUpper(); $Code = $Code.Trim()
    $servers = @(); foreach ($sv in ($Server -split ',')) { $sv = $sv.Trim(); if (-not $sv) { continue }; if ($sv -notmatch '^https://') { $sv = 'https://' + $sv }; if ($sv -notmatch ':\d+$') { $sv += ':8443' }; if ($sv -notmatch '^https://[0-9A-Za-z.\-]+:\d{1,5}$') { throw ('SERVER khong hop le: ' + $sv) }; $servers += $sv }
    if ($servers.Count -eq 0) { throw 'thieu SERVER' }
    if ($Pin -notmatch '^[0-9A-F]{64}$') { throw 'PIN phai la SHA-256 (64 ky tu hex) cua CA' }
    if ($Code -notmatch '^[A-Za-z0-9_-]{20,64}$') { throw 'CODE khong hop le' }
    Add-Type 'using System;using System.Net;using System.Net.Security;using System.Security.Cryptography;using System.Security.Cryptography.X509Certificates;public static class CsPin{static string H(byte[] b){return BitConverter.ToString(SHA256.Create().ComputeHash(b)).Replace("-","");}public static void On(string h){ServicePointManager.ServerCertificateValidationCallback=delegate(object s,X509Certificate c,X509Chain ch,SslPolicyErrors e){try{if(H(c.GetRawCertData())==h)return true;if(ch==null)return false;bool co=false;foreach(X509ChainElement el in ch.ChainElements)if(H(el.Certificate.RawData)==h)co=true;if(!co)return false;foreach(X509ChainStatus st in ch.ChainStatus)if(st.Status!=X509ChainStatusFlags.NoError&&st.Status!=X509ChainStatusFlags.UntrustedRoot&&st.Status!=X509ChainStatusFlags.PartialChain&&st.Status!=X509ChainStatusFlags.RevocationStatusUnknown&&st.Status!=X509ChainStatusFlags.OfflineRevocation)return false;return true;}catch{return false;}};}}'
    [CsPin]::On($Pin)
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $s = $null; $lastErr = $null
    foreach ($sv in $servers) {
        L ('ghi danh voi ' + $sv)
        try { $s = Invoke-RestMethod -UseBasicParsing -TimeoutSec 25 -Uri ($sv + '/uem/agent/cai/' + $Code + '.ps1?h=' + [uri]::EscapeDataString($env:COMPUTERNAME)); break } catch { $lastErr = $_; L ('khong noi duoc ' + $sv + ': ' + $_) }
    }
    if (-not $s) { throw $lastErr }
    $env:CS_EXE_SAN = '1'
    $r = (& ([scriptblock]::Create([string]$s)) | Out-String).Trim()
    L $r
    if ($r -notmatch 'ST=DA_LAM') { throw $r }
    exit 0
} catch {
    L ('LOI: ' + $_)
    exit 1
}
