"""LOI-013 goc: phien SSH rieng KHONG co shell (launcher phien-ssh.py), ssh chay bang danh sach doi so, tmux khong con duong ra shell root. Co test tmux that."""
import json
import os
import shutil
import subprocess
import sys
import time

import pytest

GOC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SCRIPTS = os.path.join(GOC, "src", "scripts")
sys.path.insert(0, os.path.join(GOC, "src"))
sys.path.insert(0, SCRIPTS)


def _launcher():
    import importlib.util
    spec = importlib.util.spec_from_file_location("phien_ssh", os.path.join(SCRIPTS, "phien-ssh.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_lenh_ssh_la_danh_sach_doi_so_an_toan():
    L = _launcher()
    a = L.lenh_ssh("10.0.0.5", "admin", 22, "/tmp/kh")
    assert a[0] == "ssh" and "--" in a and a[-1] == "admin@10.0.0.5"
    assert ["-e", "none"] == a[a.index("-e"):a.index("-e") + 2]                    # tat ky tu thoat ~ (khong co ~C / ~! )
    assert "PermitLocalCommand=no" in a and ["-F", "/dev/null"] == a[1:3]
    for host, user in (("-oProxyCommand=id", "u"), ("10.0.0.5;id", "u"), ("h", "-oX"), ("h h", "u"), ("", "u"), ("h", "u\nid")):
        assert L.lenh_ssh(host, user, 22, "/tmp/kh") is None, (host, user)
    assert L.lenh_ssh("h", "u", 0, "/tmp/kh") is None and L.lenh_ssh("h", "u", "x", "/tmp/kh") is None


def test_phien_mo_sh_khong_con_duong_ra_shell():
    s = open(os.path.join(SCRIPTS, "phien-mo.sh"), encoding="utf-8").read()
    i = s.index("ssh-*|xem-*)")
    j = s.index("serial-tty*)")
    ssh_case = s[i:j]
    assert 'new-session -A -s "$TEN"' not in ssh_case and "phien-ssh.py" in ssh_case and "khoa_tmux" in ssh_case
    assert "setpriv --reuid=console-ssh" in ssh_case                                   # chay duoi user khong dac quyen neu co
    for hang in ("prefix None", "prefix2 None", "mouse off", "default-command /bin/false"):
        assert hang in s, hang
    # moi phien khong phai 'local' deu qua khoa_tmux (khong con new-session -A tran)
    assert s.count("khoa_tmux ") >= 3
    assert "new-session -A" in s[s.index("    local)"):s.index("    ssh-*|xem-*)")]      # chi 'local' (admin) con shell


@pytest.mark.skipif(not shutil.which("tmux"), reason="khong co tmux")
def test_phien_ssh_tmux_that_khong_go_duoc_lenh_shell(tmp_path):
    env = dict(os.environ, TMUX_TMPDIR=str(tmp_path), CS_SSH_YC=str(tmp_path / "yc"), CS_SSH_HOME=str(tmp_path / "home"), CS_SSH_CHO_PHEP_ROOT="1")
    os.makedirs(env["CS_SSH_YC"])
    os.makedirs(env["CS_SSH_HOME"])
    fake = tmp_path / "bin"
    fake.mkdir()
    (fake / "ssh").write_text('#!/bin/bash\necho "FAKE-SSH $*"\nread -t 3 dong\necho "NHAN:[$dong]"\nsleep 1\n')
    (fake / "ssh").chmod(0o755)
    env["PATH"] = str(fake) + os.pathsep + env["PATH"]

    def tmux(*a):
        return subprocess.run(["tmux", *a], env=env, capture_output=True, text=True, timeout=15)

    def man_hinh():
        return tmux("capture-pane", "-p", "-t", "ssh-test").stdout

    def cho(chuoi, giay=8):
        het = time.time() + giay
        while time.time() < het:
            if chuoi in man_hinh():
                return True
            time.sleep(0.2)
        return False

    tmux("new-session", "-d", "-x", "300", "-y", "30", "-s", "ssh-test", sys.executable, os.path.join(SCRIPTS, "phien-ssh.py"), "ssh-test")
    try:
        assert cho("Chưa kết nối")
        tmux("send-keys", "-t", "ssh-test", "id", "Enter")                               # go lenh luc chua ket noi
        tmux("send-keys", "-t", "ssh-test", "echo $0; cat /etc/hostname", "Enter")
        time.sleep(1.2)
        hien = man_hinh()
        assert "uid=" not in hien and "bash" not in hien.replace("Chưa", "") and "gid=" not in hien, hien
        assert tmux("display-message", "-p", "-t", "ssh-test", "#{pane_current_command}").stdout.strip().startswith("python")
        # yeu cau hop le -> ssh (gia) chay voi doi so cung; phim go truoc do KHONG ro ri sang ssh
        json.dump({"host": "10.0.0.5", "user": "admin", "port": 22}, open(os.path.join(env["CS_SSH_YC"], "ssh-test.json"), "w"))
        assert cho("FAKE-SSH")
        assert os.path.exists(os.path.join(env["CS_SSH_YC"], "ssh-test.dang-ssh"))                 # LOI-014: tep danh dau ssh dang chay
        hien = man_hinh()
        assert "-e none" in hien and "PermitLocalCommand=no" in hien and "admin@10.0.0.5" in hien
        tmux("send-keys", "-t", "ssh-test", "xin-chao", "Enter")
        assert cho("NHAN:[xin-chao]"), man_hinh()                                        # sau khi noi ssh, phim toi ssh; truoc do khong lan
        assert cho("Kết nối SSH đã kết thúc", 10)
        assert not os.path.exists(os.path.join(env["CS_SSH_YC"], "ssh-test.dang-ssh"))
        # yeu cau xau bi tu choi, khong chay gi
        json.dump({"host": "-oProxyCommand=id", "user": "admin", "port": 22}, open(os.path.join(env["CS_SSH_YC"], "ssh-test.json"), "w"))
        assert cho("không hợp lệ")
        assert "uid=" not in man_hinh()
    finally:
        tmux("kill-server")


@pytest.mark.skipif(os.geteuid() != 0, reason="chi y nghia khi chay bang root")
def test_launcher_tu_choi_chay_bang_root(tmp_path):
    """NV8-12: fail closed - launcher chay root (khong ha quyen duoc) thi tu choi, khong cho chay ssh."""
    env = dict(os.environ, CS_SSH_YC=str(tmp_path), CS_SSH_HOME=str(tmp_path))
    env.pop("CS_SSH_CHO_PHEP_ROOT", None)
    (tmp_path / "ssh-ab.json").write_text(json.dumps({"host": "10.0.0.5", "user": "x", "port": 22}))
    r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "phien-ssh.py"), "ssh-ab"], env=env, capture_output=True, text=True, timeout=5 + 10)
    assert r.returncode == 1 and "Tu choi" in r.stdout
    assert (tmp_path / "ssh-ab.json").exists()                                    # khong doc/khong chay yeu cau


