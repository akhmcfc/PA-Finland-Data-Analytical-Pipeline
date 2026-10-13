import os, sys, csv, json, shutil, sqlite3, tempfile, datetime
sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(os.getcwd(), "scripts"))
import config.config as cc
REAL = cc.DATABASE_FILE
tmp = os.path.join(tempfile.gettempdir(), "pa_e2e.db")
shutil.copy(REAL, tmp)
cc.DATABASE_FILE = tmp
fails = 0
def check(name, ok, detail=""):
    global fails
    fails += (not ok)
    print(("PASS  " if ok else "FAIL  ") + name + ((" | " + str(detail)) if (detail and not ok) else ""))
def info(m): print("INFO  " + m)

print("== 1. personal links (real file, no personal data printed) ==")
c = sqlite3.connect(tmp)
ids = {r[0] for r in c.execute("select candidate_id from candidate_mapping_2026")}
lf = "data/processed/2026_personalized_links.csv"
if not os.path.exists(lf):
    check("links file exists", False, lf)
else:
    rows = list(csv.DictReader(open(lf, encoding="utf-8-sig", newline="")))
    f2, f3 = getattr(cc, "SURVEY_2_FORM_ID", "?"), getattr(cc, "SURVEY_3_FORM_ID", "?")
    check("one link row per bootcamper", len(rows) == len(ids), "%d rows vs %d bootcampers" % (len(rows), len(ids)))
    check("no duplicate candidate IDs", len({r.get("candidate_id") for r in rows}) == len(rows))
    check("every ID exists in the database", all(r.get("candidate_id") in ids for r in rows))
    check("Survey 2 links point to the Survey 2 form and carry the student's ID",
          all(f2 in (r.get("survey2_link") or "") and ("candidate_id=" + (r.get("candidate_id") or "?")) in (r.get("survey2_link") or "") for r in rows))
    check("Survey 3 links point to the Survey 3 form and carry the student's ID",
          all(f3 in (r.get("survey3_link") or "") and ("candidate_id=" + (r.get("candidate_id") or "?")) in (r.get("survey3_link") or "") for r in rows))
    if rows: info("link shape: " + (rows[0].get("survey2_link") or "").replace(rows[0].get("candidate_id") or "?", "<ID>"))

print("\n== 2. building the app on the temporary database ==")
import typeform_sync as ts
import api.models.acceptance as acc
app = None
try:
    from api import create_app
    app = create_app()
except Exception as e1:
    try:
        src = open("run_api.py", encoding="utf-8").read()
        if "__main__" in src:
            import run_api; app = getattr(run_api, "app", None)
        else: info("run_api.py has no __main__ guard, not importing it")
    except Exception as e2:
        info("could not build the app: %s | %s" % (e1, e2))
