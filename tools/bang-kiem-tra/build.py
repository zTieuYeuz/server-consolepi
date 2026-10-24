# -*- coding: utf-8 -*-
"""Dựng BANG-KIEM-TRA-CONSOLE-SYSTEM.xlsx từ d1..d5. Chạy: python3 build.py <file-ra.xlsx>"""
import os
import sys

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import d1, d2, d3, d4, d5, d6  # noqa: E402

FONT = "Arial"
UU = {"C": "Cao", "T": "Trung bình", "L": "Thấp"}
EM = {"TH": "Đã thử thật", "TD": "Có test tự động", "TT": "Thật + tự động", "CH": "Chưa thử / chưa rõ"}
TRANG_THAI = ["Chưa test", "Đang test", "Đạt", "Lỗi", "Không áp dụng"]

SHEETS = [
    ("01 Cài đặt-Khởi động", d1.S01, "Cài đặt, ISO/ảnh Pi, khởi động, tự kiểm tra"),
    ("02 Đăng nhập-Giao diện", d1.S02, "Đăng nhập, chế độ PC/cảm ứng, menu, tìm nhanh, header, bàn phím ảo"),
    ("03 Tổng quan-Cài đặt", d1.S03, "Trang Tổng quan, Cài đặt chung (dung lượng, sao lưu...)"),
    ("04 Kết nối server", d1.S04, "WiFi/AP, Bluetooth, Truy cập từ xa (Cloudflare, Tailscale)"),
    ("05 Thiết bị", d2.S05, "Phiên kết nối, Console, Cắm thẳng, Thư viện lệnh"),
    ("06 Network Tools", d2.S06, "Toàn bộ công cụ mạng"),
    ("07 DeployOS Kịch bản", d3.S07, "Trình tạo kịch bản cài Windows"),
    ("08 DeployOS Tài nguyên", d3.S08, "Hệ điều hành, phần mềm, driver, WinPE, kho trung tâm"),
    ("09 DeployOS PXE-Máy khách", d3.S09, "Bật/tắt PXE, menu, kiểu máy, Secure Boot, máy ảo"),
    ("10 DeployOS Theo dõi", d3.S10, "Dò ổ đĩa, tiến trình, lịch sử, sẵn sàng, Wake-on-LAN"),
    ("11 Triển khai phần mềm", d4.S11, "Triển khai phần mềm kiểu PDQ qua WinRM"),
    ("12 Quản lý máy trạm", d4.S12, "Nhóm Quản lý máy trạm (UEM), VNC"),
    ("13 Agent", d4.S13, "Agent Windows, MSI/script, passkey, khay, mTLS"),
    ("14 Kho-Nhật ký-Khác", d5.S14, "Kho file, Nhật ký, Nguồn điện, Góp ý, Giải trí, Tài liệu"),
    ("15 Tương thích-Bảo mật", d5.S15, "Nền tảng, chịu tải, bảo mật, cập nhật/phục hồi"),
    ("16 Kiểm tra bổ sung", d6.S16, "Nhập liệu bất thường, trường hợp biên, độ bền, chi tiết sâu từng module"),
]

