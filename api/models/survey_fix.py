import sqlite3
from config.config import DATABASE_FILE


def _title(col):
    return col.replace("_", " ").capitalize()


def _text_titles():
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        t = {_title(r[0]) for r in conn.execute("select column_name from survey_field_map where kind='text'")}
        conn.close()
        return t
    except Exception:
        return set()


def fix_survey(d, n):
    text = _text_titles()
    charts, notes = [], []
    for ch in d.get("charts") or []:
        title = ch.get("title") or ""
        labels, values = ch.get("labels") or [], ch.get("values") or []
        if title in text:
            notes.append({"title": title, "answers": sum(values)})
            continue
        if any(" | " in str(l) for l in labels):
            agg = {}
            for l, v in zip(labels, values):
                for part in str(l).split(" | "):
                    part = part.strip()
                    if part:
                        agg[part] = agg.get(part, 0) + v
            items = sorted(agg.items(), key=lambda x: -x[1])
            ch["labels"], ch["values"] = [k for k, _ in items], [v for _, v in items]
        charts.append(ch)
    d["charts"] = charts
    if notes:
        seen = {t.get("title") for t in d.get("text_columns") or []}
        d["text_columns"] = (d.get("text_columns") or []) + [t for t in notes if t["title"] not in seen]
    w = d.get("window") or {}
    eligible = (w.get("open") or 0) + (w.get("closed") or 0)
    if eligible:
        resp = d.get("responses_count") or 0
        d["bootcampers_count"] = eligible
        d["status"] = "no_responses" if not resp else ("complete" if resp >= eligible else "in_progress")
    return d
