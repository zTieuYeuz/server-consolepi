"""
Console Pi Network Tools - PCAP Capture (netool.io Phan 8)

Bat goi tin bang tcpdump, uu tien ghi ra USB drive neu co cam, khong thi
ghi vao thu muc local. Cho phep xem lai bang tshark (convert sang text).
"""
import glob
import os
import shutil
import signal
import subprocess
import time

from flask import request, render_template_string, send_from_directory, abort

from . import nettools_bp

LOCAL_CAPTURE_DIR = "/opt/console-pi/captures"
MAX_DURATION_SEC = 600  # 10 phut, chan runaway capture lam day dia
MIN_FREE_MB = 200

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


def start_capture(iface="eth0", bpf_filter="", duration=60):
    if is_capturing():
        return {"ok": False, "error": "Da co 1 phien capture dang chay."}

    duration = max(5, min(int(duration or 60), MAX_DURATION_SEC))
    capture_dir = get_capture_dir()

    if free_space_mb(capture_dir) < MIN_FREE_MB:
        return {"ok": False, "error": f"Khong du dung luong trong ({capture_dir})."}

    fname = f"capture_{iface}_{time.strftime('%Y%m%d_%H%M%S')}.pcap"
    fpath = os.path.join(capture_dir, fname)

    cmd = ["tcpdump", "-i", iface, "-w", fpath]
    if bpf_filter:
        cmd += bpf_filter.split()

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    except FileNotFoundError:
        return {"ok": False, "error": "Chua cai tcpdump."}

    CAPTURE_STATE.update(proc=proc, pid=proc.pid, file=fpath, started=time.time())

    def _auto_stop():
        time.sleep(duration)
        if CAPTURE_STATE.get("pid") == proc.pid and proc.poll() is None:
            stop_capture()

    import threading
    threading.Thread(target=_auto_stop, daemon=True).start()

    return {"ok": True, "file": fpath, "duration": duration}


def stop_capture():
    proc = CAPTURE_STATE.get("proc")
    if proc is None or proc.poll() is not None:
        return {"ok": False, "error": "Khong co phien capture nao dang chay."}
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
    fpath = os.path.join(capture_dir, filename)
    if not os.path.isfile(fpath) or not filename.endswith(".pcap"):
        return {"ok": False, "error": "File khong hop le."}
    txt_path = fpath + ".txt"
    try:
        result = subprocess.run(
            ["tshark", "-r", fpath, "-T", "text"],
            capture_output=True, text=True, timeout=60
        )
        with open(txt_path, "w") as f:
            f.write(result.stdout)
        return {"ok": True, "file": os.path.basename(txt_path)}
    except FileNotFoundError:
        return {"ok": False, "error": "Chua cai tshark."}
    except Exception as e:
        return {"ok": False, "error": str(e)}


