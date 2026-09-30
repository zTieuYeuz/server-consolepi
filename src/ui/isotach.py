# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Console Pi - Tu dong tach boot.wim / install.wim tu file ISO Windows.

VI SAO CO MUC NAY (anh Thoai yeu cau 19/09/2026): truoc day muon them 1 he
dieu hanh thi phai TU tay mount ISO tren 1 may Windows khac, mo thu muc
sources\\, chep rieng 2 file boot.wim va install.wim ra, roi tai len tung
file mot. Ngoai hien truong khong phai luc nao cung co san may Windows de
lam viec do - ma file ISO thi luon co san. Nay chi can tai thang ISO len,
Pi tu lam phan con lai.

CACH LAM (khong mount, khong can quyen dac biet):
    7z l -slt <iso>          -> doc MUC LUC cua ISO, biet chinh xac trong do
                                co file gi, duong dan nao, kich thuoc bao nhieu
    7z e -o<dir> <iso> <duong trong iso>
                             -> giai nen DUNG 2 FILE CAN, khong bung ca ISO
                                (bung het se ton them vai GB vo ich)

VI SAO KHONG MOUNT: mount ISO can quyen root + thiet bi loop, va neu tien
trinh chet giua chung thi ISO bi ket o trang thai da mount, lan sau khong
xoa duoc file. 7z doc thang file, chet giua chung khong de lai gi.

AN TOAN - KHONG BAO GIO XOA ISO TRUOC KHI KIEM CHUNG (anh Thoai dan ro:
"nho tao file check day du truoc khi xoa"). File ISO la thu anh Thoai vua
mat hang chuc phut tai len; xoa nham la mat trang. Vi vay truoc khi xoa,
2 file vua tach ra phai qua DU BA phep kiem tra THAT:

    1. Co ton tai va khac rong
    2. Kich thuoc KHOP TUNG BYTE voi so ghi trong muc luc ISO
       (bat duoc truong hop giai nen dut giua chung vi het dia/mat dien)
    3. wimlib doc duoc muc luc ben trong (`wiminfo`) - chung minh do that su
       la file WIM hop le chu khong phai 1 dong byte dung kich thuoc nhung
       hong ruot

