"""Certificate issuance and printable PDF export for CodeBreak save slots."""
from datetime import datetime, timezone
import re
import secrets

CERTIFICATE_CATALOG = {
    "island": ("Certificate of Programming Foundations", "Foundation Explorer"),
    "castle": ("Certificate of Intermediate Programming", "Code Architect"),
    "citadel": ("Certificate of Advanced Programming", "Master Programmer"),
}
GRANDMASTER = ("CodeBreak Grandmaster", "Grandmaster Programmer")


def issue_stage_certificate(state, stage_id, issued_at=None):
    """Idempotently issue a certificate after the campaign marks a stage complete."""
    if stage_id not in CERTIFICATE_CATALOG:
        return None
    completed = set(state.get("completed_stages", ()))
    if stage_id not in completed:
        return None
    records = list(state.get("certificates", ()))
    existing = next((c for c in records if c.get("stage_id") == stage_id), None)
    if existing:
        return existing
    title, achievement = CERTIFICATE_CATALOG[stage_id]
    record = {
        "certificate_id": f"CB-{stage_id[:2].upper()}-{secrets.token_hex(3).upper()}",
        "stage_id": stage_id,
        "title": title,
        "achievement": achievement,
        "issuer": "CodeBreak",
        "issued_at": issued_at or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "verification_code": secrets.token_hex(8).upper(),
    }
    records.append(record)
    state["certificates"] = records
    if all(stage in completed for stage in CERTIFICATE_CATALOG):
        if not any(c.get("stage_id") == "grandmaster" for c in records):
            records.append({
                "certificate_id": f"CB-GM-{secrets.token_hex(3).upper()}",
                "stage_id": "grandmaster",
                "title": GRANDMASTER[0],
                "achievement": GRANDMASTER[1],
                "issuer": "CodeBreak",
                "issued_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "verification_code": secrets.token_hex(8).upper(),
            })
    return record


def _pdf_escape(value):
    return str(value).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def certificate_pdf_bytes(certificate, player_name):
    """Build a one-page PDF without an optional runtime dependency."""
    lines = [
        ("CODEBREAK", 30), ("CERTIFICATE OF ACHIEVEMENT", 20),
        (certificate.get("title", "CodeBreak Certificate"), 17),
        ("This certificate is proudly presented to", 12),
        (player_name or "CodeBreak Explorer", 24),
        (certificate.get("achievement", ""), 14),
        ("For completing the required campaign challenges and assessment.", 11),
        (f"Issued: {certificate.get('issued_at', '')}", 10),
        (f"Certificate ID: {certificate.get('certificate_id', '')}", 9),
        (f"Verification: {certificate.get('verification_code', '')}", 9),
        ("Issued by CodeBreak", 12),
    ]
    stream = ["q", "0.08 0.10 0.16 rg", "0 0 612 792 re f",
              "0.78 0.61 0.30 RG", "3 w", "34 34 544 724 re S",
              "0.88 0.78 0.55 RG", "1 w", "45 45 522 702 re S",
              "Q", "BT", "/F1 12 Tf", "0.92 0.86 0.70 rg"]
    y = 650
    for index, (line, size) in enumerate(lines):
        stream.extend([f"/F1 {size} Tf", f"1 0 0 1 306 {y} Tm",
                       f"({_pdf_escape(line)}) Tj"])
        y -= 48 if index in (0, 1, 4, 5) else 34
    stream.append("ET")
    content = "\n".join(stream).encode("latin-1", "replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for i, obj in enumerate(objects, 1):
        offsets.append(len(pdf))
        pdf.extend(f"{i} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = len(pdf)
    pdf.extend(f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode())
    return bytes(pdf)
