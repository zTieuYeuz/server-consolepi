"""
Console Pi - Kho file cai dat (ISO / firmware / image).

Muc dich: mang theo bo cai OS, firmware switch, image router... de cam vao
laptop tai xuong ngay tai cho khi khong co internet.

Ba diem phai lam dung, khong thi Pi chet hoac day dia:
  1. GHI THEO LUONG ra dia, KHONG nap ca file vao RAM. Pi 4 co 4GB, mot file
     ISO 5GB nap vao RAM la het may.
  2. CHAN TRUOC khi sap day dia - the nho day co the lam hong he thong file.
  3. nginx phai nang client_max_body_size, mac dinh 64m thi ISO nao cung truot.

Uu tien ghi ra USB neu co cam (giong co che cua PCAP), vi the nho cua Pi be.
"""
import hashlib
import os
import re
import shutil
import subprocess
import time

LOCAL_DIR = "/opt/console-pi/storage"
# Con lai duoi muc nay thi khong cho tai len nua
MIN_FREE_GB = 3

# Duoi file cho phep. Khong nhan .sh/.py/... de trang nay khong tro thanh
# cho nap ma tuy y len thiet bi.
ALLOWED_EXT = {".iso", ".img", ".bin", ".tar", ".gz", ".xz", ".zip", ".zst",
               ".pkg", ".ova", ".vmdk", ".qcow2", ".rom", ".fw", ".spa",
               ".conf", ".cfg", ".txt", ".pcap", ".pdf"}


def _usb_dir():
    """Thu muc tren USB dang cam, neu co."""
    try:
        out = subprocess.run(["lsblk", "-o", "TRAN,MOUNTPOINT", "-P"],
                             capture_output=True, text=True, timeout=5).stdout
    except Exception:
        return None
    for line in out.splitlines():
        tran = re.search(r'TRAN="([^"]*)"', line)
        mnt = re.search(r'MOUNTPOINT="([^"]*)"', line)
        if tran and mnt and tran.group(1) == "usb" and mnt.group(1):
            d = os.path.join(mnt.group(1), "console-pi-storage")
            try:
                os.makedirs(d, exist_ok=True)
                return d
            except OSError:
                continue
    return None


def storage_dir():
    d = _usb_dir()
    if d:
        return d, True
    os.makedirs(LOCAL_DIR, exist_ok=True)
    return LOCAL_DIR, False


def disk_stats(path):
    """(da_dung_GB, tong_GB, con_lai_GB, phan_tram)"""
    try:
        u = shutil.disk_usage(path)
        g = 1024 ** 3
        return u.used // g, u.total // g, u.free // g, round(u.used * 100 / u.total)
    except Exception:
        return 0, 0, 0, 0


def safe_name(name):
    """
    Chi giu ten file tran, bo moi thanh phan duong dan. Chan ca '..' lan
    duong dan tuyet doi - khong thi nguoi ta ghi de duoc file he thong.
    """
    name = os.path.basename(name or "").strip()
    name = re.sub(r"[^A-Za-z0-9._+ -]", "_", name)
    name = name.lstrip(".")          # khong cho file an
    return name[:150]


def ext_ok(name):
    return os.path.splitext(name)[1].lower() in ALLOWED_EXT


def list_files():
    d, on_usb = storage_dir()
    out = []
    try:
        for n in sorted(os.listdir(d)):
            p = os.path.join(d, n)
            if not os.path.isfile(p) or n.endswith(".sha256"):
                continue
            st = os.stat(p)
            sha = ""
            sp = p + ".sha256"
            if os.path.exists(sp):
                try:
                    sha = open(sp).read().split()[0][:16]
                except Exception:
                    pass
            out.append({"name": n, "size": st.st_size,
                        "mtime": time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime)),
                        "sha": sha})
    except OSError:
        pass
    return d, on_usb, out


def human_size(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{int(n)} B"
        n /= 1024.0
    return f"{n:.1f} GB"


def save_upload(fileobj):
    """
    Ghi theo tung khoi 1MB ra dia. Vua khong ton RAM, vua kiem tra dung luong
    trong LUC ghi - file 8GB gui len o nua duong het cho thi phai dung ngay,
    khong doi den cuoi.
    """
    d, _ = storage_dir()
    name = safe_name(getattr(fileobj, "filename", ""))
    if not name:
        return False, "Chua chon file."
    if not ext_ok(name):
        return False, (f"Khong nhan duoi file nay. Cho phep: "
                       f"{', '.join(sorted(ALLOWED_EXT))}")

    _, _, free_gb, _ = disk_stats(d)
    if free_gb < MIN_FREE_GB:
        return False, (f"Chi con {free_gb} GB trong - can it nhat {MIN_FREE_GB} GB. "
                       "Xoa bot file hoac cam USB.")

    dest = os.path.join(d, name)
    if os.path.exists(dest):
        stem, ext = os.path.splitext(name)
        name = f"{stem}_{time.strftime('%H%M%S')}{ext}"
        dest = os.path.join(d, name)

    tmp = dest + ".part"
    sha = hashlib.sha256()
    written = 0
    try:
        with open(tmp, "wb") as f:
            while True:
                chunk = fileobj.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)
                sha.update(chunk)
                written += len(chunk)
                # Kiem tra moi 200MB, khong phai moi khoi (goi statvfs ton kem)
                if written % (200 * 1024 * 1024) < 1024 * 1024:
                    if disk_stats(d)[2] < 1:
                        raise OSError("Het dung luong trong luc dang ghi")
        os.replace(tmp, dest)
    except Exception as e:
        try:
            os.remove(tmp)
        except OSError:
            pass
        return False, f"Loi khi luu: {e}"

    try:
        with open(dest + ".sha256", "w") as f:
            f.write(f"{sha.hexdigest()}  {name}\n")
    except OSError:
        pass
    return True, f"Da luu {name} ({human_size(written)}). SHA256: {sha.hexdigest()[:16]}..."


