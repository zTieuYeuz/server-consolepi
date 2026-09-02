# Changelog

## 0.2.1

### Toi uu hieu nang
- Trang WiFi: **2.865s -> 0.015s** (nhanh hon ~190 lan). Truoc day quet WiFi
  dong bo moi lan tai trang; gio quet o luong nen va nho ket qua 45 giay,
  co nut "Quet lai" khi can du lieu moi
- Trang chu: 0.170s -> 0.051s. Gop 8 lenh `systemctl is-active` thanh 1
- Thanh trang thai: doc IP bang `ioctl` thay vi goi lenh `ip` (khong spawn
  tien trinh), them cache 4 giay
- Chromium tu dieu chinh theo RAM: may duoi 1.5GB (Pi 3, Pi Zero 2W) gioi han
  so tien trinh render va bo nho JS; may duoi 3GB gioi han vua phai

### Mau sac terminal
- Bang mau tuong phan cao dung chung cho ca 3 khung terminal
- Shell co mau san: dau nhac, `ls`, `grep`, va lenh mang qua `grc`
  (ping, traceroute, ip, ss, netstat, nmap, tcpdump, mtr, dig)
- Bo mau rieng cho output thiet bi Cisco (`grc-cisco.conf`)
- Ket qua chay lenh hang loat tren web duoc to mau: do=loi, xanh la=tot,
  vang=canh bao, xanh nhat=IP, xanh duong=MAC, tim=ten cong
- Loi tat: `ports`, `myip`, `routes`, `serial`, `logs`

## 0.2.0

Bản đầu tiên đóng gói được để cài lên máy khác.

### Thêm mới
- **Giao diện mới**: thanh điều hướng trái + thanh trạng thái mạng luôn hiện
  IP của cả 3 giao diện (LAN / WiFi / Bluetooth), tự làm mới mỗi 30 giây
- **Đăng nhập** bằng tài khoản Linux qua PAM
- **Terminal local** và **SSH** (tương tác + chạy hàng loạt) qua ttyd + tmux
- **Thư viện lệnh** — thêm/sửa/xoá, sẵn 5 tập lệnh Cisco, dán được vào terminal
- **Trang Tài liệu** tra cứu ngoại tuyến ngay trên thiết bị
- **nginx** làm cổng trung gian — mọi thứ chung cổng 80
- **Bàn phím ảo** cho màn hình cảm ứng, gõ được cả vào terminal
- **Bluetooth**: quét + ghép cặp bàn phím/chuột, kèm PAN
- **Nút xoay màn hình** trong tab Cài đặt
- `install.sh` cài một lệnh, tự phát hiện có màn hình hay không

### Sửa lỗi đáng chú ý
- `ttyd` chạy `Type=oneshot` nên systemd không giám sát — ttyd chết vẫn báo
  `active`. Đã thay bằng template unit có `Restart=always`
- systemd-networkd xoá mất IP tĩnh của AP sau khi bật — thêm
  `KeepConfiguration=yes`
- Đăng ký NAP của Bluetooth bị huỷ ngay khi script thoát (D-Bus gắn với vòng
  đời tiến trình) — chuyển sang daemon chạy thường trú
- `srp()` của scapy không bắt được DHCPOFFER — chuyển sang `sniff()` + `sendp()`
- Bàn phím ảo: `preventDefault()` trên `touchstart` chặn luôn sự kiện click —
  chuyển sang `pointerdown`
- Toạ độ cảm ứng không tự xoay theo màn hình — cần ma trận hiệu chỉnh khớp
  hướng, và `install.sh` từng tự ghi đè mất ma trận đúng