PCAP_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>PCAP Capture - Console Pi</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; background: #1e1e1e; color: #eee; padding: 20px; }
        h1 { color: #4CAF50; }
        a { color: #4CAF50; }
        table { width: 100%; border-collapse: collapse; margin-top: 16px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #444; }
        th { background: #2d2d2d; }
        input[type=text], select, input[type=number] { padding: 8px; background: #333; color: #eee; border: 1px solid #555; }
        button { padding: 9px 16px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; }
        button.stop { background: #f44336; }
        .err { background: #4a2d2d; border-left: 4px solid #f44336; padding: 12px 16px; border-radius: 4px; margin-top: 14px; }
        .ok { background: #2d4a2d; border-left: 4px solid #4CAF50; padding: 12px 16px; border-radius: 4px; margin-top: 14px; }
        .hint { color: #999; font-size: 13px; margin-top: 6px; }
    </style>
</head>
<body>
    <h1>📼 PCAP Capture</h1>
    <p><a href="/nettools">← Network Tools</a></p>
    <p class="hint">Thu muc dang dung: <code>{{ capture_dir }}</code>
    {% if is_usb %}(USB drive){% else %}(dia cuc bo Pi - nen cam USB de an toan hon){% endif %}</p>

    {% if msg %}<div class="{{ 'ok' if ok else 'err' }}">{{ msg }}</div>{% endif %}

    {% if capturing %}
    <form method="POST" action="/nettools/pcap/stop">
        <p>⏺ Dang capture: <strong>{{ current_file }}</strong></p>
        <button type="submit" class="stop">⏹ Dung capture</button>
    </form>
    {% else %}
    <form method="POST" action="/nettools/pcap/start">
        <label>Interface:</label>
        <select name="iface">
            <option value="eth0">eth0</option>
            <option value="wlan0">wlan0</option>
        </select>
        <label style="margin-left:10px;">BPF filter (tuy chon):</label>
        <input type="text" name="filter" placeholder="vd port 80">
        <label style="margin-left:10px;">Thoi luong (giay):</label>
        <input type="number" name="duration" value="60" min="5" max="600" style="width:80px;">
        <button type="submit" style="margin-left:10px;">⏺ Bat dau</button>
    </form>
    {% endif %}

    <h3 style="color:#4CAF50; margin-top:24px;">File da capture</h3>
    <table>
        <tr><th>Ten file</th><th>Kich thuoc</th><th>Hanh dong</th></tr>
        {% for f in files %}
        <tr>
            <td>{{ f.name }}</td>
            <td>{{ f.size_kb }} KB</td>
            <td>
                <a href="/nettools/pcap/download/{{ f.name }}">Tai ve</a>
                {% if f.has_text %}
                | <a href="/nettools/pcap/download/{{ f.name }}.txt">Xem text</a>
                {% else %}
                | <form method="POST" action="/nettools/pcap/convert" style="display:inline;">
                    <input type="hidden" name="filename" value="{{ f.name }}">
                    <button type="submit" style="padding:4px 10px;">Convert sang text</button>
                  </form>
                {% endif %}
            </td>
        </tr>
        {% endfor %}
    </table>
    {% if not files %}<p>Chua co file capture nao.</p>{% endif %}
</body>
</html>
"""


def _render(msg="", ok=True):
    capture_dir, files = list_captures()
    return render_template_string(
        PCAP_TEMPLATE, capture_dir=capture_dir, is_usb=("console-pi-captures" in capture_dir and capture_dir != LOCAL_CAPTURE_DIR),
        files=files, capturing=is_capturing(), current_file=CAPTURE_STATE.get("file"),
        msg=msg, ok=ok,
    )


@nettools_bp.route("/nettools/pcap")
def pcap_route():
    return _render()


@nettools_bp.route("/nettools/pcap/start", methods=["POST"])
def pcap_start_route():
    iface = request.form.get("iface", "eth0")
    bpf_filter = (request.form.get("filter") or "").strip()
    duration = request.form.get("duration", 60)
    res = start_capture(iface=iface, bpf_filter=bpf_filter, duration=duration)
    if res["ok"]:
        return _render(msg=f"Da bat dau capture: {res['file']} (toi da {res['duration']}s).", ok=True)
    return _render(msg=res["error"], ok=False)


@nettools_bp.route("/nettools/pcap/stop", methods=["POST"])
def pcap_stop_route():
    res = stop_capture()
    if res["ok"]:
        return _render(msg=f"Da dung capture: {res['file']}", ok=True)
    return _render(msg=res["error"], ok=False)


@nettools_bp.route("/nettools/pcap/convert", methods=["POST"])
def pcap_convert_route():
    filename = request.form.get("filename", "")
    res = convert_to_text(filename)
    if res["ok"]:
        return _render(msg=f"Da convert: {res['file']}", ok=True)
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
    print(start_capture(iface=sys.argv[1] if len(sys.argv) > 1 else "eth0", duration=5))
    time.sleep(6)
    print("Files:", list_captures())
