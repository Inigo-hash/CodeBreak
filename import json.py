import json
from PIL import Image, ImageDraw, ImageFont

FP = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
INK, DARK, ACC, LIGHT, MID = "#1F2933", "#2F3B4A", "#6B7F95", "#E6EAEE", "#ABB8C3"
GRN, RED, AMB, WHITE, PALE = "#2E7D4F", "#B3413F", "#B7791F", "#FFFFFF", "#F3F5F7"
S = 2
_fc = {}


def font(sz, b=False):
    k = (sz, b)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FB if b else FP, int(sz))
    return _fc[k]


class C:
    def __init__(s, w, h, bg=WHITE):
        s.w, s.h = w, h
        s.im = Image.new("RGB", (w * S, h * S), bg)
        s.d = ImageDraw.Draw(s.im)

    def r(s, x, y, w, h, fill=None, out=None, rad=0, wd=1):
        s.d.rounded_rectangle([x * S, y * S, (x + w) * S, (y + h) * S], radius=rad * S, fill=fill, outline=out, width=wd * S)

    def t(s, x, y, txt, sz=16, b=False, fill=INK, anchor="la"):
        s.d.text((x * S, y * S), txt, font=font(sz * S, b), fill=fill, anchor=anchor)

    def tw(s, txt, sz=16, b=False):
        return s.d.textlength(txt, font=font(sz * S, b)) / S

    def line(s, x1, y1, x2, y2, fill=MID, wd=1):
        s.d.line([x1 * S, y1 * S, x2 * S, y2 * S], fill=fill, width=wd * S)

    def arrow(s, x1, y1, x2, y2, fill=DARK, wd=2):
        s.line(x1, y1, x2, y2, fill, wd)
        import math
        a = math.atan2(y2 - y1, x2 - x1)
        L = 10
        p1 = (x2 - L * math.cos(a - 0.4), y2 - L * math.sin(a - 0.4))
        p2 = (x2 - L * math.cos(a + 0.4), y2 - L * math.sin(a + 0.4))
        s.d.polygon([(x2 * S, y2 * S), (p1[0] * S, p1[1] * S), (p2[0] * S, p2[1] * S)], fill=fill)

    def badge(s, x, y, txt, col, sz=14):
        w = s.tw(txt, sz, True) + 14
        s.r(x, y, w, 22, fill=col, rad=4)
        s.t(x + 7, y + 11, txt, sz, True, WHITE, "lm")
        return w

    def button(s, x, y, w, h, txt, primary=True, sz=16):
        if primary:
            s.r(x, y, w, h, fill=DARK, rad=5)
            s.t(x + w / 2, y + h / 2, txt, sz, True, WHITE, "mm")
        else:
            s.r(x, y, w, h, fill=WHITE, out=ACC, rad=5, wd=2)
            s.t(x + w / 2, y + h / 2, txt, sz, True, DARK, "mm")

    def inp(s, x, y, w, h, txt, sz=15):
        s.r(x, y, w, h, fill=WHITE, out=MID, rad=4, wd=1)
        s.t(x + 8, y + h / 2, txt, sz, False, "#7B8794", "lm")

    def save(s, name):
        s.im.save(f"img/{name}.png")
        return (name, s.w, s.h)


def tbl(c, x, y, heads, rows, widths, rh=30, sz=15):
    tot = sum(widths)
    c.r(x, y, tot, rh, fill=ACC)
    cx = x
    for h, w in zip(heads, widths):
        c.t(cx + 8, y + rh / 2, h, sz, True, WHITE, "lm")
        cx += w
    for i, row in enumerate(rows):
        yy = y + rh * (i + 1)
        c.r(x, yy, tot, rh, fill=(WHITE if i % 2 == 0 else PALE))
        c.line(x, yy + rh, x + tot, yy + rh, MID)
        cx = x
        for cell, w in zip(row, widths):
            if isinstance(cell, tuple):
                c.badge(cx + 6, yy + rh / 2 - 11, cell[0], cell[1])
            else:
                c.t(cx + 8, yy + rh / 2, str(cell), sz, False, INK, "lm")
            cx += w
    c.r(x, y, tot, rh * (len(rows) + 1), out=MID)


