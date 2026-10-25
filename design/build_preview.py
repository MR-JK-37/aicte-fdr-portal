#!/usr/bin/env python3
"""build_preview.py — regenerates design/preview.html from tokens.css (the visual contract for web + mobile).
   python3 -I design/build_preview.py
Screens mirror the reference layout one-to-one (see DESIGN_SPEC.md §13 mapping table). Sample text only."""
import pathlib
here = pathlib.Path(__file__).parent
css = (here / "tokens.css").read_text()

ICONS = {  # duotone line icons (preview only; production uses SF Symbols / Material Symbols / Phosphor duotone)
 'home': '<path d="M3 11l9-8 9 8v9a1 1 0 01-1 1h-5v-6h-6v6H4a1 1 0 01-1-1z"/>',
 'folder': '<path d="M3 7a2 2 0 012-2h4l2 2h8a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>',
 'bell': '<path d="M6 16V11a6 6 0 1112 0v5l2 2H4z"/><path d="M10 21h4" fill="none"/>',
 'user': '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0116 0z"/>',
 'users': '<circle cx="9" cy="8" r="3.5"/><path d="M2 20a7 7 0 0114 0z"/><circle cx="17" cy="9" r="2.8"/><path d="M15 14.5a6 6 0 017 5.5h-5"/>',
 'chev': '<path d="M9 6l6 6-6 6" fill="none"/>',
 'search': '<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5" fill="none"/>',
 'shield': '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/>',
 'doc': '<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4M9 13h6M9 17h6" fill="none"/>',
 'clock': '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2" fill="none"/>',
 'lock': '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 018 0v3" fill="none"/>',
 'finger': '<path d="M12 11v4a4 4 0 01-4 4M8 11a4 4 0 118 0v2M5 12a7 7 0 1114 0v3M12 15v1a7 7 0 01-2 5" fill="none"/>',
 'inbox': '<path d="M3 13l3-8h12l3 8v6H3z"/><path d="M3 13h5l1 3h6l1-3h5" fill="none"/>',
 'list': '<rect x="3" y="4" width="18" height="16" rx="3"/><path d="M8 9h8M8 13h8M8 17h5" fill="none"/>',
 'cal': '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4" fill="none"/>',
 'gear': '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M19 5l-2 2M7 17l-2 2" fill="none"/>',
 'globe': '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 010 18M12 3a14 14 0 000 18" fill="none"/>',
 'plus': '<path d="M12 5v14M5 12h14" fill="none"/>',
 'check': '<path d="M5 12l5 5L20 7" fill="none"/>',
 'pen': '<path d="M4 20l4-1 11-11-3-3L5 16z"/>',
 'bank': '<path d="M3 10l9-6 9 6z"/><path d="M5 10v8M9.5 10v8M14.5 10v8M19 10v8M3 21h18" fill="none"/>',
 'file': '<path d="M6 3h8l4 4v14H6z"/>',
}
SYM = ''.join(f'<symbol id="i-{k}" viewBox="0 0 24 24" fill="currentColor" fill-opacity=".18" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{v}</symbol>' for k, v in ICONS.items())

def ic(n, s=22, style=''):
    return f'<svg class="ic" width="{s}" height="{s}" style="{style}"><use href="#i-{n}"/></svg>'

