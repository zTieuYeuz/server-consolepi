# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Unattend - bang kiem tra sau cai (muc kiem, lenh reg, buoc nguoi dung).

(B4: tach nguyen van tu unattend.py; ten ham/hang giu nguyen, nguon van re-export.)"""
import re
from ui import deployos as _d
from ui import datten as _tm
from consolesystem.features.deploy_os.un_goapp_font import (APP_RAC, THU_MUC_TREN_MAY, THU_MUC_UNGDUNG_TREN_MAY, _bo_font_cai_duoc, _lenh_cai_app, _lenh_cai_bo_font, _lenh_cai_ungdung, _lenh_go_app, _lenh_mot_script, _lenh_theo_pha)  # noqa: F401
from consolesystem.features.deploy_os.un_tuychon import (TUY_CHON_WINDOWS)  # noqa: F401


def _phan_tich_lenh_reg(lenh):
    r"""
    Doc 1 lenh `reg add` roi suy ra CACH KIEM TRA lai chinh no.

    VI SAO LAM VAY thay vi viet san 1 bang "tuy chon -> cach kiem tra":
    hai danh sach song song nhu vay chac chan se lech nhau theo thoi gian
    (sua lenh o TUY_CHON_WINDOWS ma quen sua bang kiem tra -> bao cao noi
    doi ma khong ai biet). Suy thang tu chinh lenh se chay thi khong bao
    gio lech duoc.

    Tra ve None neu khong phai `reg add` (powercfg, dism, powershell... -
    nhung cai do nam trong KIEM_TRA_DAC_BIET).
    """
    m = re.match(r'^\s*reg add\s+"([^"]+)"(.*)$', lenh, re.I | re.S)
    if not m:
        return None
    duong, con_lai = m.group(1), m.group(2)
    # HKLM\... -> HKLM:\...  (dang PowerShell dung)
    # HKU/HKCR KHONG co san o dia PowerShell (chi HKLM:, HKCU:) - loi that
    # lab 26/09/2026: muc Num Lock (HKU\.DEFAULT) luon "khong tim thay".
    duong_ps = re.sub(r"^HKU\\", r"Registry::HKEY_USERS\\", duong, flags=re.I)
    duong_ps = re.sub(r"^HKCR\\", r"Registry::HKEY_CLASSES_ROOT\\", duong_ps, flags=re.I)
    duong_ps = re.sub(r"^(HKLM|HKCU)\\", r"\1:\\", duong_ps, flags=re.I)

    m_ten = re.search(r'/v\s+("[^"]+"|\S+)', con_lai)
    m_gt = re.search(r'/d\s+("[^"]+"|\S+)', con_lai)
    if not m_ten:
        # `/ve` = dat gia tri mac dinh cua khoa (vd menu chuot phai kieu
        # cu) - chi kiem duoc la KHOA CO TON TAI hay khong.
        if re.search(r"/ve\b", con_lai, re.I):
            return {"loai": "khoa", "duong": duong_ps}
        return None
    if not m_gt:
        return None
    return {"loai": "reg", "duong": duong_ps,
            "ten": m_ten.group(1).strip('"'), "gt": m_gt.group(1).strip('"')}

# Cach kiem tra cho cac tuy chon KHONG phai `reg add` (khong suy tu lenh
# duoc). Moi muc la 1 doan PowerShell tra ve mot hashtable @{Dat=...;
# ChiTiet='...'}. Muc nao khong co o day va cung khong phai reg add thi
# bao cao ghi ro "khong tu kiem duoc" - KHONG bao bua la DAT.
KIEM_TRA_DAC_BIET = {
    "xoa_loi_tat_edge": """
        $con = @("$env:PUBLIC\\Desktop\\Microsoft Edge.lnk", "$env:USERPROFILE\\Desktop\\Microsoft Edge.lnk") |
               Where-Object { Test-Path $_ }
        @{ Dat = (-not $con); ChiTiet = $(if ($con) { 'VAN CON: ' + ($con -join ', ') } else { 'khong con loi tat Edge' }) }
    """,
    "tat_last_access": """
        $r = (fsutil behavior query disableLastAccess 2>&1 | Out-String)
        @{ Dat = ($r -match '=\\s*(1|3)\\b'); ChiTiet = $r.Trim() }
    """,
    "xoa_windows_old": """
        @{ Dat = (-not (Test-Path 'C:\\Windows.old')); ChiTiet = $(if (Test-Path 'C:\\Windows.old') { 'VAN CON C:\\Windows.old' } else { 'khong co Windows.old' }) }
    """,
    "ping": """
        $r = (netsh advfirewall firewall show rule name="ICMPv4 vao" 2>&1 | Out-String)
        @{ Dat = ($r -notmatch 'No rules match'); ChiTiet = 'luat tuong lua ICMPv4' }
    """,
    "khong_ngu": """
        $r = (powercfg /query SCHEME_CURRENT SUB_SLEEP STANDBYIDLE 2>&1 | Out-String)
        if ($r -match 'Current AC Power Setting Index:\\s*0x0*([0-9a-f]+)') {
            $giay = [Convert]::ToInt32($matches[1], 16)
            @{ Dat = ($giay -eq 0); ChiTiet = "thoi gian cho = $giay giay" }
        } else { @{ Dat = $false; ChiTiet = 'khong doc duoc powercfg' } }
    """,
    "hieu_suat_cao": """
        $r = (powercfg /getactivescheme 2>&1 | Out-String)
        $ten = if ($r -match '\\(([^)]+)\\)') { $matches[1] } else { '?' }
        @{ Dat = ($r -match '8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c'); ChiTiet = $ten }
    """,
    "ps_chay_script": """
        $p = Get-ExecutionPolicy -Scope LocalMachine
        @{ Dat = ($p -eq 'RemoteSigned'); ChiTiet = "ExecutionPolicy = $p" }
    """,
    "tat_system_restore": """
        $c = Get-CimInstance -Namespace root\\default -ClassName SystemRestoreConfig -EA SilentlyContinue
        if ($c) { @{ Dat = ($c.RPSessionInterval -eq 0); ChiTiet = "RPSessionInterval = $($c.RPSessionInterval)" } }
        else { @{ Dat = $null; ChiTiet = 'khong doc duoc cau hinh System Restore' } }
    """,
    "bat_net_framework35": """
        $f = Get-WindowsOptionalFeature -Online -FeatureName NetFx3 -EA SilentlyContinue
        if ($f) { @{ Dat = ($f.State -eq 'Enabled'); ChiTiet = "State = $($f.State) (can bo nguon sxs)" } }
        else { @{ Dat = $null; ChiTiet = 'khong doc duoc trang thai tinh nang' } }
    """,
}

def _ps_chuoi(s):
    """Boc 1 chuoi Python thanh chuoi PowerShell nháy don an toan."""
    return "'" + str(s).replace("'", "''") + "'"

# Han gio cho MOI buoc cai dat sau khi dang nhap (giay).
#
# VI SAO 45 PHUT: phai du rong cho thu cai lau THAT SU - Office 365 tu
# nguon cuc bo mat 15-25 phut tren may cau hinh thap. Nhung phai co GIOI
# HAN, vi khong co thi mot buoc hong se treo vinh vien: Office tung dung
# im 45 phut (goi may chu Microsoft that bai roi tu thu lai voi khoang
# cho tang gap doi: 3 -> 7 -> 14 -> 28 phut...) ma khong cach nao biet.
# Tha dung 1 buoc, ghi ro "Qua gio" roi cai tiep nhung thu con lai.
GIAY_TOI_DA_MOI_BUOC = 2700

def _muc_kiem_tra(d):
    """
    Dung danh sach cac muc CAN KIEM TRA cho dung kich ban nay.

    DIEM MAU CHOT: chi kiem nhung gi kich ban THUC SU YEU CAU. Bao cao cu
    quet het 28 tuy chon roi bao "HONG" cho nhung muc anh Thoai khong he
    chon la bao cao vo dung - nguoi doc phai tu nho minh da chon gi de
    biet dong nao dang thuc su la loi.
    """
    muc = []

    def them(nhom, nhan, **kw):
        muc.append(dict(nhom=nhom, nhan=nhan, **kw))

    # --- Danh tinh may
    if _tm.la_dong(d):
        # Ten may dong (serial/CSV/ngau nhien/hoi): khong biet truoc ten -> chi can khong phai ten Windows tu dat.
        them("May", "Tên máy", loai="ps", ma="""
        $t = (Get-CimInstance Win32_ComputerSystem).Name
        @{ Dat = ($t -notmatch '^(DESKTOP|WIN)-'); ChiTiet = $t }
    """)
    else:
        them("May", "Tên máy", loai="ps", ma=f"""
        $t = (Get-CimInstance Win32_ComputerSystem).Name
        @{{ Dat = ($t -eq {_ps_chuoi((d.get('ten_may') or '')[:15])}); ChiTiet = $t }}
    """)
    # Tai khoan Administrator (duy nhat): tim theo SID -500 (ten doi theo ngon ngu)
    if d.get("mk_admin"):
        them("May", "Tài khoản Administrator đã mở", loai="ps", ma="""
            $a = Get-LocalUser -EA SilentlyContinue | Where-Object { $_.SID.Value -like '*-500' }
            if ($a) { @{ Dat = $a.Enabled; ChiTiet = "$($a.Name) - Enabled=$($a.Enabled)" } }
            else { @{ Dat = $false; ChiTiet = 'khong tim thay tai khoan SID -500' } }
        """)
    if d.get("tu_dang_nhap"):
        them("May", "Tự động đăng nhập", loai="reg",
             duong=r"HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon",
             ten="AutoAdminLogon", gt="1")

    if d.get("domain"):
        them("May", "Gia nhập domain", loai="ps", ma=f"""
            $c = Get-CimInstance Win32_ComputerSystem
            @{{ Dat = ($c.PartOfDomain -and $c.Domain -eq {_ps_chuoi(d['domain'])});
                ChiTiet = $(if ($c.PartOfDomain) {{ $c.Domain }} else {{ 'chua vao domain' }}) }}
        """)

    # --- Tuy chon Windows da tich: suy cach kiem tu CHINH lenh se chay
    da_chon = set(d.get("tuy_chon") or [])
    for ma, nhan, _mo_ta, pha, cac_lenh in TUY_CHON_WINDOWS:
        if ma not in da_chon:
            continue
        nhom = "Tùy chọn giao diện (mọi tài khoản)" if pha == "ho_so" else "Tùy chọn máy"
        if ma in KIEM_TRA_DAC_BIET:
            them(nhom, nhan, loai="ps", ma=KIEM_TRA_DAC_BIET[ma])
            continue
        # Lay lenh reg DAU TIEN phan tich duoc lam dai dien cho tuy chon
        # (cac tuy chon nhieu lenh deu la nhieu khoa cua CUNG 1 viec).
        kt = next((k for k in (_phan_tich_lenh_reg(l) for l in cac_lenh) if k), None)
        if kt:
            them(nhom, nhan, **kt)
        else:
            them(nhom, nhan, loai="khong_kiem")

    # --- Go app kem san
    for ma_app in (d.get("go_app") or []):
        ten_app = next((t for m, t, _n in APP_RAC if m == ma_app), ma_app)
        them("Gỡ ứng dụng", ten_app, loai="ps", ma=f"""
            $g = Get-AppxPackage -Name {_ps_chuoi(ma_app)} -EA SilentlyContinue
            @{{ Dat = ($g -eq $null); ChiTiet = $(if ($g) {{ 'VAN CON tren may' }} else {{ 'da go' }}) }}
        """)

    # --- Nhung app PHAI GIU LAI: go nham chung la loi nghiem trong, phai
    #     bao cao du anh Thoai khong he yeu cau kiem.
    for ma_app, ten_app in (("Microsoft.WindowsStore", "Microsoft Store"),
                            ("Microsoft.WindowsCalculator", "Máy tính (Calculator)")):
        them("Phải giữ lại", ten_app, loai="ps", ma=f"""
            $g = Get-AppxPackage -Name {_ps_chuoi(ma_app)} -EA SilentlyContinue
            @{{ Dat = ($g -ne $null); ChiTiet = $(if ($g) {{ 'con nguyen' }} else {{ 'DA BI GO NHAM' }}) }}
        """)

    # --- Phan mem da chon
    for a in _d.chuan_hoa_apps(d.get("apps")):
        them("Phần mềm", a["ten"], loai="ps", ma=f"""
            $f = {_ps_chuoi(THU_MUC_TREN_MAY + chr(92) + 'apps' + chr(92) + a['ten'])}
            @{{ Dat = (Test-Path $f); ChiTiet = $(if (Test-Path $f) {{ 'da chep sang may' }} else {{ 'KHONG thay file' }}) }}
        """)

    # --- Ung dung nhieu file
    for u in _d.chuan_hoa_ungdung(d.get("ungdung")):
        them("Ứng dụng", u["id"], loai="ps", ma=f"""
            $t = {_ps_chuoi(THU_MUC_UNGDUNG_TREN_MAY + chr(92) + u['id'])}
            $n = if (Test-Path $t) {{ (Get-ChildItem $t -Recurse -EA SilentlyContinue).Count }} else {{ 0 }}
            @{{ Dat = (Test-Path $t); ChiTiet = "$n muc trong thu muc" }}
        """)
        if u["id"].lower().startswith("office"):
            them("Ứng dụng", "Office đã cài xong", loai="ps", ma="""
                $k = 'HKLM:\\SOFTWARE\\Microsoft\\Office\\ClickToRun\\Configuration'
                if (Test-Path $k) {
                    $v = (Get-ItemProperty $k -EA SilentlyContinue).VersionToReport
                    @{ Dat = ($v -ne $null); ChiTiet = "phien ban $v" }
                } else { @{ Dat = $false; ChiTiet = 'chua cai (khong co khoa ClickToRun)' } }
            """)

    # --- Font chu
    cai_duoc, mat = _bo_font_cai_duoc(d)
    for b in cai_duoc:
        them("Font", b["ten_hien_thi"], loai="ps", ma=f"""
            $f = 'C:\\ConsolePi\\fonts\\ket-qua-' + {_ps_chuoi(b['id'])} + '.json'
            if (-not (Test-Path $f)) {{ @{{ Dat = $false; ChiTiet = 'chua co ket qua cai font (buoc cai font khong chay?)' }} }}
            else {{
                $k = Get-Content -Raw -Encoding UTF8 $f | ConvertFrom-Json
                $thieu = @($k.da_cai | Where-Object {{ -not (Test-Path (Join-Path $env:windir ('Fonts\\' + $_))) }})
                $ct = "$(@($k.da_cai).Count)/$($k.tong) font da cai"
                if (@($k.canh_bao).Count) {{ $ct += ", $(@($k.canh_bao).Count) canh bao (trung ten file voi font may)" }}
                if (@($k.loi).Count) {{ $ct += ", LOI: " + (@($k.loi) -join '; ') }}
                if ($thieu.Count) {{ $ct += ", $($thieu.Count) file khong thay trong Fonts" }}
                @{{ Dat = (@($k.loi).Count -eq 0 -and $thieu.Count -eq 0); ChiTiet = $ct }}
            }}
        """)
    for bo_id in mat:
        them("Font", bo_id, loai="ps", ma="""
            @{ Dat = $false; ChiTiet = 'bo font da chon khong con (hoac dang trong) tren Console System luc tao kich ban' }
        """)

    # --- File noi bo cua Console Pi khong duoc lot sang may khach
    them("Vệ sinh", "File nội bộ _thongtin.json không lọt sang", loai="ps", ma=f"""
        $l = @(Get-ChildItem {_ps_chuoi(THU_MUC_UNGDUNG_TREN_MAY)} -Recurse -Filter '_thongtin.json' -EA SilentlyContinue)
        @{{ Dat = ($l.Count -eq 0); ChiTiet = "$($l.Count) file" }}
    """)

    return muc

_RE_BAT_CMD = re.compile(r'^("[^"]+\.(?:cmd|bat)"|[^\s"]+\.(?:cmd|bat))(\s|$)', re.I)

def _them_call(lenh):
    """
    Them `call` truoc moi lenh goi file .cmd/.bat. Moi buoc chay trong 1 file
    buoc-N.cmd roi ghi ma thoat o dong SAU; goi file .cmd khac KHONG co `call` thi
    quyen dieu khien chuyen sang no va KHONG BAO GIO quay lai -> khong ghi duoc ma
    thoat -> tien trinh bao "Bo cai dung bat thuong" du ung dung chay dung (lab
    04/10/2026: "Kiem tra ung dung nhieu file" - cai.cmd chay du 4 muc [ DAT ] ma van bao loi).
    """
    cac = [x for x in re.split(r"(&&|&|\|\|)", lenh)]
    for i, seg in enumerate(cac):
        t = seg.strip()
        if t in ("&&", "&", "||") or t.lower().startswith("call "):
            continue
        if _RE_BAT_CMD.match(t):
            cac[i] = seg.replace(t, "call " + t, 1)
    return "".join(cac)

def _danh_sach_buoc_nguoi_dung(d):
    """
    Danh sach cac buoc se chay SAU KHI dang nhap, dang (ten_hien_thi, lenh, he_thong).

    Ten hien thi la thu nguoi dung doc tren bang tien trinh, nen phai la
    tieng Viet de hieu ("Cài Google Chrome") chu khong phai dong lenh tho.

    he_thong=True (buoc CAI phan mem / ung dung): chay ngam bang quyen SYSTEM (tac vu
    hen gio) trong khi bang tien trinh cho. LOI THAT (lab 03/10/2026, bo che do "cai cho
    May"): TeamViewer_Setup /S chay TRONG phien nguoi dung cai xong roi tu mo TeamViewer
    va KHONG thoat -> buoc "dang chay" toi luc qua gio (45 phut). Chay bang SYSTEM (nhu
    che do May cu, da chay on) thi khong co man hinh de mo, bo cai thoat gon.
    Tuy chon / script / lenh them van chay trong phien nguoi dung (can HKCU).
    """
    # Mang dat Private (thay cho bang hoi Yes/No da tat o specialize). Chay dau tien,
    # ngay luc dang nhap dau, khi card mang da co ket noi.
    ra = [("Đặt mạng ở chế độ riêng tư",
           'powershell -NoProfile -ExecutionPolicy Bypass -Command '
           '"Get-NetConnectionProfile | Where-Object { $_.NetworkCategory -ne \'DomainAuthenticated\' } '
           '| Set-NetConnectionProfile -NetworkCategory Private"',
           True)]

    for nhan, lenh in zip(_nhan_tuy_chon(d, "nguoi_dung"),
                          _lenh_theo_pha(d, "nguoi_dung")):
        ra.append((nhan, lenh, False))

    if d.get("go_app"):
        for lenh in _lenh_go_app(d):
            ra.append((f"Gỡ {len(d['go_app'])} ứng dụng kèm sẵn", lenh, False))

    # Font chu: cai TRUOC phan mem, de ung dung vua cai da thay font (quyen SYSTEM, he_thong=True)
    for b in _bo_font_cai_duoc(d)[0]:
        ra.append((f"Cài bộ font {b['ten_hien_thi']} ({b['so_font']} font)",
                   _lenh_cai_bo_font(b), True))

    for a in _d.chuan_hoa_apps(d.get("apps")):
        if a.get("dich") == "nguoi_dung":
            ra.append((f"Cài {a['ten']}", _lenh_cai_app(a), True))

    for u in _d.chuan_hoa_ungdung(d.get("ungdung")):
        if u.get("dich") != "nguoi_dung":
            continue
        lenh = _lenh_cai_ungdung(u)
        if lenh:
            o = _d.lay_ungdung(u["id"]) or {}
            ra.append((f"Cài {o.get('ten_hien_thi') or u['id']}", lenh, True))

    for ten in (d.get("scripts") or []):
        ra.append((f"Chạy script {ten}", _lenh_mot_script(ten), False))

    for dong in (d.get("lenh_them") or "").splitlines():
        dong = dong.strip()
        if dong and not dong.startswith("#"):
            ra.append(("Lệnh thêm", dong, False))

    return [(ten, _them_call(lenh), ht) for ten, lenh, ht in ra]

def _nhan_tuy_chon(d, pha):
    """Ten de hieu cua tung LENH trong cac tuy chon da tich, dung pha.

    1 tuy chon co the sinh ra NHIEU lenh (vd "Bat Remote Desktop" = 1 lenh
    reg + 1 lenh mo tuong lua), nen phai tra ve 1 nhan cho MOI lenh thi
    moi ghep 1-1 voi _lenh_theo_pha() duoc.
    """
    da_chon = set(d.get("tuy_chon") or [])
    ra = []
    for ma, nhan, _mo, pha_muc, cac_lenh in TUY_CHON_WINDOWS:
        if ma in da_chon and pha_muc == pha:
            # Nhieu lenh -> danh so "(1/2)" - truoc day lap nguyen ten, bang
            # tien trinh hien "Bat san Num Lock" 2 dong giong het, trong nhu
            # bi chay trung (anh chup lab 26/09/2026).
            n = len(cac_lenh)
            ra.extend([nhan] if n == 1 else
                      [f"{nhan} ({i}/{n})" for i in range(1, n + 1)])
    return ra
