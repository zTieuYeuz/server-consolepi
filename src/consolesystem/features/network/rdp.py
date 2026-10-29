# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Remote Desktop (RDP) ngay trong trinh duyet, qua guacd (Apache Guacamole) chay bang Docker tren chinh may Console System.

  trinh duyet (guacamole-common-js) --WebSocket /uem-vnc-ws/<ma>--> Console System --TCP 127.0.0.1:4822--> guacd --RDP 3389--> may Windows
  * guacd chi nghe 127.0.0.1 (khong lo ra mang). Duong WebSocket dung chung cau noi da co (core/ws_cau): phai dang nhap moi vao duoc.
  * Mat khau RDP chi nam trong bo nho cua phien (khong ghi dia), ma phien chi dung de mo ket noi trong 2 phut.
  * Anh Thoai chon Docker guacd (28/10/2026) vi Debian 13 khong con goi guacd; can Internet luc cai lan dau.
"""
import base64
import hashlib
import re
import secrets
import socket
import subprocess
import threading
import time
import uuid

from flask import Response, jsonify, request

from consolesystem.core import ws_cau as WS
from consolesystem.core import taisan as _taisan
from consolesystem.core.esc import esc_html as _esc
from consolesystem.core.nhatky import bo_qua as _bo_qua

GUACD = ("127.0.0.1", 4822)
ANH_GUACD = "guacamole/guacd:1.5.5"
TEN_CONTAINER = "cs-guacd"
LOG_CAI = "/var/log/console-system-guacd.log"
_CAI = {"dang": False}
_JS = _taisan.doc("vendor/guacamole-common-1.5.0.min.js")


# ------------------------------------------------------------------ guacd
def guacd_san_sang():
    try:
        with socket.create_connection(GUACD, timeout=1.5):
            return True
    except OSError:
        return False


def trang_thai():
    co_docker = bool(subprocess.run(["sh", "-c", "command -v docker"], capture_output=True, timeout=5).stdout.strip())
    tail = ""
    try:
        with open(LOG_CAI, encoding="utf-8", errors="replace") as f:
            tail = f.read()[-1500:]
    except OSError:
        pass
    return {"guacd": guacd_san_sang(), "docker": co_docker, "dang_cai": _CAI["dang"], "log": tail}


_SCRIPT_CAI = r"""set -e
echo "== $(date '+%d/%m/%Y %H:%M:%S') Bat dau cai guacd"
if ! command -v docker >/dev/null 2>&1; then
  echo "Cai Docker (docker.io)..."; export DEBIAN_FRONTEND=noninteractive
  apt-get update -q && apt-get install -y -q docker.io
