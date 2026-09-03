"""
Console Pi Network Tools - Ping lien tuc kem do thi song

Danh cho tinh huong rat thuc te: ky thuat vien vua rung/uon lai tung doan
day mang vua muon nhin THAY NGAY luc nao goi tin bat dau roi - cach chan
doan cap chap chon kinh dien bang tay. Bam Bat dau, do thi tu ve lien tuc,
uon day toi dau thay dut quang thi biet ngay doan do co van de.

MAU THIET KE: giong het _SCAN_CACHE (quet WiFi) va _PAIR (ghep Bluetooth)
da co trong ui/network.py - 1 dict toan cuc + 1 threading.Thread nen ghi
vao dict do, 1 ham doc trang thai cho route goi. Diem khac biet duy nhat:
ping can CAP NHAT SONG (moi giay) thay vi doi xong roi tai lai trang, nen
co them 1 route JSON rieng (/data) de JS phia trinh duyet tu poll va ve lai
canvas - khong dung thu vien bieu do ngoai (dung tinh than vkeyboard.js: tu
viet tay, khong phu thuoc gi them).

AN TOAN: dung threading.Event de bao dung (khong sua truc tiep bien
"running" tu ben ngoai - tranh tinh huong dua giua luong cu dang dong va
luong moi vua bat, da la loi thuc te tung gap voi co che tuong tu). Luon co
TRAN THOI GIAN TOI DA (30 phut) de mot luong nen bi quen khong bao gio chay
mai mai, dot het CPU/pin trong vo thuc.
"""
import re
import subprocess
import threading
import time

from flask import request, render_template_string, jsonify

from . import nettools_bp

TRAN_MAU_TOI_DA = 1800          # 30 phut du lieu (1 mau/giay)
TRAN_THOI_LUONG_GIAY = 1800     # khong cho chon qua 30 phut

_TRANG_THAI = {
    "running": False, "host": "", "iface": "eth0",
    "bat_dau_luc": 0.0, "mau": [], "ly_do_dung": None,
}
_SU_KIEN_DUNG = threading.Event()
_KHOA = threading.Lock()


def _mot_ping(host, iface, timeout=1.5):
    """1 lan ping don, tra ve (thanh_cong, rtt_ms|None)."""
    try:
        r = subprocess.run(
            ["ping", "-c", "1", "-W", str(timeout), "-I", iface, host],
            capture_output=True, text=True, timeout=timeout + 2,
        )
    except Exception:
        return False, None
    if r.returncode != 0:
        return False, None
    m = re.search(r"time=([\d.]+)", r.stdout)
    return True, (float(m.group(1)) if m else None)


def _luong_nen(host, iface, toi_da_giay):
    bat_dau = time.time()
    try:
        while not _SU_KIEN_DUNG.is_set():
            if time.time() - bat_dau > toi_da_giay:
                with _KHOA:
                    _TRANG_THAI["ly_do_dung"] = "het-thoi-luong-da-chon"
                break
            ok, rtt = _mot_ping(host, iface)
            with _KHOA:
                _TRANG_THAI["mau"].append({"t": time.time(), "ok": ok, "ms": rtt})
                if len(_TRANG_THAI["mau"]) > TRAN_MAU_TOI_DA:
                    _TRANG_THAI["mau"] = _TRANG_THAI["mau"][-TRAN_MAU_TOI_DA:]
            # Khong sleep(1) cung nhac vi ban than lenh ping da mat gan 1s -
            # tru di thoi gian da dung de nhip do gan dung 1 giay/mau.
            time.sleep(max(0.0, 1.0 - 0.05))
    finally:
        with _KHOA:
            _TRANG_THAI["running"] = False


def bat_dau(host, iface="eth0", thoi_luong_giay=600):
    if not host or not re.fullmatch(r"[A-Za-z0-9.\-:]{1,255}", host):
        return False, "Dia chi/hostname khong hop le."
    with _KHOA:
        if _TRANG_THAI["running"]:
            return False, "Dang co 1 phien theo doi khac chay - bam Dung truoc."
        thoi_luong_giay = max(10, min(int(thoi_luong_giay or 600), TRAN_THOI_LUONG_GIAY))
        _SU_KIEN_DUNG.clear()
        _TRANG_THAI.update(running=True, host=host, iface=iface,
                          bat_dau_luc=time.time(), mau=[], ly_do_dung=None)
    threading.Thread(target=_luong_nen, args=(host, iface, thoi_luong_giay),
                     daemon=True).start()
    return True, f"Da bat dau theo doi {host} qua {iface}."


