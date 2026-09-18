"""
Console Pi - Khung giao dien dung chung (thanh dieu huong trai + noi dung phai)

Moi trang trong dashboard deu goi render_page() de co cung bo cuc, thay vi
tu viet lai <html> tu dau. Thiet ke cho man hinh cam ung 1280x800:
  - Nut/muc menu du lon de cham bang ngon tay (toi thieu 44px chieu cao)
  - Thanh trang thai mang luon hien tren cung (yeu cau so 2)
  - Khong dung thu vien ngoai / CDN (Pi mang di hien truong co the khong co net)
"""
import subprocess

# (duong dan, nhan, icon)
#
# LOI THAT DA TIM RA (nguoi dung bao icon Nguon dien/reboot "bi loi" tren man
# hinh cam ung RasPad): ky tu ⏻ (U+23FB, khoi Unicode "Miscellaneous
# Technical") KHONG nam trong pham vi ma font Noto Color Emoji mac dinh cua
# Pi OS Lite phu toi - hien thanh o vuong trong (tofu) thay vi bieu tuong.
# Da doi sang ⚡ (khoi Emoji chuan, luon co san). Tuyet doi khong dung lai cac
# ky tu trong khoi U+2300-23FF (⏯ ⏸ ⏹ ⏻ ⏼ ⏽...) cho icon hien tren man hinh
# nay - chi dung emoji thuoc khoi chuan (mat cuoi, con vat, do vat thong
# thuong) da kiem chung la luon co san tren Pi OS.
# Thanh menu ben trai.
#
# GOM NHOM thay vi 16 muc phang nhu truoc: 16 dong lam thanh menu dai hon
# man hinh RasPad, phai cuon moi thay het - va cac muc lien quan nhau
# (WiFi/Bluetooth/Truy cap tu xa deu la "duong vao Pi") lai nam rai rac
# xen ke voi thu khong lien quan.
#
# Cau truc: ("href", "ten", "icon")                     -> muc don
#           ("nhom", "ten", "icon", [cac muc con...])   -> nhom mo/dong
#
# Nhom nao chua trang dang mo thi TU DONG bung ra (xem render_page) - de
# nguoi dung luon nhin thay minh dang o dau, khong phai tu mo lai.
NAV_ITEMS = [
    ("/", "Tổng quan", "🏠"),

    # Cac duong ket noi VAO chinh con Pi nay
    ("nhom", "Kết nối server", "📡", [
        ("/wifi", "WiFi / AP", "📶"),
        ("/bluetooth", "Bluetooth", "🔵"),
        ("/remote", "Truy cập từ xa", "🌍"),
    ]),

    # Cac duong tu Pi ket noi RA thiet bi mang can lam viec
    ("nhom", "Kết nối thiết bị", "🔌", [
        ("/console", "Console", "🖥️"),
        ("/terminal", "Terminal server", "⌨️"),
        ("/ssh", "SSH", "🔑"),
        ("/direct", "Cắm thẳng thiết bị", "🔗"),
    ]),

    ("/nettools", "Network Tools", "🛠️"),
    ("/deployos", "Deployment OS", "💿"),

    # Noi cat du lieu de dung lai
    ("nhom", "Kho lưu trữ", "📦", [
        ("/storage", "Kho file", "💾"),
        ("/commands", "Thư viện lệnh", "📚"),
    ]),

    ("/logs", "Nhật ký lỗi", "📋"),
    ("/power", "Nguồn điện", "⚡"),
    ("/giaitri", "Giải trí", "📺"),

    ("nhom", "Cài đặt", "⚙️", [
        ("/settings", "Cài đặt chung", "⚙️"),
        ("/docs", "Tài liệu", "📖"),
    ]),
]