MOI_TRUONG = [
    ("Server Console System (chính)", "VM x86-64 Debian (cài từ ISO Console System): 4 vCPU, 4 GB RAM, ổ 100 GB trở lên (200 GB nếu nạp nhiều ISO Windows), 2 card mạng: 1 ra mạng quản lý/Internet, 1 cho mạng cài đặt cô lập", "Toàn bộ sheet 01-15", "Muốn thử cả Raspberry Pi: 1 Pi 4/5 + thẻ 64 GB + nguồn đủ công suất (+ RasPad nếu thử màn hình cảm ứng, Bluetooth PAN)"),
    ("Mạng cài đặt cô lập", "Virtual switch/VLAN riêng KHÔNG có DHCP khác, nối card mạng thứ 2 của server với các máy khách PXE", "Sheet 09 chế độ 1 và 2 (Console System tự cấp DHCP)", "Không bao giờ nối vào mạng thật của công ty"),
    ("Mạng có sẵn DHCP", "Router ảo (pfSense/OPNsense/OpenWrt) cấp DHCP + DNS + ra Internet", "Sheet 09 chế độ 3 (proxyDHCP), sheet 10 Kiểm tra sẵn sàng, sheet 06", "Có thể là chính mạng quản lý của server"),
    ("Máy khách PXE (VM)", "VM BIOS/Legacy; VM UEFI; VM UEFI + Secure Boot; VM không TPM; VM có >=2 ổ + 1 USB; VM VMware E1000E/VMXNET3 + NVMe/PVSCSI; VM KVM virtio; chuẩn bị >=5 VM để cài cùng lúc", "Sheet 07, 08, 09, 10", "RAM >=4 GB mỗi VM (WinPE cần >=3 GB; Anhdv Boot >=3 GB)"),
    ("Bộ cài và tài nguyên", "ISO Windows 10 và Windows 11 (24H2 trở lên để thử mục Secure Boot 2023); WinPE (Strelec/Hiren's/Anhdv hoặc tự build bằng ADK); phần mềm có tham số im lặng (7-Zip, Chrome...); Office zip; gói driver giả dạng Dell/HP/Lenovo; vài file font", "Sheet 07, 08, 11", "Dùng key/bản dùng thử hợp lệ"),
    ("Domain Active Directory", "Windows Server 2019/2022 làm DC + DNS; 1 OU thử; tài khoản chỉ để join (Delegate Control: Join a computer to the domain)", "Sheet 07 (gia nhập domain), 10 (Kiểm tra sẵn sàng - DNS domain)", "Máy khách phải tìm domain qua DNS (dùng chế độ PXE có sẵn DHCP)"),
    ("Máy Windows đích (Triển khai, UEM, Agent)", "Windows 11 Pro (Smart App Control TẮT); Windows 10 Pro; Windows Server 2019/2022; máy đã gia nhập domain; máy bật WinRM (Enable-PSRemoting, LocalAccountTokenFilterPolicy=1); có người đăng nhập (RDP) để thử trợ lý phiên, biểu tượng khay, hộp xin phép VNC; (tuỳ chọn) Windows 32-bit", "Sheet 11, 12, 13", "Mỗi máy 1 tài khoản admin riêng cho test; KHÔNG dùng mật khẩu thật của công ty"),
    ("Máy Windows 11 bật Smart App Control", "Windows 11 cài mới (Smart App Control chế độ Bật)", "Sheet 13 - xác nhận giới hạn: agent chưa ký số bị chặn", "Tắt SAC không bật lại được nếu không cài lại Windows"),
    ("Thiết bị mạng + console", "Switch Cisco thật, hoặc GNS3/EVE-NG/CML có LLDP/CDP và SSH/Telnet; cáp USB-serial (FTDI, Prolific, CH340) và cáp Cisco USB console; nếu dùng VM thì chuyển USB passthrough hoặc dùng socat/pty giả cổng serial", "Sheet 05, 06", "Thiết bị SHA-1 cũ để thử SSH đời cũ"),
    ("Thiết bị quản lý máy chủ (BMC)", "Máy chủ có iLO/iDRAC/IPMI, hoặc 1 máy giả web ở 192.168.99.x", "Sheet 05 (Cắm thẳng thiết bị)", "Dây mạng nối thẳng"),
    ("WiFi và Bluetooth", "USB WiFi hỗ trợ chế độ AP (passthrough vào VM) + router WiFi + điện thoại hotspot 4G/5G; USB Bluetooth dongle + bàn phím BT + laptop Windows 11 để thử PAN", "Sheet 04", "Card WiFi laptop Intel thường không hỗ trợ AP"),
    ("Internet, router, domain công cộng", "Kết nối Internet; router cho chuyển cổng TCP (mặc định 8443 hoặc cổng đã đổi) về server; domain/DDNS trỏ IP công cộng; (tuỳ chọn) VPN Tailscale/WireGuard", "Sheet 13 (agent qua Internet), sheet 04", "Chưa từng thử thật phần agent qua Internet"),
    ("Tài khoản dịch vụ ngoài", "Tài khoản Cloudflare Zero Trust (token tunnel), Tailscale auth key, kết nối kho trung tâm (nếu có), (tuỳ chọn) Cloudflare Access", "Sheet 04, 08", "Token là bí mật - không gửi qua chat/email"),
    ("Thiết bị người dùng cuối", "Laptop Windows (Edge/Chrome/Firefox), iPad/iPhone (Safari), màn hình cảm ứng, USB để thử Kho file/PCAP", "Sheet 02, 05, 14, 15", "Thử chép/dán terminal trên nhiều trình duyệt"),
    ("Chuẩn bị chung", "Danh sách IP, tài khoản và mật khẩu TEST ghi riêng; chụp ảnh/ghi lại thông báo lỗi khi gặp; mỗi mục lỗi ghi mã mục (vd 13-007) vào cột Ghi chú", "Mọi sheet", "Gửi em danh sách mã mục lỗi để sửa"),
]