W, H = 900, 620
NAV = ["Dashboard", "Endpoints", "Activity Logs", "Detections", "Integrity Check", "Reports", "Settings"]
OK, FAIL = ("VERIFIED", GRN), ("FAILED", RED)


def shell(active, title, who="Lab Administrator"):
    c = C(W, H)
    c.r(0, 0, W, H, fill=WHITE, out=DARK, wd=2)
    c.r(0, 0, W, 42, fill=DARK)
    c.t(16, 21, "LogAegis", 21, True, WHITE, "lm")
    c.t(W - 16, 21, who + "  v", 16, False, WHITE, "rm")
    c.r(0, 42, 170, H - 42, fill=LIGHT)
    for i, n in enumerate(NAV):
        y = 62 + i * 42
        if n == active:
            c.r(8, y, 154, 34, fill=ACC, rad=5)
            c.t(20, y + 17, n, 16, True, WHITE, "lm")
        else:
            c.t(20, y + 17, n, 16, False, INK, "lm")
    c.t(190, 70, title, 23, True, DARK, "lm")
    return c


figs = []

# ---- Fig: architecture ----
c = C(900, 430)
c.r(10, 10, 250, 410, fill=PALE, out=ACC, rad=8, wd=2)
c.t(135, 30, "Laboratory Endpoint", 18, True, DARK, "mm")
c.t(135, 50, "(Windows 10/11)", 15, False, INK, "mm")
for i, tx in enumerate(["Event Collector", "Download-Folder Watcher", "Static Analyzer (rules)", "Record Builder + Queue"]):
    y = 76 + i * 86
    c.r(30, y, 210, 62, fill=WHITE, out=ACC, rad=6, wd=2)
    c.t(135, y + 31, tx, 16, True, INK, "mm")
    if i < 3:
        c.arrow(135, y + 62, 135, y + 86, DARK)
c.r(325, 10, 300, 410, fill=PALE, out=ACC, rad=8, wd=2)
c.t(475, 30, "Central Server", 18, True, DARK, "mm")
c.t(475, 50, "(web application host)", 15, False, INK, "mm")
for i, tx in enumerate(["Ingestion API", "Integrity Module", "Database (activity records)"]):
    y = 76 + i * 86
    c.r(345, y, 260, 62, fill=WHITE, out=ACC, rad=6, wd=2)
    c.t(475, y + 31, tx, 16, True, INK, "mm")
    if i < 2:
        c.arrow(475, y + 62, 475, y + 86, DARK)
c.r(345, 334, 260, 62, fill="#FFFFFF", out=RED, rad=6, wd=2)
c.t(475, 358, "Secret Key Store", 16, True, INK, "mm")
c.t(475, 380, "(kept apart from database)", 14, False, INK, "mm")
c.arrow(475, 248, 475, 334, RED, 2)
c.arrow(240, 330, 345, 107, DARK)
c.t(262, 214, "HTTPS", 14, True, DARK, "lm")
c.t(262, 232, "records", 14, False, DARK, "lm")
c.r(690, 10, 200, 410, fill=PALE, out=ACC, rad=8, wd=2)
c.t(790, 30, "Administrator", 18, True, DARK, "mm")
c.t(790, 50, "(web browser)", 15, False, INK, "mm")
c.r(710, 120, 160, 62, fill=WHITE, out=ACC, rad=6, wd=2)
c.t(790, 151, "Web Dashboard", 16, True, INK, "mm")
c.r(710, 220, 160, 62, fill=WHITE, out=ACC, rad=6, wd=2)
c.t(790, 251, "Reports / Alerts", 16, True, INK, "mm")
c.arrow(605, 335 - 150, 710, 151, DARK)
c.arrow(790, 182, 790, 220, DARK)
figs.append(c.save("arch"))

