#!/usr/bin/env python3
"""Score de base CVSS v3.1 depuis un vecteur. Usage : python3 cvss31.py 'AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N'"""
import math, sys

W = {"AV": {"N": .85, "A": .62, "L": .55, "P": .2}, "AC": {"L": .77, "H": .44},
     "UI": {"N": .85, "R": .62}, "CIA": {"H": .56, "L": .22, "N": 0}}

def roundup(x):
    i = round(x * 100000)
    return i / 100000.0 if i % 10000 == 0 else (math.floor(i / 10000) + 1) / 10.0

def score(vector):
    m = dict(p.split(":") for p in vector.removeprefix("CVSS:3.1/").split("/"))
    changed = m["S"] == "C"
    pr = {"N": .85, "L": .68 if changed else .62, "H": .5 if changed else .27}[m["PR"]]
    iss = 1 - (1 - W["CIA"][m["C"]]) * (1 - W["CIA"][m["I"]]) * (1 - W["CIA"][m["A"]])
    impact = 7.52 * (iss - .029) - 3.25 * (iss - .02) ** 15 if changed else 6.42 * iss
    expl = 8.22 * W["AV"][m["AV"]] * W["AC"][m["AC"]] * pr * W["UI"][m["UI"]]
    if impact <= 0: return 0.0
    return roundup(min(1.08 * (impact + expl), 10)) if changed else roundup(min(impact + expl, 10))

def label(s):
    return "Aucune" if s == 0 else "Faible" if s < 4 else "Moyenne" if s < 7 else "Élevée" if s < 9 else "Critique"

if __name__ == "__main__":
    s = score(sys.argv[1]); print(f"{s} ({label(s)})")
