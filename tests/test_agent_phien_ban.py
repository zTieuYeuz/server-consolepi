"""Sua ma C# cua agent MA KHONG tang VER_FILE thi agent cu se KHONG tu cap nhat (may chu chi so sanh chuoi phien ban). Test nay ep tang so."""
import hashlib
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

# phien ban -> SHA-256 cua ma nguon C# o phien ban do. Sua ma C#: tang VER_FILE roi them dong moi o day.
BAM = {"2.3.2": "1714c215e279bab32fb88852c394c263584f511f483a9374efb7059da3998a65", "2.3.3": "8509efd62df3c3248414c803eda019661aa3a47784c614c7333919fd780bfa35"}


def test_ma_agent_doi_phai_tang_phien_ban():
    from consolesystem.features.uem import uem_agent_cs as C
    bam = hashlib.sha256(C.SOURCE.encode("utf-8")).hexdigest()
    assert C.VER_FILE in BAM, "VER_FILE %s chua co trong BAM: them dong phien ban moi" % C.VER_FILE
    assert BAM[C.VER_FILE] == bam, "Ma C# cua agent da doi nhung VER_FILE van la %s: hay tang VER_FILE (de agent cu tu cap nhat) va them bam %s" % (C.VER_FILE, bam)