_kid = [0]
def kosh(size=110, peek=False, mood='smile'):
    """Original mascot: glossy cobalt shield-coin with a white face plate, small dot eyes and a smile.
    Deliberately NOT a pair of large round eyes (that is another product's character)."""
    _kid[0] += 1; k = _kid[0]
    mouth = {'smile': 'M50 71q10 9 20 0', 'wow': 'M54 70q6 9 12 0q-6-5-12 0z', 'calm': 'M52 72h16'}[mood]
    hands = '<rect x="14" y="88" width="26" height="16" rx="8" fill="#2d63cf"/><rect x="80" y="88" width="26" height="16" rx="8" fill="#2d63cf"/>' if peek else ''
    return f'''<svg width="{size}" height="{size}" viewBox="0 0 120 120" aria-hidden="true"><defs>
<linearGradient id="b{k}" x1=".1" y1="0" x2=".9" y2="1"><stop offset="0" stop-color="#8fb4ff"/><stop offset=".55" stop-color="#3b78d8"/><stop offset="1" stop-color="#2556b8"/></linearGradient>
<radialGradient id="h{k}" cx=".3" cy=".2" r=".6"><stop offset="0" stop-color="#fff" stop-opacity=".75"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
<linearGradient id="f{k}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#e6edff"/></linearGradient></defs>
<ellipse cx="60" cy="112" rx="32" ry="5" fill="#2556b8" opacity=".16"/>
<path d="M60 8l41 15v32c0 30-18 47-41 55C37 102 19 85 19 55V23z" fill="url(#b{k})"/>
<path d="M60 8l41 15v32c0 30-18 47-41 55C37 102 19 85 19 55V23z" fill="url(#h{k})"/>
<path d="M60 8l41 15v32c0 30-18 47-41 55" fill="none" stroke="#1d47a0" stroke-opacity=".25" stroke-width="2"/>
<rect x="29" y="34" width="62" height="50" rx="22" fill="url(#f{k})"/>
<ellipse cx="46" cy="55" rx="5.2" ry="6.6" fill="#16213f"/><ellipse cx="74" cy="55" rx="5.2" ry="6.6" fill="#16213f"/>
<circle cx="47.8" cy="52.6" r="1.9" fill="#fff"/><circle cx="75.8" cy="52.6" r="1.9" fill="#fff"/>
<circle cx="37" cy="66" r="4.2" fill="#ffb7c2" opacity=".55"/><circle cx="83" cy="66" r="4.2" fill="#ffb7c2" opacity=".55"/>
<path d="{mouth}" fill="none" stroke="#16213f" stroke-width="3.2" stroke-linecap="round"/>
{hands}<path d="M101 14l2.6 5.4 5.4 2.6-5.4 2.6L101 30l-2.6-5.4L93 22l5.4-2.6z" fill="#dbe6ff"/></svg>'''

def mark():
    return '<svg width="26" height="26" viewBox="0 0 26 26"><circle cx="13" cy="13" r="10" fill="none" stroke="#3b78d8" stroke-width="4"/><circle cx="13" cy="13" r="3.6" fill="#1a1a1e"/></svg>'

def wordmark(big=False):
    return f'<div class="wm{" big" if big else ""}"><span>fdr</span>{mark()}<span>portal</span></div>'

def topbar(role, pct=None):
    prog = (f'<div class="topprog"><div class="progress-ink"><i style="width:{pct}%"></i></div><b>{pct}%</b></div>' if pct is not None else '<div class="topprog"></div>')
    return f'<div class="topbar">{wordmark()}{prog}<span class="bellw">{ic("bell",22,"color:#1a1a1e")}</span><span class="pill pill-role">{role}</span></div>'

def tabs(active, items):
    out = ''.join(f'<a {"aria-current=page" if k == active else ""}>{ic(i, 26)}<span>{l}</span></a>' for k, (i, l) in enumerate(items))
    return f'<nav class="tabbar">{out}</nav><div class="homebar"></div>'

def row(icon, title, sub='', trail=''):
    s = f'<small>{sub}</small>' if sub else ''
    t = f'<small class="r">{trail}</small>' if trail else ''
    return f'<div class="row">{ic(icon,24,"color:var(--azure)")}<div class="grow"><b>{title}</b>{s}</div>{t}{ic("chev",18,"color:var(--text-3)")}</div>'

INST = [("home", "Home"), ("folder", "Deposits"), ("inbox", "Inbox"), ("user", "Profile")]
OFFR = [("home", "Home"), ("list", "Cases"), ("inbox", "Inbox"), ("user", "Profile")]
AUTH = [("home", "Home"), ("shield", "Decisions"), ("inbox", "Inbox"), ("user", "Profile")]
ADMN = [("home", "Home"), ("bank", "Institutions"), ("inbox", "Inbox"), ("user", "Profile")]