Chi khi CA BA deu dat moi xoa ISO. Thieu bat ky dieu nao thi GIU NGUYEN ISO
va bao loi ro rang - tha ton dia con hon mat du lieu cua anh.
"""

import os
import shutil
import subprocess
import threading
import time

from .duongdan import DEPLOY_DIR

OS_DIR = os.path.join(DEPLOY_DIR, "os")

# Duong dan trong ISO Windows - viet thuong de so sanh khong phan biet hoa
TEN_BOOT = "sources/boot.wim"
TEN_INSTALL = ("sources/install.wim", "sources/install.esd")

# Chua dia trong toi thieu sau khi tach xong (GB) - de he thong con cho tho
DU_PHONG_GB = 1

# 7z tren Pi doc ISO 5-6GB tu the nho rat cham. 3 tieng la thua du nhung
# van co gioi han - khong bao gio de mot lenh chay mai mai khong ai cat.
HAN_GIO_7Z = 3 * 3600


def _lenh_7z():
    """
    Tra ve ten lenh 7-Zip co tren may nay, hoac None neu khong co.

    LOI THAT (26/09/2026, test ban ISO 32-bit Debian 12 bookworm): tach
    ISO Windows bao loi ngay buoc doc muc luc vi goi `7zip` cua bookworm
    CHI co /usr/bin/7zz - khong co lenh `7z`. Debian 13 trixie (Pi, ISO
    64-bit) thi goi 7zip co san ca `7z`; Pi OS cu dung p7zip-full cung la
    `7z`. Nen thu `7z` truoc (giu nguyen hanh vi cu), khong co moi dung
    `7zz` - hai lenh cung cu phap `l -slt` / `e -o`.
    """
    for ten in ("7z", "7zz"):
        if shutil.which(ten):
            return ten
    return None


LOI_THIEU_7Z = ("máy thiếu lệnh 7z/7zz (gói 7zip) - cài bằng lệnh: "
                "sudo apt install 7zip")


# ---------------------------------------------------------------- trang thai
#
# Mot viec tach duy nhat tai mot thoi diem. Dung 1 dict + 1 khoa, giong het
# _PAIR trong ui/network.py (mau da chay on dinh tu lau).
_TIEN = {
    "chay": False,
    "huy": False,          # nguoi dung bam Huy -> dung ngay, don sach
    "os_id": "",
    "buoc": 0,
    "tong_buoc": 5,
    "ten_buoc": "",
    "phan_tram": 0,
    "xong": None,          # None = chua xong, True/False = ket qua
    "loi": "",
    "nhat_ky": [],         # [(ten_buoc, "ok"/"loi"/"dang", chi_tiet), ...]
    "bat_dau": 0.0,
}
_KHOA = threading.Lock()


def trang_thai():
    """Ban sao trang thai hien tai - trang web goi moi 1-2 giay."""
    with _KHOA:
        d = dict(_TIEN)
        d["nhat_ky"] = list(_TIEN["nhat_ky"])
        d["giay"] = int(time.time() - _TIEN["bat_dau"]) if _TIEN["bat_dau"] else 0
        return d


def dang_chay():
    with _KHOA:
        return _TIEN["chay"]


_PROCS = []                # cac tien trinh 7z dang chay (de Huy ngat duoc ngay)


def da_huy():
    with _KHOA:
        return _TIEN["huy"]


def huy_tach():
    """Bam Huy: dat co huy va ngat ngay cac tien trinh 7z dang giai nen."""
    with _KHOA:
        if not _TIEN["chay"]:
            return False
        _TIEN["huy"] = True
        procs = list(_PROCS)
    for p in procs:
        try:
            p.terminate()
        except OSError:
            pass
    return True


def _dat(**kw):
    with _KHOA:
        _TIEN.update(kw)


def _buoc(so, ten, phan_tram=None):
    with _KHOA:
        _TIEN["buoc"] = so
        _TIEN["ten_buoc"] = ten
        if phan_tram is not None:
            _TIEN["phan_tram"] = phan_tram
        _TIEN["nhat_ky"].append([ten, "dang", ""])


def _xong_buoc(trang_thai_buoc, chi_tiet=""):
    with _KHOA:
        if _TIEN["nhat_ky"]:
            _TIEN["nhat_ky"][-1][1] = trang_thai_buoc
            _TIEN["nhat_ky"][-1][2] = chi_tiet


def _chay(cmd, timeout=120):
    """Chay lenh, LUON co gioi han thoi gian (quy tac chung cua du an)."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or ""), (r.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, "", "qua-thoi-gian-cho"
    except OSError as e:
        return 127, "", str(e)


# ------------------------------------------------------------- doc muc luc
def doc_muc_luc_iso(duong_iso):
    """
    Tra ve {duong_trong_iso_viet_thuong: kich_thuoc} cho cac file .wim/.esd.

    Dung `7z l -slt` (liet ke dang "ten = gia tri" tung dong) thay vi ban
    liet ke dang bang - ban dang bang cat cot theo do rong co dinh nen ten
    file dai bi cat cut, doc ra sai duong dan.
    """
    lenh = _lenh_7z()
    if not lenh:
        return None, LOI_THIEU_7Z
    ma, ra, loi = _chay([lenh, "l", "-slt", duong_iso], timeout=600)
    if ma != 0:
        return None, (loi or ra or "khong doc duoc ISO")[:200]
    muc = {}
    duong = None
    for dong in ra.split("\n"):
        dong = dong.strip()
        if dong.startswith("Path = "):
            duong = dong[7:].replace("\\", "/").strip()
        elif dong.startswith("Size = ") and duong:
            try:
                muc[duong.lower()] = int(dong[7:].strip())
            except ValueError:
                pass
            duong = None
    return muc, ""


def _con_trong(thu_muc):
    try:
        return shutil.disk_usage(thu_muc).free
    except OSError:
        return 0


def _co(n):
    """Kich thuoc doc duoc: file nho thi hien MB/KB chu khong phai "0.00 GB"."""
    for don_vi, chia in (("GB", 1024 ** 3), ("MB", 1024 ** 2), ("KB", 1024)):
        if n >= chia:
            return f"{n / chia:.2f} {don_vi}"
    return f"{int(n)} B"


