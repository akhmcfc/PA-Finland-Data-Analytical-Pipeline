import csv, glob, os, re, sqlite3, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
f = (glob.glob(os.path.expanduser("~/Downloads/*Ex-Bootcamper*Survey*3*.csv")) or [None])[0]
if not f:
    sys.exit("CSV not found in Downloads")
with open(f, encoding="utf-8-sig", errors="replace", newline="") as fh:
    rd = csv.reader(fh); head = next(rd)
    rows = [r for r in rd if any(c.strip() for c in r)]
need = {1: "which year", 2: "applied to any", 4: "offer from any university abroad", 19: "token"}
bad = [i for i, k in need.items() if i >= len(head) or k not in head[i].lower()]
if bad:
    sys.exit("Unexpected CSV layout at columns %s - nothing changed" % bad)
g = lambda r, i: (r[i].strip() if i < len(r) else "")

c = sqlite3.connect("database/project_access_2026.db")
have = [r[1] for r in c.execute('pragma table_info("outcomes_all_years")')]
for extra in ("current_status", "response_token"):
    if extra not in have:
        c.execute('alter table outcomes_all_years add column "%s" TEXT' % extra); have.append(extra)
notnull = {r[1] for r in c.execute('pragma table_info("outcomes_all_years")') if r[3] and r[4] is None and not r[5]}

def rec(r):
    ym = re.search(r"(20\d\d)", g(r, 1))
    em = next((g(r, i).lower() for i in (17, 14) if "@" in g(r, i)), None)
    d = {"year": int(ym.group(1)) if ym else None, "first_name": g(r, 15) or None, "last_name": g(r, 16) or None, "email": em,
         "applied_abroad": g(r, 2) or None, "universities_applied_abroad": g(r, 3) or None,
         "received_offer_abroad": g(r, 4) or None, "offers_from_universities": g(r, 5) or None,
         "studying_abroad": g(r, 6) or None, "university_abroad": g(r, 7) or None, "field_abroad": g(r, 8) or None,
         "reason_not_abroad": g(r, 9) or None, "applied_finland": g(r, 10) or None,
         "university_finland": g(r, 11) or None, "field_finland": g(r, 12) or None, "future_plans": g(r, 13) or None,
         "consent_resend": "Yes" if "@" in g(r, 14) else "No", "submitted_at": g(r, 18),
         "current_status": g(r, 0) or None, "response_token": g(r, 19)}
    d = {k: v for k, v in d.items() if k in have}
    for k in notnull:
        if d.get(k) is None:
            d[k] = ""
    return d

YEARS = {int(m.group(1)) for (t,) in c.execute("select name from sqlite_master") for m in [re.fullmatch(r'bootcampers_(\d{4})', t)] if m}
ins = upd = 0
for r in rows:
    d = rec(r)
    if d.get('year') not in YEARS: continue
    ex = c.execute('select id from outcomes_all_years where response_token=? or (submitted_at=? and submitted_at != "")',
                   (g(r, 19), g(r, 18))).fetchone()
    if ex:
        c.execute('update outcomes_all_years set %s where id=?' % ",".join('"%s"=?' % k for k in d), list(d.values()) + [ex[0]]); upd += 1
    else:
        c.execute('insert into outcomes_all_years (%s) values (%s)' % (",".join('"%s"' % k for k in d), ",".join("?" * len(d))), list(d.values())); ins += 1
c.commit()
print("imported: %d new, %d updated | rows now: %d (CSV had %d)" % (ins, upd, c.execute("select count(*) from outcomes_all_years").fetchone()[0], len(rows)))
print("\nyear | replies | applied abroad | offers | studying abroad")
q = """select year, count(*),
  coalesce(sum(lower(coalesce(applied_abroad,'')) like 'yes%'),0),
  coalesce(sum(lower(coalesce(received_offer_abroad,'')) like 'yes%'),0),
  coalesce(sum(lower(coalesce(studying_abroad,'')) like 'yes%'),0)
  from outcomes_all_years group by year order by year"""
for y, n, a, o, s in c.execute(q):
    print("%s | %7d | %14d | %6d | %15d" % (y, n, a, o, s))