P = []  # (caption, screen html, extra_class)
# 0 sign-in
P.append(('Sign in', f'''<div class="screen center"><div class="stack-c">{kosh(104)}<h1>Welcome back</h1><p class="sub">Sign in to the AICTE security deposit portal</p></div>
<div class="segmented w100"><button aria-selected="true">Institution</button><button>AICTE staff</button><button>Bank</button></div>
<div class="card stackg"><label class="lab">Official e-mail</label><input class="input" value="registrar@college.example" readonly><label class="lab">Password</label><input class="input" type="password" value="••••••••••" readonly><a class="lnk">Forgot password?</a></div>
<button class="btn btn-primary btn-block">Continue</button><button class="btn btn-soft btn-block">{ic("finger",20)} Use a passkey</button>
<p class="fine">{ic("lock",14)} Two-step verification is required after you sign in.</p></div>'''))
# 1 appearance / avatar picker (reference: top-left "mood" sheet)
tiles = ''.join(f'<div class="tile{" sel" if i == 0 else ""}">{kosh(46, mood=("smile","wow","calm")[i % 3])}</div>' for i in range(12))
P.append(('Choose your avatar', f'''<div class="screen sheetscreen"><div class="card pad0"><div class="segmented w100 sm4"><button>Name</button><button>Shape</button><button aria-selected="true">Mood</button><button>Colour</button></div>
<p class="sectionlabel">Choose a mood</p><div class="grid4">{tiles}</div></div><button class="btn btn-primary btn-block">Save</button></div>'''))
# 2 home (reference: centre-left)
P.append(('Home · Institution', f'''<div class="screen">{topbar("Registrar", 56)}
<div class="hero card0"><span class="chipw">Region: South</span><span class="pencil">{ic("pen",16,"color:#fff")}</span><svg class="ring" viewBox="0 0 150 150"><circle cx="75" cy="75" r="70" fill="none" stroke="#b4c9f4" stroke-width="2"/></svg><span class="sp s1"></span><span class="sp s2"></span>
<h2>Hello,<br>Asha</h2><div class="kpeek">{kosh(150, peek=True)}</div></div>
<div class="card-group"><div class="section-label">Needs attention</div>{row("doc","Reply to an observation","Due 28 Oct 2026")}{row("clock","FDR maturing in 30 days","Renewal not yet submitted")}</div>
<div class="card-group"><div class="section-label">Main</div>{row("plus","Submit a new deposit")}{row("folder","My documents")}{row("cal","Maturity calendar")}</div>
{tabs(0, INST)}</div>'''))
# 3 profile (reference: top-centre)
P.append(('Profile', f'''<div class="screen">{topbar("Scrutiny", 56)}
<div class="card profc"><span class="reg">Region: South</span><span class="pencil2">{ic("pen",14,"color:var(--text-1)")}</span><div class="avatar xl">AK</div><b>Anil Kumar</b><small>Scrutiny Officer</small></div>
<div class="card between"><b>Show my name to institutions</b><span class="switch" role="switch" aria-checked="true"></span></div>
<div class="card-group"><div class="section-label">Main</div>{row("shield","Two-step verification","","On")}{row("finger","Passkeys","","1")}{row("globe","Language","","English")}</div>
<div class="card-group"><div class="section-label">Policies and terms</div>{row("file","Privacy policy")}</div>
{tabs(3, OFFR)}</div>'''))
# 4 decision (reference: chat request, right column)
P.append(('Release decision', f'''<div class="screen">{topbar("Authority")}
<div class="card between wrapl"><div class="hd"><div class="avatar">AI</div><div><b>Apex Institute of Technology</b><small>Release request · FDR XXXX 4417</small></div></div></div>
<div class="card"><div class="bubble"><b>Recommendation</b><p>All six clause 6.46 rows are satisfied.</p><small class="r2">Yesterday, 18:38</small></div></div>
<div class="card"><p class="sub dark">Add a reason for your decision</p><div class="textarea sm"><span>Reason (optional)</span><i>0/500</i></div><button class="btn btn-primary btn-block">Approve with step-up</button></div>
<div class="card"><p class="sub dark">If it cannot be approved</p><div class="two2"><button class="btn btn-primary">Return</button><button class="btn btn-danger-soft">Reject</button></div></div>
{tabs(1, AUTH)}</div>'''))
# 5 bottom sheet over blur (reference: centre)
P.append(('Ask the handbook (sheet)', f'''<div class="screen blur">{topbar("Institution")}<div class="h">Hello, Asha</div><div class="card"><div class="fake"></div><div class="fake s"></div></div><div class="card"><div class="fake"></div></div>
<div class="scrimv"></div><div class="sheetv"><div class="grab"></div><div class="stack-c">{kosh(112, mood="wow")}<h3>Ask me about the Approval Process Handbook. I always show the clause.</h3></div><button class="btn btn-primary btn-block">Open</button></div></div>'''))
# 6 notifications empty (reference: bottom-left)
P.append(('Notifications · empty', f'''<div class="screen">{topbar("Institution", 56)}
<div class="h2">Notifications</div><div class="chiprow"><span class="chip is-active">All</span><span class="chip">Reminders</span><span class="chip">Observations</span><span class="chip">Decisions</span></div>
<div class="empty">{kosh(92, peek=False, mood="calm")}<b>Nothing here yet</b><p class="faint">Reminders, observations and decisions will appear here as soon as they happen.</p></div>{tabs(2, INST)}</div>'''))
# 7 directory (reference: "People")
def person(n, a, s):
    return f'<div class="row"><div class="avatar sm">{a}</div><div class="grow"><b>{n}</b><small>{s}</small></div>{ic("chev",18,"color:var(--text-3)")}</div>'
