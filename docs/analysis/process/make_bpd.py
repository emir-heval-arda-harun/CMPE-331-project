"""Draws the business process diagrams (BPD) as swimlane SVG files.

Run: python make_bpd.py   (PNG versions are rendered from the SVG with a browser).
"""
import textwrap
from pathlib import Path
from xml.sax.saxutils import escape

COLW, LANEH, NW, NH, LABELW, TOP = 160, 140, 136, 60, 120, 20


class Diagram:
    def __init__(self, title, lanes, nodes, edges):
        self.title, self.lanes, self.nodes, self.edges = title, lanes, nodes, edges

    def pos(self, nid):
        lane, col, *_ = self.nodes[nid]
        return LABELW + 30 + col * COLW + NW / 2, TOP + 30 + lane * LANEH + LANEH / 2

    def box(self, nid):
        x, y = self.pos(nid)
        kind = self.nodes[nid][3]
        w, h = (NW, NH) if kind == "task" else ((46, 46) if kind in ("start", "end") else (NW, 76))
        return x, y, w, h

    def svg(self):
        ncol = max(n[1] for n in self.nodes.values()) + 1
        W = LABELW + 60 + ncol * COLW
        H = TOP + 30 + len(self.lanes) * LANEH + 20
        o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Helvetica, Arial, sans-serif">',
             '<rect width="100%" height="100%" fill="white"/>',
             '<defs><marker id="a" markerWidth="9" markerHeight="7" refX="8" refY="3.5" orient="auto-start-reverse"><path d="M0,0 L9,3.5 L0,7 z" fill="#333"/></marker></defs>',
             f'<text x="{W/2}" y="{TOP+8}" text-anchor="middle" font-size="16" font-weight="bold">{escape(self.title)}</text>']
        for i, name in enumerate(self.lanes):
            y = TOP + 30 + i * LANEH
            o.append(f'<rect x="10" y="{y}" width="{W-20}" height="{LANEH}" fill="{"#f7f9fc" if i%2==0 else "#fffaf3"}" stroke="#888"/>')
            o.append(f'<rect x="10" y="{y}" width="{LABELW}" height="{LANEH}" fill="#e8ecf4" stroke="#888"/>')
            o.append(f'<text transform="translate({10+LABELW/2},{y+LANEH/2}) " text-anchor="middle" font-size="14" font-weight="bold">{self.wrap(name, 14, 14, 0)}</text>')
        for e in self.edges:
            o += self.edge(*e)
        for nid in self.nodes:
            o += self.node(nid)
        o.append("</svg>")
        return "\n".join(o)

    def wrap(self, text, width, size, cx):
        lines = textwrap.wrap(text, width) or [text]
        y0 = -(len(lines) - 1) * size * 0.6
        return "".join(f'<tspan x="{cx}" dy="{(0 if i==0 else size*1.2)+(y0 if i==0 else 0)}">{escape(l)}</tspan>' for i, l in enumerate(lines))

    def node(self, nid):
        x, y, w, h = self.box(nid)
        label, kind = self.nodes[nid][2], self.nodes[nid][3]
        if kind == "start":
            return [f'<circle cx="{x}" cy="{y}" r="22" fill="#e6f4ea" stroke="#2e7d32" stroke-width="2"/>',
                    f'<text x="{x}" y="{y+40}" text-anchor="middle" font-size="11">{escape(label)}</text>']
        if kind == "end":
            return [f'<circle cx="{x}" cy="{y}" r="22" fill="#fdecea" stroke="#c62828" stroke-width="4"/>',
                    f'<text x="{x}" y="{y+40}" text-anchor="middle" font-size="11">{escape(label)}</text>']
        if kind == "gw":
            pts = f"{x},{y-h/2} {x+w/2},{y} {x},{y+h/2} {x-w/2},{y}"
            return [f'<polygon points="{pts}" fill="#fff8e1" stroke="#b28704" stroke-width="2"/>',
                    f'<text x="{x}" y="{y}" text-anchor="middle" font-size="11">{self.wrap(label, 16, 11, x)}</text>']
        return [f'<rect x="{x-w/2}" y="{y-h/2}" width="{w}" height="{h}" rx="8" fill="#fff4e6" stroke="#c96a1b" stroke-width="2"/>',
                f'<text x="{x}" y="{y}" text-anchor="middle" font-size="12">{self.wrap(label, 19, 12, x)}</text>']

    def edge(self, a, b, label="", both=False):
        ax, ay, aw, ah = self.box(a)
        bx, by, bw, bh = self.box(b)
        la, lb = self.nodes[a][0], self.nodes[b][0]
        ca, cb = self.nodes[a][1], self.nodes[b][1]
        ms = ' marker-start="url(#a)"' if both else ""
        if ca == cb:  # vertical
            d = 1 if by > ay else -1
            pts = [(ax, ay + d * ah / 2), (bx, by - d * bh / 2)]
        elif cb > ca:
            sx, ex = ax + aw / 2, bx - bw / 2
            if la == lb:
                pts = [(sx, ay), (ex, by)]
            else:
                mx = ex - 14
                pts = [(sx, ay), (mx, ay), (mx, by), (ex, by)]
        else:  # back edge
            d = 1 if by > ay else -1
            if la == lb:
                d = 1
                ym = ay + ah / 2 + 30
                pts = [(ax, ay + ah / 2), (ax, ym), (bx, ym), (bx, by + bh / 2)]
            else:
                ym = (ay + by) / 2
                pts = [(ax, ay + d * ah / 2), (ax, ym), (bx, ym), (bx, by - d * bh / 2)]
        p = " ".join(f"{x:.0f},{y:.0f}" for x, y in pts)
        out = [f'<polyline points="{p}" fill="none" stroke="#333" stroke-width="1.6" marker-end="url(#a)"{ms}/>']
        if label:
            (x1, y1), (x2, y2) = pts[0], pts[1]
            lx, ly = (x1 + x2) / 2, (y1 + y2) / 2
            if abs(x2 - x1) < 1:
                lx += 6; anchor = "start"
            else:
                ly -= 5; anchor = "middle"
            out.append(f'<text x="{lx:.0f}" y="{ly:.0f}" text-anchor="{anchor}" font-size="11" font-style="italic" fill="#a00" paint-order="stroke" stroke="white" stroke-width="3">{escape(label)}</text>')
        return out


