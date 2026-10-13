#!/usr/bin/env python3
"""Build du QCM : lit questions/*.txt, valide les questions, génère dist/artifact.html et dist/gh/ (PWA hors ligne).

Usage : python3 build.py [version]   (sinon variable QCM_VERSION, sinon « dev »)
"""
import json, re, sys, glob, os, hashlib, shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
VERSION = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("QCM_VERSION", "dev")

CATS = [
    ("lin", "Linux"), ("sysd", "systemd & logs"), ("users", "Comptes & droits"),
    ("disk", "Disques"), ("ssh", "SSH & durcissement"), ("net", "Réseau"),
    ("subnet", "Sous-réseaux"), ("nettroub", "Dépannage réseau"), ("fw", "Pare-feu"),
    ("sec", "Sécurité"), ("crypto", "Cryptographie"), ("soc", "SOC & SIEM"),
    ("virt", "Virtualisation"), ("ceph", "Ceph & stockage"), ("docker", "Docker"),
    ("k8s", "Kubernetes"), ("iac", "Ansible & IaC"), ("sup", "Supervision"),
    ("win", "Windows & AD"), ("endp", "Postes & support"), ("script", "Scripts & API"),
    ("git", "Git"), ("ai", "IA"), ("itil", "ITIL & process"),
    ("lab", "Mes labs"), ("scen", "Scénarios"),
]
CAT_IDS = [c for c, _ in CATS]

def parse(path):
    out, cat, cur = [], None, None
    def flush():
        nonlocal cur
        if cur: out.append(cur)
        cur = None
    for n, raw in enumerate(open(path, encoding="utf-8"), 1):
        line = raw.rstrip("\n")
        if not line.strip():
            continue
        where = f"{os.path.basename(path)}:{n}"
        if line.startswith("## "):
            flush(); cat = line[3:].strip(); continue
        if line.startswith("Q: ") or line.startswith("Q!: "):
            flush()
            cur = {"c": cat, "q": line.split(": ", 1)[1], "ok": [], "ko": [], "e": "", "at": where,
                   "f": line.startswith("Q!")}
            continue
        if cur is None:
            sys.exit(f"{where}: ligne hors question: {line}")
        if line.startswith("+ "): cur["ok"].append(line[2:])
        elif line.startswith("- "): cur["ko"].append(line[2:])
        elif line.startswith("E: "): cur["e"] = line[3:]
        elif cur["e"]: cur["e"] += "\n" + line          # suite d'explication
        else: cur["q"] += "\n" + line                   # suite d'énoncé (bloc de code)
    flush()
    return out