P.append(('Institutions', f'''<div class="screen">{topbar("Intake", 56)}
<div class="h2">Institutions</div><div class="card"><b class="t">Find an institution by name or AICTE ID</b><div class="searchbar in">{ic("search",20,"color:var(--text-3)")}<span>Search name or AICTE ID</span></div></div>
<div class="card-group"><div class="section-label">Available institutions</div>{person("Apex Institute of Tech.","AI","Karnataka · …4417")}{person("National College","NC","Tamil Nadu · …9021")}{person("St. Mary's Polytechnic","SM","Kerala · …7718")}</div>
{tabs(1, ADMN)}</div>'''))
# 8 profile completion (reference: bottom-right)
P.append(('Complete your profile', f'''<div class="screen">{topbar("Registrar", 56)}
<div class="card avc"><div class="avatar xl">AS</div><span class="badge">{ic("pen",14,"color:#fff")}</span></div>
<div class="card compl"><p>Complete your profile to unlock all notifications and alerts</p><div class="progress"><i style="width:56%"></i></div><b class="pc">56%</b></div>
<div class="card"><p class="sub dark b">Personal details</p><div class="fieldg">Full name</div><div class="fieldg">Designation</div></div>
<div class="card"><p class="sub dark b">Preferred language</p><div class="fieldg sel">English {ic("globe",20,"color:var(--azure)")}</div></div>
<button class="btn btn-primary btn-block">Save</button></div>'''))

phones = ''.join(f'<figure><div class="phone"><div class="status"><b>9:41</b><span>●●● ◔ ▭</span></div>{b}</div><figcaption>{t}</figcaption></figure>' for t, b in P)

def kpi(l, v, sub, cls='pill-neutral'):
    return f'<div class="card kpi"><small>{l}</small><b class="big">{v}</b><span class="pill {cls}">{sub}</span></div>'
side = ''.join(f'<a {"aria-current=page" if i == 0 else ""}>{ic(ico, 22)}<span>{l}</span></a>' for i, (ico, l) in enumerate([("home", "Dashboard"), ("list", "Cases"), ("folder", "Instruments"), ("inbox", "Inbox"), ("shield", "Verification"), ("cal", "Maturity calendar"), ("doc", "Reports"), ("gear", "Admin")]))
rows = ''.join(f'<tr><td><b>{a}</b><small>{b}</small></td><td class="mono">{c}</td><td class="num">{d}</td><td>{e}</td><td><span class="pill {f}">{g}</span></td></tr>' for a, b, c, d, e, f, g in [
    ("Apex Institute of Technology", "Karnataka", "XXXX 4417", "₹ 50,00,000", "14 Dec 2026", "pill-warn", "Expiring in 51 days"),
    ("National College of Engineering", "Tamil Nadu", "XXXX 9021", "₹ 35,00,000", "02 Mar 2027", "pill-ok", "Active · Bank-confirmed"),
    ("St. Mary's Polytechnic", "Kerala", "XXXX 7718", "₹ 15,00,000", "30 Oct 2026", "pill-error", "Overdue reply"),
    ("Delhi Global Technical Campus", "Delhi", "XXXX 3302", "₹ 25,00,000", "19 Jan 2027", "pill-pending", "Awaiting bank")])