BASE_CSS = """
/* =====================================================================
   HE MAU - khai bao 1 CHO DUY NHAT bang bien CSS
   =====================================================================
   Truoc day ma mau viet thang vao tung dong (#4CAF50 xuat hien hang chuc
   lan rai rac ca file, con cac trang khac tu che mau rieng) - doi tone la
   phai do tim khap noi, sai mot cho la lech hang. Nay moi thu tro toi bo
   bien duoi day.

   QUY UOC MAU (anh Thoai chon 19/09/2026 - "hien dai ky thuat"): mau phai
   CO Y NGHIA, khong dung de trang tri:
       cyan  = thao tac / duong dan / dang duoc chon
       xanh  = CHI danh cho trang thai TOT (dang chay, da bat, OK)
       vang  = canh bao, can de y
       do    = loi, hoac hanh dong pha huy (xoa, tat)
   Nho vay liec qua la biet ngay cho nao dang on cho nao khong, thay vi
   phai doc chu - truoc day nut nao cung xanh la nen nhin rat "phang",
   khong phan biet duoc dau la viec chinh dau la viec phu.
*/
:root {
  --nen:      #0B0E14;   /* nen trang */
  --nen-noi:  #10151D;   /* thanh menu, thanh trang thai */
  --the:      #141A23;   /* the noi dung */
  --the-noi:  #1A2230;   /* the khi ro len / hang bang khi cham */
  --vien:     #1F2733;
  --vien-ro:  #2B3746;
  --chu:      #E3E8EF;
  --chu-mo:   #8A94A6;
  --chu-mo2:  #5D6879;
  --nhan:     #38BDF8;
  --nhan-dam: #0EA5E9;
  --nhan-mo:  rgba(56,189,248,.13);
  --xanh:     #4ADE80;
  --xanh-mo:  rgba(74,222,128,.12);
  --vang:     #FBBF24;
  --vang-mo:  rgba(251,191,36,.12);
  --do:       #F87171;
  --do-mo:    rgba(248,113,113,.12);
  --bong:     0 1px 2px rgba(0,0,0,.45), 0 6px 20px rgba(0,0,0,.25);
  --bo:       10px;
}

* { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
html { touch-action: manipulation; }   /* bo do tre 300ms cho tap tren man hinh cam ung */
body { margin:0; font-family: system-ui, -apple-system, "Segoe UI", Arial, sans-serif;
       background:var(--nen); color:var(--chu);
       -webkit-font-smoothing:antialiased; }
a { color:var(--nhan); text-decoration:none; }
a:hover { color:var(--nhan-dam); }

/* Vien khi di chuyen bang ban phim (Tab). Dung :focus-visible chu khong
   phai :focus - neu dung :focus thi moi lan CHAM tay vao nut tren man
   hinh cam ung deu hien vien, nhin rat ban. */
:focus-visible { outline:2px solid var(--nhan); outline-offset:2px; border-radius:4px; }

/* ---- Khung tong ---- */
.wrap { display:flex; min-height:100vh; }
/* Thanh menu DINH CHET theo man hinh (position:sticky + tu cuon rieng).
   Truoc day no cuon chung voi noi dung: o trang dai (Tong quan, Tai lieu,
   Nhat ky) keo xuong mot doan la menu bien mat, muon sang tab khac phai
   keo nguoc len tan dau trang - rat vuong khi dung tablet bang ngon tay. */
.side { width:214px; flex:0 0 214px; background:var(--nen-noi);
        border-right:1px solid var(--vien);
        display:flex; flex-direction:column; position:sticky; top:0;
        height:100vh; overflow-y:auto; scrollbar-width:thin; }
.brand { padding:15px 16px; font-size:14px; font-weight:700; color:var(--chu);
         border-bottom:1px solid var(--vien); letter-spacing:.6px;
         display:flex; align-items:center; gap:8px; }
.brand small { display:block; color:var(--chu-mo2); font-weight:400;
               font-size:11px; margin-top:3px; letter-spacing:.3px; }
.brand .bten { flex:1; min-width:0; }
/* Cham cyan truoc ten: dau hieu nhan dien, thay cho viec to xanh ca dong
   chu (chu mau nhat kho doc hon chu trang tren nen toi). */
.brand .bten::before { content:""; display:inline-block; width:7px; height:7px;
         border-radius:50%; background:var(--nhan); margin-right:8px;
         vertical-align:middle; box-shadow:0 0 8px var(--nhan); }
/* Nut thu gon: 40px de ngon tay bam trung tren man hinh cam ung */
.brand .thu { flex:none; width:40px; height:40px; border-radius:9px; cursor:pointer;
              background:transparent; border:1px solid var(--vien-ro);
              color:var(--chu-mo); font-size:15px; line-height:1;
              transition:background .12s, color .12s; }
.brand .thu:hover { background:var(--the-noi); color:var(--chu); }
.brand .thu:active { background:var(--vien-ro); }

.nav { padding:8px 8px 4px; }

/* ---- Nhom muc menu (the <details> chinh chu cua trinh duyet - khong
   can JS, bung/thu chay duoc ngay ca khi JS loi) ---- */
.nav .nhom > summary { display:flex; align-items:center; gap:11px;
    padding:12px 12px; min-height:48px; color:var(--chu-mo); font-size:14.5px;
    cursor:pointer; white-space:nowrap; list-style:none; border-radius:9px;
    -webkit-user-select:none; user-select:none;
    transition:background .12s, color .12s; }
.nav .nhom > summary::-webkit-details-marker { display:none; }
/* Mui ten chi huong mo/dong - xoay khi bung ra */
.nav .nhom > summary::after { content:"\\25B8"; margin-left:auto; font-size:11px;
    color:var(--chu-mo2); transition:transform .18s; }
.nav .nhom[open] > summary::after { transform:rotate(90deg); }
.nav .nhom > summary:hover { background:var(--the); color:var(--chu); }
.nav .nhom > summary:active { background:var(--the-noi); }
.nav .nhom .con { margin:2px 0 6px; }
.nav .nhom .con a { padding-left:26px; font-size:14px; min-height:44px; }
.nav .nhom .con a .ic { font-size:15px; width:20px; }

/* ---- Che do THU GON: chi con day icon ----
   Dat class tren <body> (khong phai tren .side) de CSS o day doi duoc ca
   be rong cot ben trai lan hien thi cua tung muc con. */
body.thu-gon .side { width:64px; flex:0 0 64px; }
body.thu-gon .side .nl,
body.thu-gon .side .brand .bten,
body.thu-gon .side .foot { display:none; }
body.thu-gon .side .brand { justify-content:center; padding:15px 8px; }
body.thu-gon .side .nav a,
body.thu-gon .side .nav .nhom > summary { justify-content:center; padding:12px 6px; }
body.thu-gon .side .nav .nhom > summary::after { display:none; }
/* Khi thu gon thi luon bung cac nhom ra (chi con icon nen khong chiem cho),
   neu khong cac muc con se bi giau han, khong bam vao dau duoc. */
body.thu-gon .side .nav .nhom .con a { padding-left:6px; }
/* Muc menu toi thieu 44px chieu cao (khuyen nghi cho man hinh cam ung) va co
   hieu ung bam :active - :hover khong bao gio kich hoat tren cam ung nen
   thieu no nguoi dung khong biet minh vua cham trung hay chua.
   white-space:nowrap: truoc day "Cam thang thiet bi" bi xuong 2 dong lam
   danh sach cao thap khong deu, kho nham trung muc can bam. */
.nav a { display:flex; align-items:center; gap:11px; padding:12px; min-height:48px;
         color:var(--chu-mo); font-size:14.5px; border-radius:9px;
         white-space:nowrap; -webkit-user-select:none; user-select:none;
         position:relative; transition:background .12s, color .12s; }
.nav a:hover { background:var(--the); color:var(--chu); }
.nav a:active { background:var(--the-noi); }
/* Muc dang mo: nen cyan mo + 1 vach cyan ben trai. Vach dung ::before chu
   khong dung border-left nhu truoc - border-left lam chu bi day lech 3px so
   voi cac muc khac, nhin ca cot bi so le. */
.nav a.active { background:var(--nhan-mo); color:var(--nhan); font-weight:600; }
.nav a.active::before { content:""; position:absolute; left:0; top:9px; bottom:9px;
         width:3px; border-radius:0 3px 3px 0; background:var(--nhan); }
.nav a .ic { font-size:18px; width:24px; text-align:center; flex:none;
         filter:grayscale(.25); }
.nav a.active .ic { filter:none; }
.side .foot { margin-top:auto; padding:10px 16px; border-top:1px solid var(--vien);
              font-size:12px; color:var(--chu-mo2); }
.side .foot a { display:inline-block; min-height:36px; line-height:36px;
                color:var(--chu-mo); }
.side .foot a:hover { color:var(--do); }

.main { flex:1; min-width:0; display:flex; flex-direction:column; }

/* ---- Thanh trang thai mang ---- */
.status { display:flex; gap:9px; padding:11px 16px; background:var(--nen-noi);
          border-bottom:1px solid var(--vien); flex-wrap:wrap; align-items:stretch;
          position:sticky; top:0; z-index:20; }
.chip { background:var(--the); border:1px solid var(--vien); border-radius:9px;
        padding:8px 13px 8px 12px; min-width:172px; position:relative;
        display:flex; flex-direction:column; justify-content:center; }
/* Cham trang thai thay cho vach mau ben trai: nho hon, de nhan ra hon, va
   khong lam o bi lech chieu rong nhu border-left 3px truoc day. */
.chip .k { font-size:10.5px; color:var(--chu-mo2); text-transform:uppercase;
           letter-spacing:.6px; display:flex; align-items:center; gap:6px; }
.chip .k::before { content:""; width:7px; height:7px; border-radius:50%;
           background:var(--chu-mo2); flex:none; }
.chip.up .k::before { background:var(--xanh); box-shadow:0 0 7px var(--xanh); }
.chip.down .k::before { background:var(--chu-mo2); }
.chip.up { border-color:rgba(74,222,128,.28); }
.chip .v { font-size:14px; color:var(--chu); font-weight:600; margin-top:3px;
           font-family:ui-monospace, monospace; letter-spacing:-.2px; }
.chip .x { font-size:11px; color:var(--chu-mo); margin-top:2px; }
.status .spacer { flex:1; }
.status .act { display:flex; gap:8px; align-items:center; }
.status .act .btn { min-height:40px; }

/* ---- Vung noi dung ----
   Dem duoi 96px (khong phai 40px): nut ban phim ao noi o goc phai duoi cao
   58px - dem mong lam no de len dung hang/nut cuoi trang, bam khong trung. */
.content { padding:22px 24px 96px; flex:1; max-width:1500px; width:100%; }
h1 { font-size:24px; color:var(--chu); margin:0 0 5px; font-weight:650;
     letter-spacing:-.3px; }
/* Tieu de muc co vach cyan ben trai - mat luot qua la biet trang chia lam
   may phan, thay vi ca trang toan chu cung mau. */
h2 { font-size:16.5px; color:var(--chu); margin:28px 0 12px; font-weight:600;
     display:flex; align-items:center; gap:9px; }
h2::before { content:""; width:3px; height:16px; border-radius:2px;
     background:var(--nhan); flex:none; }
.sub { color:var(--chu-mo); font-size:13.5px; margin:0 0 20px; }

/* ---- Thanh phan chung ---- */
.card { background:var(--the); border:1px solid var(--vien); border-radius:var(--bo);
        padding:18px 20px; margin-bottom:16px; box-shadow:var(--bong); }
.card h3 { margin:0 0 12px; font-size:15.5px; color:var(--chu); font-weight:600; }
/* Bang co the rat rong (danh sach ARP, LLDP, quet WiFi). Cho no tu cuon
   NGANG BEN TRONG khung noi dung thay vi day ca trang lech sang phai -
   tren tablet ca trang bi lech ngang la rat kho keo lai cho cu. */
.tbl-scroll { overflow-x:auto; -webkit-overflow-scrolling:touch; margin-bottom:6px;
              border:1px solid var(--vien); border-radius:var(--bo);
              background:var(--the); }
.tbl-scroll table { border-radius:var(--bo); overflow:hidden; }
table { width:100%; border-collapse:collapse; }
th,td { padding:12px 13px; text-align:left; border-bottom:1px solid var(--vien);
        font-size:14.5px; }
tbody tr:last-child td, table tr:last-child td { border-bottom:none; }
tbody tr:hover, table tr:hover { background:rgba(255,255,255,.018); }
tbody tr:active, table tr:active { background:var(--the-noi); }
th { background:rgba(255,255,255,.028); color:var(--chu-mo); font-size:11.5px;
     text-transform:uppercase; letter-spacing:.5px; font-weight:600;
     white-space:nowrap; }
input[type=text],input[type=password],input[type=number],input[type=search],
input[type=url],select,textarea {
  padding:11px 13px; background:var(--nen); color:var(--chu);
  border:1px solid var(--vien-ro);
  border-radius:8px; font-size:15px; width:100%; max-width:440px; font-family:inherit;
  min-height:44px; transition:border-color .12s, box-shadow .12s; }
input:focus,select:focus,textarea:focus { outline:none; border-color:var(--nhan);
  box-shadow:0 0 0 3px var(--nhan-mo); }
input::placeholder, textarea::placeholder { color:var(--chu-mo2); }
textarea { font-family:ui-monospace, monospace; min-height:110px; }
label { display:block; margin:13px 0 6px; font-size:13.5px; color:var(--chu-mo);
        font-weight:500; }

/* ---- NUT ----
   VI SAO CHIA 3 MUC RO RANG (anh Thoai: "khong roi mat, de lai cac nut va mo
   cac nut 1 cach hop ly"): truoc day MOI nut deu la 1 khoi mau dac - tren
   trang co bang nhieu hang thi moi hang 2-3 khoi mau, ca man hinh thanh mot
   manh mau loang lo, nhin khong ra dau la viec chinh.
   Nay:
     nut chinh  (mac dinh)  = nen cyan dac  -> 1 trang thuong chi co 1-2 cai
     nut phu    (.gray)     = vien mo, nen trong -> lui han ve sau, khong gianh
     nut nguy hiem (.red)   = vien do, chu do -> chi to do dac khi cham vao,
                              van nhan ra ngay nhung khong "hu doa" ca trang
   Chu tren nen cyan de mau xanh than THAY VI trang: cyan #38BDF8 kha sang,
   chu trang tren no doc rat met mat. */
button, .btn { padding:11px 18px; background:var(--nhan); color:#04212E; border:none;
  border-radius:8px; font-size:14.5px; cursor:pointer; display:inline-flex;
  align-items:center; justify-content:center; gap:7px;
  min-height:46px; font-family:inherit; font-weight:600;
  -webkit-user-select:none; user-select:none;
  transition:transform .08s, background .12s, box-shadow .12s; }
button:hover,.btn:hover { background:var(--nhan-dam); color:#04212E; }
/* :active thay cho :hover - tren man hinh cam ung khong co chuot di qua de
   :hover kich hoat, thieu phan hoi nay nguoi dung khong biet vua cham trung
   nut hay chua va hay bam lai nhieu lan (co the go trung lenh). */
button:active,.btn:active { transform:scale(.97); }
button[disabled], .btn[disabled] { transform:none; opacity:.45; cursor:not-allowed; }
/* .gray = nut PHU: nen trong, chi co vien. Day la thay doi lam trang do roi
   nhat, vi .gray la class duoc dung nhieu thu nhi trong ca du an (57 cho). */
button.gray,.btn.gray { background:transparent; color:var(--chu);
  border:1px solid var(--vien-ro); }
button.gray:hover,.btn.gray:hover { background:var(--the-noi); color:var(--chu);
  border-color:var(--chu-mo2); }
/* .blue gop chung voi nut chinh: truoc day cyan/xanh duong/xanh la dung lan
   lon nhau khong theo quy tac nao, 3 sac xanh canh nhau lam roi mat ma
   khong he mang y nghia gi khac nhau. */
button.blue,.btn.blue { background:var(--nhan); color:#04212E; }
button.blue:hover,.btn.blue:hover { background:var(--nhan-dam); }
/* .red = hanh dong PHA HUY (xoa, tat, khoi dong lai). */
button.red,.btn.red { background:transparent; color:var(--do);
  border:1px solid rgba(248,113,113,.45); }
button.red:hover,.btn.red:hover { background:var(--do); color:#2A0A0A;
  border-color:var(--do); }
/* Nut bao trang thai TOT (dang chay/da bat) - dung cho cac cho can nhan
   manh la moi thu on. */
button.xanh,.btn.xanh { background:var(--xanh); color:#06240F; }
button.xanh:hover,.btn.xanh:hover { background:#3BC96D; }
/* Van giu nho hon nut chinh de phan biet muc do quan trong, nhung khong duoi
   nguong 40px - duoi muc nay ngon tay nguoi lon rat de bam nham nut ben canh. */
button.small,.btn.small,button.nho,.btn.nho { padding:9px 14px; font-size:13.5px;
  min-height:40px; border-radius:7px; }

pre { background:#070A0F; border:1px solid var(--vien); padding:14px;
      border-radius:8px; overflow-x:auto; white-space:pre-wrap;
      word-break:break-word; font-size:13.5px; color:#CBD5E1; line-height:1.55; }
code { font-family:ui-monospace, monospace; background:rgba(56,189,248,.09);
       color:#7DD3FC; padding:2px 7px; border-radius:5px; font-size:13.5px; }

/* ---- Bang thong bao ----
   Vien trai 3px + nen mo cung tone: doc duoc ngay la loai gi ma khong can
   doc chu, va khong chiem nhieu mau nhu khoi dac. */
.msg { padding:13px 16px; border-radius:9px; margin:15px 0; font-size:14.5px;
       line-height:1.6; border:1px solid transparent; border-left-width:3px; }
.msg.ok   { background:var(--xanh-mo); border-color:rgba(74,222,128,.3);
            border-left-color:var(--xanh); color:#BBF7D0; }
.msg.err  { background:var(--do-mo);   border-color:rgba(248,113,113,.3);
            border-left-color:var(--do);   color:#FECACA; }
.msg.warn { background:var(--vang-mo); border-color:rgba(251,191,36,.3);
            border-left-color:var(--vang); color:#FDE68A; }
.msg.info { background:var(--nhan-mo); border-color:rgba(56,189,248,.3);
            border-left-color:var(--nhan); color:#BAE6FD; }

.row { display:flex; gap:11px; flex-wrap:wrap; align-items:flex-end; }
.grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(255px,1fr)); gap:14px; }

/* ---- Thanh tab cua muc Deployment OS ----
   De o day (khung chung) thay vi trong rieng ui/deployos.py: trang "Tien
   trinh" (ui/tiendo.py) la mot trang RIENG nhung van thuoc muc Deployment
   OS - truoc day no khong lay duoc CSS nay nen KHONG CO thanh tab nao ca,
   vao roi khong co duong quay lai (anh Thoai bao dung cho nay). */
.dep-tabs { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:12px; }
.dep-tabs.sub { margin-top:-4px; margin-bottom:18px; }
.dep-tab { padding:10px 16px; min-height:44px; display:inline-flex;
  align-items:center; background:var(--the); border:1px solid var(--vien);
  border-radius:8px; color:var(--chu-mo); font-size:14px;
  transition:background .12s, color .12s, border-color .12s; }
.dep-tab:hover { background:var(--the-noi); color:var(--chu); }
.dep-tab:active { transform:scale(.97); }
.dep-tab.on { background:var(--nhan-mo); border-color:var(--nhan);
  color:var(--nhan); font-weight:600; }
.dep-tabs.sub .dep-tab { padding:8px 13px; min-height:38px; font-size:13px; }

/* ---- Cac lop chu dung rai rac trong cac trang cong cu mang ---- */
.hint { color:var(--chu-mo); font-size:13px; }
.ok-txt  { color:var(--xanh); font-weight:600; }
.bad-txt { color:var(--do);   font-weight:600; }
.none-val { color:var(--chu-mo2); }
.big { font-size:19px; font-weight:650; color:var(--chu); }

/* ---- Man hinh rong (PC): tang mat do thong tin ----
   Anh Thoai dung CA man cam ung RasPad LAN trinh duyet PC. Tren PC man
   rong, khoang cach thua cua thiet ke cho ngon tay lam trang trong hoac
   phai cuon nhieu vo ich - o day thu gon lai mot chut, nhung van giu nut
   >=40px de con cham tay duoc neu dung man cam ung do phan giai cao. */
@media (min-width: 1200px) and (pointer: fine) {
  .content { padding:24px 28px 96px; }
  th,td { padding:10px 13px; }
  .nav a, .nav .nhom > summary { min-height:42px; padding:9px 12px; }
  .nav .nhom .con a { min-height:38px; }
  button, .btn { min-height:40px; padding:9px 16px; }
  button.small,.btn.small,button.nho,.btn.nho { min-height:34px; padding:7px 12px; }
  input[type=text],input[type=password],input[type=number],input[type=search],
  input[type=url],select,textarea { min-height:40px; padding:9px 12px; }
}

/* ---- Man hinh nho (dien thoai) ---- */
@media (max-width: 760px) {
  .wrap { flex-direction:column; }
  /* Bo sticky/chieu cao co dinh o day: tren dien thoai menu nam NGANG tren
     cung, ep height:100vh se chiem tron man hinh. */
  .side { width:100%; flex:none; position:static; height:auto; }
  .nav { display:flex; overflow-x:auto; padding:6px; }
  .nav a { border-radius:8px; white-space:nowrap; }
  .nav a.active::before { left:9px; right:9px; top:auto; bottom:0; width:auto;
       height:3px; border-radius:3px 3px 0 0; }
  .side .foot, .brand small { display:none; }
  .status { position:static; }
  .content { padding:16px 14px 96px; }
}
"""


