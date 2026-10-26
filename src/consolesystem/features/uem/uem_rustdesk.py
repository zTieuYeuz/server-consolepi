# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""RustDesk phia quan ly may tram: cai client RustDesk len may qua agent/WinRM va liet ke may/ID/mat khau. Logic may chu: integrations/rustdesk_may_chu.py."""
import re
import secrets
import time

from flask import jsonify, request

from consolesystem.features.uem import uem_dieukhien as DK
from consolesystem.integrations import rustdesk_may_chu as RD
from ui import tk_dulieu as DL
from ui import uem_agent as UA


def cai_client_may(m):
    """Cai qua agent/WinRM. Tra (ok, thong_diep, id)."""
    cfg = RD.doc_cfg()
    ban = cfg["may"].get(m["id"]) or {}
    mk = ban.get("mk") or secrets.token_hex(6)
    try:
        sc = RD.script_client(mk)
    except RuntimeError as e:
        return False, str(e), ""
    ok, out = DK._chay(m, sc)
    ma = re.search(r"RUSTDESK_ID=(\d{6,12})", out or "")
    if not ok or not ma:
        return False, (out or "Không lấy được ID RustDesk.")[-400:], ""
    cfg = RD.doc_cfg()
    cfg["may"][m["id"]] = {"id": ma.group(1), "mk": mk, "luc": int(time.time())}
    RD.luu_cfg(cfg)
    return True, "Đã cài RustDesk, ID %s." % ma.group(1), ma.group(1)



def register_uem_rustdesk(app):
    @app.route("/rustdesk/api/thiet-bi")
    def rustdesk_api_dev():
        cfg = RD.doc_cfg()
        ds_may = DL.MAY.doc()
        ten = {m["id"]: (m.get("ten") or m["ip"]) for m in ds_may}
        agent = [{"id": m["id"], "ten": m.get("ten") or m["ip"], "ip": m["ip"], "online": UA.con_song(m)} for m in ds_may if UA.co_agent(m) and not m.get("an")]
        may = [{"ten": ten.get(k, k), "id": v.get("id", ""), "mk": v.get("mk", "")} for k, v in cfg["may"].items()]
        return jsonify({"ds": RD.thiet_bi(), "may": may, "agent": agent})

    @app.route("/rustdesk/api/cai-client", methods=["POST"])
    def rustdesk_api_cai_client():
        ids = (request.get_json(silent=True) or {}).get("may") or []
        kq = []
        for m in DL.MAY.doc():
            if m["id"] in ids:
                ok, tb, _id = cai_client_may(m)
                kq.append({"ten": m.get("ten") or m["ip"], "ok": ok, "tb": tb})
        return jsonify({"ok": True, "kq": kq})
