import os, sys, json, sqlite3, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import requests
from config.config import DATABASE_FILE
try:
    from config.config import TYPEFORM_API_TOKEN as _CFG
except Exception:
    _CFG = None
try:
    from config.config import SURVEY_2_FORM_ID, SURVEY_3_FORM_ID
except Exception:
    SURVEY_2_FORM_ID = SURVEY_3_FORM_ID = None

API = "https://api.typeform.com/forms"

SEED = {
 2: {"8efe1b0a-107c-4f1e-8440-d994296575c5": "changed_universities",
     "00c71511-088e-4eaf-8f13-b5e2ac99e1e2": "changed_destination",
     "9dbc04f3-08f0-489f-b227-d22dc59eb0df": "changed_major",
     "b3b11284-a577-4e8a-a879-8585b564511a": "biggest_challenge",
     "be6ed6cb-83a5-4883-9cba-92fba5f4e07b": "resources_used",
     "f5bf196b-f3eb-4017-b9d6-b3c2380b7394": "support_needed",
     "ed6e9f78-daf7-4f57-8845-897cb6061838": "whats_working"},
 3: {"fc33c649-c263-4045-8f36-64141dd475be": "received_offers",
     "027abaad-d05e-4e5e-9e80-6a64a222e8e4": "universities_applied",
     "c6370b78-1b1f-48c5-912c-e23950cb4894": "universities_accepted",
     "2310672a-da17-4450-aafc-fe8545356589": "final_choice",
     "f7eb845b-7b52-427b-a21a-b2dbafaeac53": "bootcamp_impact_final",
     "97661f7f-5431-4672-91b3-8d01579e5fae": "most_valuable_element",
     "01730b12-1df4-4745-ab1a-fb159e1a3b42": "resources_missing"},
}
NEW_COLS = {"mid_bootcamp": ["resources_used", "support_needed", "submitted_at", "response_id"],
            "post_bootcamp": ["received_offers", "resources_missing", "submitted_at", "response_id"]}


def token():
    return os.environ.get("TYPEFORM_API_TOKEN") or _CFG


def cols(conn, t):
    return [r[1] for r in conn.execute('pragma table_info("%s")' % t)]


def setup(conn, forms):
    conn.execute("create table if not exists survey_forms (year integer, survey_no integer, form_id text, primary key (year, survey_no))")
    conn.execute("create table if not exists survey_field_map (form_id text, ref text, column_name text, primary key (form_id, ref))")
    conn.execute("create table if not exists survey_responses (response_id text primary key, year integer, survey_no integer, candidate_id text, submitted_at text, answers_json text)")
    for year, survey, fid in forms:
        if not fid or fid == "INPUT_LATER":
            continue
        conn.execute("insert or ignore into survey_forms values (?,?,?)", (year, survey, fid))
        for ref, col in SEED.get(survey, {}).items():
            conn.execute("insert or ignore into survey_field_map (form_id, ref, column_name) values (?,?,?)", (fid, ref, col))
        t = ("mid" if survey == 2 else "post") + "_bootcamp_%d" % year
        have = cols(conn, t)
        for c in NEW_COLS["mid_bootcamp" if survey == 2 else "post_bootcamp"]:
            if c not in have:
                conn.execute('alter table "%s" add column "%s" TEXT' % (t, c))
    if "kind" not in cols(conn, "survey_field_map"):
        conn.execute('alter table survey_field_map add column kind TEXT')
    conn.execute("update survey_field_map set kind='text' where column_name in ('support_needed','whats_working','universities_applied','final_choice','resources_missing')")
    conn.commit()


def value(a):
    t = a.get("type")
    if t == "choice":
        ch = a.get("choice") or {}
        return ch.get("label") or ch.get("other")
    if t == "choices":
        ch = a.get("choices") or {}
        v = list(ch.get("labels") or [])
        if ch.get("other"):
            v.append(ch["other"])
        return " | ".join(v) if v else None
    return a.get(t)


def ingest_response(conn, year, survey, form_id, resp):
    rid = resp.get("response_id") or resp.get("token")
    cid = ((resp.get("hidden") or {}).get("candidate_id") or "").strip()
    if not rid or not cid:
        return "skipped"
    if not conn.execute("select 1 from candidate_mapping_%d where candidate_id=?" % year, (cid,)).fetchone():
        return "unknown_candidate"
    fmap = dict(conn.execute("select ref, column_name from survey_field_map where form_id=?", (form_id,)).fetchall())
    vals = {}
    for a in resp.get("answers", []):
        col = fmap.get((a.get("field") or {}).get("ref"))
        if col:
            vals[col] = value(a)
    when = resp.get("submitted_at") or resp.get("landed_at") or ""
    cur = conn.execute("insert or ignore into survey_responses values (?,?,?,?,?,?)",
                       (rid, year, survey, cid, when, json.dumps(vals, ensure_ascii=False)))
    if cur.rowcount == 0:
        return "duplicate"
    rid2, when2, js = conn.execute("select response_id, submitted_at, answers_json from survey_responses where year=? and survey_no=? and candidate_id=? order by submitted_at desc, rowid desc limit 1", (year, survey, cid)).fetchone()
    latest = json.loads(js)
    table = ("mid" if survey == 2 else "post") + "_bootcamp_%d" % year
    have = cols(conn, table)
    data = {"candidate_id": cid}
    for col in set(fmap.values()):
        if col in have:
            data[col] = latest.get(col)
    if "submitted_at" in have: data["submitted_at"] = when2
    if "response_id" in have: data["response_id"] = rid2
    names = list(data)
    upd = ",".join('"%s"=excluded."%s"' % (n, n) for n in names if n != "candidate_id")
    sql = 'insert into "%s" (%s) values (%s)' % (table, ",".join('"%s"' % n for n in names), ",".join("?" * len(names)))
    sql += (" on conflict(candidate_id) do update set " + upd) if upd else " on conflict(candidate_id) do nothing"
    conn.execute(sql, [data[n] for n in names])
    return "saved"


