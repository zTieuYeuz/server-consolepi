# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
[integrations] Giam sat ket noi RustDesk: nhan nhip + nhat ky kiem toan cua client RustDesk, ap che do ket noi, luu lich su 90 ngay, quan ly ban ghi hinh.

  * Client RustDesk (ban chinh thuc, may chu tu dung) tu gui ve "API server" = http://<may chu ID>:<cong ID - 2> (mac dinh 21114):
      - POST /api/heartbeat  {id, uuid, ver, conns:[ma ket noi dang mo]}  3 giay/lan khi co ket noi, 15 giay khi khong.
        Tra loi {"disconnect": [ma]} thi client NGAT ngay ket noi do (ke ca ket noi dang o buoc nhap mat khau).
      - POST /api/audit/conn {id, conn_id, session_id, action:new, ip} / {peer:[id, ten], type} (da xac thuc) / {action:close}
      - POST /api/sysinfo (ten may, nguoi dung, he dieu hanh) -> tra "SYSINFO_UPDATED".
    hbbs ban mien phi khong nghe cong nay; Console System nghe thay (luong rieng trong tien trinh web).
  * Che do (cai dat o trang RustDesk, ap cho MOI ket noi):
      - "thong_bao": khi co ket noi da xac thuc -> hien thong bao tren man hinh may (qua agent) ai dang ket noi.
      - "xin_phep":  ket noi chi duoc giu neu nguoi dung da bam Dong y trong vong 5 phut truoc do (hop thoai do Console hien qua agent,
                     nut Ket noi o buoc 5); moi ket noi khac bi ngat ngay qua nhip.
  * Gioi han: client chi gui duoc khi den duoc cong API (router NAT them cong P-2/TCP). Nhip/kiem toan khong co chu ky:
    ghim uuid theo ID lan dau thay (doi uuid -> bo qua) de may la khong gia mao ID da biet.
