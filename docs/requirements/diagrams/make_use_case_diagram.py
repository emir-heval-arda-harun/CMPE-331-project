"""Generates use_case_diagram.svg (run: python make_use_case_diagram.py).

The PNG version can be rendered with any browser, e.g.:
chromium --headless --screenshot=use_case_diagram.png --window-size=1500,1000 use_case_diagram.svg
"""

import math
from pathlib import Path

W, H = 1500, 1000
RX, RY = 150, 36

NAMES = {
    "UC-01": "Register &amp; Verify E-mail",
    "UC-02": "Log In",
    "UC-03": "Manage Profile",
    "UC-13": "Track Activity History",
    "UC-05": "Browse &amp; Filter Matches",
    "UC-06": "Join Match",
    "UC-04": "Create Match",
    "UC-11": "View Facility Schedule /\nCheck Conflicts",
    "UC-07": "AI Team Balancing",
    "UC-08": "Create Tournament",
    "UC-09": "Generate Bracket",
    "UC-10": "Record Score &amp; Advance",
    "UC-12": "Manage Facility Schedule",
}
COLUMN_A = ["UC-01", "UC-02", "UC-03", "UC-13", "UC-05", "UC-06", "UC-04", "UC-11", "UC-07"]
POS = {uc: (560, 120 + i * 97) for i, uc in enumerate(COLUMN_A)}
POS.update({"UC-08": (930, 170), "UC-09": (930, 290), "UC-10": (930, 410), "UC-12": (930, 600)})

ACTORS = {
    "Student": (150, 520),
    "E-mail Service": (150, 150),
    "Club\nRepresentative": (1350, 290),
    "Facility Staff": (1350, 600),
    "Gemini Pro\n(AI Service)": (1350, 880),
}
ASSOCIATIONS = {
    "Student": COLUMN_A,
    "E-mail Service": ["UC-01"],
    "Club\nRepresentative": ["UC-08", "UC-09", "UC-10"],
    "Facility Staff": ["UC-12"],
    "Gemini Pro\n(AI Service)": ["UC-07"],
}
DEPENDENCIES = [("UC-06", "UC-05", "«extend»"), ("UC-04", "UC-11", "«include»")]


def actor(x, y, label):
    out = [
        f'<circle cx="{x}" cy="{y - 45}" r="14" fill="white" stroke="#333" stroke-width="2"/>',
        f'<line x1="{x}" y1="{y - 31}" x2="{x}" y2="{y + 5}" stroke="#333" stroke-width="2"/>',
        f'<line x1="{x - 22}" y1="{y - 18}" x2="{x + 22}" y2="{y - 18}" stroke="#333" stroke-width="2"/>',
        f'<line x1="{x}" y1="{y + 5}" x2="{x - 16}" y2="{y + 35}" stroke="#333" stroke-width="2"/>',
        f'<line x1="{x}" y1="{y + 5}" x2="{x + 16}" y2="{y + 35}" stroke="#333" stroke-width="2"/>',
    ]
    for j, line in enumerate(label.split("\n")):
        out.append(f'<text x="{x}" y="{y + 58 + j * 20}" text-anchor="middle" font-size="17">{line}</text>')
    return out


def build():
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        'font-family="Helvetica, Arial, sans-serif">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<defs><marker id="ar" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">'
        '<path d="M0,0 L10,4 L0,8" fill="none" stroke="#333"/></marker></defs>',
        '<rect x="370" y="30" width="760" height="950" rx="8" fill="#f7f9fc" stroke="#333" stroke-width="2"/>',
        '<text x="750" y="60" text-anchor="middle" font-size="22" font-weight="bold">CampusEvent</text>',
    ]
    # Associations end at the ellipse's near edge so they never cross other use cases.
    for name, ucs in ASSOCIATIONS.items():
        ax, ay = ACTORS[name]
        left = ax < W / 2
        ax, ay = ax + (25 if left else -25), ay - 15
        for uc in ucs:
            x, y = POS[uc]
            ex = x - RX if left else x + RX
            out.append(f'<line x1="{ax}" y1="{ay}" x2="{ex}" y2="{y}" stroke="#555" stroke-width="1.5"/>')
    for uc, (x, y) in POS.items():
        out.append(f'<ellipse cx="{x}" cy="{y}" rx="{RX}" ry="{RY}" fill="#fff4e6" stroke="#c96a1b" stroke-width="2"/>')
        lines = NAMES[uc].split("\n")
        top = y - (14 if len(lines) > 1 else 6)
        out.append(f'<text x="{x}" y="{top}" text-anchor="middle" font-size="14" font-weight="bold">{uc}</text>')
        for j, line in enumerate(lines):
            out.append(f'<text x="{x}" y="{top + 18 + j * 16}" text-anchor="middle" font-size="15">{line}</text>')
    offset = 95
    edge_dy = RY * math.sqrt(1 - (offset / RX) ** 2)
    for src, dst, label in DEPENDENCIES:
        (x1, y1), (_, y2) = POS[src], POS[dst]
        direction = 1 if y2 > y1 else -1
        x, sy, ey = x1 + offset, y1 + edge_dy * direction, y2 - edge_dy * direction
        out.append(
            f'<line x1="{x}" y1="{sy:.0f}" x2="{x}" y2="{ey:.0f}" stroke="#333" stroke-width="1.5" '
            'stroke-dasharray="6,4" marker-end="url(#ar)"/>'
        )
        out.append(f'<text x="{x + 8}" y="{(sy + ey) / 2 + 5:.0f}" font-size="13" font-style="italic">{label}</text>')
    for name, (x, y) in ACTORS.items():
        out += actor(x, y, name)
    out.append('<text x="1350" y="395" text-anchor="middle" font-size="13" fill="#555">(a Student with club role)</text>')
    out.append('<text x="930" y="760" text-anchor="middle" font-size="13" fill="#555">'
               'All registered actors use UC-02 Log In.</text>')
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    Path(__file__).with_name("use_case_diagram.svg").write_text(build())