# ---- Fig: hash chain ----
c = C(900, 360)
xs = [20, 240, 460, 680]
seqs = [840, 841, 842, 843]
for i, (x, q) in enumerate(zip(xs, seqs)):
    c.r(x, 20, 200, 190, fill=WHITE, out=DARK, rad=8, wd=2)
    c.r(x, 20, 200, 36, fill=DARK, rad=8)
    c.t(x + 100, 38, f"Record {q}", 17, True, WHITE, "mm")
    c.t(x + 12, 76, f"seq = {q}", 16)
    c.t(x + 12, 106, "fields F (event data)", 16)
    c.t(x + 12, 136, f"prev = H{q-1}", 16)
    c.r(x + 8, 156, 184, 38, fill=LIGHT, rad=5)
    c.t(x + 100, 175, f"seal  H{q}", 16, True, DARK, "mm")
    if i < 3:
        c.arrow(x + 200, 175, xs[i + 1], 175, ACC, 3)
        c.t(x + 210, 150, "feeds", 13, False, ACC, "lm")
c.r(20, 232, 860, 112, fill=PALE, out=MID, rad=6)
c.t(36, 254, "Seal rule:   H(i) = HMAC-SHA256( K , canonical(F(i)) || i || H(i-1) )", 17, True, DARK)
c.t(36, 284, "Verification recomputes each seal with the secret key K and checks that:", 15)
c.t(36, 306, "(1) the stored seal matches   (2) prev equals the preceding seal   (3) seq has no gap", 15)
c.t(36, 326, "(4) the newest seq and seal agree with the server checkpoint", 15)
figs.append(c.save("chain"))

# ---- Fig 3.3 login ----
c = C(900, 500, LIGHT)
c.r(270, 50, 360, 400, fill=WHITE, out=MID, rad=10, wd=2)
c.t(450, 100, "LogAegis", 32, True, DARK, "mm")
c.t(450, 134, "Tamper-Evident Endpoint Activity Monitoring", 14, False, INK, "mm")
c.t(300, 178, "Username", 16, True)
c.inp(300, 200, 300, 38, "e.g., lab.admin")
c.t(300, 258, "Password", 16, True)
c.inp(300, 280, 300, 38, "••••••••")
c.button(300, 340, 300, 42, "Sign In")
c.t(450, 412, "Authorized laboratory personnel only", 14, False, "#52606D", "mm")
figs.append(c.save("p_login"))

# ---- Fig 3.4 dashboard ----
c = shell("Dashboard", "Dashboard Overview")
stats = [("Endpoints Online", "28 / 30"), ("Detections Today", "5"), ("Integrity Failures", "1"), ("Records Verified", "12,480")]
for i, (a, b) in enumerate(stats):
    x = 190 + i * 172
    c.r(x, 100, 160, 74, fill=WHITE, out=MID, rad=6)
    c.t(x + 12, 120, a, 14, False, "#52606D", "lm")
    c.t(x + 12, 150, b, 26, True, RED if a == "Integrity Failures" else DARK, "lm")
c.r(190, 188, 352, 188, fill=WHITE, out=MID, rad=6)
c.t(204, 206, "Detections per Day (last 7 days)", 15, True, DARK, "lm")
vals = [2, 4, 1, 5, 3, 0, 5]
days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
c.line(210, 350, 526, 350, INK)
for i, (v, dn) in enumerate(zip(vals, days)):
    x = 220 + i * 43
    hgt = v * 24
    if hgt:
        c.r(x, 350 - hgt, 28, hgt, fill=ACC)
    c.t(x + 14, 362, dn, 13, False, INK, "mm")
