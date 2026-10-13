import os, sys, json, sqlite3, tempfile, datetime
sys.path.insert(0, os.getcwd())
from flask import Flask, Response
import api.models.acceptance as acc
from api.routes import multi_year_routes as routes

tmp = os.path.join(tempfile.gettempdir(), "pa_test_accept.db")

def make_db(r27, o27, r28, o28, c2027=False):
    if os.path.exists(tmp): os.remove(tmp)
    c = sqlite3.connect(tmp)
    def cohort(y, groups):
        c.execute(f"create table candidate_mapping_{y} (candidate_id text, expected_uni_start_year integer, survey_3_send_start text, survey_3_send_end text)")
        c.execute(f"create table post_bootcamp_{y} (candidate_id text, universities_accepted text)")
        for tag, start, n, resp, offers in groups:
            for i in range(n):
                c.execute(f"insert into candidate_mapping_{y} values (?,?,?,?)", (f"{y}{tag}{i}", start, f"{start}-03-01", f"{start}-08-31"))
            for i in range(resp):
                c.execute(f"insert into post_bootcamp_{y} values (?,?)", (f"{y}{tag}{i}", "Oxford" if i < offers else "none"))
    cohort(2026, [("A", 2027, 21, r27, o27), ("B", 2028, 15, r28, o28)])
    if c2027: cohort(2027, [("A", 2028, 10, 10, 7)])
    for y in (2024, 2025):
        c.execute(f"create table bootcampers_{y} (candidate_id text, email text)")
        for i in range(10):
            c.execute(f"insert into bootcampers_{y} values (?,?)", (f"B{y}-{i}", f"b{y}_{i}@x.fi"))
    c.execute("create table outcomes_all_years (id integer, bootcamper_id text, year integer, email text, received_offer_abroad text, studying_abroad text)")
    for n, (y, e, o, s) in enumerate([(2024,"b2024_0@x.fi","Yes","Yes"),(2024,"b2024_1@x.fi","Yes","No"),(2024,"b2024_2@x.fi","No","No"),
                                      (2025,"b2025_0@x.fi","Yes","Yes"),(2025,"b2025_1@x.fi","No","No")]):
        c.execute("insert into outcomes_all_years values (?,?,?,?,?,?)", (n, "x", y, e, o, s))
    c.commit(); c.close()
    acc.DATABASE_FILE = tmp

def setdate(y, m, d):
    class FD(datetime.date):
        @classmethod
        def today(cls): return datetime.date(y, m, d)
    acc.date = FD

app = Flask("t")
def run(years):
    with app.test_request_context("/api/multi-year/range/dashboard"):
        r = Response(json.dumps({"years_included": years}), mimetype="application/json")
        return json.loads(routes._acceptance_fix(r).get_data(as_text=True))

fails = 0
def check(name, got, want):
    global fails
    ok = got == want
    fails += (not ok)
    print(("PASS  " if ok else "FAIL  ") + name + ("" if ok else f"\n        expected: {want}\n        got:      {got}"))

PEND = "pending: 2026 (2028 starters)"
setdate(2027, 5, 1); make_db(3, 1, 0, 0)
d = run([2026])
check("May 2027, 3 of 21 answered: TBD", (d["acceptance_rate"], d["acceptance_rate_note"]), ("TBD", "2026 bootcampers only - awaiting Survey 3"))

make_db(21, 12, 0, 0)
d = run([2026])
check("May 2027, all 21 answered: rate on 21", d["acceptance_rate"], "57.1%")
check("  note says 21 of 36 counted", d["acceptance_rate_note"], "2026 bootcampers only - 21 of 36 bootcampers counted so far (2026 (2027 starters)); " + PEND)
check("  status in_progress", d["acceptance_by_year"][0]["status"], "in_progress")

setdate(2027, 9, 1); make_db(18, 10, 0, 0)
d = run([2026])
check("Sep 2027, window closed, 18 of 21 answered, 10 offers: 10/21", d["acceptance_rate"], "47.6%")

setdate(2028, 9, 1); make_db(21, 12, 15, 9)
d = run([2026])
check("Sep 2028, everyone done: full rate 21/36", d["acceptance_rate"], "58.3%")
check("  note says full cohort", d["acceptance_rate_note"], "2026 bootcampers only - full cohort (36 of 36)")
check("  status completed", d["acceptance_by_year"][0]["status"], "completed")

make_db(21, 12, 15, 9, c2027=True)
d = run([2026, 2027])
check("2026-2027 combined", (d["acceptance_rate"], d["acceptance_rate_note"]), ("60.9%", "2026-2027 bootcampers only - full cohort (46 of 46)"))

setdate(2027, 5, 1); make_db(21, 12, 0, 0)
d = run([2024, 2025, 2026])
check("2024-2026: pre-2026 ignored, rate is 2026 only", d["acceptance_rate"], "57.1%")
check("  retro per year (year, responses, offers)", [(x["year"], x["responses"], x["with_offer"]) for x in d["historical_outcomes"]["years"]], [(2024, 3, 2), (2025, 2, 1)])
d = run([2025])
check("single historical year: no rate", d["acceptance_rate"], None)
d = run([2024, 2025])
check("full historical range: retro rate", d["acceptance_rate"], "15.0%")

print("\nALL PASS" if not fails else f"\n{fails} CHECK(S) FAILED")
os.remove(tmp)