web = f'''<div class="web"><aside class="sidebar card">{wordmark(True)}<nav>{side}</nav><div class="sideft">{kosh(72, mood="smile")}<small>Need help? Ask the handbook</small></div></aside>
<main><header class="wtop"><div class="searchbar wide">{ic("search",20,"color:var(--text-3)")}<span>Search FDR no., institution, bank</span><kbd>Ctrl K</kbd></div><div class="topprog"><div class="progress-ink"><i style="width:56%"></i></div><b>56%</b></div><span class="bellw">{ic("bell",22,"color:#1a1a1e")}</span><span class="pill pill-role">Scrutiny Officer</span><div class="avatar sm">AK</div></header>
<div class="hero herow"><div class="heroT"><span class="chipw">South region</span><h1>Good afternoon,<br>Anil</h1><p class="sub">Saturday, 24 Oct 2026</p><button class="btn btn-primary">{ic("plus",18,"color:#fff")} New observation</button></div><svg class="ring big" width="260" height="260"><circle cx="130" cy="130" r="122" fill="none" stroke="#b4c9f4" stroke-width="2"/></svg><div class="kpeekw">{kosh(190, peek=True)}</div></div>
<section class="kpis">{kpi("Active instruments","—","live from database")}{kpi("Expiring in 90 days","—","live from database",'pill-warn')}{kpi("Open observations","—","live from database",'pill-error')}{kpi("Awaiting bank","—","live from database",'pill-pending')}</section>
<section class="two-col"><div class="card"><div class="between"><h3>Needs action</h3><div class="segmented"><button aria-selected="true">Mine</button><button>Team</button></div></div><table><thead><tr><th>Institution</th><th>FDR no.</th><th class="num">Amount</th><th>Maturity</th><th>Status</th></tr></thead><tbody>{rows}</tbody></table></div>
<div class="card"><h3>Evidence attributes</h3><p class="sub">Never one score. Each fact keeps its source.</p><div class="legend"><div><span class="pill pill-neutral">Declared</span><small>Institution said so</small></div><div><span class="pill pill-pending">Extracted</span><small>Read from a document</small></div><div><span class="pill pill-ok">{ic("check",14)} Bank-confirmed</span><small>Bank answered</small></div><div><span class="pill pill-info">{ic("shield",14)} Ledger-reconciled</span><small>Matched a statement line</small></div><div><span class="pill pill-warn">Inconclusive</span><small>Needs a human decision</small></div></div></div></section>
<p class="fine">Design preview. Values shown as — are filled from the database at run time; names and amounts here are illustrative.</p></main></div>'''

