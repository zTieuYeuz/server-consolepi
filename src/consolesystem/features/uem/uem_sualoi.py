# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Quan ly may tram - SUA LOI MAY IN va CHIA SE O DIA / THU MUC tu xa qua agent (hoac WinRM).

Moi muc la mot kich ban PowerShell DA DUYET truoc (khong cho go lenh tuy y o day - muon go lenh thi dung tab Dong lenh). Cac loi pho bien duoc xu ly:
  May in : hang doi in ket (Spooler), loi 0x0000011b / 0x00000709 / 0x00000bcb khi noi may in dung chung (Windows moi chan RPC/Point and Print),
           cong 9100 khong toi duoc.
  Chia se: tuong lua "Chia se tep va may in" / "Kham pha mang" bi tat, dich vu Server/Workstation/FDResPub dung, mang dang o che do Public,
           Windows 11 24H2 chan dang nhap khach (guest) khi vao NAS/may chia se khong mat khau (0x80070035).
LUU Y: agent chay quyen SYSTEM nen KHONG dat duoc may in mac dinh / thong tin dang nhap luu cua tung nguoi dung (la cau hinh theo phien nguoi dung).
Muc lam GIAM AN TOAN (RPC privacy, guest) co co "nguy_hiem" -> giao dien hoi xac nhan.
"""
import json
import re

from flask import jsonify, request

from consolesystem.features.uem import uem_dieukhien as DK
from ui import uem_dulieu as UD
from ui.uem_trang import _esc, may_theo_id
from ui import uem_trang as T

TEN = r"[^\x00-\x1f\"'`$;|&<>^%]{1,120}"
MAU = {
    "ten": re.compile(TEN),
    "host": re.compile(r"[A-Za-z0-9][A-Za-z0-9.\-]{0,253}"),
    "duong": re.compile(r"[A-Za-z]:\\[^\x00-\x1f\"'`$;|&<>^%*?]{0,240}"),
    "nguoi": re.compile(r"[A-Za-z0-9_.\-\\ ]{1,60}"),
}


def _q(x):
    return "'" + str(x).replace("'", "''") + "'"


# id -> (nhom, tieu_de, mo_ta, nguy_hiem, [(ten_tham_so, nhan, kieu)], ham_tao_script(tham_so) -> str)
def _dung_dang_ky():
    R = {}

    def them(id_, nhom, tieu, mo, nguy, tham, ham):
        R[id_] = (nhom, tieu, mo, nguy, tham, ham)

    them("in-chan-doan", "in", "Chẩn đoán máy in", "Chỉ đọc: dịch vụ in, danh sách máy in và hàng đợi, các khóa registry hay gây lỗi 0x0000011b.", False, [],
         lambda p: r"""$s = Get-Service Spooler; "Dịch vụ in (Spooler): $($s.Status), khởi động $($s.StartType)"
Get-Printer | ForEach-Object { $j = @(Get-PrintJob -PrinterName $_.Name -ErrorAction SilentlyContinue).Count; "{0} | trạng thái {1} | cổng {2} | {3} việc trong hàng đợi" -f $_.Name, $_.PrinterStatus, $_.PortName, $j }
$k = Get-ItemProperty 'HKLM:\System\CurrentControlSet\Control\Print' -ErrorAction SilentlyContinue
"RpcAuthnLevelPrivacyEnabled = " + $(if ($k.RpcAuthnLevelPrivacyEnabled -eq $null) { 'chưa đặt (mặc định bật)' } else { $k.RpcAuthnLevelPrivacyEnabled })
$pp = Get-ItemProperty 'HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\Printers\PointAndPrint' -ErrorAction SilentlyContinue
"RestrictDriverInstallationToAdministrators = " + $(if ($pp.RestrictDriverInstallationToAdministrators -eq $null) { 'chưa đặt (mặc định bật)' } else { $pp.RestrictDriverInstallationToAdministrators })
Get-ChildItem C:\Windows\System32\spool\PRINTERS -ErrorAction SilentlyContinue | Measure-Object | ForEach-Object { "File kẹt trong spool: $($_.Count)" }""")
    them("in-hang-doi", "in", "Xóa hàng đợi in bị kẹt và khởi động lại dịch vụ in",
         "Máy in báo 'đang in' mãi hoặc không in được: dừng Spooler, xóa file kẹt trong thư mục spool, chạy lại Spooler. Các lệnh in đang chờ sẽ mất.", False, [],
         lambda p: r"""Stop-Service Spooler -Force -ErrorAction Stop