def main():
    items = []
    for f in sorted(glob.glob(os.path.join(ROOT, "questions", "*.txt"))):
        items += parse(f)
    errs, seen_q, counters, questions = [], {}, {}, []
    for it in items:
        w = it["at"]
        if it["c"] not in CAT_IDS: errs.append(f"{w}: thème inconnu {it['c']}")
        if len(it["ok"]) != 1: errs.append(f"{w}: {len(it['ok'])} bonne(s) réponse(s)")
        if not 2 <= len(it["ko"]) <= 4: errs.append(f"{w}: {len(it['ko'])} mauvaises réponses")
        if not it["e"]: errs.append(f"{w}: pas d'explication")
        opts = it["ok"] + it["ko"]
        if len(set(opts)) != len(opts): errs.append(f"{w}: réponses en double")
        for o in opts:
            if re.search(r"(toutes|aucune) (les|des) réponses", o, re.I): errs.append(f"{w}: option interdite « {o} »")
        key = re.sub(r"\W+", " ", it["q"].lower()).strip()
        if key in seen_q: errs.append(f"{w}: question en double avec {seen_q[key]}")
        seen_q[key] = w
        counters[it["c"]] = counters.get(it["c"], 0) + 1
        q = {"id": f"{it['c']}-{counters[it['c']]:03d}", "c": it["c"], "q": it["q"], "a": opts, "e": it["e"]}
        if it["f"]: q["f"] = 1
        questions.append(q)
    if errs:
        print("\n".join(errs)); sys.exit(1)

    # Biais « la bonne réponse est la plus longue »
    # (nettement plus longue que toutes les autres ; le hasard donnerait environ 25 %)
    longest = sum(1 for q in questions if len(q["a"][0]) > max(len(x) for x in q["a"][1:]) + 5)
    by_cat = {c: counters.get(c, 0) for c in CAT_IDS}
    print(f"{len(questions)} questions | bonne réponse nettement la plus longue : {longest} ({100*longest//len(questions)} %)")
    print("  " + "  ".join(f"{c}:{n}" for c, n in by_cat.items()))
    empty = [c for c, n in by_cat.items() if n == 0]
    cats = [{"id": c, "name": n} for c, n in CATS if c not in empty]

    data = {"version": VERSION, "cats": cats, "questions": questions}
    js = "window.QCM_DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";"
    js = js.replace("</", "<\\/")
    tpl = open(os.path.join(ROOT, "src", "app.html"), encoding="utf-8").read()
    assert "/*__DATA__*/" in tpl and "/*__SW__*/" in tpl
    page = tpl.replace("/*__DATA__*/", js)

    dist = os.path.join(ROOT, "dist"); gh = os.path.join(dist, "gh")
    shutil.rmtree(dist, ignore_errors=True); os.makedirs(gh)
    open(os.path.join(dist, "artifact.html"), "w", encoding="utf-8").write(page.replace("/*__SW__*/", ""))

    # ---------- Version GitHub Pages : document complet + PWA ----------
    sw_reg = ("if ('serviceWorker' in navigator) { window.addEventListener('load', function () {"
              " navigator.serviceWorker.register('sw.js').catch(function () {}); }); }")
    body = page.replace("/*__SW__*/", sw_reg)
    head = ('<!doctype html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '<meta name="theme-color" content="#0e6a70">\n'
            '<meta name="apple-mobile-web-app-capable" content="yes">\n'
            '<meta name="mobile-web-app-capable" content="yes">\n'
            '<meta name="apple-mobile-web-app-status-bar-style" content="default">\n'
            '<meta name="apple-mobile-web-app-title" content="Révisions">\n'
            '<link rel="manifest" href="manifest.webmanifest">\n'
            '<link rel="apple-touch-icon" href="icon-180.png">\n'
            '<link rel="icon" href="icon-192.png">\n'
            '<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}'
            'body{margin:0;font:14px/1.4 system-ui,-apple-system,sans-serif}[hidden]{display:none!important}</style>\n')
    # <title> et <style> du gabarit vont dans <head>, le reste dans <body>
    m = re.match(r"\s*(<title>.*?</title>\s*<style>.*?</style>)(.*)", body, re.S)
    full = head + m.group(1) + "\n</head>\n<body>\n" + m.group(2) + "\n</body>\n</html>\n"
    open(os.path.join(gh, "index.html"), "w", encoding="utf-8").write(full)

    manifest = {"name": "Révisions Admin SecOps", "short_name": "Révisions", "lang": "fr",
                "start_url": "./", "scope": "./", "display": "standalone",
                "background_color": "#eef2f5", "theme_color": "#0e6a70",
                "icons": [{"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
                          {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"},
                          {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}]}
    json.dump(manifest, open(os.path.join(gh, "manifest.webmanifest"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    make_icons(gh)
    files = ["./", "index.html", "manifest.webmanifest", "icon-180.png", "icon-192.png", "icon-512.png"]
    h = hashlib.sha256(full.encode()).hexdigest()[:10]
    sw = f"""// Cache hors ligne : tout est mis en cache à l'installation, puis servi depuis le cache.
const CACHE = 'revisions-{VERSION}-{h}';
const FILES = {json.dumps(files)};
self.addEventListener('install', e => {{ e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)).then(() => self.skipWaiting())); }});
self.addEventListener('activate', e => {{ e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())); }});
self.addEventListener('fetch', e => {{
  if (e.request.method !== 'GET') return;
  // Page : le cache répond tout de suite (pas d'attente sur un réseau de train),
  // puis la version en ligne est récupérée en arrière-plan pour la prochaine ouverture
  if (e.request.mode === 'navigate') {{
    const net = fetch(e.request).then(r => {{ if (r.ok) {{ const copy = r.clone(); caches.open(CACHE).then(c => c.put('./', copy)); }} return r; }});
    e.respondWith(caches.match('./').then(r => r || net).catch(() => net));
    e.waitUntil(net.catch(() => {{}}));
    return;
  }}
  e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
}});
"""
    open(os.path.join(gh, "sw.js"), "w").write(sw)
    open(os.path.join(gh, ".nojekyll"), "w").write("")
    print("OK ->", dist, "| artifact", os.path.getsize(os.path.join(dist, "artifact.html")) // 1024, "Ko")

def make_icons(gh):
    from PIL import Image, ImageDraw, ImageFont
    def font(sz):
        for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                  "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"]:
            if os.path.exists(p): return ImageFont.truetype(p, sz)
        return ImageFont.load_default(sz)
    for s in (180, 192, 512):
        im = Image.new("RGB", (s, s), "#0e6a70"); d = ImageDraw.Draw(im)
        # case à cocher stylisée + prompt
        pad = s * 0.22; r = s * 0.08
        d.rounded_rectangle([pad, pad, s - pad, s - pad], radius=r, outline="#ffffff", width=max(4, s // 28))
        d.line([(s*.34, s*.52), (s*.46, s*.64), (s*.68, s*.38)], fill="#ffd166", width=max(6, s // 14), joint="curve")
        f = font(int(s * .11)); txt = "QCM"
        w = d.textlength(txt, font=f); d.text(((s - w) / 2, s * .80), txt, fill="#ffffff", font=f)
        im.save(os.path.join(gh, f"icon-{s}.png"))

if __name__ == "__main__":
    main()
