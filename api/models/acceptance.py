import re, sqlite3
from datetime import date, datetime
from config.config import DATABASE_FILE

NO_OFFER = {"", "none", "no", "n/a", "na", "-", "0", "nothing", "no offers"}


def _cols(cur, table):
    return [r[1] for r in cur.execute('PRAGMA table_info("%s")' % table)]


def _offer(v):
    s = str(v or "").strip().lower()
    return bool(s) and s not in NO_OFFER and not s.startswith(("none", "no ", "not yet", "ei ", "en ", "n/a", "nothing"))


def span(ys):
    ys = sorted(ys)
    if len(ys) == 1:
        return str(ys[0])
    if ys == list(range(ys[0], ys[-1] + 1)):
        return "%d-%d" % (ys[0], ys[-1])
    return ", ".join(str(y) for y in ys)


def year_config():
    live, hist = [], []
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        for (n,) in conn.execute("SELECT name FROM sqlite_master WHERE type='table'"):
            m = re.fullmatch(r"candidate_mapping_(\d{4})", n)
            if m: live.append(int(m.group(1)))
            m = re.fullmatch(r"bootcampers_(\d{4})", n)
            if m: hist.append(int(m.group(1)))
        conn.close()
    except Exception:
        pass
    live = sorted(set(live))
    hist = sorted(y for y in set(hist) if y not in live)
    return {"live": live, "historical": hist, "years": sorted(set(live + hist))}


def _d(v):
    if not v:
        return None
    s = str(v).strip()[:10]
    for f in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, f).date()
        except Exception:
            pass
    return None


def _find(cols, name):
    return next((c for c in cols if c.lower() == name), None)


def _lab(y, w):
    return "%d (%s starters)" % (y, w) if w != "all" else str(y)


def live_years_summary(years):
    """Per cohort year. Bootcampers are grouped into waves by expected_uni_start_year.
    A wave is counted once its Survey 3 window has closed (or everyone in it responded).
    Rate = offers / all bootcampers selected in the counted waves."""
    out = []
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cur = conn.cursor()
        today = date.today()
        for y in years:
            mt, pt = "candidate_mapping_%d" % y, "post_bootcamp_%d" % y
            try:
                mc = _cols(cur, mt)
            except Exception:
                continue
            if not mc:
                continue
            uc, sc, ec = _find(mc, "expected_uni_start_year"), _find(mc, "survey_3_send_start"), _find(mc, "survey_3_send_end")
            sel = ", ".join(['"candidate_id"'] + ['"%s"' % c if c else "NULL" for c in (uc, sc, ec)])
            members = {}
            for cid, w, s0, e0 in cur.execute('SELECT %s FROM "%s"' % (sel, mt)).fetchall():
                members[cid] = (str(w) if w not in (None, "") else "all", _d(s0), _d(e0))
            seen = {}
            try:
                pc = _cols(cur, pt)
                col = next((c for c in ("universities_accepted", "acceptances_received", "offers_received", "offers") if c in pc), None)
                sel2 = ', "%s"' % col if col else ", NULL"
                for cid, v in cur.execute('SELECT candidate_id%s FROM "%s"' % (sel2, pt)).fetchall():
                    if cid in members:
                        seen[cid] = seen.get(cid, False) or _offer(v)
            except Exception:
                pass
            waves, ends, starts = {}, {}, []
            for cid, (w, s0, e0) in members.items():
                W = waves.setdefault(w, {"wave": w, "bootcampers": 0, "responses": 0, "with_offer": 0})
                W["bootcampers"] += 1
                if cid in seen:
                    W["responses"] += 1
                    W["with_offer"] += int(seen[cid])
                if e0 and (w not in ends or e0 > ends[w]):
                    ends[w] = e0
                if s0:
                    starts.append(s0)
            wl = []
            for w in sorted(waves):
                W = waves[w]
                W["complete"] = W["responses"] > 0 and (W["responses"] >= W["bootcampers"] or (w in ends and today > ends[w]))
                wl.append(W)
            boot = sum(W["bootcampers"] for W in wl)
            resp = sum(W["responses"] for W in wl)
            offers = sum(W["with_offer"] for W in wl)
            done = [W for W in wl if W["complete"]]
            todo = [W for W in wl if not W["complete"]]
            cb = sum(W["bootcampers"] for W in done)
            co = sum(W["with_offer"] for W in done)
            cl = [_lab(y, W["wave"]) for W in done]
            pl = [_lab(y, W["wave"]) for W in todo]
            if wl and not todo:
                status, detail = "completed", "Completed (full cohort)"
            elif done:
                status = "in_progress"
                detail = "%s counted (%d of %d bootcampers); %s pending" % (", ".join(cl), cb, boot, ", ".join(pl))
            elif resp > 0 or (starts and today >= min(starts)):
                status, detail = "in_progress", "Survey 3 in progress"
            else:
                status, detail = "not_started", "Awaiting Survey 3"
            out.append({"year": y, "status": status, "detail": detail, "bootcampers": boot, "responses": resp,
                        "with_offer": offers, "counted_bootcampers": cb, "counted_offers": co,
                        "counted_labels": cl, "pending": pl, "waves": wl})
        conn.close()
    except Exception:
        pass
    return out