def dung():
    with _KHOA:
        if not _TRANG_THAI["running"]:
            return False, "Khong co phien nao dang chay."
        _TRANG_THAI["ly_do_dung"] = "nguoi-dung-bam-dung"
    _SU_KIEN_DUNG.set()
    return True, "Da dung theo doi."


def trang_thai():
    with _KHOA:
        d = dict(_TRANG_THAI)
        d["mau"] = list(d["mau"])
    mau = d["mau"]
    tong = len(mau)
    thanh_cong = sum(1 for m in mau if m["ok"])
    rtts = [m["ms"] for m in mau if m["ok"] and m["ms"] is not None]
    d["thong_ke"] = {
        "tong_so": tong,
        "mat_goi_pct": round((tong - thanh_cong) * 100 / tong, 1) if tong else 0,
        "rtt_hien_tai": rtts[-1] if rtts else None,
        "rtt_min": round(min(rtts), 1) if rtts else None,
        "rtt_max": round(max(rtts), 1) if rtts else None,
        "rtt_avg": round(sum(rtts) / len(rtts), 1) if rtts else None,
    }
    return d


PING_MONITOR_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Ping lien tuc - Console Pi</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; background: #1e1e1e; color: #eee; padding: 20px; }
        h1 { color: #4CAF50; }
        a { color: #4CAF50; }
        input[type=text], input[type=number], select { padding: 8px; background: #333; color: #eee; border: 1px solid #555; }
        button { padding: 10px 20px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 15px; }
        button.red { background: #c0392b; }
        .card { background:#262626; border:1px solid #3a3a3a; border-left:4px solid #4CAF50;
                border-radius:6px; padding:14px 16px; margin-top:16px; }
        .err { background: #4a2d2d; border-left: 4px solid #f44336; padding: 12px 16px; border-radius: 4px; margin-top: 14px; }
        .hint { color: #999; font-size: 13px; }
        .stats { display:flex; gap:22px; flex-wrap:wrap; margin-top:6px; }
        .stat { min-width:110px; }
        .stat .so { font-size:22px; font-weight:700; }
        .stat .nhan { color:#999; font-size:12px; }
        #canvas_ping { background:#111; border-radius:6px; width:100%; height:220px; display:block; margin-top:12px; }
    </style>
</head>
<body>
    <h1>📈 Ping lien tuc (do thi song)</h1>
    <p><a href="/nettools">← Network Tools</a></p>
    <p class="hint">Bat len roi vua rung/uon lai tung doan day mang, vua nhin do thi - dut quang
    dung luc nao la biet doan do co van de. Tu dong dung sau toi da 30 phut de tranh chay quen.</p>

    <form id="form_bat_dau" method="POST" action="/nettools/ping-monitor/start" style="margin-top:16px;">
        <label>Dia chi can theo doi:</label>
        <input type="text" name="host" placeholder="vd 192.168.1.1" required>
        <label style="margin-left:10px;">Interface:</label>
        <select name="iface">
            <option value="eth0">eth0</option>
            <option value="wlan0">wlan0</option>
        </select>
        <label style="margin-left:10px;">Thoi luong toi da (giay):</label>
        <input type="number" name="thoi_luong_giay" value="600" min="10" max="1800" style="width:90px;">
        <button type="submit" style="margin-left:10px;" data-busy="Dang bat dau...">▶ Bat dau</button>
    </form>
    <form id="form_dung" method="POST" action="/nettools/ping-monitor/stop" style="margin-top:10px;">
        <button type="submit" class="red">⏹ Dung</button>
    </form>

    <div class="card">
        <div class="stats">
            <div class="stat"><div class="so" id="s_trang_thai">-</div><div class="nhan">Trang thai</div></div>
            <div class="stat"><div class="so" id="s_mat_goi">-</div><div class="nhan">Mat goi</div></div>
            <div class="stat"><div class="so" id="s_hien_tai">-</div><div class="nhan">RTT hien tai (ms)</div></div>
            <div class="stat"><div class="so" id="s_min_max">-</div><div class="nhan">RTT min/avg/max (ms)</div></div>
        </div>
        <canvas id="canvas_ping" width="900" height="220"></canvas>
    </div>

<script>
(function () {
  "use strict";
  var canvas = document.getElementById("canvas_ping");
  var ctx = canvas.getContext("2d");
  var hen_gio = null;

  function ve(mau) {
    var w = canvas.clientWidth || 900, h = canvas.clientHeight || 220;
    canvas.width = w; canvas.height = h;
    ctx.clearRect(0, 0, w, h);
    if (!mau.length) return;

    var rtts = mau.filter(function(m){return m.ok && m.ms != null;}).map(function(m){return m.ms;});
    var max_ms = Math.max(50, rtts.length ? Math.max.apply(null, rtts) * 1.2 : 50);
    var so_diem = mau.length;
    var buoc_x = w / Math.max(so_diem - 1, 1);

    // Duong ke ngang tham chieu
    ctx.strokeStyle = "#333"; ctx.lineWidth = 1;
    for (var g = 0; g <= 4; g++) {
      var y = h - (g / 4) * (h - 20) - 10;
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
    }

    // Duong RTT
    ctx.strokeStyle = "#4CAF50"; ctx.lineWidth = 2; ctx.beginPath();
    var dang_ve = false;
    mau.forEach(function (m, i) {
      var x = i * buoc_x;
      if (m.ok && m.ms != null) {
        var y = h - 10 - (m.ms / max_ms) * (h - 20);
        if (!dang_ve) { ctx.moveTo(x, y); dang_ve = true; } else { ctx.lineTo(x, y); }
      } else {
        dang_ve = false;
      }
    });
    ctx.stroke();

    // Cham do tai diem mat goi
    ctx.fillStyle = "#ff4d4d";
    mau.forEach(function (m, i) {
      if (!m.ok) {
        var x = i * buoc_x;
        ctx.beginPath(); ctx.arc(x, h - 8, 3, 0, Math.PI * 2); ctx.fill();
      }
    });
  }

  function cap_nhat() {
    fetch("/nettools/ping-monitor/data", { cache: "no-store" })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        document.getElementById("s_trang_thai").textContent = d.running ? ("Dang chay: " + d.host) : "Da dung";
        document.getElementById("s_mat_goi").textContent = d.thong_ke.mat_goi_pct + "%";
        document.getElementById("s_hien_tai").textContent = d.thong_ke.rtt_hien_tai != null ? d.thong_ke.rtt_hien_tai : "-";
        document.getElementById("s_min_max").textContent =
          (d.thong_ke.rtt_min != null) ? (d.thong_ke.rtt_min + " / " + d.thong_ke.rtt_avg + " / " + d.thong_ke.rtt_max) : "-";
        ve(d.mau);
        if (!d.running && hen_gio) { clearInterval(hen_gio); hen_gio = null; }
      })
      .catch(function () {});
  }

  hen_gio = setInterval(cap_nhat, 1000);
  cap_nhat();

  // Sau khi bam Bat dau/Dung (form POST binh thuong lam trang tai lai), cu
  // de trinh duyet submit form nhu binh thuong - script nay se tu chay lai
  // tu dau va bat dau poll ngay khi trang moi load xong.
})();
</script>
</body>
</html>
"""


@nettools_bp.route("/nettools/ping-monitor")
def ping_monitor_route():
    return render_template_string(PING_MONITOR_TEMPLATE)


@nettools_bp.route("/nettools/ping-monitor/start", methods=["POST"])
def ping_monitor_start_route():
    host = request.form.get("host", "").strip()
    iface = request.form.get("iface", "eth0")
    thoi_luong = request.form.get("thoi_luong_giay", "600")
    bat_dau(host, iface=iface, thoi_luong_giay=thoi_luong)
    from flask import redirect
    return redirect("/nettools/ping-monitor")


@nettools_bp.route("/nettools/ping-monitor/stop", methods=["POST"])
def ping_monitor_stop_route():
    dung()
    from flask import redirect
    return redirect("/nettools/ping-monitor")


@nettools_bp.route("/nettools/ping-monitor/data")
def ping_monitor_data_route():
    return jsonify(trang_thai())


if __name__ == "__main__":
    import sys
    host = sys.argv[1] if len(sys.argv) > 1 else "8.8.8.8"
    ok, msg = bat_dau(host, iface="eth0", thoi_luong_giay=8)
    print(msg)
    time.sleep(10)
    print(trang_thai()["thong_ke"])