c.r(554, 188, 312, 188, fill=WHITE, out=MID, rad=6)
c.t(568, 206, "Integrity Status (all endpoints)", 15, True, DARK, "lm")
c.r(568, 232, 284, 26, fill=RED, rad=4)
c.r(568, 232, 274, 26, fill=GRN, rad=4)
c.badge(568, 276, "VERIFIED", GRN)
c.t(660, 287, "29 endpoints", 15, False, INK, "lm")
c.badge(568, 308, "FAILED", RED)
c.t(660, 319, "1 endpoint", 15, False, INK, "lm")
c.t(568, 352, "Last full verification: 10:30", 14, False, "#52606D", "lm")
c.t(190, 396, "Recent Alerts", 17, True, DARK, "lm")
tbl(c, 190, 410, ["Time", "Endpoint", "File", "Verdict", "Integrity"],
    [["10:42", "LAB1-PC07", "setup_tool.exe", ("HIGH RISK", RED), OK],
     ["10:15", "LAB2-PC03", "mod_helper.exe", ("SUSPICIOUS", AMB), OK],
     ["09:58", "LAB1-PC11", "installer_x.exe", ("SUSPICIOUS", AMB), FAIL],
     ["09:20", "LAB3-PC01", "patch_run.exe", ("SUSPICIOUS", AMB), OK]],
    [90, 120, 170, 150, 146], rh=34)
figs.append(c.save("p_dash"))

# ---- Fig 3.5 endpoints ----
c = shell("Endpoints", "Endpoint Management", "IT Personnel")
c.inp(190, 100, 230, 36, "Search endpoint...")
c.inp(432, 100, 150, 36, "All labs  v")
c.button(716, 100, 150, 36, "+ Register", True)
G, R2 = ("ONLINE", GRN), ("OFFLINE", "#7B8794")
tbl(c, 190, 152, ["Endpoint ID", "Lab Room", "Agent", "Last Heartbeat", "Chain"],
    [["LAB1-PC01", "Lab 1", G, "10:44:12", OK],
     ["LAB1-PC07", "Lab 1", G, "10:44:09", OK],
     ["LAB1-PC11", "Lab 1", G, "10:44:15", FAIL],
     ["LAB2-PC03", "Lab 2", G, "10:44:02", OK],
     ["LAB2-PC08", "Lab 2", R2, "08:12:47", OK],
     ["LAB3-PC01", "Lab 3", G, "10:43:58", OK],
     ["LAB3-PC05", "Lab 3", G, "10:44:20", OK]],
    [160, 120, 130, 150, 116], rh=40)
c.t(190, 480, "Select a row to view endpoint details, deactivate the agent, or open its activity log.", 15, False, "#52606D")
figs.append(c.save("p_endpoints"))

# ---- Fig 3.6 activity logs ----
c = shell("Activity Logs", "Activity Logs")
c.inp(190, 100, 150, 34, "Endpoint: All  v")
c.inp(350, 100, 150, 34, "Event: All  v")
c.inp(510, 100, 210, 34, "Oct 1 - Oct 5, 2026")
c.button(732, 100, 134, 34, "Apply Filters", True, 15)
tbl(c, 190, 150, ["Seq", "Timestamp", "Endpoint", "Event Type", "Summary", "Integrity"],
    [["840", "10-05 09:14:02", "LAB1-PC07", "Logon", "Session start", OK],
     ["841", "10-05 09:14:40", "LAB1-PC07", "File detected", "setup_tool.exe", OK],
     ["842", "10-05 09:14:41", "LAB1-PC07", "Static scan", "Score 78 / 100", FAIL],
     ["843", "10-05 09:15:03", "LAB1-PC07", "Process start", "setup_tool.exe", FAIL],
     ["844", "10-05 09:41:10", "LAB1-PC07", "Heartbeat", "Agent running", OK],
     ["845", "10-05 10:02:55", "LAB1-PC07", "Logoff", "Session end", OK],
     ["846", "10-05 10:03:30", "LAB1-PC07", "Audit log", "Event 1102 cleared", OK]],
    [46, 134, 100, 112, 160, 124], rh=40)