THU_TU = [
    "1. Dựng server từ ISO (hoặc ảnh Pi), chạy sheet 01 và selftest, rồi sheet 02-03 (giao diện, tổng quan).",
    "2. Sheet 04 (WiFi/AP, Bluetooth, truy cập từ xa) và sheet 05 (phiên kết nối, console, cắm thẳng).",
    "3. Sheet 06 (Network Tools) với mạng thật hoặc switch giả lập.",
    "4. Sheet 08 (tài nguyên) trước, rồi 07 (kịch bản), 09 (PXE/máy khách), 10 (theo dõi, lịch sử, WoL): cài thử từng loại máy ảo.",
    "5. Dựng máy Windows đích, chạy sheet 11 (triển khai phần mềm) rồi sheet 12 (quản lý máy trạm).",
    "6. Sheet 13 (agent): MSI/script, passkey, khay, gỡ cài đặt, mTLS, địa chỉ dự phòng; cuối cùng thử qua Internet/VPN.",
    "7. Sheet 14 và 15: Kho, Nhật ký, bảo mật, tương thích, chịu tải, cập nhật/phục hồi.",
    "8. Sheet 16 (kiểm tra bổ sung): nhập liệu bất thường, trường hợp biên, độ bền, chi tiết sâu từng module - làm sau khi các sheet chính đạt.",
]


def kieu(c, bold=False, size=10, color="000000", fill=None, wrap=True, h="left", v="top"):
    c.font = Font(name=FONT, size=size, bold=bold, color=color)
    c.alignment = Alignment(wrap_text=wrap, horizontal=h, vertical=v)
    if fill:
        c.fill = PatternFill("solid", start_color=fill)


VIEN = Border(*(Side(style="thin", color="D0D5DD"),) * 4)


def doc(chuoi):
    ra = []
    for ln in chuoi.strip().split("\n"):
        p = [x.strip() for x in ln.split("|")]
        assert len(p) == 7, (len(p), ln[:90])
        assert p[5] in UU and p[6] in EM, ln[:90]
        ra.append(p)
    return ra