# ------------------------------------------------------------------- worker
def _uu_tien_cao():
    """
    Tien to lenh de tien trinh giai nen duoc uu tien o dia + CPU cao nhat co
    the (anh Thoai 30/09/2026: "tan dung toi da suc manh cua may"). Chay duoi
    root nen nang duoc muc uu tien; khong co ionice/nice thi bo qua.
    """
    t = []
    if shutil.which("ionice"):
        t += ["ionice", "-c2", "-n0"]
    if os.geteuid() == 0 and shutil.which("nice"):
        t += ["nice", "-n", "-5"]
    return t


def _chay_huy(cmd, timeout):
    """
    Chay lenh nhu _chay() nhung NGAT DUOC ngay khi nguoi dung bam Huy
    (kiem tra moi 0,5 giay). Tra (ma, stdout, stderr); ma 130 = da huy.
    """
    try:
        p = subprocess.Popen(_uu_tien_cao() + cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True)
    except OSError as e:
        return 127, "", str(e)
    with _KHOA:
        _PROCS.append(p)
    t0 = time.time()
    try:
        while True:
            try:
                ra, loi = p.communicate(timeout=0.5)
                return p.returncode, ra or "", loi or ""
            except subprocess.TimeoutExpired:
                if da_huy():
                    p.terminate()
                    try:
                        p.wait(5)
                    except subprocess.TimeoutExpired:
                        p.kill()
                    return 130, "", "da-huy"
                if time.time() - t0 > timeout:
                    p.kill()
                    return 124, "", "qua-thoi-gian-cho"
    finally:
        with _KHOA:
            if p in _PROCS:
                _PROCS.remove(p)


def _theo_doi_kich_thuoc(duong_ra, cap_nhat, dung_lai):
    """
    Bao so byte THAT da ghi ra (doc kich thuoc file dang duoc ghi) - khong doan
    theo thoi gian (bai hoc tu man hinh cho kiosk: thanh doan theo thoi gian
    dung o 92% nhin y het bi treo).
    """
    while not dung_lai.is_set():
        try:
            cap_nhat(os.path.getsize(duong_ra))
        except OSError:
            pass
        dung_lai.wait(1.0)


def _giai_nen_1_file(duong_iso, duong_trong_iso, thu_muc_ra, ten_dich, cap_nhat):
    """
    Giai nen DUNG 1 file tu ISO ra thu_muc_ra/ten_dich. Moi file co thu muc
    tam RIENG (.tach-tam-<ten>) de 2 file giai nen SONG SONG khong dam nhau.
    """
    lenh = _lenh_7z()
    if not lenh:
        return False, LOI_THIEU_7Z
    thu_muc_tam = os.path.join(thu_muc_ra, ".tach-tam-" + ten_dich)
    shutil.rmtree(thu_muc_tam, ignore_errors=True)
    os.makedirs(thu_muc_tam, exist_ok=True)
    # 7z `e` giai nen PHANG (bo thu muc) va tu dat ten theo ten goc trong
    # ISO, nen phai giai ra thu muc tam roi doi ten - neu khong se de len
    # chinh file cu dang dung khi tach lai lan hai.
    ten_goc = duong_trong_iso.split("/")[-1]
    duong_theo_doi = os.path.join(thu_muc_tam, ten_goc)

    dung_lai = threading.Event()
    threading.Thread(target=_theo_doi_kich_thuoc,
                     args=(duong_theo_doi, cap_nhat, dung_lai), daemon=True).start()
    try:
        ma, ra, loi = _chay_huy([lenh, "e", f"-o{thu_muc_tam}", "-y",
                                 duong_iso, duong_trong_iso], HAN_GIO_7Z)
    finally:
        dung_lai.set()

    def don():
        shutil.rmtree(thu_muc_tam, ignore_errors=True)

    if ma == 130:
        don()
        return False, "Đã huỷ."
    if ma != 0:
        don()
        return False, (loi or ra or "7z bao loi")[-200:]
    if not os.path.isfile(duong_theo_doi):
        don()
        return False, "giai nen xong nhung khong thay file dau ra"
    # KHONG dua vao cho that ngay: file van nam trong thu muc tam cho toi khi
    # CA 2 file giai nen xong va qua kiem chung (xem _worker) - neu 1 file loi
    # giua chung thi file OS dang dung (vd "Tai lai") van nguyen ven, khong bi
    # tron 2 phien ban.
    duong_tam = os.path.join(thu_muc_tam, ten_dich)
    try:
        os.replace(duong_theo_doi, duong_tam)
    except OSError as e:
        don()
        return False, f"khong doi ten duoc: {e}"
    return True, duong_tam


