# Console System - (c) 2026 zTieuYeuz. All rights reserved.
# Thu chuot trong terminal cua Phien ket noi tren Pi that (qua duong ham 18880): cuon, boi den, chep, chuot phai.
# Dung: python3 thu-chuot-terminal.py [cong_debug]  (can /root/dev-giaodien/cdp.py)
import sys, time, json; sys.path.insert(0, "/root/dev-giaodien")
from cdp import Trinh
B = "http://127.0.0.1:18880"
cong = int(sys.argv[1]) if len(sys.argv) > 1 else 9441
t = Trinh(cong=cong, rong=1280, cao=900)
def fr(js):   # chay JS trong iframe terminal
    return t.js("(function(){var f=document.querySelector('#than iframe.on');var w=f&&f.contentWindow;if(!w||!w.term)return 'CHUA CO term';return (function(){%s}).call(w);})()" % js)
try:
    t.gui("Browser.grantPermissions", permissions=["clipboardReadWrite","clipboardSanitizedWrite"], origin="http://127.0.0.1:18880"); t.cookie("cs_che_do", "pc", B); t.cookie("cs_nen", "toi", B)
    t.mo(B + "/healthz", cho=.2); t.js("localStorage.clear();localStorage.setItem('cpvk_enabled','0')")
    t.mo(B + "/phien", cho=2.5)
    t.bam('.ph-muc[data-ma="local"]'); time.sleep(4)
    print("term:", fr("return 'ok '+this.term.cols+'x'+this.term.rows"))
    # tao 150 dong de co lich su
    t.js("document.querySelector('#than iframe.on').focus()")
    for ch in "clear; seq 1 150; echo XONG-DONG-CUOI":
        t.phim(ch, text=ch)
    t.phim("Enter", code="Enter", text="\r"); time.sleep(2)
    print("buf:", fr("var b=this.term.buffer.active;return JSON.stringify({baseY:b.baseY,viewportY:b.viewportY,len:b.length,type:b.type})"))
    # keo chuot chon (khong Shift)
    r2 = t.js("(function(){var f=document.querySelector('#than iframe.on').getBoundingClientRect();return [f.left,f.top,f.width,f.height]})()"); x0, y0 = r2[0] + 12, r2[1] + r2[3] * 0.40
    t.gui("Input.dispatchMouseEvent", type="mousePressed", x=x0, y=y0, button="left", clickCount=1); 
    for k in range(1, 9):
        t.gui("Input.dispatchMouseEvent", type="mouseMoved", x=x0 + k * 12, y=y0, button="left", buttons=1); time.sleep(.03)
    t.gui("Input.dispatchMouseEvent", type="mouseReleased", x=x0 + 100, y=y0, button="left", clickCount=1); time.sleep(.6)
    print("boi den:", repr(fr("return this.term.getSelection()"))[:100])
    time.sleep(.5)
    print("clipboard:", repr(t.js("(async function(){try{var f=document.querySelector('#than iframe.on');f.contentWindow.focus();return await f.contentWindow.navigator.clipboard.readText()}catch(e){return 'LOI '+e}})()") )[:100])
    t.chup("/root/claude-demo/s/thu-term-1.png")
    # cuon len bang banh xe
    r = t.js("(function(){var f=document.querySelector('#than iframe.on').getBoundingClientRect();return [f.left+f.width/2,f.top+f.height/2]})()")
    for _ in range(6):
        t.gui("Input.dispatchMouseEvent", type="mouseWheel", x=r[0], y=r[1], deltaX=0, deltaY=-300); time.sleep(.15)
    time.sleep(.5)
    print("sau cuon len:", fr("var b=this.term.buffer.active;return JSON.stringify({baseY:b.baseY,viewportY:b.viewportY,type:b.type})"))
    # chuot phai
    t.gui("Input.dispatchMouseEvent", type="mousePressed", x=r[0], y=r[1], button="right", clickCount=1)
    t.gui("Input.dispatchMouseEvent", type="mouseReleased", x=r[0], y=r[1], button="right", clickCount=1); time.sleep(.8)
    print("noi dung sau chuot phai (co menu tmux?):", repr(fr("var b=this.term.buffer.active,s='';for(var i=0;i<this.term.rows;i++){s+=b.getLine(b.viewportY+i).translateToString(true)+'|'}return s"))[:400])
    t.chup("/root/claude-demo/s/thu-term-2.png")
    print(t.loi[:2])
finally:
    t.dong()