def S(lane, col, label): return (lane, col, label, "start")
def E(lane, col, label): return (lane, col, label, "end")
def T(lane, col, label): return (lane, col, label, "task")
def G(lane, col, label): return (lane, col, label, "gw")


DIAGRAMS = {
    "bpd_account_onboarding": Diagram(
        "BPD 1: Account registration and profile setup (UC-01, UC-02, UC-03)",
        ["Student", "CampusEvent system", "E-mail service"],
        {"s1": S(0, 0, "Wants to join"), "s2": T(0, 1, "Fill sign-up form"), "y1": G(1, 2, "University e-mail?"),
         "y2": T(1, 3, "Create unverified account"), "m1": T(2, 4, "Send verification code"),
         "s5": T(0, 5, "Enter verification code"), "y3": G(1, 6, "Code correct?"), "y4": T(1, 7, "Mark account verified"),
         "s8": T(0, 8, "Set sports, skill levels, availability"), "y5": T(1, 9, "Save profile"), "e": E(0, 10, "Ready to find matches")},
        [("s1", "s2"), ("s2", "y1"), ("y1", "s2", "No"), ("y1", "y2", "Yes"), ("y2", "m1"), ("m1", "s5"), ("s5", "y3"),
         ("y3", "s5", "No"), ("y3", "y4", "Yes"), ("y4", "s8"), ("s8", "y5"), ("y5", "e")]),
    "bpd_match_lifecycle": Diagram(
        "BPD 2: Organizing and playing a match (UC-04 to UC-07, UC-11, UC-13, UC-15)",
        ["Organizer", "Other students", "CampusEvent system", "Gemini Pro"],
        {"o1": S(0, 0, "Wants to play"), "o2": T(0, 1, "Choose sport, facility, time, capacity, teams"),
         "y1": G(2, 2, "Facility free?"), "y2": T(2, 3, "Create match (open)"),
         "o6": T(0, 4, "Cancel match (slot is released)"), "e2": E(0, 5, "Match cancelled"),
         "p1": T(1, 4, "Search matches with filters"), "p2": T(1, 5, "Join match"),
         "y3": G(2, 6, "Free place left?"), "y4": T(2, 7, "Add participant; status full at capacity"),
         "o7": T(0, 8, "Balance teams"), "y8": T(2, 9, "Rate players and form balanced teams"),
         "a1": T(3, 9, "Return skill ratings"), "p4": T(1, 10, "Play match"),
         "y9": T(2, 11, "Mark completed, add to history"), "e": E(2, 12, "History updated")},
        [("o1", "o2"), ("o2", "y1"), ("y1", "o2", "No: free slots shown"), ("y1", "y2", "Yes"), ("y2", "o6"), ("o6", "e2"), ("y2", "p1"), ("p1", "p2"),
         ("p2", "y3"), ("y3", "p1", "No: match full"), ("y3", "y4", "Yes"), ("y4", "o7"), ("o7", "y8"),
         ("y8", "a1", "profiles without names / ratings", True), ("y8", "p4"), ("p4", "y9"), ("y9", "e")]),
    "bpd_tournament": Diagram(
        "BPD 3: Running a tournament (UC-08, UC-09, UC-10)",
        ["Club representative", "CampusEvent system"],
        {"c1": S(0, 0, "Wants a tournament"), "c2": T(0, 1, "Enter name, sport, team names"),
         "y1": G(1, 2, "Role ok, 2+ teams, no duplicates?"), "y2": T(1, 3, "Create tournament"),
         "c4": T(0, 4, "Generate bracket"), "y3": T(1, 5, "Pair round 1, give byes, create later rounds"),
         "c6": T(0, 6, "Enter score of a played game"), "y4": G(1, 7, "Scores different?"),
         "y5": T(1, 8, "Store result, move winner on"), "y6": G(1, 9, "Was it the final?"),
         "y7": T(1, 10, "Set champion"), "e": E(0, 11, "Champion known")},
        [("c1", "c2"), ("c2", "y1"), ("y1", "c2", "No"), ("y1", "y2", "Yes"), ("y2", "c4"), ("c4", "y3"), ("y3", "c6"),
         ("c6", "y4"), ("y4", "c6", "No"), ("y4", "y5", "Yes"), ("y5", "y6"), ("y6", "c6", "No"), ("y6", "y7", "Yes"), ("y7", "e")]),
    "bpd_facility_management": Diagram(
        "BPD 4: Facility schedule and conflict check (UC-11, UC-12)",
        ["Facility staff", "CampusEvent system", "Student"],
        {"f1": S(0, 0, "Defines facilities"), "f2": T(0, 1, "Add facility with sports"), "y1": T(1, 2, "Store facility"),
         "f3": T(0, 3, "Add blocked period and reason"), "y2": T(1, 4, "Store block, show in schedule"),
         "s1": T(2, 5, "Create a match for a time slot"), "y3": G(1, 6, "Slot overlaps a block or match?"),
         "s4": T(2, 7, "See conflict and free slots"), "y5": T(1, 7, "Accept slot, create match")},
        [("f1", "f2"), ("f2", "y1"), ("y1", "f3"), ("f3", "y2"), ("y2", "s1"), ("s1", "y3"), ("y3", "s4", "Yes"), ("y3", "y5", "No")]),
}

if __name__ == "__main__":
    here = Path(__file__).parent
    for name, d in DIAGRAMS.items():
        (here / f"{name}.svg").write_text(d.svg())
        print(name)
