#!/usr/bin/env python3
# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Bien dich cs-agent.exe tu ma nguon C# (uem_agent_cs.py) tren MOT may Windows qua WinRM, luu vao src/ui/agent_bin/.
Dung: PW=<mat khau> python3 tools/dung-agent-exe.py <ip> <user>   (mat khau chi qua bien moi truong, khong luu)"""
import base64
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from pypsrp.client import Client  # noqa: E402
from ui import uem_agent_cs as CS  # noqa: E402

ip, user, pw = sys.argv[1], sys.argv[2], os.environ["PW"]
c = Client(ip, username=user, password=pw, ssl=False, auth="ntlm", cert_validation=False)
src = base64.b64encode(CS.nguon().encode("utf-8")).decode()
ps = r"""
$d = Join-Path $env:TEMP 'cs-build'; New-Item -ItemType Directory -Force $d | Out-Null
[IO.File]::WriteAllBytes((Join-Path $d 'agent.cs'), [Convert]::FromBase64String('%s'))
$csc = Join-Path $env:windir 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$o = & $csc /nologo /target:winexe /codepage:65001 /optimize+ ('/out:' + (Join-Path $d 'cs-agent.exe')) /r:System.ServiceProcess.dll /r:System.Web.Extensions.dll /r:System.Windows.Forms.dll /r:System.Drawing.dll (Join-Path $d 'agent.cs') 2>&1 | Out-String
if ($LASTEXITCODE -ne 0) { 'LOI ' + $o; return }
[Convert]::ToBase64String([IO.File]::ReadAllBytes((Join-Path $d 'cs-agent.exe')))
Remove-Item $d -Recurse -Force
""" % src
out, streams, err = c.execute_ps(ps)
out = out.strip()
if err or out.startswith("LOI"):
    sys.exit("Bien dich loi: " + out[:500])
dich = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "ui", "agent_bin", "cs-agent.exe")
open(dich, "wb").write(base64.b64decode(out))
print("OK", dich, os.path.getsize(dich), "bytes, ver", CS.VER_FILE)