def _yes(v):
    return str(v or "").strip().lstrip("* ").lower().startswith(("yes", "kyll"))


def outcomes_by_year(years):
    cfg = year_config()
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cur = conn.cursor()
        low = {c.lower(): c for c in _cols(cur, "outcomes_all_years")}
        ycol = next((low[k] for k in ("year", "cohort_year", "cohort", "bootcamp_year") if k in low), None)
        ecol, ocol, scol = low.get("email"), low.get("received_offer_abroad"), low.get("studying_abroad")
        if not ocol:
            conn.close(); return None
        sel = ", ".join('"%s"' % c if c else "NULL" for c in (ecol, ycol, ocol, scol))
        rows = cur.execute("SELECT %s FROM outcomes_all_years" % sel).fetchall()
        email_year, boots = {}, {}
        for y in cfg["historical"]:
            t = "bootcampers_%d" % y
            try:
                c2 = _cols(cur, t)
                ec = next((c for c in c2 if c.lower() == "email"), None)
                boots[y] = cur.execute('SELECT COUNT(*) FROM "%s"' % t).fetchone()[0]
                if ec:
                    for (e,) in cur.execute('SELECT "%s" FROM "%s"' % (ec, t)):
                        if e: email_year.setdefault(str(e).strip().lower(), y)
            except Exception:
                pass
        conn.close()
        per = {y: {"year": y, "bootcampers": boots.get(y, 0), "responses": 0, "with_offer": 0, "studying_abroad": 0} for y in years}
        seen, unattr = set(), 0
        for i, (e, yv, off, stu) in enumerate(rows):
            e = str(e).strip().lower() if e else ""
            y = None
            if yv is not None:
                m = re.search(r"(20\d\d)", str(yv))
                y = int(m.group(1)) if m else None
            if y is None: y = email_year.get(e)
            if y is None: unattr += 1; continue
            if y not in per: continue
            key = (e or "row%d" % i, y)
            if key in seen: continue
            seen.add(key)
            p = per[y]; p["responses"] += 1; p["with_offer"] += int(_yes(off)); p["studying_abroad"] += int(_yes(stu))
        ys = [per[y] for y in sorted(per)]
        boot = sum(p["bootcampers"] for p in ys); resp = sum(p["responses"] for p in ys)
        return {"years": ys, "bootcampers": boot, "responses": resp,
                "with_offer": sum(p["with_offer"] for p in ys),
                "studying_abroad": sum(p["studying_abroad"] for p in ys),
                "response_rate": ("%.1f%%" % (100.0 * resp / boot)) if boot else None,
                "unattributed": unattr}
    except Exception:
        return None
