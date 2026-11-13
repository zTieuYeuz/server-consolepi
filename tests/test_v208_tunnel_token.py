"""2.0.8 V1-10: token Cloudflare Tunnel khong nam trong argv (ps/cmdline); di qua bien moi truong TUNNEL_TOKEN."""
import os
import subprocess

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _exec_start():
    for d in open(os.path.join(GOC, "systemd", "console-system-tunnel.service"), encoding="utf-8").read().splitlines():
        if d.startswith("ExecStart="):
            return d[len("ExecStart="):]


def test_exec_start_khong_dua_token_vao_argv():
    d = _exec_start()
    assert "--token" not in d and 'TUNNEL_TOKEN="$(cat ' in d and d.rstrip().endswith("tunnel run'")


def test_hanh_vi_that_token_o_environ_khong_o_cmdline(tmp_path):
    """Chay dung chuoi sh -c cua don vi, thay cloudflared va cat bang tien trinh gia: token phai o environ, khong o argv."""
    tk = tmp_path / "tk"
    tk.write_text("TOKEN-BI-MAT-123")
    gia = tmp_path / "cloudflared"
    gia.write_text('#!/bin/sh\nprintf "ARGV:%s\\n" "$*"\nprintf "ENV:%s\\n" "$TUNNEL_TOKEN"\n')
    gia.chmod(0o755)
    lenh = _exec_start()
    assert lenh.startswith("/bin/sh -c '")
    thân = lenh[len("/bin/sh -c '"):-1].replace("/usr/bin/cloudflared", str(gia)).replace("/var/lib/console-system/secrets/cloudflared-token", str(tk))
    r = subprocess.run(["/bin/sh", "-c", thân], capture_output=True, text=True, timeout=10)
    assert "ARGV:" in r.stdout and "TOKEN-BI-MAT-123" not in r.stdout.split("ENV:")[0]
    assert "ENV:TOKEN-BI-MAT-123" in r.stdout and "tunnel run" in r.stdout