def test_phien_mo_sh_fail_closed_va_khop_chinh_xac():
    s = open(os.path.join(SCRIPTS, "phien-mo.sh"), encoding="utf-8").read()
    ssh_case = s[s.index("ssh-*|xem-*)"):s.index("serial-tty*)")]
    assert "exit 1" in ssh_case and "tu choi mo terminal SSH" in ssh_case
    assert "phien-ssh.py \"$TEN\")\n        else\n            LAUNCH=(/usr/bin/python3" not in ssh_case          # khong con nhanh chay root
    import re
    for m in re.finditer(r"tmux [a-z-]+ (?:-[a-z] )*-t \"([^\"]+)\"", s):
        assert m.group(1).startswith("="), m.group(0)                                  # moi -t deu '=ten:' (khop chinh xac)


@pytest.mark.skipif(not shutil.which("tmux"), reason="khong co tmux")
def test_tmux_khop_chinh_xac_khong_theo_tien_to(tmp_path):
    """NV8-11: user 'admin' chua co phien khong the gui phim/xem man hinh/attach vao 'ssh-administrator'."""
    from consolesystem.core.tmuxten import chinh_xac
    env = dict(os.environ, TMUX_TMPDIR=str(tmp_path))

    def tmux(*a):
        return subprocess.run(["tmux", *a], env=env, capture_output=True, text=True, timeout=15)
    tmux("new-session", "-d", "-s", "ssh-administrator", "sleep 30")
    try:
        assert tmux("has-session", "-t", "ssh-admin").returncode == 0                  # hanh vi cu: khop tien to (loi)
        assert tmux("has-session", "-t", chinh_xac("ssh-admin")).returncode != 0
        assert tmux("send-keys", "-t", chinh_xac("ssh-admin"), "x").returncode != 0
        assert tmux("capture-pane", "-p", "-t", chinh_xac("ssh-admin")).returncode != 0
        assert tmux("has-session", "-t", chinh_xac("ssh-administrator")).returncode == 0
        assert tmux("capture-pane", "-p", "-t", chinh_xac("ssh-administrator")).returncode == 0
        assert chinh_xac("=x:") == "=x:"
    finally:
        tmux("kill-server")


def test_moi_lenh_tmux_trong_python_dung_ten_chinh_xac():
    """Moi ["tmux", ..., "-t", X] trong ma Python phai boc _tx(...) (core.tmuxten.chinh_xac) tru ten chuoi hang bat dau bang '='."""
    import re
    bad = []
    for d, _ds, fs in os.walk(os.path.join(GOC, "src")):
        for f in fs:
            if f.endswith(".py"):
                t = open(os.path.join(d, f), encoding="utf-8").read()
                for m in re.finditer(r'"tmux",[^\]\n]*?"-t", (?!_tx\()([^,\]\)]+)', t):
                    bad.append("%s: %s" % (f, m.group(0)[:80]))
    assert not bad, bad