def sync():
    if not token():
        sys.exit("No Typeform token. Set $env:TYPEFORM_API_TOKEN first.")
    conn = sqlite3.connect(DATABASE_FILE)
    setup(conn, [(2026, 2, SURVEY_2_FORM_ID), (2026, 3, SURVEY_3_FORM_ID)])
    for year, survey, fid in conn.execute("select year, survey_no, form_id from survey_forms order by year, survey_no").fetchall():
        r = requests.get("%s/%s/responses" % (API, fid), headers={"Authorization": "Bearer " + token()}, params={"page_size": 1000}, timeout=30)
        if r.status_code == 401:
            sys.exit("401: this token cannot read responses. Create one with 'Responses: read'.")
        r.raise_for_status()
        items = r.json().get("items", [])
        if len(items) >= 1000:
            print("WARNING: 1000 responses returned, pagination needed")
        tally = {}
        for it in items:
            k = ingest_response(conn, year, survey, fid, it)
            tally[k] = tally.get(k, 0) + 1
        conn.commit()
        print("%d survey %d: fetched %d -> %s" % (year, survey, len(items), tally or "nothing new"))
    conn.close()


def watch(minutes):
    while True:
        print(time.strftime("[%Y-%m-%d %H:%M:%S]"), "syncing...")
        try:
            sync()
        except SystemExit as e:
            print(e)
        except Exception as e:
            print("sync error:", e)
        time.sleep(minutes * 60)


def reset_sent(year):
    conn = sqlite3.connect(DATABASE_FILE)
    n = conn.execute("update candidate_mapping_%d set survey_2_sent_date=NULL where survey_2_sent_date is not null" % year).rowcount
    conn.commit()
    print("Cleared survey_2_sent_date for %d bootcampers" % n)


def selftest():
    import tempfile
    tmp = os.path.join(tempfile.gettempdir(), "pa_typeform_selftest.db")
    if os.path.exists(tmp): os.remove(tmp)
    c = sqlite3.connect(tmp)
    c.execute("create table candidate_mapping_2026 (candidate_id text)")
    c.execute("insert into candidate_mapping_2026 values ('PA-1')")
    c.execute("create table mid_bootcamp_2026 (candidate_id text primary key)")
    c.execute("create table post_bootcamp_2026 (candidate_id text primary key, universities_accepted text, universities_applied text, final_choice text, bootcamp_impact_final text, most_valuable_element text)")
    setup(c, [(2026, 3, "FORM3")])
    ref = {v: k for k, v in SEED[3].items()}
    def fake(rid, cid, when, offers, accepted):
        a = [{"type": "choice", "field": {"ref": ref["received_offers"]}, "choice": {"label": offers}}]
        if accepted:
            a.append({"type": "choices", "field": {"ref": ref["universities_accepted"]}, "choices": {"labels": accepted}})
        return {"response_id": rid, "submitted_at": when, "hidden": {"candidate_id": cid} if cid else {}, "answers": a}
    row = lambda: c.execute("select received_offers, universities_accepted from post_bootcamp_2026 where candidate_id='PA-1'").fetchone()
    bad = 0
    def check(name, got, want):
        nonlocal bad
        ok = got == want; bad += (not ok)
        print(("PASS  " if ok else "FAIL  ") + name + ("" if ok else "  got %r want %r" % (got, want)))
    check("first submission saved", ingest_response(c, 2026, 3, "FORM3", fake("r1", "PA-1", "2027-04-01T10:00:00Z", "Yes", ["Oxford", "Harvard"])), "saved")
    check("  stored values", row(), ("Yes", "Oxford | Harvard"))
    check("same submission again is ignored", ingest_response(c, 2026, 3, "FORM3", fake("r1", "PA-1", "2027-04-01T10:00:00Z", "Yes", ["Oxford"])), "duplicate")
    check("resubmission saved", ingest_response(c, 2026, 3, "FORM3", fake("r2", "PA-1", "2027-04-05T10:00:00Z", "No", [])), "saved")
    check("  latest answers replace old ones", row(), ("No", None))
    check("  history keeps both", c.execute("select count(*) from survey_responses").fetchone()[0], 2)
    check("older late-arriving submission does not override", (ingest_response(c, 2026, 3, "FORM3", fake("r0", "PA-1", "2027-03-30T10:00:00Z", "Yes", ["Yale"])), row()), ("saved", ("No", None)))
    check("unknown candidate rejected", ingest_response(c, 2026, 3, "FORM3", fake("r3", "PA-999", "2027-04-06T10:00:00Z", "Yes", [])), "unknown_candidate")
    check("missing candidate_id skipped", ingest_response(c, 2026, 3, "FORM3", fake("r4", None, "2027-04-06T10:00:00Z", "Yes", [])), "skipped")
    print("\nALL PASS" if not bad else "\n%d CHECK(S) FAILED" % bad)
    c.close(); os.remove(tmp)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "sync"
    if cmd == "sync": sync()
    elif cmd == "watch": watch(float(sys.argv[2]) if len(sys.argv) > 2 else 5)
    elif cmd == "reset-sent": reset_sent(int(sys.argv[2]))
    elif cmd == "selftest": selftest()
    else: print("usage: typeform_sync.py [sync | watch MINUTES | reset-sent YEAR | selftest]")
