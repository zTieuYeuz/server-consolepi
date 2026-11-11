"""Sua ma C# cua agent MA KHONG tang VER_FILE thi agent cu se KHONG tu cap nhat (may chu chi so sanh chuoi phien ban). Test nay ep tang so."""
import hashlib
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

# phien ban -> SHA-256 cua ma nguon C# o phien ban do. Sua ma C#: tang VER_FILE roi them dong moi o day.
BAM = {"2.3.2": "1714c215e279bab32fb88852c394c263584f511f483a9374efb7059da3998a65", "2.3.3": "8509efd62df3c3248414c803eda019661aa3a47784c614c7333919fd780bfa35", "2.3.5": "fa770e85c65044a0e32e445631c8333cf5140d053cbe152f93b08686984c6d89", "2.3.6": "ffd338f1e44c52175e83a1c30b6e1afd5eed6b88a12a5fe353585e47b74a7db4", "2.3.7": "e7adb31178999e0ffa0589fdaeb39bd237dfbcd9bd08af48d07a94c08cf13ecc", "2.3.8": "80a158da9d497768086bc0020f21fbd8f25c4a3daba99e8391079b9c4a72de23", "2.3.9": "5d63a3657bd6ae4bc1b21d0f6b0c19acf7973a79b795c333c141f8d343ad7dff"}


def test_ma_agent_doi_phai_tang_phien_ban():
    from consolesystem.features.uem import uem_agent_cs as C
    bam = hashlib.sha256(C.SOURCE.encode("utf-8")).hexdigest()
    assert C.VER_FILE in BAM, "VER_FILE %s chua co trong BAM: them dong phien ban moi" % C.VER_FILE
    assert BAM[C.VER_FILE] == bam, "Ma C# cua agent da doi nhung VER_FILE van la %s: hay tang VER_FILE (de agent cu tu cap nhat) va them bam %s" % (C.VER_FILE, bam)
