import csv, datetime, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
src = "data/processed/survey_2_send_list_2026.csv"
if not os.path.exists(src): sys.exit("send list not found - run 12_prepare_survey_2_list.py first")
rows = list(csv.DictReader(open(src, encoding="utf-8-sig", newline="")))
SUBJECT = "Quick check-in on your university applications"
BODY = """Hi {first},

How are your university applications going? As part of the Project Access Finland bootcamp follow-up, we'd like to hear how it's going so we can support you better.

Please fill in this short survey (7 questions):
{link}

It asks which universities and fields you're considering now, what's been hardest, which bootcamp resources helped, and what support you need.

- The link is personal to you, so please don't share it.
- If something changes, you can fill it in again before {deadline}. We'll use your latest answers.
- Results are shown only as group totals, never with your name.

Thank you,
Project Access Finland"""
def nice(d):
    try: return datetime.date.fromisoformat(str(d)[:10]).strftime("%B %d, %Y").replace(" 0", " ")
    except Exception: return str(d)
out = []
for r in rows:
    out.append({"email": r["email"], "subject": SUBJECT,
                "body": BODY.format(first=r.get("first_name", ""), link=r["survey_2_link"], deadline=nice(r.get("send_end", "")))})
with open("data/processed/survey_2_emails.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["email", "subject", "body"]); w.writeheader(); w.writerows(out)
print("emails prepared:", len(out), "-> data\\processed\\survey_2_emails.csv")
print("\nsample (name replaced):\n" + out[0]["body"].replace(rows[0].get("first_name", ""), "Alex", 1).replace(rows[0]["survey_2_link"], "<personal link>") if out else "no students are in their window right now")
