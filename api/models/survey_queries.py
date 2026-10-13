import sqlite3
from collections import Counter
from datetime import date
from config.config import DATABASE_FILE

TABLES = {1: "pre_bootcamp_2026", 2: "mid_bootcamp_2026", 3: "post_bootcamp_2026"}
SKIP = {"id", "candidate_id", "submitted_at", "response_id", "created_at", "token", "landed_at"}
LIST_HINTS = ("accept", "offer", "reject", "applied")
SCALE_HINTS = ("level", "impact", "confidence", "rating", "score")


def _title(col):
    return col.replace("_", " ").strip().capitalize()


def _label(v, n=60):
    v = " ".join(str(v).split())
    return v if len(v) <= n else v[: n - 3] + "..."


def _numbers(vals):
    out = []
    for v in vals:
        try:
            out.append(float(str(v).strip().replace(",", ".")))
        except ValueError:
            return None
    return out


def _chart(col, counter, limit=15, numeric=False):
    items = list(counter.items())
    if numeric:
        items.sort(key=lambda kv: float(kv[0]))
    else:
        items.sort(key=lambda kv: -kv[1])
        items = items[:limit]
    return {"key": col, "title": _title(col), "labels": [k for k, _ in items], "values": [v for _, v in items]}


def _window(cur, n):
    if n not in (2, 3):
        return None
    cols = [r[1] for r in cur.execute('PRAGMA table_info("candidate_mapping_2026")')]
    a, b = "survey_%d_send_start" % n, "survey_%d_send_end" % n
    if a not in cols or b not in cols:
        return None
    today = date.today().isoformat()
    base = "SELECT COUNT(*) FROM candidate_mapping_2026 WHERE "
    return {
        "open": cur.execute(base + "%s <= ? AND %s >= ?" % (a, b), (today, today)).fetchone()[0],
        "upcoming": cur.execute(base + "%s > ?" % a, (today,)).fetchone()[0],
        "closed": cur.execute(base + "%s < ?" % b, (today,)).fetchone()[0],
    }


def get_survey_data(n):
    table = TABLES[n]
    conn = sqlite3.connect(DATABASE_FILE)
    cur = conn.cursor()
    boot = cur.execute("SELECT COUNT(*) FROM candidate_mapping_2026").fetchone()[0]
    cols = [r[1] for r in cur.execute('PRAGMA table_info("%s")' % table)]
    out = {"survey": n, "responses_count": 0, "bootcampers_count": boot, "status": "no_responses",
           "window": _window(cur, n), "charts": [], "numeric": [], "text_columns": []}
    if not cols:
        conn.close()
        return out
    if "candidate_id" in cols:
        resp = cur.execute('SELECT COUNT(DISTINCT candidate_id) FROM "%s" WHERE candidate_id IS NOT NULL' % table).fetchone()[0]
    else:
        resp = cur.execute('SELECT COUNT(*) FROM "%s"' % table).fetchone()[0]
    out["responses_count"] = resp
    if resp == 0:
        conn.close()
        return out
    out["status"] = "complete" if resp >= boot else "in_progress"

    for col in cols:
        if col.lower() in SKIP or col.lower().endswith("_raw"):
            continue
        q = 'SELECT "%s" FROM "%s" WHERE "%s" IS NOT NULL' % (col, table, col)
        vals = [r[0] for r in cur.execute(q) if str(r[0]).strip() != ""]
        if not vals:
            continue
        low = {str(v).strip().lower() for v in vals}
        is_bool = low <= {"0", "1", "true", "false"}
        nums = _numbers(vals)
        scale = any(h in col.lower() for h in SCALE_HINTS)
        if nums is not None and (scale or not is_bool):
            out["numeric"].append({"title": _title(col), "average": round(sum(nums) / len(nums), 2), "n": len(nums)})
            cnt = Counter(str(int(x)) if x.is_integer() else str(x) for x in nums)
            out["charts"].append(_chart(col, cnt, numeric=True))
        elif is_bool:
            cnt = Counter("Yes" if str(v).strip().lower() in ("1", "true") else "No" for v in vals)
            out["charts"].append(_chart(col, cnt))
        elif any(h in col.lower() for h in LIST_HINTS):
            items = []
            for v in vals:
                items += [p.strip() for p in str(v).split(",") if p.strip()]
            out["charts"].append(_chart(col, Counter(items)))
        else:
            distinct = len(set(str(v).strip() for v in vals))
            if distinct <= 12 or distinct <= len(vals) * 0.5:
                out["charts"].append(_chart(col, Counter(_label(v) for v in vals)))
            else:
                out["text_columns"].append({"title": _title(col), "answers": len(vals)})
    conn.close()
    return out
