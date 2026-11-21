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
    """Build a decorative landscape parchment-style certificate PDF."""
    width, height = 792, 612
    def centered(text, y, font, size, color):
        text = str(text)
        x = max(58, (width - len(text) * size * 0.48) / 2)
        return f"{color} rg BT /{font} {size} Tf 1 0 0 1 {x:.1f} {y} Tm ({_pdf_escape(text)}) Tj ET"
    lines = [
        centered('CODEBREAK', 510, 'F2', 27, '0.35 0.22 0.10'),
        centered('CERTIFICATE OF ACHIEVEMENT', 470, 'F2', 17, '0.48 0.32 0.14'),
        centered('This certificate is proudly presented to', 410, 'F3', 13, '0.35 0.30 0.23'),
        centered(player_name or 'CodeBreak Explorer', 365, 'F2', 29, '0.22 0.18 0.13'),
        centered(certificate.get('title', 'CodeBreak Certificate'), 318, 'F2', 19, '0.43 0.28 0.13'),
        centered(certificate.get('achievement', ''), 278, 'F3', 17, '0.35 0.25 0.14'),
        centered('For completing all required stage lessons, challenges, and the final assessment.', 232, 'F1', 11, '0.30 0.27 0.21'),
        centered(f"Issued: {str(certificate.get('issued_at', ''))[:10]}   Certificate ID: {certificate.get('certificate_id', '')}", 104, 'F1', 9, '0.35 0.30 0.23'),
        centered(f"Verification code: {certificate.get('verification_code', '')}", 84, 'F1', 9, '0.35 0.30 0.23'),
        centered('OFFICIALLY AWARDED BY CODEBREAK', 62, 'F2', 10, '0.43 0.28 0.13'),
    ]
    stream = [
        'q', '0.96 0.92 0.80 rg 0 0 792 612 re f',
        '0.91 0.84 0.66 rg 12 12 768 588 re f',
        '0.97 0.94 0.85 rg 20 20 752 572 re f',
        '0.43 0.28 0.13 RG 4 w 30 30 732 552 re S',
        '0.69 0.51 0.25 RG 1.5 w 42 42 708 528 re S',
        '0.43 0.28 0.13 RG 1 w 54 54 684 504 re S',
        '0.58 0.39 0.17 RG 2 w 70 70 m 70 112 l 112 112 l S 722 70 m 722 112 l 680 112 l S',
        '70 542 m 70 500 l 112 500 l S 722 542 m 722 500 l 680 500 l S',
        '0.69 0.51 0.25 RG 1 w 180 468 m 612 468 l S 180 138 m 612 138 l S',
        'Q', *lines,
        'q 0.75 0.56 0.22 rg 396 172 0 0 m 396 172 25 0 0 25 c 0 25 -25 25 -25 0 c f Q',
    ]
    content = '\n'.join(stream).encode('latin-1', 'replace')
    objects = [
        b'<< /Type /Catalog /Pages 2 0 R >>',
        b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
        b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 792 612] /Resources << /Font << /F1 4 0 R /F2 5 0 R /F3 6 0 R >> >> /Contents 7 0 R >>',
        b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
        b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>',
        b'<< /Type /Font /Subtype /Type1 /BaseFont /Times-Italic >>',
        b'<< /Length ' + str(len(content)).encode() + b' >>\nstream\n' + content + b'\nendstream',
    ]
    pdf = bytearray(b'%PDF-1.4\n')
    offsets = [0]
    for i, obj in enumerate(objects, 1):
        offsets.append(len(pdf))
        pdf.extend(f'{i} 0 obj\n'.encode() + obj + b'\nendobj\n')
    xref = len(pdf)
    pdf.extend(f'xref\n0 {len(objects)+1}\n0000000000 65535 f \n'.encode())
    for offset in offsets[1:]:
        pdf.extend(f'{offset:010d} 00000 n \n'.encode())
    pdf.extend(f'trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF'.encode())
    return bytes(pdf)
