# Console System - (c) 2026 zTieuYeuz. All rights reserved.
# Thu tren Pi that: bam 1 lan vao terminal cua Phien ket noi roi go duoc ngay (can /root/dev-giaodien/cdp.py). Dung: python3 thu-focus-terminal.py <cong_debug>
import sys, time; sys.path.insert(0, "/root/dev-giaodien")
from cdp import Trinh
B="http://127.0.0.1:18880"
t=Trinh(cong=int(sys.argv[1]),rong=1280,cao=900)
def fr(js): return t.js("(function(){var f=document.querySelector('#than iframe.on');var w=f&&f.contentWindow;if(!w||!w.term)return 'CHUA CO term';return (function(){%s}).call(w);})()" % js)
MAN="var b=this.term.buffer.active,s='';for(var i=0;i<this.term.rows;i++){s+=b.getLine(b.viewportY+i).translateToString(true)+'|'}return s"
try:
    t.cookie("cs_che_do","pc",B); t.mo(B+"/healthz",cho=.2); t.js("localStorage.clear();localStorage.setItem('cpvk_enabled','0')")
    t.mo(B+"/phien",cho=2.5); t.bam('.ph-muc[data-ma="local"]'); time.sleep(4)
    # bo tieu diem hoan toan: bam vao khoang trong cua trang cha (nhu nguoi dung vua bam ra ngoai)
    t.bam('.ph-tabs'); time.sleep(.5)
    print("truoc khi bam terminal: tieu diem iframe =", t.js("document.activeElement.tagName"), "| trong iframe:", fr("return this.document.activeElement.tagName"))
    r=t.js("(function(){var f=document.querySelector('#than iframe.on').getBoundingClientRect();return [f.left,f.top,f.width,f.height]})()")
    x,y=r[0]+r[2]/2, r[1]+r[3]/2
    t.gui("Input.dispatchMouseEvent",type="mousePressed",x=x,y=y,button="left",clickCount=1)
    t.gui("Input.dispatchMouseEvent",type="mouseReleased",x=x,y=y,button="left",clickCount=1); time.sleep(.6)
    print("sau khi bam vao terminal: iframe duoc focus =", t.js("document.activeElement.tagName=='IFRAME'"), "| trong iframe:", fr("var a=this.document.activeElement;return a.tagName+'.'+a.className"))
    for ch in "echo GOSAUCLICK": t.phim(ch,text=ch)
    t.phim("Enter",code="Enter",text="\r"); time.sleep(1.2)
    print("go duoc sau 1 click:", "GOSAUCLICK" in fr(MAN))
finally: t.dong()
