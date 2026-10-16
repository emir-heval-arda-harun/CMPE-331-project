"""Generates the low-fidelity UI mockups (HTML + PNG). Run: python make_mockups.py
PNG files are rendered from the HTML with a headless browser (see README)."""
from pathlib import Path

CSS = """
*{box-sizing:border-box}body{margin:0;font-family:Helvetica,Arial,sans-serif;background:#f4f6fa;color:#1d2433;font-size:15px}
.top{background:#1f3a68;color:#fff;display:flex;align-items:center;gap:22px;padding:12px 28px}
.top b{font-size:19px;margin-right:12px}.top a{color:#cfd9ee;text-decoration:none}.top .r{margin-left:auto}
.wrap{max-width:1180px;margin:22px auto;padding:0 28px}h1{font-size:23px;margin:0 0 4px}.sub{color:#5a6478;margin-bottom:18px}
.card{background:#fff;border:1px solid #d5dbe7;border-radius:10px;padding:18px;margin-bottom:16px}
.row{display:flex;gap:16px;flex-wrap:wrap}.col{flex:1;min-width:240px}
label{display:block;font-size:12px;color:#5a6478;margin:10px 0 4px;text-transform:uppercase;letter-spacing:.04em}
.in{border:1px solid #b9c2d4;border-radius:6px;padding:9px 11px;background:#fff;color:#6b7488}
.btn{display:inline-block;background:#2f6fed;color:#fff;border-radius:7px;padding:10px 18px;font-weight:bold;margin-top:12px}
.btn.o{background:#fff;color:#2f6fed;border:1px solid #2f6fed}.btn.d{background:#c62828}.btn.g{background:#2e7d32}
.tag{display:inline-block;border-radius:12px;padding:2px 10px;font-size:12px;background:#e3e9f6;margin-right:6px}
.tag.ok{background:#dcf2e1;color:#1b5e20}.tag.warn{background:#fff3cd;color:#7a5b00}.tag.bad{background:#fde0e0;color:#8e1b1b}
table{border-collapse:collapse;width:100%}th,td{text-align:left;padding:9px 10px;border-bottom:1px solid #e3e8f2}th{font-size:12px;color:#5a6478;text-transform:uppercase}
.match{display:flex;align-items:center;gap:14px;border:1px solid #d5dbe7;border-radius:10px;padding:14px;background:#fff;margin-bottom:10px}
.match .t{width:92px;font-weight:bold}.match .m{flex:1}.note{font-size:12px;color:#7a5b00;background:#fff8e1;border:1px dashed #d1a800;border-radius:6px;padding:6px 9px;margin-top:10px}
.bracket{display:flex;gap:46px;align-items:center}.rd{display:flex;flex-direction:column;gap:22px}.g{border:1px solid #9fb0d3;border-radius:7px;background:#fff;width:190px}
.g div{padding:7px 10px;display:flex;justify-content:space-between}.g div+div{border-top:1px solid #e3e8f2}.win{font-weight:bold;background:#e8f5e9}
.cal{display:grid;grid-template-columns:70px repeat(5,1fr);gap:3px;font-size:12px}.cal div{padding:8px;border-radius:5px;background:#eef1f8}.cal .h{background:#dfe5f3;font-weight:bold}
.busy{background:#fde0e0!important}.blk{background:#ffe9bf!important}.free{background:#e2f4e6!important}
.chips span{display:inline-block;margin:0 6px 6px 0}.mob{max-width:390px;margin:0 auto}
"""
TOP = '<div class="top"><b>CampusEvent</b><a>Find a Match</a><a>Create Match</a><a>My Activities</a><a>Facilities</a><a>Tournaments</a><span class="r"><a>Ayşe Yılmaz ▾</a></span></div>'


def page(title, body, top=True, cls="wrap"):
    return f'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>{CSS}</style></head><body>{TOP if top else ""}<div class="{cls}">{body}</div></body></html>'


def match(t, d, title, meta, tags, btn):
    return f'<div class="match"><div class="t">{d}<br>{t}</div><div class="m"><b>{title}</b><br><span style="color:#5a6478">{meta}</span><br>{tags}</div><span class="btn {btn[1]}" style="margin:0">{btn[0]}</span></div>'