check("app built", app is not None)
if app is not None:
    client = app.test_client()
    def api(p):
        r = client.get(p); return r.status_code, (r.get_json(silent=True) or {})
    def survey(n):
        for p in ("/api/multi-year/survey/%d" % n, "/survey/%d" % n):
            code, d = api(p)
            if code == 200: return d
        return None
    def show(d):
        info("responses=%s of %s bootcampers | status=%s | window=%s" % (d.get("responses_count"), d.get("bootcampers_count"), d.get("status"), d.get("window")))
        for ch in d.get("charts") or []: info("  chart '%s': %s" % (ch.get("title"), list(zip(ch.get("labels", []), ch.get("values", [])))))
    def chart_with(d, label):
        for ch in d.get("charts") or []:
            if label in (ch.get("labels") or []): return dict(zip(ch["labels"], ch["values"]))
        return {}
    conn = sqlite3.connect(tmp)
    ts.setup(conn, [(2026, 2, "TEST2"), (2026, 3, "TEST3")])
    ref = {n: {v: k for k, v in ts.SEED[n].items()} for n in (2, 3)}
    TEXT = {"support_needed", "whats_working", "universities_applied", "final_choice", "resources_missing"}
    def resp(rid, cid, when, survey_no, vals):
        A = []
        for col, v in vals.items():
            f = {"ref": ref[survey_no][col]}
            if isinstance(v, list): A.append({"type": "choices", "field": f, "choices": {"labels": v}})
            elif isinstance(v, (int, float)): A.append({"type": "number", "field": f, "number": v})
            elif col in TEXT: A.append({"type": "text", "field": f, "text": v})
            else: A.append({"type": "choice", "field": f, "choice": {"label": v}})
        return {"response_id": rid, "submitted_at": when, "hidden": {"candidate_id": cid}, "answers": A}

    print("\n== 3. Survey 2 tab with test answers ==")
    d0 = survey(2)
    check("Survey 2 endpoint answers", d0 is not None)
    if d0 is not None:
        check("starts empty", d0.get("responses_count") == 0, d0.get("responses_count"))
        cids = [r[0] for r in conn.execute("select candidate_id from candidate_mapping_2026 order by candidate_id limit 3")]
        S2 = {"changed_universities": ["Oxford", "Harvard"], "changed_destination": "No change", "changed_major": ["Law"], "biggest_challenge": "Time management", "resources_used": ["Mentoring", "Workshops"], "support_needed": "test", "whats_working": "test"}
        for i, cid in enumerate(cids):
            ts.ingest_response(conn, 2026, 2, "TEST2", resp("s2-%d" % i, cid, "2026-10-1%dT10:00:00Z" % (i + 1), 2, S2))
        conn.commit()
        d1 = survey(2); show(d1)
        check("3 test replies are counted", d1.get("responses_count") == 3, d1.get("responses_count"))
        m = chart_with(d1, "Harvard")
        check("university answers are charted (Oxford 3, Harvard 3)", m.get("Oxford") == 3 and m.get("Harvard") == 3, m)
        check("completion counts only the 21 students asked", d1.get("bootcampers_count") == 21, d1.get("bootcampers_count"))
        titles = [ch.get("title") for ch in d1.get("charts") or []]
        check("written answers are not charted", not ({"Whats working", "Support needed"} & set(titles)), titles)
        check("written answers are counted instead", {t.get("title") for t in d1.get("text_columns") or []} >= {"Whats working", "Support needed"}, d1.get("text_columns"))
        S2b = dict(S2); S2b["changed_universities"] = ["Yale"]
        ts.ingest_response(conn, 2026, 2, "TEST2", resp("s2-resub", cids[0], "2026-10-20T10:00:00Z", 2, S2b)); conn.commit()
        d2 = survey(2)
        check("a resubmission does not add a second person", d2.get("responses_count") == 3, d2.get("responses_count"))
        m2 = chart_with(d2, "Yale")
        check("latest answers replace the old ones (Oxford 2, Harvard 2, Yale 1)", m2.get("Oxford") == 2 and m2.get("Harvard") == 2 and m2.get("Yale") == 1, m2)
        check("history keeps all 4 submissions", conn.execute("select count(*) from survey_responses where survey_no=2").fetchone()[0] == 4)

    print("\n== 4. Survey 3 and the acceptance rate ==")
    wave = [r[0] for r in conn.execute("select candidate_id from candidate_mapping_2026 where cast(expected_uni_start_year as text)='2027'")]
    tot = conn.execute("select count(*) from candidate_mapping_2026").fetchone()[0]
    if not wave: info("no 2027 starters found, skipped")
    else:
        k = len(wave) * 4 // 7
        for i, cid in enumerate(wave):
            v = {"received_offers": "Yes" if i < k else "No", "universities_applied": "test", "final_choice": "test", "bootcamp_impact_final": 4, "most_valuable_element": ["Mentoring"], "resources_missing": "test"}
            if i < k: v["universities_accepted"] = ["Oxford"]
            ts.ingest_response(conn, 2026, 3, "TEST3", resp("s3-%d" % i, cid, "2027-04-%02dT10:00:00Z" % (1 + i % 28), 3, v))
        conn.commit()
        class FD(datetime.date):
            @classmethod
            def today(cls): return datetime.date(2027, 9, 1)
        acc.date = FD
        exp = "%.1f%%" % (100.0 * k / len(wave))
        code, d = api("/api/multi-year/year/2026/dashboard")
        check("2026 rate = offers / wave size (%d of %d)" % (k, len(wave)), d.get("acceptance_rate") == exp, "got %r want %r" % (d.get("acceptance_rate"), exp))
        check("note says %d of %d bootcampers counted" % (len(wave), tot), ("%d of %d" % (len(wave), tot)) in (d.get("acceptance_note") or d.get("acceptance_rate_note") or ""), d.get("acceptance_rate_note"))
        code, d = api("/api/multi-year/range/dashboard?start_year=2024&end_year=2026")
        check("range 2024-2026 uses the 2026 cohort only", d.get("acceptance_rate") == exp, d.get("acceptance_rate"))
        s3 = survey(3)
        check("Survey 3 endpoint answers", s3 is not None)
        if s3 is not None: show(s3)

    print("\n== 5. privacy of what gets published ==")
    import publish
    for n in (1, 2, 3):
        d = survey(n)
        if d is None: info("survey %d not reachable, skipped" % n); continue
        s = publish.suppress(json.loads(json.dumps(d)))
        left = [(ch.get("title"), l) for ch in s.get("charts") or [] for l, v in zip(ch.get("labels", []), ch.get("values", [])) if v < publish.MIN_COUNT and l != "Other (single answers)"]
        txt = json.dumps(s)
        check("survey %d: no single-answer bars after suppression" % n, not left, left[:3])
        check("survey %d: no email or candidate ID in the data" % n, not (publish.EMAIL.search(txt) or publish.CID.search(txt)))

print("\n== 6. Typeform questions vs the saved mapping (real forms) ==")
tok = os.environ.get("TYPEFORM_API_TOKEN")
if not tok: info("no token in this window, skipped")
else:
    import requests
    real = sqlite3.connect(REAL)
    def walk(fs):
        for f in fs:
            yield f
            sub = (f.get("properties") or {}).get("fields")
            if sub: yield from walk(sub)
    for fid in (cc.SURVEY_2_FORM_ID, cc.SURVEY_3_FORM_ID):
        r = requests.get("https://api.typeform.com/forms/" + fid, headers={"Authorization": "Bearer " + tok}, timeout=30)
        if not r.ok: check("form %s readable" % fid, False, r.status_code); continue
        refs = {f["ref"] for f in walk(r.json().get("fields", [])) if f.get("type") not in ("statement",)}
        mapped = {x[0] for x in real.execute("select ref from survey_field_map where form_id=?", (fid,))}
        check("form %s: every question is mapped" % fid, refs <= mapped, "unmapped questions: %d" % len(refs - mapped))
        check("form %s: no stale mappings" % fid, mapped <= refs, "stale: %d" % len(mapped - refs))

print("\nALL PASS" if not fails else "\n%d CHECK(S) FAILED" % fails)
try: conn.close(); c.close(); os.remove(tmp)
except Exception: pass