import socket
import struct
import time

# Thanh trang thai duoc goi lai moi 30 giay tu MOI trang dang mo. Nho ket qua
# vai giay de khong lam viec trung lap - dang ke tren Pi doi thap.
_STATUS_CACHE = {"data": None, "at": 0.0}
STATUS_TTL = 4.0


def _ipv4_of(name):
    """
    Lay dia chi IPv4 cua 1 interface bang ioctl - KHONG spawn tien trinh.
    Truoc day goi lenh `ip` cho tung interface (3 lan moi lan tai trang);
    tren Pi 3/Zero moi lan spawn ton hang chuc mili giay.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sk:
            packed = struct.pack("256s", name.encode()[:15])
            return socket.inet_ntoa(
                __import__("fcntl").ioctl(sk.fileno(), 0x8915, packed)[20:24]
            )
    except Exception:
        return ""


def _iface_info(name):
    """Tra ve (co_ip, ip, trang_thai_link) cua 1 interface."""
    ip = _ipv4_of(name)
    try:
        with open(f"/sys/class/net/{name}/operstate") as f:
            state = f.read().strip()
    except Exception:
        state = "?"
    return bool(ip), ip, state


def get_status_chips(use_cache=True):
    """
    Thong tin cho thanh trang thai: card LAN, card WiFi, Bluetooth PAN.
    Co IP thi hien IP, khong thi ghi ro ly do.
    """
    if use_cache and _STATUS_CACHE["data"] is not None:
        if time.time() - _STATUS_CACHE["at"] < STATUS_TTL:
            return _STATUS_CACHE["data"]

    chips = []

    # --- eth0 (card LAN) ---
    up, ip, state = _iface_info("eth0")
    chips.append({
        "key": "LAN (eth0)",
        "val": ip if ip else ("Đã cắm dây" if state == "up" else "Chưa cắm dây"),
        "extra": ("link " + state) if not ip else f"link {state}",
        "up": up,
    })

    # --- wlan0 (card WiFi) ---
    up_w, ip_w, state_w = _iface_info("wlan0")
    ssid, mode = "", ""
    try:
        info = subprocess.run(["iw", "dev", "wlan0", "info"],
                              capture_output=True, text=True, timeout=4).stdout
        for line in info.splitlines():
            line = line.strip()
            if line.startswith("ssid "):
                ssid = line[5:].strip()
            elif line.startswith("type "):
                mode = line[5:].strip()
    except Exception:
        pass

    if mode == "AP":
        extra = "Đang phát AP: " + (ssid or "ConsolePi")
    elif ssid:
        extra = "Đã nối: " + ssid
    else:
        extra = "Chưa kết nối WiFi"
    chips.append({
        "key": "WiFi (wlan0)",
        "val": ip_w if ip_w else "Không có IP",
        "extra": extra,
        "up": up_w,
    })

    # --- pan0 (Bluetooth) ---
    up_b, ip_b, _ = _iface_info("pan0")
    n_bt = 0
    try:
        out = subprocess.run(["ip", "neigh", "show", "dev", "pan0"],
                             capture_output=True, text=True, timeout=4).stdout
        n_bt = sum(1 for l in out.splitlines() if "REACHABLE" in l or "STALE" in l)
    except Exception:
        pass
    chips.append({
        "key": "Bluetooth (pan0)",
        "val": ip_b if ip_b else "Chưa bật",
        "extra": (f"{n_bt} thiết bị đang nối" if n_bt else "Chưa có thiết bị"),
        "up": up_b,
    })

    # --- Cloudflare Tunnel (yeu cau: muon thay trang thai nay ngay tren thanh
    # trang thai, ngang hang voi LAN/WiFi/Bluetooth thay vi phai vao rieng
    # tab Truy cap tu xa moi biet duong ham co dang chay hay khong) ---
    # Import cho vao trong ham (khong dat o dau file): remote.py co import
    # nguoc lai render_page tu chinh file nay - dat import o dau file se tao
    # vong lap import. Cac ham duoc goi o day deu re (shutil.which/os.path,
    # toi da 1 lenh systemctl is-active), cung muc chi phi voi cac chip khac.
    from . import remote as _remote
    cf_cai = _remote.da_cai()
    cf_tok = _remote.co_token() if cf_cai else False
    cf_chay = _remote.dang_chay() if (cf_cai and cf_tok) else False
    if not cf_cai:
        cf_val, cf_extra = "Chưa cài đặt", "Xem tab Truy cập từ xa"
    elif not cf_tok:
        cf_val, cf_extra = "Chưa cấu hình", "Thiếu token đường hầm"
    elif cf_chay:
        cf_val, cf_extra = "Đang chạy", "Ra Internet qua Cloudflare"
    else:
        cf_val, cf_extra = "Đã tắt", "Đường hầm đang không bật"
    chips.append({
        "key": "Cloudflare",
        "val": cf_val,
        "extra": cf_extra,
        "up": cf_chay,
    })

    _STATUS_CACHE["data"] = chips
    _STATUS_CACHE["at"] = time.time()
    return chips


def render_page(body_html, active="/", title="Console Pi", subtitle="", extra_css=""):
    """
    Dung 1 trang hoan chinh voi khung chung.
      body_html : phan noi dung rieng cua trang (chuoi HTML da render xong)
      active    : duong dan de to sang muc menu tuong ung
    """
    chips = get_status_chips()

    chips_html = ""
    for idx, c in enumerate(chips):
        cls = "up" if c["up"] else "down"
        chips_html += (
            f'<div class="chip {cls}" data-chip="{idx}"><div class="k">{c["key"]}</div>'
            f'<div class="v">{c["val"]}</div><div class="x">{c["extra"]}</div></div>'
        )

    def _dang_mo(href):
        """'/' chi sang khi khop tuyet doi; cac muc khac sang khi la tien to."""
        return (active == href) if href == "/" else active.startswith(href)

    def _ve_muc(href, label, icon):
        return (f'<a href="{href}" class="{"active" if _dang_mo(href) else ""}" '
                f'title="{label}">'
                f'<span class="ic">{icon}</span><span class="nl">{label}</span></a>')

    nav_html = ""
    for muc in NAV_ITEMS:
        if muc[0] != "nhom":
            nav_html += _ve_muc(*muc)
            continue
        _, ten_nhom, icon_nhom, cac_con = muc
        # Nhom chua trang dang mo thi bung san - nguoi dung luon thay minh
        # dang dung o dau ma khong phai tu mo lai sau moi lan chuyen trang.
        mo = any(_dang_mo(h) for h, _l, _i in cac_con)
        con_html = "".join(_ve_muc(*c) for c in cac_con)
        nav_html += (
            f'<details class="nhom"{" open" if mo else ""}>'
            f'<summary title="{ten_nhom}">'
            f'<span class="ic">{icon_nhom}</span>'
            f'<span class="nl">{ten_nhom}</span></summary>'
            f'<div class="con">{con_html}</div></details>'
        )

    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} - Console Pi</title>
<style>{BASE_CSS}
{extra_css}</style>
</head>
<body>
<div class="wrap">
  <div class="side">
    <div class="brand">
      <span class="bten">CONSOLE PI<small>Network Toolkit</small></span>
      <button type="button" id="nut-thu" class="thu"
              title="Thu gọn / mở rộng thanh menu">&raquo;</button>
    </div>
    <div class="nav">{nav_html}</div>
    <div class="foot">
      <a href="/logout">Đăng xuất</a>
    </div>
  </div>
  <div class="main">
    <div class="status">
      {chips_html}
      <div class="spacer"></div>
      <div class="act"><a href="{active}" class="btn gray small">🔃 Lam moi</a></div>
    </div>
    <div class="content">
      <h1>{title}</h1>
      {f'<p class="sub">{subtitle}</p>' if subtitle else ''}
      {body_html}
    </div>
  </div>
</div>
<script>
/* Thu gon / mo rong thanh menu ben trai.
   Nho lua chon vao localStorage de giu nguyen khi chuyen trang - neu
   khong thi moi lan bam sang trang khac menu lai bung ra nhu cu, rat
   kho chiu. Ap dung NGAY (khong doi DOMContentLoaded) de trang khong
   bi "nhay" tu rong sang hep truoc mat nguoi dung. */
(function() {{
  var K = 'consolepi-menu-thu-gon';
  try {{
    if (localStorage.getItem(K) === '1') document.body.classList.add('thu-gon');
  }} catch (e) {{}}
  var n = document.getElementById('nut-thu');
  if (!n) return;
  function veLai() {{
    var gon = document.body.classList.contains('thu-gon');
    n.innerHTML = gon ? '&laquo;' : '&raquo;';
  }}
  veLai();
  n.addEventListener('click', function() {{
    var gon = document.body.classList.toggle('thu-gon');
    try {{ localStorage.setItem(K, gon ? '1' : '0'); }} catch (e) {{}}
    // Thu gon thi bung het cac nhom (chi con icon, khong ton cho) de moi
    // muc con van bam vao duoc.
    document.querySelectorAll('.nav .nhom').forEach(function(d) {{
      if (gon) d.open = true;
    }});
    veLai();
  }});
}})();
</script>
<script src="/dashboard.js"></script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Boc lai trang cu vao khung moi
#
# 9 cong cu trong goi nettools/ duoc viet truoc khi co khung giao dien chung,
# moi cai tu dung <html> rieng. Thay vi sua 9 file (nhieu rui ro), ham nay
# boc lai phan noi dung cua chung vao khung chung - 1 diem sua duy nhat,
# va cong cu moi them sau nay cung tu dong duoc boc.
# ---------------------------------------------------------------------------
import re as _re

_BODY_RE = _re.compile(r"<body[^>]*>(.*?)</body>", _re.S | _re.I)
_STYLE_RE = _re.compile(r"<style[^>]*>(.*?)</style>", _re.S | _re.I)
_TITLE_RE = _re.compile(r"<title[^>]*>(.*?)</title>", _re.S | _re.I)
_H1_RE = _re.compile(r"<h1[^>]*>.*?</h1>", _re.S | _re.I)
# Dong "← Network Tools" / "← Quay lai Dashboard" - da thua vi co thanh trai
_BACKLINK_RE = _re.compile(r"<p>\s*<a href=\"/(?:nettools)?\"[^>]*>←[^<]*</a>\s*</p>", _re.I)


def wrap_legacy_html(html, active="/nettools"):
    """Boc 1 trang HTML hoan chinh (kieu cu) vao khung giao dien chung."""
    m = _BODY_RE.search(html)
    if not m:
        return html                      # khong nhan dang duoc thi de nguyen

    body = m.group(1)

    title = "Network Tools"
    tm = _TITLE_RE.search(html)
    if tm:
        title = tm.group(1).split(" - ")[0].strip()

    # Bo <h1> va link quay lai cu (khung moi da co tieu de + thanh dieu huong)
    body = _H1_RE.sub("", body, count=1)
    body = _BACKLINK_RE.sub("", body, count=1)

    # Giu lai CSS rieng cua trang do (vd bang mau, pre...), nhung bo phan
    # dinh dang body/nen vi khung chung da lo
    css = ""
    for sm in _STYLE_RE.finditer(html):
        for rule in sm.group(1).split("}"):
            sel = rule.split("{")[0].strip()
            if sel and not sel.startswith(("body", "html", "a ", "a{", "a:")):
                css += rule + "}\n"

    return render_page(body, active=active, title=title, extra_css=css)
