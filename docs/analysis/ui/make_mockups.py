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
.ev{display:flex;align-items:center;gap:14px;border:1px solid #d5dbe7;border-radius:10px;padding:14px;background:#fff;margin-bottom:10px}
.ev .t{width:92px;font-weight:bold}.ev .m{flex:1}.note{font-size:12px;color:#7a5b00;background:#fff8e1;border:1px dashed #d1a800;border-radius:6px;padding:6px 9px;margin-top:10px}
.cal{display:grid;grid-template-columns:70px repeat(5,1fr);gap:3px;font-size:12px}.cal div{padding:8px;border-radius:5px;background:#eef1f8}.cal .h{background:#dfe5f3;font-weight:bold}
.busy{background:#fde0e0!important}.blk{background:#ffe9bf!important}.free{background:#e2f4e6!important}
.chips span{display:inline-block;margin:0 6px 6px 0}.mob{max-width:390px;margin:0 auto}
"""
TOP = '<div class="top"><b>CampusEvent</b><a>Find an Event</a><a>Create Event</a><a>My Activities</a><a>Facilities</a><span class="r"><a>Ayşe Yılmaz ▾</a></span></div>'


def page(title, body, top=True, cls="wrap"):
    return f'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>{CSS}</style></head><body>{TOP if top else ""}<div class="{cls}">{body}</div></body></html>'


def event(t, d, title, meta, tags, btn):
    return f'<div class="ev"><div class="t">{d}<br>{t}</div><div class="m"><b>{title}</b><br><span style="color:#5a6478">{meta}</span><br>{tags}</div><span class="btn {btn[1]}" style="margin:0">{btn[0]}</span></div>'


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
<h1>My Profile</h1><div class="sub">Interests and availability are used to pre-fill the event filters.</div>
<div class="row"><div class="col card"><b>Interests (any category)</b>
<div class="in chips" style="margin-top:10px"><span class="tag">football ✕</span><span class="tag">board games ✕</span><span class="tag">study group ✕</span><span class="tag">photography ✕</span></div>
<label>Add an interest</label><div class="in">e.g. chess, hiking, robotics</div><span class="btn o">+ Add interest</span>
<div class="note">Free text: there is no fixed category list (BR-14).</div></div>
<div class="col card"><b>Weekly availability</b><table><tr><th>Day</th><th>From</th><th>To</th><th></th></tr>
<tr><td>Monday</td><td>18:00</td><td>21:00</td><td>✕</td></tr><tr><td>Wednesday</td><td>19:00</td><td>22:00</td><td>✕</td></tr><tr><td>Saturday</td><td>11:00</td><td>16:00</td><td>✕</td></tr></table>
<span class="btn o">+ Add time slot</span><div class="note">Error: end time before start time (UC-03 5b).</div></div></div>
<span class="btn">Save profile</span>"""))
SCREENS["04_find_event"] = ("UC-05, UC-06 Find an event", page("Find an event", """
<h1>Find an Event</h1><div class="sub">Upcoming open events, soonest first.</div>
<div class="card"><div class="row"><div class="col"><label>Keyword</label><div class="in">night</div></div><div class="col"><label>Category</label><div class="in">board games</div></div><div class="col"><label>Date</label><div class="in">02.11.2026</div></div>
<div class="col"><label>Time range</label><div class="in">17:00 – 22:00</div></div></div><span class="btn">Apply filters</span></div>
"""
    + event("18:00", "Mon 2 Nov", "Board game night, Student Lounge", "Organizer: Mert K. · 7 of 12 participants", "<span class='tag'>board games</span><span class='tag warn'>Open</span>", ("Join", ""))
    + event("20:00", "Mon 2 Nov", "Football 5-a-side, Santral Pitch", "Organizer: Can Ö. · 10 of 10 participants", "<span class='tag'>football</span><span class='tag bad'>Full</span>", ("Full", "o"))
    + event("19:00", "Tue 3 Nov", "Algorithms study group, Room B-204", "Organizer: Elif D. · 3 of 8 participants", "<span class='tag'>study group</span><span class='tag warn'>Open</span>", ("Join", ""))
    + '<div class="note">No result: "No event found. Create an event?" with a link to Create Event (UC-05 3a).</div>'))
SCREENS["05_event_details"] = ("UC-06, UC-10, UC-11 Event details", page("Event details", """
<h1>Board game night <span class="tag">board games</span> <span class="tag warn">Open</span></h1><div class="sub">Mon 2 Nov 2026, 18:00 – 21:00 · Student Lounge · 7 of 12 participants</div>
<div class="row"><div class="col card"><b>About</b><p>Bring your favourite board game. Beginners welcome, we have snacks.</p>
<b>Participants (7 / 12)</b><table><tr><th>Name</th><th>Role</th></tr>
<tr><td>Mert K.</td><td><span class="tag">Organizer</span></td></tr><tr><td>Zeynep A.</td><td>Participant</td></tr><tr><td>Can Ö.</td><td>Participant</td></tr><tr><td>… 4 more</td><td></td></tr></table></div>
<div class="col card"><b>Actions</b><br><span class="btn g">Join event</span><br><span class="btn o">Leave event</span><br><span class="btn d">Cancel event</span>
<div class="note">Visitors see "Join event" (or "This event is full"). Participants see "Leave event". Only the organizer sees "Cancel event"; the organizer cannot leave (BR-12).</div>
<div class="note">E-mail addresses are never shown to other students (NFR-05).</div></div></div>"""))
SCREENS["06_create_event"] = ("UC-04, UC-07 Create event", page("Create event", """
<h1>Create Event</h1><div class="sub">Any kind of event. The facility must be free in the chosen time.</div>
<div class="row"><div class="col card"><label>Title</label><div class="in">Board game night</div><label>Category (free text)</label><div class="in">board games</div>
<label>Description</label><div class="in">Bring your favourite board game.</div>
<label>Facility</label><div class="in">Student Lounge (capacity 50) ▾</div>
<label>Date</label><div class="in">02.11.2026</div><div class="row"><div class="col"><label>Start</label><div class="in">18:00</div></div><div class="col"><label>End</label><div class="in">21:00</div></div>
<div class="col"><label>Participants (capacity)</label><div class="in">12</div></div></div>
<span class="btn">Create event</span><div class="note">Error: capacity above the facility capacity (UC-04 3b).</div></div>
<div class="col card"><b>Student Lounge, week of 2 Nov</b><div class="cal" style="margin-top:10px"><div class="h">Time</div><div class="h">Mon</div><div class="h">Tue</div><div class="h">Wed</div><div class="h">Thu</div><div class="h">Fri</div>
<div class="h">17:00</div><div class="free">free</div><div class="free">free</div><div class="busy">event</div><div class="free">free</div><div class="free">free</div>
<div class="h">18:00</div><div class="free">your slot</div><div class="blk">class</div><div class="free">free</div><div class="free">free</div><div class="busy">event</div>
<div class="h">19:00</div><div class="free">your slot</div><div class="free">free</div><div class="blk">maintenance</div><div class="free">free</div><div class="free">free</div></div>
<div class="note">Conflict (UC-07 3a): "This slot is busy" and the free slots of the day are suggested.</div></div></div>"""))
SCREENS["07_facility_management"] = ("UC-07, UC-08 Facility management", page("Facility management", """
<h1>Facility Management</h1><div class="sub">Facility staff only.</div>
<div class="row"><div class="col card"><b>Facilities</b><table><tr><th>Name</th><th>Capacity</th></tr><tr><td>Student Lounge</td><td>50</td></tr><tr><td>Santral Football Pitch</td><td>22</td></tr><tr><td>Room B-204</td><td>30</td></tr></table>
<label>New facility name</label><div class="in">Dorm Basketball Court</div><label>Capacity</label><div class="in">20</div><span class="btn">Add facility</span></div>
<div class="col card"><b>Block a time period</b><label>Facility</label><div class="in">Student Lounge ▾</div><label>From – to</label><div class="in">03.11.2026 09:00 – 12:00</div>
<label>Reason</label><div class="in">Official faculty meeting</div><span class="btn">Block time</span>
<div class="note">Students cannot create events in blocked periods (UC-08 postcondition).</div></div></div>"""))
SCREENS["08_my_activities"] = ("UC-09 My activities", page("My activities", """
<h1>My Activities</h1><div class="sub">Completed events, newest first.</div>
<div class="card"><table><tr><th>Date</th><th>Time</th><th>Event</th><th>Category</th><th>Facility</th></tr><tr><td>26.10.2026</td><td>18:00</td><td>Football 5-a-side</td><td>football</td><td>Santral Football Pitch</td></tr>
<tr><td>19.10.2026</td><td>20:00</td><td>Algorithms study group</td><td>study group</td><td>Room B-204</td></tr><tr><td>12.10.2026</td><td>17:00</td><td>Photo walk</td><td>photography</td><td>Main Campus</td></tr></table>
<div class="note">Empty state: "No completed events yet." Upcoming and cancelled events are not listed (UC-09, UC-11).</div></div>"""))
SCREENS["09_find_event_mobile"] = ("NFR-01 Mobile view (390 px)", page("Mobile", """
<h1 style="font-size:20px">Find an Event</h1><div class="card"><label>Category</label><div class="in">board games</div><label>Date</label><div class="in">02.11.2026</div><label>Keyword</label><div class="in">night</div><span class="btn">Apply filters</span></div>
<div class="ev" style="flex-wrap:wrap"><div class="t">18:00<br>Mon 2 Nov</div><div class="m"><b>Board game night</b><br><span style="color:#5a6478">Student Lounge · 7 of 12</span></div><span class="btn" style="margin:0">Join</span></div>
<div class="ev" style="flex-wrap:wrap"><div class="t">19:00<br>Tue 3 Nov</div><div class="m"><b>Algorithms study group</b><br><span style="color:#5a6478">Room B-204 · 3 of 8</span></div><span class="btn" style="margin:0">Join</span></div>""", cls="mob"))

if __name__ == "__main__":
    here = Path(__file__).parent
    for name, (_, html) in SCREENS.items():
        (here / f"{name}.html").write_text(html, encoding="utf-8")
    print(len(SCREENS), "screens")