def kiem_chung_wim(duong, mong_doi):
    """
    BA phep kiem tra THAT truoc khi dam xoa ISO goc. Tra (ok, chi_tiet).
    """
    if not os.path.isfile(duong):
        return False, "khong thay file"
    thuc = os.path.getsize(duong)
    if thuc == 0:
        return False, "file rong"
    if mong_doi and thuc != mong_doi:
        return False, (f"kich thuoc lech: co {thuc} byte, muc luc ISO ghi "
                       f"{mong_doi} byte (giai nen bi dut giua chung?)")
    ma, ra, loi = _chay(["wiminfo", duong], timeout=300)
    if ma != 0:
        # Loi tho cua wimlib dai vai dong, kem ca duong dan tuyet doi - vo
        # dung voi nguoi dung. Chi giu y chinh.
        tho = " ".join((loi or ra).split())
        if "not a WIM" in tho or "magic" in tho.lower():
            tho = "không phải file WIM hợp lệ"
        elif "unexpected end" in tho.lower() or "truncated" in tho.lower():
            tho = "file bị cụt (giải nén chưa xong)"
        else:
            tho = tho[-90:]
        return False, f"ruột file hỏng - {tho}"
    return True, f"{_co(thuc)}, wimlib đọc được mục lục bên trong"


def don_thu_muc_tam(thu_muc):
    """Xoa moi thu tam cua viec tach (.tach-tam*, *.dangtach) trong thu muc OS."""
    try:
        for ten in os.listdir(thu_muc):
            if ten.startswith(".tach-tam") or ten.endswith(".dangtach"):
                x = os.path.join(thu_muc, ten)
                if os.path.isdir(x):
                    shutil.rmtree(x, ignore_errors=True)
                else:
                    try:
                        os.remove(x)
                    except OSError:
                        pass
    except OSError:
        pass