"""
import json
import os
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from consolesystem.core.nhatky import bo_qua as _bo_qua
from consolesystem.core.store import ghi_nguyen_tu
from consolesystem.integrations import rustdesk_may_chu as RD

CONG_API = 21114                     # cong noi bo; cong ngoai = cong ID ngoai - 2 (RustDesk tu tinh)
GIU_NGAY = 90
CHO_DUYET_GIAY = 300                 # hop thoai xin phep cho toi da 5 phut; dong y xong co 5 phut de bat dau ket noi
CHE_DO = ("thong_bao", "xin_phep")
LOAI_KET_NOI = {0: "Điều khiển", 1: "Truyền file", 2: "Chuyển cổng", 3: "Camera", 4: "Terminal"}

_KHOA = threading.Lock()
_TT = {}             # rustdesk id -> {luc, conns:set, ngat:set, uuid, ip}
_DUYET = {}          # rustdesk id -> {luc, nguoi, cho_phep:set(conn)}
_CHO_TEN = {}        # rustdesk id -> (luc, nguoi Console) : ai vua bam Ket noi o che do thong bao
_CO_PHIEN = set()    # rustdesk id da co ket noi tu lan lay ban ghi hinh truoc
_GHIM = {}           # rustdesk id -> uuid ghim lan dau (luu file, giu qua khoi dong lai)
_ID_BIET = {"luc": 0, "ds": set()}
_TB_LUC = {}         # rustdesk id -> luc thong bao gan nhat (toi da 1 thong bao / 60 giay / may)
LS_TOI_DA = 100 * 1024 * 1024        # lich su qua 100 MB thi ngung ghi (chong lam day dia)
_MAY_CHU = {"srv": None, "loi": ""}
_XU_LY = {"thong_bao": None}         # ham(rustdesk_id, noi_dung) do phan may tram (agent) dang ky


# ------------------------------------------------------------------ cai dat
def cai_dat():
    d = RD.doc_cfg()
    gb = d.get("ghi_hinh_gb", 20)
    return {"che_do": d.get("che_do") if d.get("che_do") in CHE_DO else "thong_bao", "ghi_hinh": bool(d.get("ghi_hinh")),
            "ghi_hinh_gb": gb if isinstance(gb, (int, float)) and gb > 0 else 20}


def luu_cai_dat(che_do, ghi_hinh, gb):
    if che_do not in CHE_DO:
        return False, "Chế độ không hợp lệ."
    try:
        gb = round(float(gb), 1)
    except (TypeError, ValueError):
        return False, "Dung lượng phải là số GB."
    if not 1 <= gb <= 10000:
        return False, "Dung lượng lưu ghi hình từ 1 đến 10000 GB."
    d = RD.doc_cfg()
    doi_ghi = bool(d.get("ghi_hinh")) != bool(ghi_hinh)
    d.update(che_do=che_do, ghi_hinh=bool(ghi_hinh), ghi_hinh_gb=gb)
    d.pop("duyet", None)
    RD.luu_cfg(d)
    don_ghi_hinh()
    return True, doi_ghi


# ------------------------------------------------------------------ lich su (jsonl, giu 90 ngay)
def _ls_file():
    return os.path.join(RD._goc(), "lich-su.jsonl")


def ghi_su_kien(**kw):
    kw["t"] = round(time.time(), 1)
    with _KHOA:
        os.makedirs(RD._goc(), mode=0o700, exist_ok=True)
        if os.path.isfile(_ls_file()) and os.path.getsize(_ls_file()) > LS_TOI_DA:
            return
        with open(_ls_file(), "a", encoding="utf-8") as f:
            f.write(json.dumps(kw, ensure_ascii=False) + "\n")


def _doc_su_kien():
    try:
        with open(_ls_file(), encoding="utf-8") as f:
            for dong in f:
                try:
                    yield json.loads(dong)
                except ValueError:
                    continue
    except OSError:
        return


def don_lich_su():
    """Bo su kien qua 90 ngay (chay moi ngay o vong nen)."""
    han = time.time() - GIU_NGAY * 86400
    with _KHOA:
        giu = [json.dumps(x, ensure_ascii=False) for x in _doc_su_kien() if x.get("t", 0) >= han]
        if os.path.isfile(_ls_file()):
            ghi_nguyen_tu(_ls_file(), ("\n".join(giu) + ("\n" if giu else "")).encode("utf-8"), 0o600)


def lich_su(ten_theo_id=None, gioi_han=500):
    """Gop su kien thanh cac dong: moi phien ket noi (new -> xac thuc -> close) + cac lan xin phep tu Console. Moi nhat truoc."""
    ten_theo_id = ten_theo_id or {}
    phien, mo, xin = [], {}, []

    def mo_phien(x, rid, k):
        p = {"bat_dau": x["t"], "ket_thuc": None, "rid": rid, "may": ten_theo_id.get(rid, ""), "ip": x.get("ip", ""), "nguoi": "", "peer": "",
             "loai": "", "kq": "Đang kết nối", "nguoi_console": "", "conn": x.get("conn")}
        mo[k] = p
        phien.append(p)
        return p

    for x in _doc_su_kien():
        rid, loai = str(x.get("rid", "")), x.get("loai")
        k = (rid, x.get("conn"))
        if loai == "kn_moi":
            mo_phien(x, rid, k)
        elif loai in ("kn_ngat", "kn_cho_phep") or (loai in ("kn_xac_thuc", "kn_dong") and k in mo):
            p = mo.get(k) or mo_phien(x, rid, k)           # nhip co the den truoc ban ghi "new"
            if loai == "kn_xac_thuc":
                p.update(peer=x.get("peer", ""), nguoi=x.get("ten", ""), loai=LOAI_KET_NOI.get(x.get("kieu"), str(x.get("kieu", ""))), kq="Đã vào")
            elif loai == "kn_cho_phep":
                p["nguoi_console"] = x.get("nguoi", "")
            elif loai == "kn_ngat":
                p["kq"] = "Bị ngắt: " + x.get("ly_do", "")
            else:
                p["ket_thuc"] = x["t"]
                if p["kq"] in ("Đang kết nối",):
                    p["kq"] = "Không vào được (sai mật khẩu hoặc tự hủy)"
                mo.pop(k, None)
        elif loai == "console":
            xin.append({"bat_dau": x["t"], "ket_thuc": None, "rid": rid, "may": x.get("ten_may") or ten_theo_id.get(rid, ""), "ip": "", "nguoi": "",
                        "peer": "", "loai": "Yêu cầu từ Console", "kq": x.get("kq", ""), "nguoi_console": x.get("nguoi", ""), "conn": None})
    ra = sorted(phien + xin, key=lambda p: p["bat_dau"], reverse=True)[:gioi_han]
    return ra


# ------------------------------------------------------------------ che do: duyet / thong bao
def dang_ky_thong_bao(ham):
    _XU_LY["thong_bao"] = ham


def dat_duyet(rid, nguoi):
    """Nguoi dung tren may vua bam Dong y: cho phep ket noi moi toi may nay trong 5 phut."""
    with _KHOA:
        _DUYET[str(rid)] = {"luc": time.time(), "nguoi": nguoi or "", "cho_phep": set()}


def dat_cho_ten(rid, nguoi):
    with _KHOA:
        _CHO_TEN[str(rid)] = (time.time(), nguoi or "")


def _duoc_phep(rid, conn, conns):
    """Ket noi conn co duoc giu khong (che do xin phep): trong 5 phut sau khi dong y, hoac khi phien da duoc phep cua lan dong y do van con mo."""
    d = _DUYET.get(rid)
    if not d:
        return None
    con_mo = d["cho_phep"] & conns
    if time.time() - d["luc"] <= CHO_DUYET_GIAY or con_mo:
        d["cho_phep"].add(conn)
        return d["nguoi"]
    _DUYET.pop(rid, None)
    return None


def _ghim_file():
    return os.path.join(RD._goc(), "uuid-ghim.json")


def _id_biet(rid):
    """Chi nhan ID da co trong Console (gan vao may) hoac da dang ky voi hbbs (doc lai toi da 1 lan / 60 giay)."""
    if time.time() - _ID_BIET["luc"] > 60:
        ds = {v.get("id") for v in RD.doc_cfg()["may"].values() if v.get("id")} | {x["id"] for x in RD.thiet_bi()}
        _ID_BIET.update(luc=time.time(), ds=ds)
    return rid in _ID_BIET["ds"]


def _hop_le(rid, uuid):
    """ID da biet + uuid khop ban ghim (lan dau thay thi ghim). Thieu uuid -> khong tin."""
    if not re.fullmatch(r"\d{6,12}", rid) or not uuid or not _id_biet(rid):
        return False
    with _KHOA:
        if not _GHIM:
            try:
                with open(_ghim_file(), encoding="utf-8") as f:
                    _GHIM.update(json.load(f))
            except (OSError, ValueError):
                _GHIM["_"] = ""
        if rid in _GHIM:
            return _GHIM[rid] == uuid
        _GHIM[rid] = uuid
        ghi_nguyen_tu(_ghim_file(), json.dumps({k: v for k, v in _GHIM.items() if k != "_"}).encode("utf-8"), 0o600)
        return True


def nhip(body, ip=""):
    """Xu ly POST /api/heartbeat. Tra dict tra loi cho client."""
    rid, uuid = str(body.get("id", ""))[:20], str(body.get("uuid", ""))[:200]
    if not _hop_le(rid, uuid):
        return {}
    conns = {c for c in (body.get("conns") or []) if isinstance(c, int)}
    che_do = cai_dat()["che_do"]
    moi_phep = []
    with _KHOA:
        st = _TT.setdefault(rid, {"conns": set(), "ngat": set()})
        st["luc"], st["ip"] = time.time(), ip
        if conns:
            _CO_PHIEN.add(rid)
        moi = conns - st["conns"]
        st["conns"] = conns
        st["ngat"] &= conns
        if che_do == "xin_phep":
            for c in sorted(moi):
                nguoi = _duoc_phep(rid, c, conns)
                if nguoi is None:
                    st["ngat"].add(c)
                else:
                    moi_phep.append((c, nguoi))
        ngat = sorted(st["ngat"])
    for c, nguoi in moi_phep:
        ghi_su_kien(loai="kn_cho_phep", rid=rid, conn=c, nguoi=nguoi)
    for c in sorted(moi & set(ngat)):
        ghi_su_kien(loai="kn_ngat", rid=rid, conn=c, ly_do="người dùng chưa cho phép")
    return {"disconnect": ngat} if ngat else {}


def kiem_toan(body, ip=""):
    """Xu ly POST /api/audit/conn. Chi nhan tu may da gui nhip (cung IP nguon voi nhip gan nhat)."""
    rid = str(body.get("id", ""))[:20]
    if not _hop_le(rid, str(body.get("uuid", ""))[:200]):
        return
    st = _TT.get(rid)
    if not st or (ip and st.get("ip") and st["ip"] != ip):
        return
    conn = body.get("conn_id") if isinstance(body.get("conn_id"), int) else None
    hd = body.get("action")
    if hd == "new":
        ghi_su_kien(loai="kn_moi", rid=rid, conn=conn, ip=str(body.get("ip", ""))[:60].replace("::ffff:", ""))
    elif hd == "close":
        ghi_su_kien(loai="kn_dong", rid=rid, conn=conn)
    elif isinstance(body.get("peer"), list) and len(body["peer"]) >= 2:
        peer_id, ten = str(body["peer"][0])[:20], str(body["peer"][1])[:80]
        kieu = body.get("type") if isinstance(body.get("type"), int) else None
        ghi_su_kien(loai="kn_xac_thuc", rid=rid, conn=conn, peer=peer_id, ten=ten, kieu=kieu)
        if cai_dat()["che_do"] == "thong_bao" and _XU_LY["thong_bao"] and time.time() - _TB_LUC.get(rid, 0) > 60:
            with _KHOA:
                _TB_LUC[rid] = time.time()
                luc, nguoi = _CHO_TEN.get(rid, (0, ""))
            ai = (nguoi + " (quản trị Console System)") if nguoi and time.time() - luc < CHO_DUYET_GIAY else (ten or ("máy " + peer_id))
            noi_dung = "%s đang kết nối vào máy tính của bạn bằng RustDesk (%s)." % (ai, LOAI_KET_NOI.get(kieu, "kết nối").lower())
            threading.Thread(target=_goi_thong_bao, args=(rid, noi_dung), daemon=True).start()


def _goi_thong_bao(rid, noi_dung):
    try:
        _XU_LY["thong_bao"](rid, noi_dung)
    except Exception as e:                              # may tat / mat agent: chi ghi nhat ky
        _bo_qua(e)


def lay_may_co_phien():
    """Cac ID vua co ket noi (de vong nen chi hoi may can lay ban ghi hinh), roi xoa danh sach."""
    with _KHOA:
        ra = set(_CO_PHIEN)
        _CO_PHIEN.clear()
        return ra


def trang_thai_nhip():
    """{rustdesk id: giay tu nhip cuoi} + so ket noi dang mo."""
    now = time.time()
    with _KHOA:
        return {k: {"cach": int(now - v.get("luc", 0)), "ket_noi": len(v["conns"])} for k, v in _TT.items()}


# ------------------------------------------------------------------ may chu HTTP cong 21114
class _XuLy(BaseHTTPRequestHandler):
    server_version = "ConsoleSystemRustDesk/1"

    def log_message(self, *a):                              # khong ghi moi nhip vao nhat ky
        pass

    def _tra(self, ma, noi_dung, kieu="application/json"):
        b = noi_dung.encode("utf-8")
        self.send_response(ma)
        self.send_header("Content-Type", kieu)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n > 256 * 1024:
            return self._tra(413, "{}")
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
        except ValueError:
            body = {}
        if not isinstance(body, dict):
            body = {}
        p = self.path.split("?")[0].rstrip("/")
        try:
            if p == "/api/heartbeat":
                return self._tra(200, json.dumps(nhip(body, self.client_address[0])))
            if p == "/api/audit/conn":
                kiem_toan(body, self.client_address[0])
                return self._tra(200, "")
            if p.startswith("/api/audit/"):
                return self._tra(200, "")
            if p == "/api/sysinfo":
                return self._tra(200, "SYSINFO_UPDATED", "text/plain")
            if p == "/api/sysinfo_ver":
                return self._tra(200, "", "text/plain")
        except Exception as e:
            _bo_qua(e)
            return self._tra(500, "{}")
        return self._tra(404, "{}")

    def do_GET(self):
        self._tra(404, "{}")


def khoi_dong():
    """Bat may chu nhan nhip (1 lan). Chi chay khi da cai may chu RustDesk. Tra (dang_chay, loi)."""
    with _KHOA:
        if _MAY_CHU["srv"]:
            return True, ""
        if not RD.da_cai():
            return False, "Chưa cài máy chủ RustDesk."
        try:
            srv = ThreadingHTTPServer(("0.0.0.0", CONG_API), _XuLy)
        except OSError as e:
            _MAY_CHU["loi"] = "Không mở được cổng %d (%s). Có chương trình khác đang dùng cổng này." % (CONG_API, e.strerror or e)
            return False, _MAY_CHU["loi"]
        srv.daemon_threads = True
        _MAY_CHU.update(srv=srv, loi="")
    threading.Thread(target=srv.serve_forever, daemon=True, name="rustdesk-api-21114").start()
    return True, ""


def tt_may_chu():
    return {"chay": bool(_MAY_CHU["srv"]), "loi": _MAY_CHU["loi"], "cong": CONG_API}


# ------------------------------------------------------------------ ghi hinh (luu tren Console System, gioi han GB)
def thu_muc_ghi_hinh():
    return os.path.join(RD._goc(), "ghi-hinh")


MAU_TEP_GHI = re.compile(r"[A-Za-z0-9_.\-]{1,200}\.(webm|mp4|mkv)")


def ds_ghi_hinh():
    """[{mid, ten, kich_thuoc, luc}] moi nhat truoc."""
    goc, ra = thu_muc_ghi_hinh(), []
    if not os.path.isdir(goc):
        return ra
    for mid in os.listdir(goc):
        d = os.path.join(goc, mid)
        if not os.path.isdir(d) or not re.fullmatch(r"[A-Za-z0-9_\-]{1,64}", mid):
            continue
        for ten in os.listdir(d):
            f = os.path.join(d, ten)
            if MAU_TEP_GHI.fullmatch(ten) and os.path.isfile(f):
                st = os.stat(f)
                ra.append({"mid": mid, "ten": ten, "kich_thuoc": st.st_size, "luc": int(st.st_mtime)})
    return sorted(ra, key=lambda x: x["luc"], reverse=True)


def duong_ghi_hinh(mid, ten):
    if not re.fullmatch(r"[A-Za-z0-9_\-]{1,64}", mid or "") or not MAU_TEP_GHI.fullmatch(ten or ""):
        return None
    f = os.path.join(thu_muc_ghi_hinh(), mid, ten)
    return f if os.path.isfile(f) else None


def don_ghi_hinh():
    """Xoa ban ghi CU NHAT cho toi khi tong dung luong <= gioi han GB. Tra so file da xoa."""
    gioi_han = cai_dat()["ghi_hinh_gb"] * 1024 ** 3
    ds = ds_ghi_hinh()
    tong, xoa = sum(x["kich_thuoc"] for x in ds), 0
    for x in reversed(ds):                                    # cu nhat truoc
        if tong <= gioi_han:
            break
        try:
            os.remove(os.path.join(thu_muc_ghi_hinh(), x["mid"], x["ten"]))
            tong -= x["kich_thuoc"]
            xoa += 1
        except OSError as e:
            _bo_qua(e)
    return xoa
