"""Draws the level-1 data flow diagram (DFD) as SVG. Run: python make_dfd.py"""
from pathlib import Path
from xml.sax.saxutils import escape

W, H = 1560, 1010
PX, SX = 560, 1200
ENT = {  # name: (x, y, w, h)
    "mail": (140, 55, 180, 50, "E-mail service"), "stu": (140, 300, 180, 50, "Student"),
    "ai": (1440, 385, 180, 56, "Gemini Pro AI service"), "staff": (140, 770, 180, 50, "Facility staff"),
    "club": (140, 920, 180, 50, "Club representative"),
}
PROC = {  # centre y
    "p1": (110, "1.0 Manage accounts and profiles"), "p6": (270, "6.0 Show activity history"),
    "p3": (430, "3.0 Balance teams"), "p2": (590, "2.0 Manage matches"),
    "p5": (770, "5.0 Manage facility schedule"), "p4": (920, "4.0 Manage tournaments"),
}
STORE = {"d1": (110, "D1 Users and verification codes"), "d2": (270, "D2 Profiles"), "d3": (500, "D3 Matches and participants"),
         "d4": (770, "D4 Facilities and blocks"), "d5": (920, "D5 Tournaments, teams, bracket")}


def box(n):
    if n in ENT:
        x, y, w, h, _ = ENT[n]; return x, y, w, h
    if n in PROC:
        return PX, PROC[n][0], 230, 70
    return SX, STORE[n][0], 240, 50


def clip(n, tx, ty):
    x, y, w, h = box(n)
    dx, dy = tx - x, ty - y
    s = min((w / 2) / abs(dx) if dx else 1e9, (h / 2) / abs(dy) if dy else 1e9)
    return x + dx * s, y + dy * s


FLOWS = [  # a, b, label lines, direction: '>' a->b, '<' b->a, '=' both
    ("stu", "p1", ["→ registration, login, profile", "← confirmation, session"], "="),
    ("p1", "mail", ["→ verification code"], ">"),
    ("p1", "d1", ["users, codes"], "="),
    ("p1", "d2", ["profile data"], "="),
    ("stu", "p6", ["→ history request", "← completed matches"], "="),
    ("d3", "p6", ["completed matches"], ">"),
    ("p3", "stu", ["teams"], ">"),
    ("p3", "ai", ["→ profile data, no names", "← skill ratings"], "="),
    ("d2", "p3", ["skill levels in, ratings out"], "="),
    ("p3", "d3", ["teams"], ">"),
    ("p2", "p3", ["full match"], ">"),
    ("stu", "p2", ["→ search, create, join, leave, cancel", "← match list, details"], "="),
    ("p2", "d3", ["matches, participants"], "="),
    ("p2", "d4", ["→ slot check", "← busy slots"], "="),
    ("staff", "p5", ["→ facilities, blocks", "← schedule"], "="),
    ("p5", "d4", ["facilities, blocks"], "="),
    ("club", "p4", ["→ tournament data, scores", "← bracket, results"], "="),
    ("p4", "d5", ["tournament data"], "="),
    ("p4", "d4", ["optional game slot"], ">"),
]


def build():
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Helvetica, Arial, sans-serif">',
         '<rect width="100%" height="100%" fill="white"/>',
         '<defs><marker id="a" markerWidth="9" markerHeight="7" refX="8" refY="3.5" orient="auto-start-reverse"><path d="M0,0 L9,3.5 L0,7 z" fill="#333"/></marker></defs>',
         f'<text x="{W/2}" y="24" text-anchor="middle" font-size="17" font-weight="bold">DFD level 1: CampusEvent</text>']
    for a, b, lab, d in FLOWS:
        ax, ay, _, _ = box(a); bx, by, _, _ = box(b)
        x1, y1 = clip(a, bx, by); x2, y2 = clip(b, ax, ay)
        ms = ' marker-start="url(#a)"' if d == "=" else ""
        o.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="#333" stroke-width="1.6" marker-end="url(#a)"{ms}/>')
        t = 0.5
        mx, my = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
        for i, line in enumerate(lab):
            o.append(f'<text x="{mx:.0f}" y="{my + i*14 - (len(lab)-1)*7 + 4:.0f}" text-anchor="middle" font-size="11.5" fill="#222" paint-order="stroke" stroke="white" stroke-width="5">{escape(line)}</text>')
    for n, (x, y, w, h, lab) in ENT.items():
        o.append(f'<rect x="{x-w/2}" y="{y-h/2}" width="{w}" height="{h}" fill="#fff4e6" stroke="#c96a1b" stroke-width="2"/>'
                 f'<text x="{x}" y="{y+4}" text-anchor="middle" font-size="13">{escape(lab)}</text>')
    for n, (y, lab) in PROC.items():
        o.append(f'<rect x="{PX-115}" y="{y-35}" width="230" height="70" rx="14" fill="#e8ecf4" stroke="#3f51b5" stroke-width="2"/>'
                 f'<text x="{PX}" y="{y+4}" text-anchor="middle" font-size="13" font-weight="bold">{escape(lab)}</text>')
    for n, (y, lab) in STORE.items():
        o.append(f'<line x1="{SX-120}" y1="{y-25}" x2="{SX+120}" y2="{y-25}" stroke="#2e7d32" stroke-width="2"/>'
                 f'<line x1="{SX-120}" y1="{y+25}" x2="{SX+120}" y2="{y+25}" stroke="#2e7d32" stroke-width="2"/>'
                 f'<rect x="{SX-120}" y="{y-25}" width="240" height="50" fill="#e6f4ea" fill-opacity="0.6" stroke="none"/>'
                 f'<text x="{SX}" y="{y+4}" text-anchor="middle" font-size="13">{escape(lab)}</text>')
    o.append('<text x="30" y="995" font-size="11" fill="#555">Orange: external entities. Blue: processes. Green: data stores.</text>')
    o.append("</svg>")
    return "\n".join(o)


if __name__ == "__main__":
    Path(__file__).with_name("dfd_level1.svg").write_text(build())