def _worker(os_id, duong_iso, xoa_iso_sau_khi_xong):
    thu_muc = os.path.dirname(duong_iso)
    try:
        # --- 1. Doc muc luc ISO
        _buoc(1, "Đọc mục lục file ISO", 2)
        muc, loi = doc_muc_luc_iso(duong_iso)
        if muc is None:
            _xong_buoc("loi", loi)
            _dat(xong=False, loi=f"Không đọc được file ISO: {loi}")
            return
        d_boot = next((k for k in muc if k == TEN_BOOT), None)
        d_inst = next((k for k in muc if k in TEN_INSTALL), None)
        if not d_boot or not d_inst:
            co_gi = ", ".join(sorted(k for k in muc if k.endswith((".wim", ".esd")))[:6]) or "không có file .wim/.esd nào"
            _xong_buoc("loi", f"trong ISO chỉ thấy: {co_gi}")
            _dat(xong=False, loi=(
                "File ISO này không có đủ sources/boot.wim và "
                "sources/install.wim - có thể không phải ISO cài Windows."))
            return
        cd_boot, cd_inst = muc[d_boot], muc[d_inst]
        la_esd = d_inst.endswith(".esd")
        _xong_buoc("ok", f"boot.wim {_co(cd_boot)} · "
                         f"{'install.esd' if la_esd else 'install.wim'} {_co(cd_inst)}")

        # --- 2. Kiem tra dung luong
        _buoc(2, "Kiểm tra dung lượng trống", 5)
        can = cd_boot + cd_inst + DU_PHONG_GB * (1024 ** 3)
        trong = _con_trong(thu_muc)
        if trong < can:
            _xong_buoc("loi", f"cần {_co(can)}, chỉ còn {_co(trong)}")
            _dat(xong=False, loi=(
                f"Không đủ dung lượng: cần thêm {_co(can)} nhưng chỉ còn "
                f"{_co(trong)}. Xoá bớt hệ điều hành/ứng dụng cũ rồi thử lại "
                f"(file ISO vẫn được giữ nguyên)."))
            return
        _xong_buoc("ok", f"cần {_co(can)}, còn {_co(trong)}")

        # --- 3. Tach boot.wim VA install.wim SONG SONG (30/09/2026, anh Thoai:
        # "tan dung toi da suc manh cua may de lam nhanh nhat"): 2 tien trinh 7z
        # chay cung luc, uu tien o dia + CPU cao nhat. install.wim chiem ~93%
        # thoi gian nen loi thuc te nam o viec khong de o dia roi; boot.wim di
        # kem mien phi.
        ten_dich = "install.esd" if la_esd else "install.wim"
        _buoc(3, f"Tách boot.wim và {ten_dich} cùng lúc", 6)
        da_ghi = {"boot": 0, "inst": 0}
        tong_can = max(1, cd_boot + cd_inst)

        def cap_nhat(khoa):
            def f(n):
                da_ghi[khoa] = n
                _dat(phan_tram=int(6 + 82 * min(1.0, (da_ghi["boot"] + da_ghi["inst"]) / tong_can)))
            return f

        kq = {}

        def lam(khoa, duong_trong, dich):
            kq[khoa] = _giai_nen_1_file(duong_iso, duong_trong, thu_muc, dich, cap_nhat(khoa))

        cac_luong = [threading.Thread(target=lam, args=("boot", d_boot, "boot.wim")),
                     threading.Thread(target=lam, args=("inst", d_inst, ten_dich))]
        for lg in cac_luong:
            lg.start()
        for lg in cac_luong:
            lg.join()
        if da_huy():
            _xong_buoc("loi", "đã huỷ")
            _dat(xong=False, loi="Đã huỷ.")
            return
        for khoa, ten in (("boot", "boot.wim"), ("inst", ten_dich)):
            ok, loi = kq.get(khoa, (False, "khong chay"))
            if not ok:
                _xong_buoc("loi", f"{ten}: {loi}")
                _dat(xong=False, loi=f"Tách {ten} thất bại: {loi}")
                return
        _xong_buoc("ok", f"boot.wim {_co(cd_boot)} · {ten_dich} {_co(cd_inst)}")

        # --- 4. Kiem chung TRUOC khi dam xoa/ghi de bat cu thu gi (2 file song
        # song). Kiem chung ngay tren file TAM - chua dong toi file that.
        _buoc(4, "Kiểm chứng 2 file vừa tách", 90)
        kc = {}

        def kiem(khoa, duong, chuan):
            kc[khoa] = kiem_chung_wim(duong, chuan)

        cac_luong = [threading.Thread(target=kiem, args=("boot", kq["boot"][1], cd_boot)),
                     threading.Thread(target=kiem, args=("inst", kq["inst"][1], cd_inst))]
        for lg in cac_luong:
            lg.start()
        for lg in cac_luong:
            lg.join()
        (ok_b, ct_b), (ok_i, ct_i) = kc["boot"], kc["inst"]
        if not (ok_b and ok_i):
            # DON SACH file vua tach ra khi kiem chung truot.
            #
            # LY DO THAT (bat duoc khi tu thu voi 1 ISO ruot hong, truoc khi
            # dua vao dung): neu de lai, thu muc OS se co dung 2 file ten
            # "boot.wim"/"install.wim" nhung ruot hong - ma cac cho khac
            # trong du an (lay_os -> co_boot_wim, bang "San sang PXE") chi
            # kiem tra FILE CO TON TAI HAY KHONG. Ket qua: giao dien bao
            # xanh "Da co" trong khi thuc te khong boot duoc, va chi vo ra
            # luc dang cai that cho khach - dung kieu loi te nhat.
            # Xoa di thi trang thai hien dung: "Chua co", moi nguoi biet
            # phai lam lai. ISO VAN GIU NGUYEN de tach lai.
            # (Nay file tach nam trong thu muc TAM nen khong co gi o cho that de
            # xoa; thu muc tam duoc don o khoi finally. File OS dang dung, neu co,
            # van nguyen ven.)
            _xong_buoc("loi", f"boot.wim: {ct_b} | {ten_dich}: {ct_i}")
            _dat(xong=False, loi=(
                "File tách ra KHÔNG qua được kiểm chứng. Đã bỏ 2 file hỏng "
                "đó và GIỮ NGUYÊN file ISO để bạn tách lại. "
                f"Lý do - boot.wim: {ct_b}; {ten_dich}: {ct_i}."))
            return
        # Qua kiem chung -> moi dua vao cho that (doi ten nguyen tu, cung o dia)
        try:
            os.replace(kq["boot"][1], os.path.join(thu_muc, "boot.wim"))
            os.replace(kq["inst"][1], os.path.join(thu_muc, ten_dich))
        except OSError as e:
            _xong_buoc("loi", f"không đưa được file vào chỗ: {e}")
            _dat(xong=False, loi=f"Không đưa được file vào thư mục hệ điều hành: {e}")
            return
        _xong_buoc("ok", f"boot.wim: {ct_b} · {ten_dich}: {ct_i}")

        # --- 6. Don dep
        _buoc(5, "Dọn file không cần nữa", 95)
        da_xoa = []
        for thua in ("install.wim", "install.esd"):
            if thua != ten_dich and os.path.isfile(os.path.join(thu_muc, thua)):
                try:
                    os.remove(os.path.join(thu_muc, thua))
                    da_xoa.append(f"{thua} cũ")
                except OSError:
                    pass
        if xoa_iso_sau_khi_xong:
            cd_iso = os.path.getsize(duong_iso)
            try:
                os.remove(duong_iso)
                da_xoa.append(f"{os.path.basename(duong_iso)} ({_co(cd_iso)})")
            except OSError as e:
                _xong_buoc("loi", f"không xoá được ISO: {e}")
                _dat(xong=True, phan_tram=100, loi="")
                return
        # Thu muc tam + file do cua moi lan tach - khong bao gio de lai rac
        don_thu_muc_tam(thu_muc)
        _xong_buoc("ok", ("đã xoá " + ", ".join(da_xoa)) if da_xoa
                          else "giữ lại file ISO theo yêu cầu")

        _dat(xong=True, phan_tram=100, loi="")
    except Exception as e:                      # khong de luong nen chet am
        _xong_buoc("loi", f"{type(e).__name__}: {e}")
        _dat(xong=False, loi=f"Lỗi bất ngờ: {type(e).__name__}: {e}")
    finally:
        don_thu_muc_tam(thu_muc)
        # BAI HOC TU _pair_worker (ui/network.py): dong nay PHAI nam trong
        # finally ngoai cung. Neu khong, mot loi bat ngo se lam trang thai
        # ket cung o "dang chay" MAI MAI, moi lan tach sau deu bi tu choi ma
        # nguoi dung khong hieu vi sao, phai khoi dong lai ca dashboard.
        _dat(chay=False)


def bat_dau_tach(os_id, duong_iso, xoa_iso_sau_khi_xong=True):
    """Bat dau tach o luong nen. Tra (ok, thong_bao)."""
    if not os.path.isfile(duong_iso):
        return False, "Không thấy file ISO."
    with _KHOA:
        if _TIEN["chay"]:
            return False, (f"Đang tách ISO cho \"{_TIEN['os_id']}\" - "
                           "đợi xong rồi làm tiếp cái này.")
        _TIEN.update({
            "chay": True, "huy": False, "os_id": os_id, "buoc": 0, "ten_buoc": "",
            "phan_tram": 0, "xong": None, "loi": "", "nhat_ky": [],
            "bat_dau": time.time(),
        })
    threading.Thread(target=_worker,
                     args=(os_id, duong_iso, xoa_iso_sau_khi_xong),
                     daemon=True).start()
    return True, "Đã bắt đầu tách file ISO."