c.t(190, 480, "Rows marked FAILED fail the integrity check and are highlighted for review.", 15, False, "#52606D")
c.button(190, 520, 150, 36, "Export CSV", False, 15)
figs.append(c.save("p_logs"))

# ---- Fig 3.7 detection detail ----
c = shell("Detections", "Detection Alert Details")
c.badge(190, 98, "SUSPICIOUS", AMB)
c.t(300, 109, "Alert #A-0312  |  Reported 09:14:41  |  LAB1-PC07", 15, False, "#52606D", "lm")
c.r(190, 132, 280, 250, fill=WHITE, out=MID, rad=6)
c.t(204, 150, "File Information", 16, True, DARK, "lm")
info = [("File name", "setup_tool.exe"), ("Location", "...\\Downloads"), ("SHA-256", "9f2c4e...a71e"), ("Size", "2.4 MB"),
        ("Signature", "Not signed"), ("Detected", "09:14:40")]
for i, (a, b) in enumerate(info):
    y = 184 + i * 32
    c.t(204, y, a, 14, False, "#52606D", "lm")
    c.t(300, y, b, 15, False, INK, "lm")
c.r(482, 132, 384, 250, fill=WHITE, out=MID, rad=6)
c.t(496, 150, "Static Analysis Result", 16, True, DARK, "lm")
c.t(496, 182, "Risk score", 14, False, "#52606D", "lm")
c.r(580, 172, 270, 20, fill=LIGHT, rad=4)
c.r(580, 172, int(270 * 0.78), 20, fill=AMB, rad=4)
c.t(850, 205, "78 / 100", 15, True, DARK, "rm")
c.t(496, 222, "Triggered rules (reasons)", 14, True, DARK, "lm")
rules = [("R1 No valid digital signature", "+15"), ("R2 High section entropy", "+20"), ("R3 Suspicious API imports", "+25"), ("R4 Packer indicator", "+18")]
for i, (a, b) in enumerate(rules):
    y = 250 + i * 30
    c.t(496, y, a, 14, False, INK, "lm")
    c.t(850, y, b, 14, True, DARK, "rm")
    c.line(496, y + 15, 850, y + 15, LIGHT)
c.r(190, 396, 676, 70, fill=PALE, out=MID, rad=6)
c.t(204, 416, "Record integrity", 15, True, DARK, "lm")
c.badge(204, 436, "VERIFIED", GRN)
c.t(300, 447, "Record #841 seal matches; chain intact up to the latest checkpoint.", 14, False, INK, "lm")
c.button(190, 484, 150, 38, "Mark Reviewed", True, 15)
c.button(352, 484, 170, 38, "Add Review Note", False, 15)
c.button(534, 484, 150, 38, "Open in Logs", False, 15)
figs.append(c.save("p_alert"))

# ---- Fig 3.8 integrity ----
c = shell("Integrity Check", "Integrity Verification")
c.inp(190, 98, 200, 36, "Endpoint: LAB1-PC07  v")
c.inp(402, 98, 210, 36, "Range: All records  v")
c.button(724, 98, 142, 36, "Run Verification", True, 15)
c.r(190, 150, 676, 64, fill="#F8E7E6", out=RED, rad=6, wd=2)
c.t(206, 172, "INTEGRITY FAILURE DETECTED", 18, True, RED, "lm")
c.t(206, 197, "1,250 records checked  |  first failure at seq 842  |  2 records flagged", 14, False, INK, "lm")
c.t(190, 238, "Chain view (seq 841 - 844)", 16, True, DARK, "lm")
nodes = [("841", "OK", GRN), ("842", "Content mismatch", RED), ("843", "Link mismatch", RED), ("844", "OK", GRN)]
for i, (q, st, col) in enumerate(nodes):
    x = 190 + i * 172
    c.r(x, 258, 140, 78, fill=WHITE, out=col, rad=6, wd=3)
    c.t(x + 70, 280, f"Record {q}", 16, True, INK, "mm")
    c.t(x + 70, 312, st, 14, True, col, "mm")
    if i < 3:
        c.arrow(x + 140, 297, x + 172, 297, ACC, 3)
