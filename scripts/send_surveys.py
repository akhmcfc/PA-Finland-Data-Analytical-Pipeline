"""Send survey emails (Survey 2 / Survey 3) to every student whose window is open.
Works for any year table candidate_mapping_YYYY. Nothing hardcoded.
Default = DRY RUN (sends nothing). Add --send to really send.
Secrets (SMTP) come only from environment variables.
Commands:
  init                      create tracking tables
  set-form N URL            save the Typeform link for survey N (2 or 3)
  status                    counts only, no names/emails
  run [--send] [--max 60]   send what is due (initial + reminders)
  test ADDRESS              send one sample mail to yourself
  pause / resume            global stop switch
  optout CANDIDATE_ID       never email this student again
"""
import os, sys, re, sqlite3, smtplib, ssl, datetime as dt
from email.message import EmailMessage
from urllib.parse import quote

DB = os.environ.get("PA_DB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "database", "project_access_2026.db"))
REMIND_EVERY_DAYS = int(os.environ.get("PA_REMIND_DAYS", "7"))
MAX_REMINDERS = int(os.environ.get("PA_MAX_REMINDERS", "2"))
SURVEYS = {2: "mid_bootcamp", 3: "post_bootcamp"}

def con():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c

def init(c):
    c.executescript("""
    CREATE TABLE IF NOT EXISTS survey_send_forms(survey_no INTEGER PRIMARY KEY, form_url TEXT);
    CREATE TABLE IF NOT EXISTS survey_send_log(id INTEGER PRIMARY KEY AUTOINCREMENT, yr INTEGER, survey_no INTEGER,
        candidate_id TEXT, kind TEXT, sent_at TEXT);
    CREATE TABLE IF NOT EXISTS survey_send_optout(candidate_id TEXT PRIMARY KEY);
    CREATE TABLE IF NOT EXISTS survey_send_state(k TEXT PRIMARY KEY, v TEXT);
    """); c.commit()

def years(c):
    names = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'candidate_mapping_%'")]
    return sorted(int(n.rsplit("_", 1)[1]) for n in names if n.rsplit("_", 1)[1].isdigit())

def d(v):
    try: return dt.date.fromisoformat(str(v)[:10])
    except Exception: return None

def paused(c):
    r = c.execute("SELECT v FROM survey_send_state WHERE k='paused'").fetchone()
    return bool(r and r[0] == "1")

def due(c, today):
    """list of (yr, n, row, kind) that should get an email today"""
    out = []
    opt = {r[0] for r in c.execute("SELECT candidate_id FROM survey_send_optout")}
    for yr in years(c):
        for n, prefix in SURVEYS.items():
            tbl = f"{prefix}_{yr}"
            has = c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (tbl,)).fetchone()
            replied = {r[0] for r in c.execute(f"SELECT candidate_id FROM {tbl}")} if has else set()
            for row in c.execute(f"SELECT * FROM candidate_mapping_{yr}"):
                cid = row["candidate_id"]
                s, e = d(row[f"survey_{n}_send_start"]), d(row[f"survey_{n}_send_end"])
                if not (s and e and s <= today <= e) or cid in opt or not row["email"]:
                    continue
                logs = c.execute("SELECT kind, sent_at FROM survey_send_log WHERE yr=? AND survey_no=? AND candidate_id=? ORDER BY id",
                                 (yr, n, cid)).fetchall()
                if not logs:
                    out.append((yr, n, row, "initial")); continue
                if cid in replied: continue
                rem = [l for l in logs if l["kind"] == "reminder"]
                last = d(logs[-1]["sent_at"])
                if len(rem) < MAX_REMINDERS and last and (today - last).days >= REMIND_EVERY_DAYS and (e - today).days >= 1:
                    out.append((yr, n, row, "reminder"))
    return out

def link(c, n, cid):
    r = c.execute("SELECT form_url FROM survey_send_forms WHERE survey_no=?", (n,)).fetchone()
    if not r or not r[0]: return None
    base = r[0].split("#")[0]
    return base + "#candidate_id=" + quote(str(cid))

def build(row, n, kind, url, deadline):
    first = (row["first_name"] or "").strip() or "there"
    topic = "your university applications" if n == 2 else "how your university applications turned out"
    nq = "7" if n == 2 else "a few"
    subj = ("Reminder: " if kind == "reminder" else "") + f"Quick check-in on {topic}"
    body = (f"Hi {first},\n\nWe'd love a quick update on {topic}. It takes about 2 minutes ({nq} questions).\n\n"
            f"Your personal link:\n{url}\n\n"
            "Please don't share this link; it is only for you.\n"
            f"You can fill it in again any time before {deadline:%d %B %Y}; we'll use your latest answers.\n\n"
            "Results are shown only as group totals, never with your name.\n\nThank you!\nProject Access Finland\n")
    m = EmailMessage(); m["Subject"] = subj; m["To"] = row["email"]; m.set_content(body); return m