SCREENS = {}
SCREENS["01_sign_up"] = ("UC-01 Sign up and verify", page("Sign up", """
<div style="max-width:460px;margin:24px auto"><div class="card"><h1>Create your account</h1><div class="sub">Use your university e-mail address.</div>
<label>Full name</label><div class="in">Ayşe Yılmaz</div><label>University e-mail</label><div class="in">ayse.yilmaz@bilgiedu.net</div>
<label>Password</label><div class="in">••••••••••</div><div class="btn">Sign up</div>
<div class="note">Error (UC-01 2a): "Please use your university e-mail address." if the domain is not bilgiedu.net or bilgi.edu.tr.</div></div>
<div class="card"><b>Enter verification code</b><div class="sub">We sent a 6-digit code to your e-mail.</div><div class="in" style="letter-spacing:8px;text-align:center">4 8 1 9 2 7</div>
<span class="btn g">Verify</span> <span class="btn o">Send a new code</span></div></div>""", top=False))
SCREENS["02_log_in"] = ("UC-02 Log in", page("Log in", """
<div style="max-width:420px;margin:60px auto"><div class="card"><h1>Log in</h1><label>E-mail</label><div class="in">ayse.yilmaz@bilgiedu.net</div>
<label>Password</label><div class="in">••••••••••</div><div class="btn">Log in</div>
<div class="note">Wrong data: "Invalid e-mail or password". Account not verified: offer to resend the code (UC-02 3a).</div>
<p style="color:#2f6fed">No account yet? Sign up</p></div></div>""", top=False))
SCREENS["03_my_profile"] = ("UC-03 My profile", page("My profile", """
<h1>My Profile</h1><div class="sub">Used for match filters and AI team balancing.</div>
<div class="row"><div class="col card"><b>Sports and skill level</b>
<table><tr><th>Sport</th><th>Skill level</th><th></th></tr><tr><td>Football</td><td><span class="tag">Intermediate ▾</span></td><td>✕</td></tr>
<tr><td>Basketball</td><td><span class="tag">Beginner ▾</span></td><td>✕</td></tr><tr><td>Tennis</td><td><span class="tag">Advanced ▾</span></td><td>✕</td></tr></table>
<span class="btn o">+ Add sport</span></div>
<div class="col card"><b>Weekly availability</b><table><tr><th>Day</th><th>From</th><th>To</th><th></th></tr>
<tr><td>Monday</td><td>18:00</td><td>21:00</td><td>✕</td></tr><tr><td>Wednesday</td><td>19:00</td><td>22:00</td><td>✕</td></tr><tr><td>Saturday</td><td>11:00</td><td>16:00</td><td>✕</td></tr></table>
<span class="btn o">+ Add time slot</span><div class="note">Error: end time before start time (UC-03 6b).</div></div></div>
<span class="btn">Save profile</span>"""))
SCREENS["04_find_match"] = ("UC-05, UC-06 Find a match", page("Find a match", """
<h1>Find a Match</h1><div class="sub">Upcoming open matches, soonest first.</div>
<div class="card"><div class="row"><div class="col"><label>Sport</label><div class="in">Football ▾</div></div><div class="col"><label>Date</label><div class="in">02.11.2026</div></div>
<div class="col"><label>Time range</label><div class="in">17:00 – 22:00</div></div><div class="col"><label>Skill level</label><div class="in">Intermediate ▾</div></div></div><span class="btn">Apply filters</span></div>
"""+match("18:00","Mon 2 Nov","Football 5-a-side, Santral Football Pitch","Organizer: Mert K. · 7 of 10 players","<span class='tag'>Intermediate</span><span class='tag warn'>Open</span>",("Join",""))
+match("20:00","Mon 2 Nov","Football 5-a-side, Santral Football Pitch","Organizer: Can Ö. · 10 of 10 players","<span class='tag'>Intermediate</span><span class='tag bad'>Full</span>",("Full","o"))
+match("19:00","Tue 3 Nov","Football, Dorm Pitch","Organizer: Elif D. · 3 of 12 players","<span class='tag'>Intermediate</span><span class='tag warn'>Open</span>",("Join",""))
+'<div class="note">No result: "No match found. Create a match?" with a link to Create Match (UC-05 3a).</div>'))
SCREENS["05_match_details"] = ("UC-06, UC-07, UC-14, UC-15 Match details", page("Match details", """
<h1>Football 5-a-side <span class="tag ok">Full</span></h1><div class="sub">Mon 2 Nov 2026, 18:00 – 19:00 · Santral Football Pitch · Intermediate</div>
<div class="row"><div class="col card"><b>Participants (10 / 10)</b><table><tr><th>Player</th><th>Skill</th><th>Team</th></tr>
<tr><td>Mert K. (organizer)</td><td>Intermediate</td><td><span class="tag">Team 1</span></td></tr><tr><td>Zeynep A.</td><td>Intermediate</td><td><span class="tag">Team 2</span></td></tr>
<tr><td>Can Ö.</td><td>Advanced</td><td><span class="tag">Team 2</span></td></tr><tr><td>Elif D.</td><td>Beginner</td><td><span class="tag">Team 1</span></td></tr><tr><td>… 6 more</td><td></td><td></td></tr></table></div>
<div class="col card"><b>Actions</b><br><span class="btn g">Balance teams (AI)</span><br><span class="btn o">Leave match</span><br><span class="btn d">Cancel match</span>
<div class="note">Participants see "Leave match". Only the organizer sees "Balance teams" and "Cancel match". Teams: 2 (set at creation).</div>
<div class="note">If the AI service is not available: teams are balanced by declared skill levels (UC-07 2a) and a small notice is shown.</div></div></div>"""))
SCREENS["06_create_match"] = ("UC-04, UC-11 Create match", page("Create match", """
<h1>Create Match</h1><div class="sub">The facility must be free in the chosen time.</div>
<div class="row"><div class="col card"><label>Sport</label><div class="in">Football ▾</div><label>Facility (supports this sport)</label><div class="in">Santral Football Pitch ▾</div>
<label>Date</label><div class="in">02.11.2026</div><div class="row"><div class="col"><label>Start</label><div class="in">18:00</div></div><div class="col"><label>End</label><div class="in">19:00</div></div></div>
<div class="row"><div class="col"><label>Players (capacity)</label><div class="in">10</div></div><div class="col"><label>Teams</label><div class="in">2</div></div><div class="col"><label>Skill level</label><div class="in">Intermediate ▾</div></div></div>
<span class="btn">Create match</span></div>
<div class="col card"><b>Santral Football Pitch, Mon 2 Nov</b><div class="cal" style="margin-top:10px"><div class="h">Time</div><div class="h">Mon</div><div class="h">Tue</div><div class="h">Wed</div><div class="h">Thu</div><div class="h">Fri</div>
<div class="h">17:00</div><div class="free">free</div><div class="free">free</div><div class="busy">match</div><div class="free">free</div><div class="free">free</div>
<div class="h">18:00</div><div class="free">your slot</div><div class="blk">class</div><div class="free">free</div><div class="free">free</div><div class="busy">match</div>
<div class="h">19:00</div><div class="busy">match</div><div class="free">free</div><div class="blk">maintenance</div><div class="free">free</div><div class="free">free</div></div>
<div class="note">Conflict (UC-11 3a): "This slot is busy" and free slots of the day are suggested.</div></div></div>"""))
SCREENS["07_tournament"] = ("UC-08, UC-09, UC-10 Tournament bracket", page("Tournament", """
<h1>Spring Cup 2026 <span class="tag">Football</span> <span class="tag warn">In progress</span></h1><div class="sub">Organizer: Club representative · single elimination, 4 teams</div>
<div class="card"><div class="bracket"><div class="rd"><b>Round 1</b>
<div class="g"><div class="win"><span>Eagles</span><span>3</span></div><div><span>Lions</span><span>1</span></div></div>
<div class="g"><div><span>Wolves</span><span>2</span></div><div class="win"><span>Sharks</span><span>4</span></div></div></div>
<div class="rd"><b>Final</b><div class="g"><div><span>Eagles</span><span>–</span></div><div><span>Sharks</span><span>–</span></div></div></div>
<div class="rd"><b>Champion</b><div class="g"><div><span>to be decided</span></div></div></div></div>
<span class="btn g">Enter score for the final</span> <span class="btn o">Generate bracket</span>
<div class="note">Only club representatives see the buttons. Equal scores are rejected: "A knockout game needs a winner" (UC-10 2a). Teams are plain names.</div></div>
<div class="card"><b>New tournament</b><div class="row"><div class="col"><label>Name</label><div class="in">Spring Cup 2026</div></div><div class="col"><label>Sport</label><div class="in">Football ▾</div></div>
<div class="col"><label>Team names (one per line)</label><div class="in">Eagles, Lions, Wolves, Sharks</div></div></div><span class="btn">Create tournament</span></div>"""))
SCREENS["08_facility_management"] = ("UC-11, UC-12 Facility management", page("Facility management", """
<h1>Facility Management</h1><div class="sub">Facility staff only.</div>
<div class="row"><div class="col card"><b>Facilities</b><table><tr><th>Name</th><th>Sports</th></tr><tr><td>Santral Football Pitch</td><td>Football</td></tr><tr><td>Dorm Basketball Court</td><td>Basketball</td></tr></table>
<label>New facility name</label><div class="in">Tennis Court 1</div><label>Supported sports</label><div class="in chips"><span class="tag">Tennis ✕</span></div><span class="btn">Add facility</span></div>
<div class="col card"><b>Block a time period</b><label>Facility</label><div class="in">Santral Football Pitch ▾</div><label>From – to</label><div class="in">03.11.2026 09:00 – 12:00</div>
<label>Reason</label><div class="in">Physical education class</div><span class="btn">Block time</span>
<div class="note">Students cannot create matches in blocked periods (UC-12 postcondition).</div></div></div>"""))
SCREENS["09_my_activities"] = ("UC-13 My activities", page("My activities", """
<h1>My Activities</h1><div class="sub">Completed matches, newest first.</div>
<div class="card"><table><tr><th>Date</th><th>Time</th><th>Sport</th><th>Facility</th></tr><tr><td>26.10.2026</td><td>18:00</td><td>Football</td><td>Santral Football Pitch</td></tr>
<tr><td>19.10.2026</td><td>20:00</td><td>Basketball</td><td>Dorm Basketball Court</td></tr><tr><td>12.10.2026</td><td>17:00</td><td>Tennis</td><td>Tennis Court 1</td></tr></table>
<div class="note">Empty state: "No completed matches yet." Upcoming and cancelled matches are not listed (UC-13, UC-15).</div></div>"""))
SCREENS["10_find_match_mobile"] = ("NFR-01 Mobile view (390 px)", page("Mobile", """
<h1 style="font-size:20px">Find a Match</h1><div class="card"><label>Sport</label><div class="in">Football ▾</div><label>Date</label><div class="in">02.11.2026</div><label>Skill level</label><div class="in">Intermediate ▾</div><span class="btn">Apply filters</span></div>
<div class="match" style="flex-wrap:wrap"><div class="t">18:00<br>Mon 2 Nov</div><div class="m"><b>Football 5-a-side</b><br><span style="color:#5a6478">Santral Football Pitch · 7 of 10</span></div><span class="btn" style="margin:0">Join</span></div>
<div class="match" style="flex-wrap:wrap"><div class="t">19:00<br>Tue 3 Nov</div><div class="m"><b>Football, Dorm Pitch</b><br><span style="color:#5a6478">3 of 12 players</span></div><span class="btn" style="margin:0">Join</span></div>""", cls="mob"))

if __name__ == "__main__":
    here = Path(__file__).parent
    for name, (_, html) in SCREENS.items():
        (here / f"{name}.html").write_text(html, encoding="utf-8")
    print(len(SCREENS), "screens")