def dung_sheet(wb, ten, rows, mota, stt):
    ws = wb.create_sheet(ten)
    dau = ["Mã", "Nhóm", "Chức năng", "Cách kiểm tra", "Kết quả mong đợi", "Điều kiện / thiết bị cần", "Ưu tiên",
           "Em đã kiểm trước đó (theo nhật ký)", "Kết quả", "Ngày test", "Người test", "Ghi chú / lỗi gặp"]
    rong = [9, 24, 34, 52, 58, 26, 11, 20, 14, 12, 14, 36]
    for i, (t, w) in enumerate(zip(dau, rong), 1):
        c = ws.cell(row=1, column=i, value=t)
        kieu(c, bold=True, color="FFFFFF", fill="1F3864", h="center", v="center")
        c.border = VIEN
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 34
    for n, p in enumerate(rows, 1):
        r = n + 1
        gt = [f"{stt:02d}-{n:03d}", p[0], p[1], p[2], p[3], p[4], UU[p[5]], EM[p[6]], "Chưa test", None, None, None]
        for i, val in enumerate(gt, 1):
            c = ws.cell(row=r, column=i, value=val)
            kieu(c, h="center" if i in (1, 7, 8, 9, 10) else "left", bold=(i == 3))
            c.border = VIEN
        up = ws.cell(row=r, column=7)
        up.fill = PatternFill("solid", start_color={"Cao": "FDE2E2", "Trung bình": "FFF2CC", "Thấp": "E2EFDA"}[up.value])
    cuoi = len(rows) + 1
    dv = DataValidation(type="list", formula1='"' + ",".join(TRANG_THAI) + '"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"I2:I{cuoi + 200}")
    rng = f"I2:I{cuoi + 200}"
    for gt, mau in (("Đạt", "C6EFCE"), ("Lỗi", "FFC7CE"), ("Đang test", "FFEB9C"), ("Không áp dụng", "D9D9D9")):
        ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=[f'"{gt}"'], fill=PatternFill("solid", start_color=mau, end_color=mau)))
    ws.freeze_panes = "D2"
    ws.auto_filter.ref = f"A1:L{cuoi}"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = "1:1"
    return cuoi