def smtp_send(msg):
    h, u, p = (os.environ.get(k) for k in ("PA_SMTP_HOST", "PA_SMTP_USER", "PA_SMTP_PASS"))
    f = os.environ.get("PA_FROM") or u
    if not (h and u and p): raise RuntimeError("Set PA_SMTP_HOST, PA_SMTP_USER, PA_SMTP_PASS (and PA_FROM) first")
    msg["From"] = f
    with smtplib.SMTP(h, int(os.environ.get("PA_SMTP_PORT", "587")), timeout=30) as s:
        s.starttls(context=ssl.create_default_context()); s.login(u, p); s.send_message(msg)

SENDER = smtp_send  # tests replace this

def run(c, send, mx, today=None):
    today = today or dt.date.today()
    if paused(c): print("PAUSED - nothing sent."); return 0
    todo = due(c, today); sent = 0
    print(f"{len(todo)} due ({sum(1 for t in todo if t[3]=='initial')} first, {sum(1 for t in todo if t[3]=='reminder')} reminders)")
    for yr, n, row, kind in todo[:mx]:
        url = link(c, n, row["candidate_id"])
        if not url: print(f"Survey {n}: no form link saved (use set-form). Skipping."); break
        msg = build(row, n, kind, url, d(row[f"survey_{n}_send_end"]))
        if not send: continue
        try: SENDER(msg)
        except Exception as ex: print("send failed:", type(ex).__name__); continue
        now = dt.datetime.now().isoformat(timespec="seconds")
        c.execute("INSERT INTO survey_send_log(yr,survey_no,candidate_id,kind,sent_at) VALUES(?,?,?,?,?)", (yr, n, row["candidate_id"], kind, now))
        if kind == "initial":
            c.execute(f"UPDATE candidate_mapping_{yr} SET survey_{n}_sent_date=? WHERE candidate_id=?", (today.isoformat(), row["candidate_id"]))
        c.commit(); sent += 1
    print(f"Sent {sent}." if send else "DRY RUN - nothing sent. Add --send to send.")
    if len(todo) > mx: print(f"{len(todo)-mx} more wait for the next run (limit {mx}).")
    return sent

def status(c, today=None):
    today = today or dt.date.today()
    print("paused:", paused(c))
    for n in SURVEYS:
        print(f"Survey {n} link saved:", bool(link(c, n, "x")))
    for yr in years(c):
        for n, prefix in SURVEYS.items():
            tot = c.execute(f"SELECT COUNT(*) FROM candidate_mapping_{yr}").fetchone()[0]
            sent = c.execute("SELECT COUNT(DISTINCT candidate_id) FROM survey_send_log WHERE yr=? AND survey_no=? AND kind='initial'", (yr, n)).fetchone()[0]
            try: rep = c.execute(f"SELECT COUNT(*) FROM {prefix}_{yr}").fetchone()[0]
            except Exception: rep = 0
            print(f"{yr} Survey {n}: students {tot}, emailed {sent}, replied {rep}")
    print("due today:", len(due(c, today)))

def main(a):
    if not a: print(__doc__); return
    c = con(); init(c); cmd = a[0]
    if cmd == "init": print("ready")
    elif cmd == "set-form":
        c.execute("INSERT OR REPLACE INTO survey_send_forms VALUES(?,?)", (int(a[1]), a[2])); c.commit(); print("saved")
    elif cmd == "status": status(c)
    elif cmd == "run":
        mx = int(a[a.index("--max") + 1]) if "--max" in a else 60
        run(c, "--send" in a, mx)
    elif cmd == "test":
        row = {"first_name": "Test", "email": a[1]}
        SENDER(build(row, 2, "initial", "https://example.com/?candidate_id=TEST", dt.date.today())); print("test sent")
    elif cmd in ("pause", "resume"):
        c.execute("INSERT OR REPLACE INTO survey_send_state VALUES('paused',?)", ("1" if cmd == "pause" else "0",)); c.commit(); print(cmd + "d")
    elif cmd == "optout":
        c.execute("INSERT OR IGNORE INTO survey_send_optout VALUES(?)", (a[1],)); c.commit(); print("done")
    else: print(__doc__)

if __name__ == "__main__": main(sys.argv[1:])
