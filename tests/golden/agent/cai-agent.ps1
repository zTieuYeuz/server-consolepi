# Console System - script cài agent 'May Mau' (tạo <GIO>).
# Chạy: chuột phải, Run with PowerShell (tự xin quyền Administrator). Mã ghi danh có hạn dùng; không chứa mật khẩu hay chứng chỉ.
$Servers = @('http://192.168.98.1:8880/uem/agent'); $Pin = '123456'; $Code = 'MA-MAU'
$adm = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $adm) { Start-Process -FilePath powershell.exe -Verb RunAs -ArgumentList ('-NoProfile -ExecutionPolicy Bypass -File "' + $PSCommandPath + '"'); exit }
$ErrorActionPreference = 'Stop'
try {
  Add-Type 'using System;using System.Net;using System.Net.Security;using System.Security.Cryptography;using System.Security.Cryptography.X509Certificates;public static class CsPin{static string H(byte[] b){return BitConverter.ToString(SHA256.Create().ComputeHash(b)).Replace("-","");}public static void On(string h){ServicePointManager.ServerCertificateValidationCallback=delegate(object s,X509Certificate c,X509Chain ch,SslPolicyErrors e){try{if(H(c.GetRawCertData())==h)return true;if(ch==null)return false;bool co=false;foreach(X509ChainElement el in ch.ChainElements)if(H(el.Certificate.RawData)==h)co=true;if(!co)return false;foreach(X509ChainStatus st in ch.ChainStatus)if(st.Status!=X509ChainStatusFlags.NoError&&st.Status!=X509ChainStatusFlags.UntrustedRoot&&st.Status!=X509ChainStatusFlags.PartialChain&&st.Status!=X509ChainStatusFlags.RevocationStatusUnknown&&st.Status!=X509ChainStatusFlags.OfflineRevocation)return false;return true;}catch{return false;}};}}'
  [CsPin]::On($Pin)
  [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
  $s = $null; $lastErr = ''
  foreach ($sv in $Servers) { try { $s = Invoke-RestMethod -UseBasicParsing -TimeoutSec 25 -Uri ($sv + '/uem/agent/cai/' + $Code + '.ps1?h=' + [uri]::EscapeDataString($env:COMPUTERNAME)); break } catch { $lastErr = $_; Write-Host ('Khong noi duoc ' + $sv + ', thu dia chi tiep theo...') } }
  if (-not $s) { throw $lastErr }
  $r = (& ([scriptblock]::Create([string]$s)) | Out-String).Trim()
  Write-Host $r
} catch { Write-Host ('LOI: ' + $_) -ForegroundColor Red }
Read-Host 'Nhan Enter de dong'
