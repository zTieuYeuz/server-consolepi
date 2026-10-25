# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""CSS dung chung cua cac trang Trien khai phan mem va Quan ly may tram (tach tu tk_trang.py o B3 de uem khong phai import software_deploy)."""

CSS = """
<style>
.tk-hang { display:flex; gap:10px; flex-wrap:wrap; align-items:center; }
.tk-luoi { display:grid; grid-template-columns:repeat(auto-fill,minmax(250px,1fr)); gap:10px; margin:8px 0 14px; }
.tk-o { border:1px solid var(--vien-ro,#2a323e); border-radius:10px; padding:10px 12px; display:flex; gap:10px; align-items:flex-start; cursor:pointer; }
.tk-o:hover { background:var(--hang-nen,rgba(255,255,255,.03)); }
.tk-o:has(input:checked) { border-color:var(--nhan,#6c9cff); background:var(--nhan-mo,rgba(108,156,255,.14)); }
.tk-o input { margin-top:3px; }
.tk-o b { display:block; font-size:14px; } .tk-o small { color:var(--chu-mo2,#7a8496); display:block; }
.tk-chip { display:inline-block; padding:2px 10px; border-radius:99px; font-size:12px; font-weight:600; background:var(--hang-nen); color:var(--chu-mo); }
.tk-chip.xanh { background:var(--xanh-mo); color:var(--xanh); } .tk-chip.do { background:var(--do-mo); color:var(--do); }
.tk-dem { margin-top:5px; display:flex; flex-wrap:wrap; gap:4px; }
.tk-chip.vang { background:var(--vang-mo); color:var(--vang); } .tk-chip.nhan { background:var(--nhan-mo); color:var(--nhan); }
.tk-bang { width:100%; border-collapse:collapse; }
.tk-bang th { text-align:left; font-size:12px; text-transform:uppercase; letter-spacing:.04em; color:var(--chu-mo2); padding:8px 10px; border-bottom:1px solid var(--vien); }
.tk-bang td { padding:10px; border-bottom:1px solid var(--vien); vertical-align:middle; font-size:14px; }
.tk-bang input[type=text], .tk-bang select { margin:0; height:36px; max-width:100%; }
.tk-vach { height:8px; border-radius:5px; background:var(--vien-ro); overflow:hidden; min-width:90px; }
.tk-vach > i { display:block; height:100%; background:var(--xanh); border-radius:5px; transition:width .6s var(--muot); }
.tk-nut { height:38px; min-height:38px; padding:0 14px; border-radius:8px; border:1px solid var(--vien-ro); background:transparent; color:var(--chu);
          font:550 13.5px var(--chu-font); cursor:pointer; display:inline-flex; align-items:center; gap:6px; text-decoration:none; }
.tk-nut:hover { background:var(--hang-nen); }
.tk-nut.chinh { background:var(--nhan); border-color:var(--nhan); color:var(--chu-tren-nhan); }
.tk-nut.xanh { background:var(--xanh); border-color:var(--xanh); color:#fff; }
.tk-nut.xanh:hover { filter:brightness(1.1); background:var(--xanh); }
.tk-act { display:flex; gap:6px; flex-wrap:wrap; align-items:center; }
.tk-act form { display:inline-flex; margin:0; }
body.cd-cu .tk-nut { min-height:44px; height:44px; }
@media (max-width:980px) { .an-hep { display:none; } }
.tk-nut.do { color:var(--do); border-color:var(--do-mo); } .tk-nut.do:hover { background:var(--do-mo); }
.tk-nut svg { width:16px; height:16px; stroke:currentColor; fill:none; stroke-width:1.8; stroke-linecap:round; stroke-linejoin:round; }
.tk-tieude { margin:22px 0 8px; }
.tk-ghi { color:var(--chu-mo2); font-size:13px; line-height:1.55; margin:6px 0; }
.tk-ghi code, .tk-canhbao code { background:var(--code-nen); color:var(--code-chu); border-radius:4px; padding:1px 5px; }
.tk-canhbao { border:1px solid var(--vang); background:var(--vang-mo); color:var(--chu); border-radius:12px; padding:14px 16px; font-size:13.5px; line-height:1.6; margin-bottom:16px; }
.tk-f label { display:block; font-size:13px; font-weight:600; color:var(--chu-mo); margin:14px 0 6px; }
.tk-f input[type=text], .tk-f input[type=password], .tk-f input[type=time], .tk-f input[type=date], .tk-f input[type=number], .tk-f select { margin:0; height:42px; }
.tk-thu { display:flex; gap:6px; flex-wrap:wrap; }
.tk-thu label { margin:0; display:inline-flex; gap:6px; align-items:center; border:1px solid var(--vien-ro); border-radius:99px; padding:6px 12px; cursor:pointer; font-weight:500; }
.tk-thu label:has(input:checked) { background:var(--nhan-mo); border-color:var(--nhan); color:var(--nhan); }
.tk-buoc { display:flex; gap:8px; align-items:center; padding:8px 10px; border:1px solid var(--vien-ro); border-radius:10px; margin-bottom:6px; }
.tk-buoc .stt { width:24px; height:24px; border-radius:50%; background:var(--nhan-mo); color:var(--nhan); display:flex; align-items:center; justify-content:center; font-size:12px; font-weight:700; flex:none; }
.tk-buoc .nd { flex:1; min-width:0; } .tk-buoc .nd small { display:block; color:var(--chu-mo2); }
.tk-modal { position:fixed; inset:0; background:rgba(0,0,0,.6); z-index:2147482000; display:flex; align-items:center; justify-content:center; padding:16px; }
.tk-modal[hidden] { display:none; }
.tk-mbox { background:var(--the); border:1px solid var(--vien-ro); border-radius:16px; width:min(980px,100%); max-height:92vh; display:flex; flex-direction:column; box-shadow:0 20px 60px rgba(0,0,0,.5); }
.tk-mdau { display:flex; align-items:center; gap:12px; padding:16px 20px; border-bottom:1px solid var(--vien); }
.tk-mdau h3 { margin:0; flex:1; font-size:18px; }
.tk-mthan { padding:16px 20px 20px; overflow:auto; }
.tk-may { border:1px solid var(--vien); border-radius:10px; margin-bottom:8px; overflow:hidden; }
.tk-may > summary { cursor:pointer; padding:10px 14px; display:flex; gap:10px; align-items:center; list-style:none; }
.tk-may > summary::-webkit-details-marker { display:none; }
.tk-may[open] > summary { background:var(--hang-nen); }
.tk-b { padding:6px 14px 6px 40px; font-size:13px; border-top:1px solid var(--vien); display:grid; grid-template-columns:22px 1fr; gap:8px; }
.tk-b .dau { font-weight:700; } .tk-b.ok .dau { color:var(--xanh); } .tk-b.loi .dau { color:var(--do); } .tk-b.dang .dau { color:var(--nhan); }
.tk-b small { color:var(--chu-mo2); display:block; overflow-wrap:anywhere; }
.tk-nk { background:var(--pre-nen); color:var(--pre-chu); border:1px solid var(--vien); border-radius:10px; padding:10px 12px; font:12.5px/1.6 var(--mono); max-height:200px; overflow:auto; white-space:pre-wrap; }
@media (max-width:760px) { .tk-bang { display:block; overflow-x:auto; } }
</style>
"""