fi
systemctl enable --now docker
docker rm -f {ten} >/dev/null 2>&1 || true
echo "Tai va chay {anh}..."
docker run -d --name {ten} --restart unless-stopped -p 127.0.0.1:4822:4822 {anh}
for i in $(seq 1 30); do (exec 3<>/dev/tcp/127.0.0.1/4822) 2>/dev/null && {{ echo "XONG: guacd dang chay (127.0.0.1:4822)"; exit 0; }}; sleep 1; done
echo "LOI: guacd chua mo cong 4822"; exit 1
"""


def cai_guacd():
    """Cai Docker (neu chua co) + chay container guacd, chay nen, ghi log."""
    if _CAI["dang"]:
        return False

    def viec():
        _CAI["dang"] = True
        try:
            with open(LOG_CAI, "w", encoding="utf-8") as f:
                subprocess.run(["bash", "-c", _SCRIPT_CAI.format(ten=TEN_CONTAINER, anh=ANH_GUACD)], stdout=f, stderr=subprocess.STDOUT, timeout=1800)
        except Exception as e:
            _bo_qua(e)
        finally:
            _CAI["dang"] = False
    threading.Thread(target=viec, daemon=True, name="cai-guacd").start()
    return True


# ------------------------------------------------------------------ giao thuc Guacamole
def _ma(*phan):
    """Ma hoa 1 lenh Guacamole: do dai tinh theo ky tu (code point), khong phai byte."""
    return ",".join(f"{len(str(p))}.{p}" for p in phan) + ";"


def _tach(buf):
    """Tach cac lenh hoan chinh o dau `buf`. Tra (danh_sach_lenh_tho, phan_con_lai). Moi lenh: (chuoi_tho, [phan...])."""
    ra, i, n = [], 0, len(buf)
    while i < n:
        j, phan = i, []
        while True:
            dot = buf.find(".", j)
            if dot < 0:
                return ra, buf[i:]
            try:
                dai = int(buf[j:dot])
            except ValueError:
                raise ValueError("lenh Guacamole hong")
            k = dot + 1 + dai
            if k >= n:
                return ra, buf[i:]
            phan.append(buf[dot + 1:k])
            if buf[k] == ";":
                ra.append((buf[i:k + 1], phan))
                i = k + 1
                break
            if buf[k] != ",":
                raise ValueError("lenh Guacamole hong")
            j = k + 1
    return ra, ""


class _Doc:
    """Doc lenh tu socket guacd (giai ma UTF-8 tung khuc, khong cat ngang ky tu)."""
    def __init__(self, s):
        import codecs
        self.s, self.buf, self.dec = s, "", codecs.getincrementaldecoder("utf-8")()

    def them(self):
        d = self.s.recv(65536)
        if not d:
            raise ConnectionError
        self.buf += self.dec.decode(d)

    def mot_lenh(self):
        while True:
            ds, du = _tach(self.buf)
            if ds:
                self.buf = self.buf[len(ds[0][0]):]
                return ds[0][1]
            self.them()


def _bat_tay_guacd(s, ts):
    """select rdp -> args -> size/audio/video/image/timezone -> connect -> ready. Tra id ket noi."""
    d = _Doc(s)
    s.sendall(_ma("select", "rdp").encode())
    lenh = d.mot_lenh()
    if not lenh or lenh[0] != "args":
        raise RuntimeError("guacd trả lời lạ: " + str(lenh[:1]))
    ten_ts = lenh[1:]
    s.sendall((_ma("size", ts["w"], ts["h"], ts["dpi"]) + _ma("audio", "audio/L16") + _ma("video")
               + _ma("image", "image/png", "image/jpeg", "image/webp") + _ma("timezone", "Asia/Ho_Chi_Minh")).encode())
    gia_tri = {
        "hostname": ts["host"], "port": str(ts["port"]), "username": ts["user"], "password": ts["mk"], "domain": ts["domain"],
        "security": ts["security"], "ignore-cert": "true", "resize-method": "display-update", "server-layout": "en-us-qwerty",
        "enable-wallpaper": "false", "enable-font-smoothing": "true", "enable-full-window-drag": "false",
        "enable-desktop-composition": "false", "enable-menu-animations": "false", "disable-audio": "false",
        "color-depth": "24", "client-name": "Console System",
    }
    if ten_ts and ten_ts[0].startswith("VERSION_"):         # guacd 1.1+: phan dau la phien ban giao thuc, phai gui lai y nguyen
        vals = [ten_ts[0]] + [gia_tri.get(t, "") for t in ten_ts[1:]]
    else:
        vals = [gia_tri.get(t, "") for t in ten_ts]
    s.sendall(_ma("connect", *vals).encode())
    lenh = d.mot_lenh()
    if not lenh or lenh[0] != "ready":
        raise RuntimeError("guacd không sẵn sàng: " + " ".join(lenh[:3]))
    return lenh[1] if len(lenh) > 1 else "", d


def _tra_101(cs, hdr, key):
    acc = base64.b64encode(hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode(), usedforsecurity=False).digest()).decode()
    sub = "\r\nSec-WebSocket-Protocol: guacamole" if "guacamole" in (hdr.get("sec-websocket-protocol") or "") else ""
    cs.sendall(f"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: {acc}{sub}\r\n\r\n".encode())
    cs.settimeout(None)


def _xu_ly_ws(ts):
    """Ham xu ly WebSocket cho 1 phien (dang ky voi core/ws_cau)."""
    def ham(cs, hdr, key, doc_khung, khung):
        g = None
        xong = threading.Event()
        try:
            _tra_101(cs, hdr, key)
            gui_web = threading.Lock()

            def ra_web(txt):
                with gui_web:
                    cs.sendall(khung(1, txt.encode("utf-8")))
            try:
                g = socket.create_connection(GUACD, timeout=8)
                g.settimeout(30)
                _id, d = _bat_tay_guacd(g, ts)
                g.settimeout(None)
            except Exception as e:
                ra_web(_ma("error", "Không kết nối được: " + str(e)[:200], "519"))
                return
            ra_web(_ma("", str(uuid.uuid4())))          # lenh noi bo dau tien: trinh duyet chuyen tunnel sang OPEN

            def guacd_den_web():
                try:
                    while not xong.is_set():
                        ds, du = _tach(d.buf)
                        if ds:
                            d.buf = du
                            ra_web("".join(x[0] for x in ds))
                        else:
                            d.them()
                except (OSError, ConnectionError, ValueError):
                    pass
                finally:
                    xong.set()
                    try:
                        cs.shutdown(socket.SHUT_RDWR)
                    except OSError:
                        pass
            threading.Thread(target=guacd_den_web, daemon=True).start()
            con = ""
            while not xong.is_set():
                _fin, op, data = doc_khung(cs)
                if op == 8:
                    break
                if op == 9:
                    cs.sendall(khung(10, data))
                    continue
                if op not in (0, 1, 2):
                    continue
                con += data.decode("utf-8", "replace")
                ds, con = _tach(con)
                gui = []
                for tho, phan in ds:
                    if phan and phan[0] == "":                  # lenh noi bo cua tunnel (ping) -> tra lai y nguyen, khong gui guacd
                        if len(phan) > 1 and phan[1] == "ping":
                            ra_web(tho)
                        continue
                    gui.append(tho)
                if gui:
                    g.sendall("".join(gui).encode("utf-8"))
        except (OSError, ConnectionError, ValueError):
            pass
        finally:
            xong.set()
            for s in (g, cs):
                if s is not None:
                    try:
                        s.close()
                    except OSError:
                        pass
    return ham


def mo_phien(host, port, user, mk, domain, security, w, h, dpi):
    if not re.fullmatch(r"[A-Za-z0-9.\-:\[\]_]{1,253}", host or ""):
        return None, "Địa chỉ máy không hợp lệ."
    if not guacd_san_sang():
        return None, "guacd chưa chạy: bấm \"Cài / bật guacd\" ở trên."
    if not WS.dam_bao_chay():
        return None, "Cầu nối WebSocket chưa sẵn sàng."
    ts = {"host": host, "port": max(1, min(65535, int(port or 3389))), "user": user or "", "mk": mk or "", "domain": domain or "",
          "security": security if security in ("any", "nla", "tls", "rdp") else "any",
          "w": max(640, min(3840, int(w or 1280))), "h": max(480, min(2160, int(h or 720))), "dpi": max(72, min(192, int(dpi or 96)))}
    tok = secrets.token_urlsafe(24)
    WS.dang_ky(tok, _xu_ly_ws(ts), giay=120)
    return tok, ""


# ------------------------------------------------------------------ giao dien
CSS = """<style>
.rdp-luoi{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px 14px;}
.rdp-luoi label{display:block;font-size:13px;color:var(--chu-mo);margin-bottom:4px;}
.rdp-luoi input,.rdp-luoi select{width:100%;margin:0;}
.rdp-tt{display:inline-flex;align-items:center;gap:8px;font-weight:600;}
.rdp-tt i{width:9px;height:9px;border-radius:50%;background:var(--do);display:inline-block;}
.rdp-tt.ok i{background:var(--xanh);}
#rdp-log{background:#0f1114;color:#cfd6df;padding:10px;border-radius:8px;max-height:220px;overflow:auto;white-space:pre-wrap;font-size:12.5px;margin-top:10px;}
</style>"""

TRANG = """<div class="card" style="padding:12px 16px;"><div class="tk-hang" style="gap:12px;align-items:center;"><span class="rdp-tt" id="rdp-tt"><i></i><span>Đang kiểm tra...</span></span>
<span id="rdp-hop" hidden><button class="tk-nut" type="button" id="rdp-cai">Cài / bật guacd</button></span></div>
<div id="rdp-cho" hidden><p class="tk-ghi" style="margin:8px 0 0;">guacd chạy bằng Docker trên chính Console System, chỉ nghe 127.0.0.1. Lần cài đầu cần Internet để tải Docker và image (vài phút).</p>
<pre id="rdp-log" hidden></pre></div></div>
<div class="card"><h3>Kết nối Remote Desktop</h3>
<form id="rdp-f" autocomplete="off"><div class="rdp-luoi">
<div><label>Máy (IP hoặc tên)</label><input name="host" required placeholder="192.168.110.33"></div>
<div><label>Cổng</label><input name="port" value="3389" inputmode="numeric"></div>
<div><label>Tài khoản</label><input name="user" placeholder="Administrator"></div>
<div><label>Mật khẩu</label><input name="mk" type="password" autocomplete="new-password"></div>
<div><label>Domain (nếu có)</label><input name="domain"></div>
<div><label>Bảo mật</label><select name="security"><option value="any">Tự chọn</option><option value="nla">NLA</option><option value="tls">TLS</option><option value="rdp">RDP cũ</option></select></div>
</div>
<div class="tk-hang" style="margin-top:14px;gap:10px;"><button class="tk-nut chinh" type="submit">Kết nối</button>
<label style="display:flex;gap:6px;align-items:center;margin:0;"><input type="checkbox" name="tab_moi" checked> Mở trong tab mới</label><span class="tk-ghi" id="rdp-tb"></span></div></form>
<p class="tk-ghi" style="margin-top:8px;">Mật khẩu chỉ dùng cho lần kết nối này, Console System không lưu. Máy Windows cần bật Remote Desktop (cổng 3389).</p>
<div id="rdp-gan"></div></div>
<script>(function(){var $=function(i){return document.getElementById(i);};
var GAN='cs-rdp-gan'; function ganDoc(){try{return JSON.parse(localStorage.getItem(GAN)||'[]');}catch(e){return [];}}
function veGan(){var ds=ganDoc(); $('rdp-gan').innerHTML=ds.length?'<p class="tk-ghi" style="margin:10px 0 4px;">Gần đây:</p>'+ds.map(function(x,i){return '<button type="button" class="tk-nut" data-g="'+i+'" style="margin:0 6px 6px 0;">'+(x.user?x.user+'@':'')+x.host+'</button>';}).join(''):'';}
$('rdp-gan').onclick=function(e){var i=e.target.dataset.g; if(i==null)return; var x=ganDoc()[i], f=$('rdp-f'); ['host','port','user','domain','security'].forEach(function(k){if(x[k]!=null)f[k].value=x[k];}); f.mk.focus();};
function tt(){fetch('/remote-desktop/trang-thai').then(function(r){return r.json();}).then(function(d){
 var e=$('rdp-tt'); e.className='rdp-tt'+(d.guacd?' ok':''); e.querySelector('span').textContent=d.guacd?'guacd đang kết nối được':(d.dang_cai?'Đang cài guacd...':'guacd chưa chạy');
 $('rdp-hop').hidden=!!d.guacd; $('rdp-cho').hidden=!!d.guacd; $('rdp-cai').disabled=!!d.dang_cai;
 if(!d.guacd&&d.log){$('rdp-log').hidden=false;$('rdp-log').textContent=d.log;$('rdp-log').scrollTop=1e9;}
 if(d.dang_cai)setTimeout(tt,3000);});}
$('rdp-cai').onclick=function(){if(!confirm('Cài Docker (nếu chưa có) và chạy guacd trên Console System? Cần Internet, mất vài phút.'))return;
 fetch('/remote-desktop/cai',{method:'POST'}).then(function(){setTimeout(tt,800);});};
$('rdp-f').onsubmit=function(e){e.preventDefault(); var f=e.target, sc=window.screen||{};
 var d={host:f.host.value.trim(),port:f.port.value,user:f.user.value,mk:f.mk.value,domain:f.domain.value,security:f.security.value,
  w:Math.min(innerWidth,sc.availWidth||innerWidth),h:Math.min(innerHeight,sc.availHeight||innerHeight),dpi:Math.round(96*(window.devicePixelRatio||1))};
 $('rdp-tb').textContent='Đang chuẩn bị...';
 var w=f.tab_moi.checked?window.open('about:blank','_blank'):null;
 fetch('/remote-desktop/ket-noi',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)}).then(function(r){return r.json();}).then(function(k){
  if(!k.tok){$('rdp-tb').textContent=k.tb||'Không mở được.'; if(w)w.close(); return;}
  var ds=ganDoc().filter(function(x){return !(x.host===d.host&&x.user===d.user);}); ds.unshift({host:d.host,port:d.port,user:d.user,domain:d.domain,security:d.security});
  try{localStorage.setItem(GAN,JSON.stringify(ds.slice(0,8)));}catch(e){} veGan(); f.mk.value=''; $('rdp-tb').textContent='';
  var u='/remote-desktop/xem?tok='+encodeURIComponent(k.tok)+'&ten='+encodeURIComponent(d.host); if(w)w.location=u; else location.href=u;
 }).catch(function(){$('rdp-tb').textContent='Không gọi được máy chủ.'; if(w)w.close();});};