def delete_file(name):
    d, _ = storage_dir()
    name = safe_name(name)
    p = os.path.join(d, name)
    # Kiem tra lai sau khi giai duong dan that - chan moi kieu vuot thu muc
    if not name or os.path.realpath(p) != os.path.join(os.path.realpath(d), name):
        return False, "Ten file khong hop le."
    if not os.path.isfile(p):
        return False, "Khong tim thay file."
    try:
        os.remove(p)
        if os.path.exists(p + ".sha256"):
            os.remove(p + ".sha256")
    except OSError as e:
        return False, f"Khong xoa duoc: {e}"
    return True, f"Da xoa {name}."


# =============================================================== giao dien web
def register_storage(app):
    from flask import request, send_from_directory, abort
    from .layout import render_page
    from .home import _esc

    def page(msg="", ok=True):
        d, on_usb, files = list_files()
        used, total, free, pct = disk_stats(d)

        msg_html = f'<div class="msg {"ok" if ok else "err"}">{_esc(msg)}</div>' if msg else ""

        bar_color = "#4CAF50" if pct < 75 else ("#ffb74d" if pct < 90 else "#ff6b6b")
        noi_luu = (f"USB dang cam &mdash; <code>{_esc(d)}</code>" if on_usb
                   else f"The nho cua Pi &mdash; <code>{_esc(d)}</code>"
                        " <span style='color:#8b93a1;'>(cam USB vao se tu chuyen sang ghi ra USB)</span>")

        rows = ""
        for f in files:
            rows += f"""
            <tr>
              <td><strong>{_esc(f['name'])}</strong>
                  {f'<br><small style="color:#8b93a1;">SHA256 {_esc(f["sha"])}...</small>' if f['sha'] else ''}</td>
              <td>{human_size(f['size'])}</td>
              <td style="color:#8b93a1;">{f['mtime']}</td>
              <td>
                <a class="btn small" href="/storage/tai/{_esc(f['name'])}">Tai ve</a>
                <form method="POST" action="/storage/xoa" style="display:inline;"
                      onsubmit="return confirm('Xoa {_esc(f['name'])}?');">
                  <input type="hidden" name="name" value="{_esc(f['name'])}">
                  <button type="submit" class="red small">Xoa</button>
                </form>
              </td>
            </tr>"""

        du_cho = free >= MIN_FREE_GB
        upload_html = f"""
        <form method="POST" action="/storage/len" enctype="multipart/form-data">
          <label>Chon file (ISO, IMG, firmware, cau hinh...)</label>
          <input type="file" name="file" required>
          <div class="row" style="margin-top:13px;">
            <button type="submit" data-busy="Dang tai len, dung dong trang...">⬆ Tai len</button>
            <span style="color:#8b93a1;font-size:13px;margin-left:10px;">
              File lon mat vai phut. Trang se dung yen cho den khi xong.</span>
          </div>
        </form>""" if du_cho else f"""
        <div class="msg err">Chi con {free} GB trong. Xoa bot file hoac cam USB
        truoc khi tai them (can it nhat {MIN_FREE_GB} GB de he thong chay an toan).</div>"""

        body = f"""
        {msg_html}
        <div class="card">
          <h3>Noi dang luu</h3>
          <p style="margin:0 0 11px;">{noi_luu}</p>
          <div style="background:#20242c;border-radius:5px;height:19px;overflow:hidden;max-width:520px;">
            <div style="background:{bar_color};height:100%;width:{pct}%;"></div>
          </div>
          <p style="color:#8b93a1;font-size:13px;margin:7px 0 0;">
            Da dung {used} GB / {total} GB &nbsp;&middot;&nbsp; con trong <strong>{free} GB</strong></p>
        </div>

        <h2>Tai file len</h2>
        <div class="card">{upload_html}</div>

        <h2>File dang co ({len(files)})</h2>
        <table>
          <tr><th>Ten file</th><th style="width:110px;">Kich thuoc</th>
              <th style="width:140px;">Ngay luu</th><th style="width:170px;">Thao tac</th></tr>
          {rows}
        </table>
        {'<p style="color:#8b93a1;">Chua co file nao. Tai bo cai OS, firmware switch, hay file cau hinh len de mang theo dung khi khong co internet.</p>' if not files else ''}"""

        return render_page(body, active="/storage", title="Kho file",
                           subtitle="Mang theo bo cai OS, firmware, cau hinh")

    @app.route("/storage")
    def storage_page():
        return page()

    @app.route("/storage/len", methods=["POST"])
    def storage_upload():
        f = request.files.get("file")
        if not f:
            return page(msg="Chua chon file.", ok=False)
        ok_u, msg = save_upload(f)
        return page(msg=msg, ok=ok_u)

    @app.route("/storage/xoa", methods=["POST"])
    def storage_delete():
        ok_d, msg = delete_file(request.form.get("name", ""))
        return page(msg=msg, ok=ok_d)

    @app.route("/storage/tai/<path:name>")
    def storage_download(name):
        d, _ = storage_dir()
        n = safe_name(name)
        if not n or os.path.realpath(os.path.join(d, n)) != os.path.join(os.path.realpath(d), n):
            abort(404)
        if not os.path.isfile(os.path.join(d, n)):
            abort(404)
        return send_from_directory(d, n, as_attachment=True)
