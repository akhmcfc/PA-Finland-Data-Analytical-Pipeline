import shutil
SHIM = r"""<script>/*PA-STATIC-SHIM*/(function(){
  if(/^(localhost|127\.0\.0\.1)$/.test(location.hostname)) return;
  var of=window.fetch.bind(window);
  window.fetch=function(u,o){
    var s=String(u&&u.url?u.url:u),m,t=null;
    if((m=s.match(/\/year\/(\d{4})\/dashboard/))) t='data/year-'+m[1]+'.json';
    else if((m=s.match(/\/range\/dashboard\?start_year=(\d{4})&end_year=(\d{4})/))) t='data/range-'+m[1]+'-'+m[2]+'.json';
    else if(/\/multi-year\/config/.test(s)) t='data/config.json';
    else if(/\/years\/available/.test(s)) t='data/years.json';
    else if((m=s.match(/\/survey\/(\d)(?:\D|$)/))) t='data/survey-'+m[1]+'.json';
    if(!t) return of(u,o);
    return of(t,{cache:'no-store'});
  };
})();</script>"""
for f in ("index.html", "survey1.html"):
    s = open(f, encoding="utf-8").read()
    if "PA-STATIC-SHIM" in s: print(f, "already has the shim"); continue
    if s.count("</head>") != 1: print(f, "NOT patched: </head> not found once"); continue
    shutil.copy(f, f + ".before-static.backup")
    open(f, "w", encoding="utf-8", newline="\n").write(s.replace("</head>", SHIM + "</head>"))
    print(f, "patched")