veGan(); tt();})();</script>"""

XEM = """<!DOCTYPE html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TEN__ - Remote Desktop</title><style>
html,body{margin:0;height:100%;background:#000;overflow:hidden;font-family:system-ui,sans-serif;}
#man{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;}
#man>div{cursor:none;} #thanh{position:fixed;top:0;left:50%;transform:translate(-50%,-34px);transition:transform .2s;z-index:5;display:flex;gap:6px;
background:rgba(20,26,35,.94);border:1px solid #2b3746;border-top:0;border-radius:0 0 10px 10px;padding:6px 10px 8px;color:#e3e8ef;font-size:13px;align-items:center;}
#thanh:hover,#thanh.mo{transform:translate(-50%,0);} #thanh b{margin-right:6px;} #thanh button{background:#222b38;color:#e3e8ef;border:1px solid #33404f;border-radius:7px;padding:5px 10px;cursor:pointer;font-size:12.5px;}
#thanh button:hover{background:#2d3949;} #tb{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;color:#cfd6df;font-size:15px;text-align:center;padding:20px;z-index:4;}
</style></head><body><div id="man"></div><div id="tb">Đang kết nối tới __TEN__...</div>
<div id="thanh"><b>__TEN__</b><button id="b-cad" title="Gửi Ctrl+Alt+Del">Ctrl+Alt+Del</button><button id="b-win" title="Gửi phím Windows">Phím Win</button>
<button id="b-full">Toàn màn hình</button><button id="b-dong">Ngắt kết nối</button></div>
<script>__JS__</script>
<script>(function(){var tok=new URLSearchParams(location.search).get('tok'), man=document.getElementById('man'), tb=document.getElementById('tb');
var tun=new Guacamole.WebSocketTunnel('/uem-vnc-ws/'+tok), c=new Guacamole.Client(tun), disp=c.getDisplay(), el=disp.getElement();
man.appendChild(el);
function vua(){var dw=disp.getWidth(), dh=disp.getHeight(); if(!dw||!dh)return; disp.scale(Math.min(innerWidth/dw, innerHeight/dh, 1.5));}
disp.onresize=vua; var hen=null; window.addEventListener('resize',function(){clearTimeout(hen); hen=setTimeout(function(){c.sendSize(innerWidth,innerHeight); vua();},300);});
var TT={0:'',1:'Đang kết nối...',2:'Đang chờ máy trả lời...',3:'',4:'',5:'Đã ngắt kết nối. Nếu chưa vào được màn hình máy: kiểm tra tài khoản, mật khẩu và chế độ Bảo mật (máy Windows mới thường cần NLA kèm tài khoản).'}, daVao=false;
c.onstatechange=function(s){if(s===5&&daVao)TT[5]='Đã ngắt kết nối.'; if(s===3){daVao=true; tb.style.display='none'; document.getElementById('thanh').classList.add('mo'); setTimeout(function(){document.getElementById('thanh').classList.remove('mo');},2500);}
 else if(TT[s]){tb.style.display='flex'; if(s!==5||!tb.dataset.loi)tb.textContent=TT[s];}};
c.onerror=function(st){tb.style.display='flex'; tb.dataset.loi=1; tb.textContent='Lỗi: '+(st.message||'không rõ')+(st.code===519||st.code===769?' (kiểm tra máy đã bật Remote Desktop, tài khoản / mật khẩu)':'');};
tun.onerror=function(st){if(!tb.dataset.loi){tb.style.display='flex'; tb.textContent='Mất kết nối: '+(st.message||'');}};
c.connect('');
var m=new Guacamole.Mouse(el); m.onEach(['mousedown','mouseup','mousemove'],function(e){c.sendMouseState(e.state,true);});
var t=new Guacamole.Mouse.Touchscreen(el); t.onEach(['mousedown','mouseup','mousemove'],function(e){c.sendMouseState(e.state,true);});
var k=new Guacamole.Keyboard(document); k.onkeydown=function(s){c.sendKeyEvent(1,s);}; k.onkeyup=function(s){c.sendKeyEvent(0,s);};
function phim(ds){ds.forEach(function(s){c.sendKeyEvent(1,s);}); ds.slice().reverse().forEach(function(s){c.sendKeyEvent(0,s);});}
document.getElementById('b-cad').onclick=function(){phim([0xFFE3,0xFFE9,0xFFFF]);};
document.getElementById('b-win').onclick=function(){phim([0xFFEB]);};
document.getElementById('b-full').onclick=function(){if(document.fullscreenElement)document.exitFullscreen(); else document.documentElement.requestFullscreen();};
document.getElementById('b-dong').onclick=function(){c.disconnect();};
c.onclipboard=function(st,mt){if(mt!=='text/plain')return; var r=new Guacamole.StringReader(st), s=''; r.ontext=function(x){s+=x;}; r.onend=function(){try{navigator.clipboard.writeText(s);}catch(e){}};};
window.addEventListener('paste',function(e){var s=(e.clipboardData||{}).getData&&e.clipboardData.getData('text/plain'); if(!s)return; var st=c.createClipboardStream('text/plain'), w=new Guacamole.StringWriter(st); w.sendText(s); w.sendEnd();});
window.onbeforeunload=function(){try{c.disconnect();}catch(e){}};
})();</script></body></html>"""


def register_rdp(app):
    from ui import render_page

    @app.route("/remote-desktop")
    def rdp_trang():
        return render_page(CSS + TRANG, active="/remote-desktop", title="Remote Desktop",
                           subtitle="Điều khiển máy Windows qua RDP ngay trong trình duyệt (guacd)")

    @app.route("/remote-desktop/trang-thai")
    def rdp_trang_thai():
        return jsonify(trang_thai())

    @app.route("/remote-desktop/cai", methods=["POST"])
    def rdp_cai():
        return jsonify({"ok": cai_guacd()})

    @app.route("/remote-desktop/ket-noi", methods=["POST"])
    def rdp_ket_noi():
        j = request.get_json(silent=True) or {}
        try:
            tok, tb = mo_phien(str(j.get("host", "")).strip(), j.get("port"), str(j.get("user", "")), str(j.get("mk", "")),
                               str(j.get("domain", "")), str(j.get("security", "any")), j.get("w"), j.get("h"), j.get("dpi"))
        except (TypeError, ValueError):
            tok, tb = None, "Thông số không hợp lệ."
        return jsonify({"tok": tok, "tb": tb})

    @app.route("/remote-desktop/xem")
    def rdp_xem():
        ten = _esc((request.args.get("ten") or "Remote Desktop")[:80])
        html = XEM.replace("__TEN__", ten).replace("__JS__", _JS.replace("</script", "<\\/script"))
        return Response(html, mimetype="text/html")