Start-Sleep 2
$n = @(Get-ChildItem C:\Windows\System32\spool\PRINTERS -Force -ErrorAction SilentlyContinue).Count
Remove-Item C:\Windows\System32\spool\PRINTERS\* -Force -ErrorAction SilentlyContinue
Start-Service Spooler -ErrorAction Stop
"Đã xóa $n file kẹt, dịch vụ in: " + (Get-Service Spooler).Status""")
    them("in-0x11b", "in", "Sửa lỗi 0x0000011b khi kết nối máy in dùng chung",
         "Đặt RpcAuthnLevelPrivacyEnabled = 0 (khóa Print) rồi khởi động lại dịch vụ in. Cách này của Microsoft để máy cũ/chia sẻ qua mạng in lại được sau bản vá 2021, nhưng giảm mức bảo mật in qua mạng. Nên đặt trên MÁY CHỦ IN (máy chia sẻ máy in).", True, [],
         lambda p: r"""New-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Print' -Name RpcAuthnLevelPrivacyEnabled -Value 0 -PropertyType DWord -Force | Out-Null
Restart-Service Spooler -Force -ErrorAction Stop
"Đã đặt RpcAuthnLevelPrivacyEnabled=0 và khởi động lại dịch vụ in." """)
    them("in-pointandprint", "in", "Sửa lỗi 0x00000bcb / 0x00000709 (cài driver máy in dùng chung)",
         "Cho phép cài driver máy in từ máy chủ in không cần quyền quản trị (RestrictDriverInstallationToAdministrators = 0). Giảm bảo mật, chỉ dùng trong mạng tin cậy.", True, [],
         lambda p: r"""$k = 'HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\Printers\PointAndPrint'
New-Item -Path $k -Force | Out-Null
New-ItemProperty -Path $k -Name RestrictDriverInstallationToAdministrators -Value 0 -PropertyType DWord -Force | Out-Null
Restart-Service Spooler -Force -ErrorAction Stop
"Đã cho phép cài driver máy in qua Point and Print." """)
    them("in-thu-cong-9100", "in", "Thử kết nối tới máy in mạng (cổng 9100)", "Kiểm tra máy này có tới được máy in mạng qua TCP 9100 không.", False, [("host", "IP hoặc tên máy in", "host")],
         lambda p: f"$r = Test-NetConnection -ComputerName {_q(p['host'])} -Port 9100 -WarningAction SilentlyContinue; 'Ping: ' + $r.PingSucceeded + ' | TCP 9100: ' + $r.TcpTestSucceeded + ' | IP: ' + $r.RemoteAddress")

    them("cs-chan-doan", "chia-se", "Chẩn đoán chia sẻ tệp", "Chỉ đọc: thư mục đang chia sẻ, SMB, tường lửa, dịch vụ, loại mạng, đăng nhập khách.", False, [],
         lambda p: r"""Get-SmbShare | ForEach-Object { "Share: {0} -> {1}" -f $_.Name, $_.Path }
$c = Get-SmbServerConfiguration; "SMB2/3 bật: $($c.EnableSMB2Protocol) | SMB1 bật: $($c.EnableSMB1Protocol) | Bắt buộc ký: $($c.RequireSecuritySignature)"
foreach ($g in 'File and Printer Sharing','Network Discovery') { $r = @(Get-NetFirewallRule -DisplayGroup $g -ErrorAction SilentlyContinue | Where-Object { $_.Enabled -eq 'True' }).Count; "Tường lửa '$g': $r luật đang bật" }
foreach ($s in 'LanmanServer','LanmanWorkstation','FDResPub','fdPHost') { $v = Get-Service $s -ErrorAction SilentlyContinue; "Dịch vụ {0}: {1} ({2})" -f $s, $v.Status, $v.StartType }
Get-NetConnectionProfile | ForEach-Object { "Mạng '{0}': {1}" -f $_.Name, $_.NetworkCategory }
$g = Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters' -ErrorAction SilentlyContinue
"AllowInsecureGuestAuth = " + $(if ($g.AllowInsecureGuestAuth -eq $null) { 'chưa đặt' } else { $g.AllowInsecureGuestAuth })""")
    them("cs-bat", "chia-se", "Bật chia sẻ tệp và phát hiện mạng",
         "Mở luật tường lửa 'Chia sẻ tệp và máy in' + 'Phát hiện mạng', bật các dịch vụ Server/Workstation/FDResPub/fdPHost, chuyển mạng Public sang Private.", False, [],
         lambda p: r"""Get-NetConnectionProfile | Where-Object { $_.NetworkCategory -eq 'Public' } | ForEach-Object { Set-NetConnectionProfile -InterfaceIndex $_.InterfaceIndex -NetworkCategory Private }
