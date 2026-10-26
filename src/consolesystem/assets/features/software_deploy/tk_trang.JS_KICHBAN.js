
(function(){
  var D = JSON.parse(document.getElementById('kb-du-lieu').textContent), buoc = D.buoc.slice();
  var $ = function(i){ return document.getElementById(i); };
  var LOAI = [['phanmem','Phần mềm'],['ungdung','Ứng dụng nhiều file'],['script','Script'],['winget','WinGet (kho Microsoft)'],['rustdesk','RustDesk (kèm máy chủ ID / chuyển tiếp)'],
              ['nhom','Nhóm tài nguyên'],['nguon','Bật / tắt / khởi động lại máy'],['baomat','Kiểm tra bảo mật'],['kiemke','Kiểm kê phần cứng và phần mềm']];
  LOAI.forEach(function(l){ var o=document.createElement('option'); o.value=l[0]; o.textContent=l[1]; $('b-loai').appendChild(o); });
  var DS_HIEN = [];
  function bo_dau(x){ return (x||'').replace(/đ/g,'d').replace(/Đ/g,'D').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase(); }
  function ve_ref(){
    var r=$('b-ref'), q=bo_dau($('b-tim').value).split(/\s+/).filter(Boolean), l=$('b-loai').value, g=$('b-ghi'); r.textContent='';
    var kq = DS_HIEN.filter(function(x){ var h=bo_dau(x.ten+' '+(x.mo_ta||'')); return q.every(function(t){ return h.indexOf(t)>=0; }); });
    if (!kq.length){ var o=document.createElement('option'); o.value='';
      o.textContent = !DS_HIEN.length ? (l==='nhom' ? '(chưa có nhóm tài nguyên)' : '(chưa có tài nguyên loại này)') : '(không có kết quả khớp)'; r.appendChild(o); }
    kq.forEach(function(x){ var o=document.createElement('option'); o.value=x.ref; o.textContent=x.ten + (x.mo_ta ? '  -  ' + x.mo_ta : ''); o.setAttribute('data-ten', x.ten); r.appendChild(o); });
    if (q.length && kq.length) r.selectedIndex = 0;
    $('b-so').textContent = DS_HIEN.length ? kq.length + ' / ' + DS_HIEN.length : '';
  }
  function tuychon(){
    var l=$('b-loai').value, r=$('b-ref'), t=$('b-text'), g=$('b-ghi'); r.textContent=''; t.style.display='none'; r.style.display=''; g.textContent='';
    $('b-tim').value=''; $('b-tim').style.display=''; DS_HIEN=[];
    if (['winget','kiemke','baomat','rustdesk'].indexOf(l)>=0) $('b-tim').style.display='none';
    if (l==='winget'){ r.style.display='none'; t.style.display=''; g.textContent='Cài từ kho WinGet của Microsoft, luôn bản mới nhất. Máy đích cần có WinGet (Windows 11 và Windows 10 bản mới thường có sẵn).'; return; }
    if (l==='rustdesk'){ r.style.display='none'; g.textContent='Tải bộ cài RustDesk chính thức (kiểm SHA-256), cài im lặng, điền sẵn Máy chủ ID, Máy chủ chuyển tiếp và Key đang đặt ở trang RustDesk, đặt mật khẩu chung. ID của máy hiện ở trang RustDesk.'; return; }
    if (l==='kiemke'){ r.style.display='none'; g.textContent='Thu thập hãng, model, serial, CPU, RAM, ổ đĩa và danh sách phần mềm đã cài của từng máy (xem ở Máy - nhóm máy).'; return; }
    if (l==='baomat'){ r.style.display='none'; g.textContent='Thu thập diệt virus, tường lửa, BitLocker, bản cập nhật đang chờ của từng máy và lưu ở Máy - nhóm máy.'; return; }
    var ds = l==='nguon' ? Object.keys(D.nguon).map(function(k){return {ref:k,ten:D.nguon[k]};}) : (l==='nhom' ? D.nhom : D.tn[l] || []);
    DS_HIEN = ds; if (l==='nguon') $('b-tim').style.display='none'; ve_ref(); 
    if (l==='nguon') g.textContent = 'Bật máy dùng Wake-on-LAN (máy cần có địa chỉ MAC và bật Wake on LAN trong BIOS).';
  }
  function ten(b){
    if (b.loai==='nguon') return D.nguon[b.ref]||b.ref; if (b.loai==='baomat') return 'Kiểm tra bảo mật'; if (b.loai==='kiemke') return 'Kiểm kê phần cứng và phần mềm'; if (b.loai==='rustdesk') return 'Cài RustDesk (kèm máy chủ ID / chuyển tiếp)'; return b.ten||b.ref;
  }
  function ve(){
    var h=$('ds-buoc'); h.textContent='';
    if (!buoc.length){ var p=document.createElement('p'); p.className='tk-ghi'; p.textContent='Chưa có bước nào. Chọn loại bước bên dưới rồi bấm Thêm bước.'; h.appendChild(p); }
    buoc.forEach(function(b,i){
      var d=document.createElement('div'); d.className='tk-buoc';
      var s=document.createElement('span'); s.className='stt'; s.textContent=i+1; d.appendChild(s);
      var n=document.createElement('div'); n.className='nd'; n.appendChild(document.createTextNode(ten(b)));
      var sm=document.createElement('small'); sm.textContent=D.ten_loai[b.loai]||b.loai; n.appendChild(sm); d.appendChild(n);
      [['↑',-1],['↓',1]].forEach(function(x){ var bt=document.createElement('button'); bt.type='button'; bt.className='tk-nut'; bt.textContent=x[0];
        bt.onclick=function(){ var j=i+x[1]; if(j<0||j>=buoc.length) return; var t=buoc[i]; buoc[i]=buoc[j]; buoc[j]=t; ve(); }; d.appendChild(bt); });
      if (['phanmem','ungdung','winget','nhom','rustdesk'].indexOf(b.loai)>=0){
        var lb=document.createElement('label'); lb.style.cssText='display:flex;gap:6px;align-items:center;margin:0;font-weight:500;font-size:12.5px;cursor:pointer;';
        var cb=document.createElement('input'); cb.type='checkbox'; cb.checked=!!b.mot_lan; cb.onchange=function(){ b.mot_lan=cb.checked; ve(); };
        lb.appendChild(cb); lb.appendChild(document.createTextNode('Chỉ cài một lần trên mỗi máy')); d.appendChild(lb); }
      var xo=document.createElement('button'); xo.type='button'; xo.className='tk-nut do'; xo.textContent='Xóa'; xo.onclick=function(){ buoc.splice(i,1); ve(); }; d.appendChild(xo);
      h.appendChild(d);
    });
    $('buoc-json').value = JSON.stringify(buoc);
  }
  $('b-loai').onchange = tuychon; $('b-tim').addEventListener('input', ve_ref);
  $('b-tim').addEventListener('keydown', function(ev){ if(ev.key==='Enter'){ ev.preventDefault(); $('b-them').click(); } });
  $('b-them').onclick = function(){
    var l=$('b-loai').value, b={loai:l};
    if (l==='winget'){ var v=$('b-text').value.trim(); if(!/^[A-Za-z0-9._+-]{2,100}$/.test(v)){ alert('Mã WinGet không hợp lệ.'); return; } b.ref=v; b.ten='WinGet: '+v; }
    else if (l==='baomat' || l==='kiemke' || l==='rustdesk'){ b.ref=''; }
    else { var o=$('b-ref').selectedOptions[0]; if(!o||!o.value){ alert('Chưa có gì để chọn.'); return; } b.ref=o.value; b.ten=o.getAttribute('data-ten')||o.textContent; }
    if (['phanmem','ungdung','winget','nhom','rustdesk'].indexOf(l)>=0) b.mot_lan=true;
    buoc.push(b); ve();
  };
  $('f-kb').addEventListener('submit', function(e){ $('buoc-json').value=JSON.stringify(buoc); if(!buoc.length){ e.preventDefault(); alert('Thêm ít nhất một bước.'); } });
  tuychon(); ve();
})();