tbl(c, 190, 356, ["Seq", "Failure Type", "Expected Seal", "Stored Seal"],
    [["842", "Content modified", "3ab1...e09d", "77c0...51af"],
     ["843", "Broken link (prev)", "3ab1...e09d", "9d44...0c2b"]],
    [70, 220, 193, 193], rh=38)
c.t(190, 462, "Findings are saved with the verification time and the administrator who ran the check.", 15, False, "#52606D")
c.button(190, 496, 160, 38, "Export Findings", False, 15)
figs.append(c.save("p_integrity"))

# ---- Fig 3.9 reports ----
c = shell("Reports", "Report Generation")
c.r(190, 100, 280, 400, fill=WHITE, out=MID, rad=6)
c.t(204, 120, "Report Options", 16, True, DARK, "lm")
for i, (a, b) in enumerate([("Report type", "Detection Summary  v"), ("Endpoint", "All endpoints  v"), ("Date range", "Oct 1 - Oct 5, 2026"), ("Format", "PDF  v")]):
    y = 148 + i * 70
    c.t(204, y, a, 14, False, "#52606D", "lm")
    c.inp(204, y + 14, 250, 34, b)
c.button(204, 440, 250, 40, "Generate Report", True, 16)
c.r(484, 100, 382, 400, fill=PALE, out=MID, rad=6)
c.t(498, 120, "Preview", 16, True, DARK, "lm")
c.r(504, 142, 342, 340, fill=WHITE, out=MID)
c.t(520, 164, "LogAegis Detection Summary", 16, True, DARK, "lm")
c.t(520, 188, "Oct 1 - Oct 5, 2026  |  All endpoints", 13, False, "#52606D", "lm")
tbl(c, 520, 210, ["Verdict", "Count"], [["High risk", "6"], ["Suspicious", "14"], ["Low risk", "31"]], [200, 110], rh=30, sz=14)
c.t(520, 322, "Integrity verification", 14, True, DARK, "lm")
c.t(520, 346, "Runs: 12   Passed: 11   Failed: 1", 14, False, INK, "lm")
c.t(520, 380, "Generated by: Lab Administrator", 13, False, "#52606D", "lm")
c.t(520, 400, "Generated on: 2026-10-05 10:50", 13, False, "#52606D", "lm")
figs.append(c.save("p_reports"))

# ---- Fig 3.10 settings ----
c = shell("Settings", "Settings: Detection Rules", "IT Personnel")
for i, n in enumerate(["Detection Rules", "Monitored Folders", "Users and Roles", "Retention"]):
    x = 190 + i * 168
    if i == 0:
        c.r(x, 98, 160, 34, fill=DARK, rad=5)
        c.t(x + 80, 115, n, 15, True, WHITE, "mm")
    else:
        c.r(x, 98, 160, 34, fill=WHITE, out=ACC, rad=5, wd=2)
        c.t(x + 80, 115, n, 15, True, DARK, "mm")
ON = ("ON", GRN)
tbl(c, 190, 150, ["Rule", "Characteristic", "Weight", "Status"],
    [["R1", "No valid digital signature", "15", ON],
     ["R2", "High section entropy", "20", ON],
     ["R3", "Suspicious API imports", "25", ON],
     ["R4", "Packer indicator", "18", ON],
     ["R5", "Anomalous PE structure", "10", ON],
     ["R6", "Suspicious embedded strings", "10", ON]],
    [60, 340, 110, 166], rh=36)