Enable-NetFirewallRule -DisplayGroup 'File and Printer Sharing' -ErrorAction SilentlyContinue
Enable-NetFirewallRule -DisplayGroup 'Network Discovery' -ErrorAction SilentlyContinue
foreach ($s in 'LanmanServer','LanmanWorkstation','FDResPub','fdPHost') { Set-Service $s -StartupType Automatic -ErrorAction SilentlyContinue; Start-Service $s -ErrorAction SilentlyContinue }
"Đã bật chia sẻ tệp, phát hiện mạng và các dịch vụ liên quan." """)
    them("cs-guest", "chia-se", "Cho phép vào thư mục chia sẻ không cần mật khẩu (đăng nhập khách)",
         "Windows 11 24H2 / Windows 10 mới chặn đăng nhập khách (lỗi 'tổ chức của bạn chặn truy cập khách không xác thực', 0x80070035). Bật AllowInsecureGuestAuth để máy này vào được NAS/máy chia sẻ không mật khẩu. Giảm bảo mật, chỉ dùng trong LAN tin cậy.", True, [],
         lambda p: r"""New-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters' -Name AllowInsecureGuestAuth -Value 1 -PropertyType DWord -Force | Out-Null
"Đã bật AllowInsecureGuestAuth=1." """)
    them("cs-thu-445", "chia-se", "Thử kết nối SMB (cổng 445) tới một máy", "Kiểm tra máy này có tới được máy chia sẻ qua TCP 445 không.", False, [("host", "IP hoặc tên máy", "host")],
         lambda p: f"$r = Test-NetConnection -ComputerName {_q(p['host'])} -Port 445 -WarningAction SilentlyContinue; 'Ping: ' + $r.PingSucceeded + ' | TCP 445: ' + $r.TcpTestSucceeded + ' | IP: ' + $r.RemoteAddress")
    them("cs-tao-share", "chia-se", "Tạo thư mục chia sẻ", "Chia sẻ một thư mục có sẵn trên máy này; người dùng/nhóm được chọn có quyền Thay đổi (Change).", False,
         [("ten", "Tên chia sẻ", "ten"), ("duong", "Đường dẫn thư mục (ví dụ D:\\DuLieu)", "duong"), ("nguoi", "Người dùng hoặc nhóm (ví dụ Everyone, hoặc Users)", "nguoi")],
         lambda p: f"if (-not (Test-Path -LiteralPath {_q(p['duong'])})) {{ throw 'Thư mục không tồn tại' }}; New-SmbShare -Name {_q(p['ten'])} -Path {_q(p['duong'])} -ChangeAccess {_q(p['nguoi'])} | Out-Null; 'Đã chia sẻ \\\\' + $env:COMPUTERNAME + '\\' + {_q(p['ten'])}")
    them("cs-go-share", "chia-se", "Gỡ một thư mục chia sẻ", "Ngừng chia sẻ (dữ liệu trong thư mục không bị xóa).", False, [("ten", "Tên chia sẻ", "ten")],
         lambda p: f"Remove-SmbShare -Name {_q(p['ten'])} -Force -ErrorAction Stop; 'Đã gỡ chia sẻ ' + {_q(p['ten'])}")
    return R


DANG_KY = _dung_dang_ky()


def kiem_tham_so(id_, tham):
    """(ok, tham_so_sach|loi)"""
    _n, _t, _m, _d, ds, _f = DANG_KY[id_]
    ra = {}
    for ten, _nhan, kieu in ds:
        v = str((tham or {}).get(ten, "")).strip()
        if not MAU[kieu].fullmatch(v):
            return False, f"Giá trị '{ten}' không hợp lệ."
        ra[ten] = v
    return True, ra


def chay(m, id_, tham):
    if id_ not in DANG_KY:
        return {"ok": False, "loi": "Mục sửa lỗi không tồn tại."}
    ok, p = kiem_tham_so(id_, tham)
    if not ok:
        return {"ok": False, "loi": p}
    tieu = DANG_KY[id_][1]
    ok, out = DK._chay(m, "$ErrorActionPreference='Stop'\n[Console]::OutputEncoding=[Text.Encoding]::UTF8\n& { " + DANG_KY[id_][5](p) + " } 2>&1 | Out-String")
    UD.ghi_tac_vu(m["id"], "tu_xa", "Sửa lỗi: " + tieu, ok, (out or "")[:200])
    return {"ok": ok, "out": out if ok else "", "loi": "" if ok else out}


def tab_sua_loi(m):
    nhom_ten = {"in": "Máy in", "chia-se": "Chia sẻ ổ đĩa / thư mục"}
    html = ('<div class="msg info">Mỗi nút chạy một kịch bản đã được duyệt sẵn trên máy này (qua agent). Bắt đầu bằng nút <b>Chẩn đoán</b>. '
            'Mục có nhãn <b>giảm bảo mật</b> sẽ hỏi xác nhận trước khi chạy.</div>')
    for nhom, ten in nhom_ten.items():
        html += f"<h2>{ten}</h2><div class='uem-2'>"
        for id_, (n, tieu, mo, nguy, tham, _f) in DANG_KY.items():
            if n != nhom:
                continue
            o = "".join(f'<label>{_esc(nhan)}</label><input type="text" data-tham="{_esc(t)}" style="width:100%;">' for t, nhan, _k in tham)
            html += (f'<div class="card" data-id="{id_}" data-nguy="{1 if nguy else 0}"><h3>{_esc(tieu)}</h3>'
                     f'{"<span class=tk-chip>giảm bảo mật</span> " if nguy else ""}<p class="tk-ghi">{_esc(mo)}</p>{o}'
                     f'<div class="tk-hang" style="margin-top:8px;"><button class="tk-nut {"do" if nguy else "chinh"}" type="button" data-chay="{id_}">Chạy</button></div>'
                     f'<pre class="kq" style="display:none;background:#0f1114;color:#d5dae2;padding:10px;border-radius:6px;white-space:pre-wrap;word-break:break-all;max-height:40vh;overflow:auto;"></pre></div>')
        html += "</div>"
    html += f"""<script>(function(){{var U='/uem/may/{m["id"]}/sua-loi/chay';
document.addEventListener('click',function(ev){{var b=ev.target.closest('[data-chay]'); if(!b)return; var c=b.closest('.card'), pre=c.querySelector('.kq'), tham={{}};
 c.querySelectorAll('[data-tham]').forEach(function(i){{tham[i.dataset.tham]=i.value;}});
 if(c.dataset.nguy==='1' && !confirm('Mục này GIẢM BẢO MẬT của máy. Chỉ dùng trong mạng tin cậy. Tiếp tục?')) return;
 b.disabled=true; pre.style.display='block'; pre.textContent='Đang chạy...';
 fetch(U,{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{id:b.dataset.chay,tham:tham}})}}).then(function(r){{return r.json();}}).then(function(d){{pre.textContent=(d.ok?'':'[LỖI] ')+(d.out||d.loi||'(xong, không có kết quả)');}}).catch(function(){{pre.textContent='Không gọi được máy chủ.';}}).then(function(){{b.disabled=false;}});}});}})();</script>"""
    return T.khung_may(m, "sua-loi", html)


def register_sualoi(app):
    @app.route("/uem/may/<mid>/sua-loi/chay", methods=["POST"])
    def uem_sua_loi_chay(mid):
        j = request.get_json(silent=True) or {}
        return jsonify(chay(may_theo_id(mid), str(j.get("id", "")), j.get("tham") if isinstance(j.get("tham"), dict) else {}))