EXTRA = r'''
*{box-sizing:border-box} body{margin:0;background:var(--canvas-deep);padding:32px 24px 64px;font-family:var(--font-body)}
.page-h{max-width:1500px;margin:0 auto 8px;font-family:var(--font-display)} .page-h h1{margin:0 0 4px;font-size:28px} .page-h p{margin:0;color:var(--text-2)}
.sec{max-width:1500px;margin:32px auto 12px;font:800 13px var(--font-body);letter-spacing:.08em;text-transform:uppercase;color:var(--text-3)}
.phones{max-width:1500px;margin:0 auto;display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:28px 20px;justify-items:center}
figure{margin:0;text-align:center} figcaption{margin-top:10px;font:700 13px var(--font-body);color:var(--text-2)}
.phone{position:relative;width:330px;height:760px;background:var(--canvas);border-radius:38px;box-shadow:0 0 0 7px #fff,0 14px 40px rgba(35,40,110,.14);overflow:hidden;text-align:left}
.status{position:absolute;top:12px;left:26px;right:24px;display:flex;justify-content:space-between;font-size:13px;z-index:3;color:#1a1a1e} .status span{letter-spacing:2px;font-size:10px}
.homebar{position:absolute;left:50%;bottom:6px;width:112px;height:4px;border-radius:2px;background:#1a1a1e;transform:translateX(-50%);z-index:3}
.screen{position:absolute;inset:0;padding:44px 12px 96px;display:flex;flex-direction:column;gap:10px;overflow:hidden} .screen>*{flex:none} .screen>.empty{flex:1}
.screen.center{justify-content:center;padding-bottom:24px} .sheetscreen{justify-content:flex-end;padding-bottom:30px;background:linear-gradient(var(--canvas),var(--canvas))}
.topbar{display:flex;align-items:center;gap:10px;height:42px;margin:2px 4px 0}
.wm{display:flex;align-items:center;gap:1px;font:800 20px/1 var(--font-display);letter-spacing:-.05em;color:#1a1a1e} .wm.big{font-size:24px;padding:4px 10px 10px} .wm svg{margin:0 1px}
.topprog{flex:1;min-width:0;display:flex;align-items:center;justify-content:flex-end;gap:6px} .topprog b{font:800 12px var(--font-body)} .topprog .progress-ink{flex:1;max-width:44px;min-width:18px}
.topbar .pill-role{height:28px;padding:0 10px;font-size:12px;flex:none} .topbar{gap:8px}
.bellw{display:inline-flex;margin:0 2px}
.ic{flex:none} .grow{flex:1;min-width:0}
.card0{padding:0}
.hero{min-height:178px;padding:16px} .hero h2{position:absolute;left:16px;bottom:18px;font:800 31px/34px var(--font-display);margin:0;letter-spacing:-.025em;color:var(--text-1)}
.chipw{display:inline-block;background:rgba(255,255,255,.7);border-radius:999px;padding:7px 12px;font:800 12px var(--font-body);color:var(--text-1)}
.pencil{position:absolute;top:12px;right:12px;width:30px;height:30px;border-radius:50%;background:#1a1a1e;display:grid;place-items:center}
.ring{position:absolute;right:-30px;top:6px;width:190px;height:190px} .ring.big{right:34px;top:10px;width:260px} .kpeek{position:absolute;right:-4px;bottom:-30px}
.sp{position:absolute;width:12px;height:12px;background:#c4d5fa;clip-path:polygon(50% 0,62% 38%,100% 50%,62% 62%,50% 100%,38% 62%,0 50%,38% 38%)} .s1{left:112px;top:62px} .s2{left:70px;top:126px}
.sub{color:var(--text-2);margin:0;font-size:14px;line-height:20px} .sub.dark{color:var(--text-1);font-weight:700} .sub.b{font-weight:800;margin-bottom:8px} .faint{color:var(--text-3);font-size:13px;line-height:18px;margin:0;font-weight:500}
.fine{color:var(--text-3);font-size:12px;line-height:16px;text-align:center;margin:4px 0}
.row b{font:700 15px/20px var(--font-body)} .row small{display:block;color:var(--text-3);font-size:12px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis} .row b{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;display:block} .row .r{margin-left:auto;display:inline;color:var(--text-3);font-weight:700;font-size:13px}
.row{min-height:52px} .section-label{padding:12px 14px 4px}
.h{font:800 28px/32px var(--font-display);letter-spacing:-.02em;margin:6px 4px 2px} .h2{font:800 20px/26px var(--font-display);margin:6px 4px 0}
.searchbar{display:flex;align-items:center;gap:10px;height:48px;padding:0 14px;border-radius:var(--radius-md);background:var(--surface);box-shadow:var(--shadow-card);color:var(--text-3);font-weight:600;font-size:14px}
.searchbar.in{background:var(--field);box-shadow:none;margin-top:10px;border-radius:999px}
.chiprow{display:flex;flex-wrap:wrap;gap:8px;margin:0 2px}
.stack-c{display:flex;flex-direction:column;align-items:center;text-align:center;gap:6px} .stack-c h1,.stack-c h3{margin:4px 0 0;font:800 24px/29px var(--font-display);letter-spacing:-.02em} .stack-c h3{font-size:18px;line-height:24px;padding:0 6px}
.stackg{display:flex;flex-direction:column;gap:8px} .lab{font:700 13px var(--font-body);color:var(--text-2)} .w100{width:100%} .w100 button{flex:1} .lnk{color:var(--primary);font-weight:700;font-size:14px}
.card{padding:14px} .card .t{font:800 14px var(--font-body);display:block}
.between{display:flex;align-items:center;justify-content:space-between;gap:8px} .between b{font:700 15px var(--font-body)}
.avatar{width:44px;height:44px;border-radius:50%;background:var(--primary-container);color:var(--primary);display:grid;place-items:center;font:800 15px var(--font-display);flex:none} .avatar.xl{width:96px;height:96px;font-size:30px;background:linear-gradient(135deg,#c9d7f7,#e6edff)} .avatar.sm{width:38px;height:38px;font-size:13px}
.profc{display:flex;flex-direction:column;align-items:center;gap:2px;position:relative;padding:34px 14px 16px} .profc b{font:800 16px var(--font-display);margin-top:8px} .profc small{color:var(--text-3);font-weight:600}
.reg{position:absolute;left:14px;top:12px;font:800 12px var(--font-body)} .pencil2{position:absolute;right:12px;top:10px;width:28px;height:28px;border-radius:50%;display:grid;place-items:center}
.avc{display:grid;place-items:center;position:relative;padding:20px} .badge{position:absolute;left:50%;margin-left:26px;bottom:18px;width:28px;height:28px;border-radius:50%;background:var(--azure);display:grid;place-items:center;box-shadow:0 0 0 3px #fff}
.compl{background:var(--field-strong)} .compl p{margin:0 0 10px;font:700 13px/18px var(--font-body)} .compl .pc{display:block;text-align:right;font:800 13px var(--font-body);margin-top:-4px}
.compl .progress{height:7px;background:#fff}
.fieldg{height:46px;border-radius:14px;background:var(--field);display:flex;align-items:center;justify-content:space-between;padding:0 14px;color:var(--text-3);font-weight:600;font-size:14px;margin-bottom:8px} .fieldg.sel{color:var(--text-1);font-weight:700}
.hd{display:flex;align-items:center;gap:10px} .hd b{display:block;font:800 14px var(--font-body)} .hd small{color:var(--text-3);font-weight:600;font-size:12px} .wrapl{align-items:flex-start}
.bubble{background:var(--field);border-radius:14px;padding:12px;margin-top:10px} .bubble b{font:800 13px var(--font-body)} .bubble p{margin:4px 0 6px;font-weight:500;font-size:13px;line-height:18px} .r2{display:block;text-align:right;color:var(--text-3);font-weight:600}
.textarea.sm{height:60px} .textarea{height:92px;border-radius:14px;background:var(--field);padding:12px 14px;display:flex;flex-direction:column;justify-content:space-between;color:var(--text-3);font-weight:600;font-size:14px;margin:8px 0 12px} .textarea i{align-self:flex-end;font-style:normal;font-size:12px}
.two2{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px} .two2 .btn{padding:0}
.tile{aspect-ratio:1;border-radius:14px;background:var(--field);display:grid;place-items:center} .tile.sel{box-shadow:inset 0 0 0 2px var(--azure);background:var(--surface)}
.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;padding:0 4px 4px} .sectionlabel{font:700 12px var(--font-body);color:var(--text-3);margin:12px 4px 8px} .pad0{padding:10px}
.sm4 button{padding:0 8px!important;font-size:13px}
.empty{display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:8px;padding:0 28px} .empty b{font:800 16px var(--font-display)}
.tabbar{position:absolute;bottom:18px;left:10px;right:10px;padding:6px} .tabbar a{padding:6px 0 4px}
.blur>*:not(.scrimv):not(.sheetv){filter:blur(3px)} .fake{height:16px;border-radius:8px;background:var(--field-strong);margin-bottom:10px;width:70%} .fake.s{width:45%}
.scrimv{position:absolute;inset:0;background:rgba(40,50,100,.30)} .sheetv{position:absolute;left:0;right:0;bottom:0;background:var(--surface);border-radius:28px 28px 0 0;padding:10px 16px 28px;display:flex;flex-direction:column;gap:14px;box-shadow:var(--shadow-sheet)}
.grab{width:40px;height:4px;border-radius:2px;background:var(--field-strong);margin:0 auto}
.sm4,.segmented{font-family:var(--font-body)}
.segmented>button,.mono,td,.pill,.chip,.btn{white-space:nowrap}
.webwrap{max-width:1500px;margin:0 auto;border-radius:28px;background:var(--canvas);box-shadow:0 0 0 7px #fff,0 14px 40px rgba(35,40,110,.14);overflow:hidden}
.web{display:grid;grid-template-columns:264px 1fr;gap:20px;padding:20px;min-height:800px}
.sidebar{display:flex;flex-direction:column;gap:12px;padding:18px 12px;height:100%} .sidebar nav{display:flex;flex-direction:column;gap:4px}
.sidebar nav a{display:flex;align-items:center;gap:12px;height:46px;padding:0 14px;border-radius:999px;color:var(--text-1);font:700 14px var(--font-body)} .sidebar nav a svg{color:var(--azure)}
.sidebar nav a[aria-current=page]{background:linear-gradient(180deg,var(--primary-container),color-mix(in srgb,var(--primary-container) 50%,#fff));color:var(--primary)}
.sideft{margin-top:auto;display:flex;flex-direction:column;align-items:center;gap:4px;background:var(--surface-muted);border-radius:18px;padding:14px;color:var(--text-2);font-weight:700;text-align:center}
.wtop{display:flex;align-items:center;gap:14px} .searchbar.wide{flex:1;max-width:560px} .searchbar kbd{margin-left:auto;font:700 11px var(--font-mono);background:var(--field);padding:3px 8px;border-radius:8px}
.herow{margin:20px 0 16px;min-height:230px;padding:28px;display:block} .heroT{position:relative;z-index:2} .herow h1{margin:14px 0 6px;font:800 36px/42px var(--font-display);letter-spacing:-.025em} .herow .btn{margin-top:14px}
.ring.big{position:absolute;right:96px;top:-10px} .kpeekw{position:absolute;right:120px;bottom:-26px} .herow::after{content:"";position:absolute;inset:0;background:radial-gradient(circle at 80% 30%,rgba(255,255,255,.5),transparent 55%)}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:16px} .kpi{display:flex;flex-direction:column;gap:8px;align-items:flex-start} .kpi small{color:var(--text-3);font-weight:700} .big{font:800 36px/40px var(--font-display)}
.two-col{display:grid;grid-template-columns:1.9fr 1fr;gap:16px} h3{margin:0 0 8px;font:800 18px var(--font-display)} table{width:100%;border-collapse:collapse;margin-top:12px;font-size:14px}
th{text-align:left;font:700 12px var(--font-body);color:var(--text-3);padding:8px 10px} td{padding:12px 10px;border-top:1px solid var(--hairline)} td small{display:block;color:var(--text-3);font-weight:600;font-size:12px} .num{text-align:right!important}
td:first-child{white-space:normal} .mono{font-family:var(--font-mono);font-size:12px;color:var(--text-3)}
.legend{display:flex;flex-direction:column;gap:12px;margin-top:12px} .legend div{display:flex;align-items:center;justify-content:space-between;gap:8px} .legend small{color:var(--text-3);font-weight:600;font-size:12px;text-align:right}
@media (max-width:1100px){.web{grid-template-columns:1fr}.sidebar{display:none}.kpis{grid-template-columns:1fr 1fr}.two-col{grid-template-columns:1fr}}
'''

html = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Lavender Ledger design preview</title><style>{css}{EXTRA}</style></head><body>
<svg width="0" height="0" style="position:absolute">{SYM}</svg>
<div class="page-h"><h1>Lavender Ledger — design preview</h1><p>Every screen mirrors the reference layout one-to-one (top bar with wordmark, progress, bell and role pill; hero card with mascot; grouped list cards; floating pill tab bar; black pill buttons; soft-red pill; bottom sheet over blur; empty state). Sample text only.</p></div>
<div class="sec">Mobile — iOS and Android share the look; each keeps its own icons, type and motion</div><div class="phones">{phones}</div>
<div class="sec">Web — same tokens; the floating sidebar becomes the floating pill tab bar below 768 px</div><div class="webwrap">{web}</div></body></html>'''
(here / "preview.html").write_text(html)
print("preview.html", len(html))