c.t(190, 396, "Thresholds", 16, True, DARK, "lm")
c.t(190, 428, "Suspicious at score >=", 15, False, INK, "lm")
c.inp(380, 414, 70, 32, "40")
c.t(480, 428, "High risk at score >=", 15, False, INK, "lm")
c.inp(660, 414, 70, 32, "70")
c.button(190, 470, 130, 38, "Save Changes", True, 15)
c.button(332, 470, 120, 38, "Reset", False, 15)
figs.append(c.save("p_settings"))

# ---- Fig 3.11 visualization samples ----
c = C(900, 600)
c.t(450, 20, "SAMPLE LAYOUT ONLY - values are placeholders, not study results", 15, True, RED, "mm")
# (a) bar: detections per day
c.r(15, 40, 430, 255, fill=WHITE, out=MID, rad=6)
c.t(28, 60, "(a) Detections per Day", 15, True, DARK, "lm")
c.line(40, 265, 430, 265, INK)
for i, v in enumerate([2, 4, 1, 5, 3, 0, 5]):
    x = 52 + i * 52
    if v:
        c.r(x, 265 - v * 28, 32, v * 28, fill=ACC)
    c.t(x + 16, 278, ["M", "T", "W", "T", "F", "S", "S"][i], 13, False, INK, "mm")
# (b) verdict distribution
c.r(455, 40, 430, 255, fill=WHITE, out=MID, rad=6)
c.t(468, 60, "(b) Verdict Distribution", 15, True, DARK, "lm")
tot = 380
parts = [("Low risk", 0.6, GRN), ("Suspicious", 0.28, AMB), ("High risk", 0.12, RED)]
x = 480
for n, p, col in parts:
    w = int(tot * p)
    c.r(x, 110, w, 40, fill=col)
    x += w
for i, (n, p, col) in enumerate(parts):
    c.r(480, 176 + i * 30, 18, 18, fill=col)
    c.t(508, 185 + i * 30, f"{n}  ({int(p*100)}%)", 15, False, INK, "lm")
# (c) integrity status per endpoint
c.r(15, 305, 430, 285, fill=WHITE, out=MID, rad=6)
c.t(28, 325, "(c) Integrity Status per Lab", 15, True, DARK, "lm")
for i, (n, ok, bad) in enumerate([("Lab 1", 9, 1), ("Lab 2", 10, 0), ("Lab 3", 10, 0)]):
    y = 355 + i * 62
    c.t(28, y + 16, n, 15, False, INK, "lm")
    unit = 30
    c.r(90, y, ok * unit, 32, fill=GRN)
    if bad:
        c.r(90 + ok * unit, y, bad * unit, 32, fill=RED)
c.t(90, 548, "green = verified endpoints   red = failed endpoints", 14, False, "#52606D", "lm")
# (d) grouped bar: tamper detection rate
c.r(455, 305, 430, 285, fill=WHITE, out=MID, rad=6)
c.t(468, 325, "(d) Tamper Detection Rate by Test Type", 15, True, DARK, "lm")
c.line(485, 530, 870, 530, INK)
for i, (n, a, b) in enumerate([("Modify", 1.0, 0.1), ("Delete", 1.0, 0.5), ("Insert", 1.0, 0.0)]):
    x = 500 + i * 125
    c.r(x, 530 - int(170 * a), 40, int(170 * a), fill=DARK)
    if b:
        c.r(x + 46, 530 - int(170 * b), 40, int(170 * b), fill=MID)
    c.t(x + 43, 546, n, 14, False, INK, "mm")
c.r(520, 560, 14, 14, fill=DARK)
c.t(540, 567, "LogAegis", 14, False, INK, "lm")
c.r(660, 560, 14, 14, fill=MID)
c.t(680, 567, "Baseline", 14, False, INK, "lm")
figs.append(c.save("viz"))

json.dump({n: [w * S, h * S] for n, w, h in figs}, open("img/sizes.json", "w"))
print(figs)