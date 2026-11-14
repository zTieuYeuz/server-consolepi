# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Console Pi Network Tools - PCAP Capture (netool.io Phan 8)

Bat goi tin bang tcpdump, uu tien ghi ra USB drive neu co cam, khong thi
ghi vao thu muc local. Cho phep xem lai bang tshark (convert sang text).
"""
from consolesystem.core import taisan as _taisan
import glob
import os
import re
import shutil
import signal
import subprocess
import time

from flask import request, render_template_string, send_from_directory, abort

from . import nettools_bp
from ui import duongdan as _DD


def _cong_mac_dinh():
    """Cong mac dinh cho o chon - cong co day that cua may nay (xem
    ui/phancung.py). Truoc day viet cung "eth0" nen chi dung tren Pi."""
    from ui.phancung import cong_mac_dinh
    return cong_mac_dinh()


def _o_chon_cong(dang_chon=""):
    """Cac the <option> liet ke dung cac cong THAT dang co tren may."""
    from ui.phancung import o_chon_cong
    return o_chon_cong(dang_chon)

LOCAL_CAPTURE_DIR = _DD.DIR_CAPTURES
MAX_DURATION_SEC = 600  # 10 phut, chan runaway capture lam day dia
MIN_FREE_MB = 200
MAX_FILE_MB = 200   # V5-3: vuot dung luong nay thi tu dung (khong day the nho du chua het gio)
MAU_CONG = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.:@-]{0,14}$")           # ten giao dien Linux (<= 15 ky tu), khong bat dau bang "-"
MAU_LOC = re.compile(r"^[A-Za-z0-9 .:/()!&|<>=\[\]_,+*%-]{0,200}$")      # cu phap BPF thong dung; khong co ky tu dac biet cua shell/nhay

# Trang thai capture dang chay (chi 1 phien tai 1 thoi diem cho don gian)
CAPTURE_STATE = {"proc": None, "pid": None, "file": None, "started": None}


def _ensure_local_dir():
    os.makedirs(LOCAL_CAPTURE_DIR, exist_ok=True)


def find_usb_capture_dir():
    """Neu co USB drive dang mount, tra ve thu muc tren do; khong thi None."""
    try:
        out = subprocess.run(
            ["lsblk", "-o", "NAME,TRAN,MOUNTPOINT", "-P"],
            capture_output=True, text=True, timeout=5
        ).stdout
    except Exception:
        return None

    for line in out.splitlines():
        fields = dict(
            kv.split("=", 1) for kv in line.replace('" ', '"\x00').split("\x00") if "=" in kv
        )
        tran = fields.get("TRAN", "").strip('"')
        mnt = fields.get("MOUNTPOINT", "").strip('"')
        if tran == "usb" and mnt:
            d = os.path.join(mnt, "console-pi-captures")
            try:
                os.makedirs(d, exist_ok=True)
                return d
            except Exception:
                continue
    return None


def get_capture_dir():
    return find_usb_capture_dir() or (_ensure_local_dir() or LOCAL_CAPTURE_DIR)


def free_space_mb(path):
    try:
        usage = shutil.disk_usage(path)
        return usage.free // (1024 * 1024)
    except Exception:
        return 0


def is_capturing():
    proc = CAPTURE_STATE.get("proc")
    return proc is not None and proc.poll() is None


def start_capture(iface=None, bpf_filter="", duration=60):
    if iface is None:
        iface = _cong_mac_dinh()
    if is_capturing():
        return {"ok": False, "error": "Đã có 1 phiên capture đang chạy."}

    if not MAU_CONG.fullmatch(iface or ""):
        return {"ok": False, "error": "Tên cổng mạng không hợp lệ."}
    bpf_filter = (bpf_filter or "").strip()
    if not MAU_LOC.fullmatch(bpf_filter) or any(t.startswith("-") for t in bpf_filter.split()):      # them lop phong thu: khong token nao giong tuy chon
        return {"ok": False, "error": "Bộ lọc chứa ký tự không hợp lệ (chỉ nhận cú pháp BPF thông thường, tối đa 200 ký tự)."}
    try:
        duration = max(5, min(int(duration or 60), MAX_DURATION_SEC))
    except (TypeError, ValueError):
        return {"ok": False, "error": "Thời lượng không hợp lệ."}
    capture_dir = get_capture_dir()

    if free_space_mb(capture_dir) < MIN_FREE_MB:
        return {"ok": False, "error": f"Không đủ dung lượng trống ({capture_dir})."}

    fname = f"capture_{iface}_{time.strftime('%Y%m%d_%H%M%S')}.pcap"
    fpath = os.path.join(capture_dir, fname)

    cmd = ["tcpdump", "-i", iface, "-w", fpath]
    if bpf_filter:
        cmd += ["--", bpf_filter]       # mot doi so sau "--": khong the chen tuy chon tcpdump (vd -z chay lenh, -w ghi tep khac)

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    except FileNotFoundError:
        return {"ok": False, "error": "Chưa cài tcpdump."}

    CAPTURE_STATE.update(proc=proc, pid=proc.pid, file=fpath, started=time.time())

    def _auto_stop():
        het = time.time() + duration
        while time.time() < het and CAPTURE_STATE.get("pid") == proc.pid and proc.poll() is None:
            try:
                if os.path.getsize(fpath) > MAX_FILE_MB * 1024 * 1024:
                    break                                     # V5-3: gioi han kich thuoc tep
            except OSError:
                pass
            time.sleep(1)
        if CAPTURE_STATE.get("pid") == proc.pid and proc.poll() is None:
            stop_capture()

    import threading
    threading.Thread(target=_auto_stop, daemon=True).start()

    return {"ok": True, "file": fpath, "duration": duration}


def stop_capture():
    proc = CAPTURE_STATE.get("proc")
    if proc is None or proc.poll() is not None:
        return {"ok": False, "error": "Không có phiên capture nào đang chạy."}
    try:
        proc.send_signal(signal.SIGTERM)
        proc.wait(timeout=5)
    except Exception:
        proc.kill()
    fpath = CAPTURE_STATE.get("file")
    CAPTURE_STATE.update(proc=None, pid=None)
    return {"ok": True, "file": fpath}


def list_captures():
    capture_dir = get_capture_dir()
    files = []
    for f in sorted(glob.glob(os.path.join(capture_dir, "*.pcap")), reverse=True):
        try:
            size = os.path.getsize(f)
        except OSError:
            size = 0
        txt = f + ".txt"
        files.append({
            "name": os.path.basename(f),
            "size_kb": size // 1024,
            "has_text": os.path.exists(txt),
        })
    return capture_dir, files


def convert_to_text(filename):
    capture_dir = get_capture_dir()
    if filename != os.path.basename(filename or ""):
        return {"ok": False, "error": "File không hợp lệ."}          # chan "../" va duong dan tuyet doi
    fpath = os.path.join(capture_dir, filename)
    if not os.path.isfile(fpath) or not filename.endswith(".pcap"):
        return {"ok": False, "error": "File không hợp lệ."}
    txt_path = fpath + ".txt"
    try:
        with open(txt_path, "w") as f:                      # ghi thang ra tep (khong giu ca ket qua trong bo nho)
            subprocess.run(["tshark", "-r", fpath, "-T", "text"], stdout=f, stderr=subprocess.DEVNULL, timeout=60)
        return {"ok": True, "file": os.path.basename(txt_path)}
    except FileNotFoundError:
        return {"ok": False, "error": "Chưa cài tshark."}
    except Exception as e:
        return {"ok": False, "error": str(e)}


PCAP_TEMPLATE = _taisan.doc("nettools/pcap.PCAP_TEMPLATE.html")


def _render(msg="", ok=True):
    capture_dir, files = list_captures()
    return render_template_string(
        PCAP_TEMPLATE, o_chon_cong=_o_chon_cong(), capture_dir=capture_dir, is_usb=("console-pi-captures" in capture_dir and capture_dir != LOCAL_CAPTURE_DIR),
        files=files, capturing=is_capturing(), current_file=CAPTURE_STATE.get("file"),
        msg=msg, ok=ok,
    )


@nettools_bp.route("/nettools/pcap")
def pcap_route():
    return _render()


@nettools_bp.route("/nettools/pcap/start", methods=["POST"])
def pcap_start_route():
    iface = request.form.get("iface") or _cong_mac_dinh()
    bpf_filter = (request.form.get("filter") or "").strip()
    duration = request.form.get("duration", 60)
    res = start_capture(iface=iface, bpf_filter=bpf_filter, duration=duration)
    if res["ok"]:
        return _render(msg=f"Đã bắt đầu capture: {res['file']} (tối đa {res['duration']} giây).", ok=True)
    return _render(msg=res["error"], ok=False)


@nettools_bp.route("/nettools/pcap/stop", methods=["POST"])
def pcap_stop_route():
    res = stop_capture()
    if res["ok"]:
        return _render(msg=f"Đã dừng capture: {res['file']}", ok=True)
    return _render(msg=res["error"], ok=False)


@nettools_bp.route("/nettools/pcap/convert", methods=["POST"])
def pcap_convert_route():
    filename = request.form.get("filename", "")
    res = convert_to_text(filename)
    if res["ok"]:
        return _render(msg=f"Đã chuyển đổi: {res['file']}", ok=True)
    return _render(msg=res["error"], ok=False)


@nettools_bp.route("/nettools/pcap/download/<path:filename>")
def pcap_download_route(filename):
    capture_dir = get_capture_dir()
    safe_name = os.path.basename(filename)
    if safe_name != filename or not os.path.isfile(os.path.join(capture_dir, safe_name)):
        abort(404)
    return send_from_directory(capture_dir, safe_name, as_attachment=True)


if __name__ == "__main__":
    import sys
    print("Capture dir:", get_capture_dir())
    print(start_capture(iface=sys.argv[1] if len(sys.argv) > 1 else _cong_mac_dinh(), duration=5))
    time.sleep(6)
    print("Files:", list_captures())