def main(ra):
    wb = Workbook()
    hd = wb.active
    hd.title = "Hướng dẫn"
    tong = wb.create_sheet("Tổng hợp")
    mt = wb.create_sheet("Môi trường mô phỏng")
    thong_ke = []
    for i, (ten, chuoi, mota) in enumerate(SHEETS, 1):
        rows = doc(chuoi)
        cuoi = dung_sheet(wb, ten, rows, mota, i)
        thong_ke.append((ten, mota, len(rows), cuoi))

    # ---------------- Hướng dẫn
    hd.column_dimensions["A"].width = 30
    hd.column_dimensions["B"].width = 120
    r = 1
    c = hd.cell(row=r, column=1, value="BẢNG KIỂM TRA TOÀN BỘ CHỨC NĂNG CONSOLE SYSTEM")
    kieu(c, bold=True, size=16, color="1F3864", wrap=False)
    r += 1
    kieu(hd.cell(row=r, column=1, value="Phiên bản kiểm thử: Console System 1.9.5 (agent 2.3.2, Triển khai phần mềm, Quản lý máy trạm; chưa phát hành chính thức). Lập ngày 23/10/2026."), wrap=False)
    r += 2
    muc = [
        ("Mục đích", "Dùng khi dựng một server Console System mới và mô phỏng mọi thứ đã làm từ trước đến nay. Mỗi dòng là một việc cụ thể cần thử: làm gì, thấy gì thì coi là đạt."),
        ("Cấu trúc", f"{len(SHEETS)} sheet theo nhóm chức năng (sheet 01-{len(SHEETS)}) + sheet Tổng hợp (tự tính tiến độ) + sheet Môi trường mô phỏng (cần chuẩn bị máy gì). Tổng cộng {sum(x[2] for x in thong_ke)} mục kiểm tra."),
        ("Cách dùng", "Mở sheet theo thứ tự đề xuất bên dưới. Với mỗi dòng: làm theo cột 'Cách kiểm tra', so với 'Kết quả mong đợi', rồi chọn cột 'Kết quả' (Đạt / Lỗi / Đang test / Không áp dụng), điền ngày, tên người test, và ghi lỗi vào 'Ghi chú'. Sheet Tổng hợp tự cập nhật."),
        ("Cột 'Ưu tiên'", "Cao = chức năng cốt lõi hoặc liên quan an toàn dữ liệu/bảo mật, phải đạt trước khi dùng thật. Trung bình = nên đạt. Thấp = tiện ích."),
        ("Cột 'Em đã kiểm trước đó'", "Đã thử thật = em đã chạy trên máy/máy ảo thật theo nhật ký phát hành hoặc ghi nhớ làm việc. Có test tự động = có bộ test chạy tự động trong repo. Thật + tự động = cả hai. Chưa thử / chưa rõ = chưa từng kiểm hoặc em không có bằng chứng; PHẢI test kỹ. Cột này chỉ là tham khảo từ nhật ký, trên server mới vẫn phải kiểm lại."),
        ("Mã mục", "Dạng SS-NNN (SS = số sheet, NNN = số thứ tự). Khi báo lỗi cho em, ghi mã mục để em tìm ngay."),
        ("Lưu ý an toàn", "Chỉ test PXE/DHCP/TFTP trên mạng cô lập, KHÔNG cắm vào mạng thật của công ty. Dùng tài khoản và mật khẩu test riêng. Tắt Smart App Control trên máy Windows dùng để thử agent (hoặc ghi nhận đúng là bị chặn)."),
        ("Hạn chế đã biết", "Agent bị Windows 11 chặn khi Smart App Control bật (chưa ký số). Hàng đợi việc lưu trong RAM (mất khi server khởi động lại). Agent qua Internet, Windows 10/Server/domain, 10+ máy song song... CHƯA từng thử thật - xem cột 'Em đã kiểm' = Chưa thử."),
    ]
    for k, v in muc:
        kieu(hd.cell(row=r, column=1, value=k), bold=True, fill="DCE6F1")
        kieu(hd.cell(row=r, column=2, value=v))
        hd.row_dimensions[r].height = max(30, 15 * (len(v) // 115 + 1))
        r += 1
    r += 1
    kieu(hd.cell(row=r, column=1, value="Thứ tự test đề xuất"), bold=True, color="1F3864", size=12, wrap=False)
    r += 1
    for t in THU_TU:
        kieu(hd.cell(row=r, column=2, value=t))
        hd.row_dimensions[r].height = 30
        r += 1
    r += 1
    kieu(hd.cell(row=r, column=1, value="Chú thích màu"), bold=True, color="1F3864", size=12, wrap=False)
    r += 1
    for gt, mau in (("Đạt", "C6EFCE"), ("Lỗi", "FFC7CE"), ("Đang test", "FFEB9C"), ("Không áp dụng", "D9D9D9")):
        kieu(hd.cell(row=r, column=1, value=gt), fill=mau, bold=True)
        r += 1

    # ---------------- Môi trường
    for col, (t, w) in enumerate((("STT", 6), ("Thành phần cần chuẩn bị", 34), ("Cấu hình gợi ý", 80), ("Dùng để thử sheet", 44), ("Lưu ý", 50)), 1):
        c = mt.cell(row=1, column=col, value=t)
        kieu(c, bold=True, color="FFFFFF", fill="1F3864", h="center", v="center")
        mt.column_dimensions[get_column_letter(col)].width = w
    for i, (a, b, cc, d) in enumerate(MOI_TRUONG, 1):
        for col, val in enumerate((i, a, b, cc, d), 1):
            c = mt.cell(row=i + 1, column=col, value=val)
            kieu(c, h="center" if col == 1 else "left", bold=(col == 2))
            c.border = VIEN
    mt.freeze_panes = "A2"

    # ---------------- Tổng hợp
    cot = ["Sheet", "Nội dung", "Số mục", "Đạt", "Lỗi", "Đang test", "Không áp dụng", "Chưa test", "% đã xong", "Tỉ lệ đạt (trong số đã test)",
           "Mục ưu tiên Cao", "Mục Cao chưa Đạt", "Mục em chưa thử / chưa rõ"]
    rong = [28, 56, 9, 9, 9, 11, 14, 11, 11, 16, 14, 14, 18]
    for i, (t, w) in enumerate(zip(cot, rong), 1):
        c = tong.cell(row=1, column=i, value=t)
        kieu(c, bold=True, color="FFFFFF", fill="1F3864", h="center", v="center")
        c.border = VIEN
        tong.column_dimensions[get_column_letter(i)].width = w
    tong.row_dimensions[1].height = 46
    for i, (ten, mota, n, cuoi) in enumerate(thong_ke, 2):
        q = f"'{ten}'!"
        rg = lambda col: f"{q}${col}$2:${col}${cuoi + 200}"
        vals = [ten, mota, f"=COUNTA({q}$A$2:$A${cuoi + 200})", f'=COUNTIF({rg("I")},"Đạt")', f'=COUNTIF({rg("I")},"Lỗi")',
                f'=COUNTIF({rg("I")},"Đang test")', f'=COUNTIF({rg("I")},"Không áp dụng")', f"=C{i}-D{i}-E{i}-F{i}-G{i}",
                f"=IF(C{i}=0,0,(D{i}+E{i}+G{i})/C{i})", f"=IF(D{i}+E{i}=0,0,D{i}/(D{i}+E{i}))",
                f'=COUNTIF({rg("G")},"Cao")', f'=COUNTIFS({rg("G")},"Cao",{rg("I")},"<>Đạt")', f'=COUNTIF({rg("H")},"Chưa thử / chưa rõ")']
        for col, val in enumerate(vals, 1):
            c = tong.cell(row=i, column=col, value=val)
            kieu(c, h="left" if col <= 2 else "center", bold=(col == 1))
            c.border = VIEN
            if col in (9, 10):
                c.number_format = "0.0%"
        tong.cell(row=i, column=1).hyperlink = f"#'{ten}'!A1"
        tong.cell(row=i, column=1).font = Font(name=FONT, size=10, bold=True, color="0563C1", underline="single")
    t = len(thong_ke) + 2
    kieu(tong.cell(row=t, column=1, value="TỔNG CỘNG"), bold=True, fill="DCE6F1")
    kieu(tong.cell(row=t, column=2, value=""), fill="DCE6F1")
    for col in range(3, 9):
        L = get_column_letter(col)
        c = tong.cell(row=t, column=col, value=f"=SUM({L}2:{L}{t - 1})")
        kieu(c, bold=True, h="center", fill="DCE6F1")
    for col, f in ((9, f"=IF(C{t}=0,0,(D{t}+E{t}+G{t})/C{t})"), (10, f"=IF(D{t}+E{t}=0,0,D{t}/(D{t}+E{t}))")):
        c = tong.cell(row=t, column=col, value=f)
        kieu(c, bold=True, h="center", fill="DCE6F1")
        c.number_format = "0.0%"
    for col in (11, 12, 13):
        L = get_column_letter(col)
        c = tong.cell(row=t, column=col, value=f"=SUM({L}2:{L}{t - 1})")
        kieu(c, bold=True, h="center", fill="DCE6F1")
    for col in range(1, 14):
        tong.cell(row=t, column=col).border = VIEN
    tong.freeze_panes = "C2"
    for w in (hd, tong, mt):
        w.page_setup.orientation = "landscape"
        w.page_setup.fitToWidth = 1
        w.page_setup.fitToHeight = 0
        w.sheet_properties.pageSetUpPr.fitToPage = True
    wb._sheets = [hd, tong, mt] + [x for x in wb._sheets if x not in (hd, tong, mt)]
    wb.save(ra)
    print("OK", ra, sum(x[2] for x in thong_ke), "mục,", len(thong_ke), "sheet")


if __name__ == "__main__":
    main(sys.argv[1])
