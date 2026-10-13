import os, sys, io, json, re, subprocess, shutil, time, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site"); DATA = os.path.join(SITE, "data")
BASE = "http://localhost:5000"
MIN_COUNT = 2   # survey chart answers given by fewer people are grouped, so nobody can be singled out

def get(path):
    with urllib.request.urlopen(BASE + path, timeout=180) as r:
        return json.loads(r.read().decode("utf-8"))

def save(name, obj):
    with open(os.path.join(DATA, name), "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))

def suppress(d):
    for ch in d.get("charts") or []:
        L, V = ch.get("labels") or [], ch.get("values") or []
        keep = [(l, v) for l, v in zip(L, V) if v >= MIN_COUNT]
        rest = sum(v for l, v in zip(L, V) if v < MIN_COUNT)
        if rest: keep.append(("Other (single answers)", rest))
        ch["labels"], ch["values"] = [k[0] for k in keep], [k[1] for k in keep]
    return d

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"); CID = re.compile(r"\bPA-\d{4}-\d+", re.I)
def scan():
    return [fn for fn in os.listdir(DATA) if (lambda t: EMAIL.search(t) or CID.search(t))(open(os.path.join(DATA, fn), encoding="utf-8").read())]

def export():
    os.makedirs(DATA, exist_ok=True)
    for fn in os.listdir(DATA): os.remove(os.path.join(DATA, fn))
    cfg = get("/api/multi-year/config"); years = cfg["years"]
    save("config.json", cfg); save("years.json", years)
    for y in years: save("year-%d.json" % y, get("/api/multi-year/year/%d/dashboard" % y))
    for a in years:
        for b in years:
            if b >= a: save("range-%d-%d.json" % (a, b), get("/api/multi-year/range/dashboard?start_year=%d&end_year=%d" % (a, b)))
    for n in (1, 2, 3):
        d = None
        for p in ("/api/multi-year/survey/%d" % n, "/survey/%d" % n):
            try: d = get(p); break
            except Exception: pass
        if d is None: print("WARNING: survey %d endpoint not reachable - that tab will show an error" % n); continue
        save("survey-%d.json" % n, suppress(d))
    bad = scan()
    if bad:
        shutil.rmtree(DATA); sys.exit("STOPPED: possible personal data found in %s - nothing published" % bad)
    for f in ("index.html", "survey1.html"): shutil.copy(os.path.join(ROOT, f), os.path.join(SITE, f))
    open(os.path.join(SITE, ".nojekyll"), "w").close()
    print("exported %d data files, privacy check passed" % len(os.listdir(DATA)))

def git(*a, check=False):
    r = subprocess.run(["git"] + list(a), cwd=SITE, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and r.returncode: sys.exit("git %s failed: %s" % (" ".join(a), (r.stderr or r.stdout).strip()))
    return r

def init(url):
    export()
    if not os.path.isdir(os.path.join(SITE, ".git")):
        if git("init", "-b", "main").returncode:
            git("init", check=True); git("checkout", "-B", "main", check=True)
    if git("remote").stdout.split(): git("remote", "set-url", "origin", url, check=True)
    else: git("remote", "add", "origin", url, check=True)
    git("add", "-A", check=True); git("commit", "-m", "Initial dashboard")
    r = git("push", "-u", "origin", "main"); print((r.stdout + r.stderr).strip())

def push():
    export()
    git("add", "-A")
    if not git("status", "--porcelain").stdout.strip():
        print("no changes to publish"); return
    git("commit", "-m", "Update data " + time.strftime("%Y-%m-%d %H:%M"), check=True)
    r = git("push"); print("published" if r.returncode == 0 else "PUSH FAILED: " + (r.stderr or r.stdout).strip())

def watch(minutes):
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    while True:
        print(time.strftime("[%H:%M:%S]"), "cycle")
        if os.environ.get("TYPEFORM_API_TOKEN"):
            try:
                import typeform_sync; typeform_sync.sync()
            except SystemExit as e: print("sync:", e)
            except Exception as e: print("sync error:", e)
        try: push()
        except SystemExit as e: print("publish:", e)
        except Exception as e: print("publish error:", e)
        time.sleep(minutes * 60)

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "export"
    if cmd == "export": export()
    elif cmd == "init": init(sys.argv[2])
    elif cmd == "push": push()
    elif cmd == "watch": watch(float(sys.argv[2]) if len(sys.argv) > 2 else 5)
    else: print("usage: publish.py [export | init REPO_URL | push | watch MINUTES]")
