#!/usr/bin/env python3
"""Remplace les réponses de questions existantes, par identifiant.

Usage : python3 tools/patch.py correctifs.txt
Format : une ligne « @lin-002 », puis la bonne réponse « + … » et 2 à 4 mauvaises « - … ».
"""
import sys, glob, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_patch(p):
    out, cur = {}, None
    for line in open(p, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line.strip(): continue
        if line.startswith("@"):
            cur = line[1:].strip(); out[cur] = []; continue
        assert line[:2] in ("+ ", "- "), line
        out[cur].append(line)
    for k, v in out.items():
        assert sum(1 for l in v if l.startswith("+ ")) == 1, k
        assert 2 <= sum(1 for l in v if l.startswith("- ")) <= 4, k
    return out

patch = load_patch(sys.argv[1]); done = set(); counters = {}
for f in sorted(glob.glob(os.path.join(ROOT, "questions", "*.txt"))):
    lines = open(f, encoding="utf-8").read().split("\n"); out = []; cat = None; i = 0
    while i < len(lines):
        l = lines[i]
        if l.startswith("## "): cat = l[3:].strip()
        if l.startswith("Q: ") or l.startswith("Q!: "):
            counters[cat] = counters.get(cat, 0) + 1
            qid = f"{cat}-{counters[cat]:03d}"
            out.append(l); i += 1
            # recopier l'énoncé multi-ligne éventuel
            while i < len(lines) and not lines[i][:2] in ("+ ", "- "):
                out.append(lines[i]); i += 1
            opts = []
            while i < len(lines) and lines[i][:2] in ("+ ", "- "):
                opts.append(lines[i]); i += 1
            if qid in patch:
                out += patch[qid]; done.add(qid)
            else:
                out += opts
            continue
        out.append(l); i += 1
    open(f, "w", encoding="utf-8").write("\n".join(out))
missing = set(patch) - done
print(f"{len(done)} questions corrigées" + (f" | introuvables : {sorted(missing)}" if missing else ""))
