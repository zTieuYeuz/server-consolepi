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
    env = dict(os.environ, TMUX_TMPDIR=str(tmp_path), CS_SSH_YC=str(tmp_path / "yc"), CS_SSH_HOME=str(tmp_path / "home"))
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
        hien = man_hinh()
        assert "-e none" in hien and "PermitLocalCommand=no" in hien and "admin@10.0.0.5" in hien
        tmux("send-keys", "-t", "ssh-test", "xin-chao", "Enter")
        assert cho("NHAN:[xin-chao]"), man_hinh()                                        # sau khi noi ssh, phim toi ssh; truoc do khong lan
        assert cho("Kết nối SSH đã kết thúc", 10)
        # yeu cau xau bi tu choi, khong chay gi
        json.dump({"host": "-oProxyCommand=id", "user": "admin", "port": 22}, open(os.path.join(env["CS_SSH_YC"], "ssh-test.json"), "w"))
        assert cho("không hợp lệ")
        assert "uid=" not in man_hinh()
    finally:
        tmux("kill-server")
