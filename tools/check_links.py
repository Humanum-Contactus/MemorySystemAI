#!/usr/bin/env python3
"""Vérifie les liens Markdown relatifs du dépôt (fichiers et ancres).

À QUOI SERT CE FICHIER
----------------------
La documentation du projet est un réseau de pages qui se citent (journal,
fiches, protocole, installation). Un lien cassé, c'est un lecteur perdu. Ce
script lit chaque fichier .md, trouve chaque lien [texte](cible) qui pointe
vers un autre fichier du dépôt, et vérifie que le fichier existe et, si le
lien vise un titre précis (#ancre), que ce titre existe.

Outil volontairement simple : bibliothèque standard uniquement, aucun service
en ligne, lisible en quelques minutes.

COMMENT L'ESSAYER
-----------------

Usage : python3 tools/check_links.py   (depuis n'importe où)
Code de sortie 0 si aucun lien cassé. Les liens http(s)/mailto ne sont pas testés.
Ancres calculées comme GitHub (minuscules, ponctuation retirée, espaces → « - »).
"""
from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import unquote

# Racine du dépôt = le dossier parent de tools/.
ROOT = Path(__file__).resolve().parents[1]
# Motifs de recherche (expressions régulières) :
# - LINK : un lien [texte](cible), sans le « ! » des images, titre optionnel ;
# - IMG : une image ![texte](cible) ;
# - HEADING : un titre Markdown « ## Titre ».
LINK = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
IMG = re.compile(r"!\[[^\]]*\]\(([^)\s]+)\)")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")


# Le code entre ``` ``` n'est pas du vrai Markdown : un « [x](y) » écrit
# dans un exemple de code n'est pas un lien. On remplace donc ces lignes par
# des lignes vides (pour garder la numérotation). Dans une ligne normale, un
# morceau `entre accents graves` qui contient « ]( » est aussi retiré ; les
# autres morceaux sont gardés tels quels.
def strip_code(text: str) -> str:
    out, fence = [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fence = not fence
            out.append("")
            continue
        out.append("" if fence else re.sub(r"`[^`]*`", lambda m: m.group(0) if "](" not in m.group(0) else "", line))
    return "\n".join(out)


# Reproduit la façon dont GitHub transforme un titre en ancre :
# « Phase T — En cours » → « phase-t--en-cours ».
# Étapes : 1) un lien dans le titre ne garde que son texte ; 2) minuscules ;
# 3) on ne garde que lettres, chiffres, espaces, « - » et « _ » ;
# 4) chaque espace devient « - ».
def slug(title: str) -> str:
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", title).lower()
    t = "".join(c for c in t if c in " -_" or unicodedata.category(c)[0] in "LN")
    return t.replace(" ", "-")


# Toutes les ancres d'un fichier. Deux titres identiques donnent
# « titre », puis « titre-1 », « titre-2 »… comme sur GitHub.
def anchors(path: Path) -> set:
    seen: dict = {}
    res = set()
    fence = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("```"):
            fence = not fence
            continue
        m = None if fence else HEADING.match(line)
        if m:
            s = slug(m.group(2))
            n = seen.get(s, 0)
            res.add(s if n == 0 else f"{s}-{n}")
            seen[s] = n + 1
    return res


# Étapes : 1) lister les .md (hors .git et .venv) ; 2) pour chaque lien
# relatif, calculer le fichier visé ; 3) vérifier qu'il existe ; 4) vérifier
# l'ancre si besoin ; 5) afficher le bilan. Code 0 = aucun lien cassé.
def main() -> int:
    files = [p for p in ROOT.rglob("*.md") if ".git" not in p.parts and ".venv" not in p.parts]
    broken, total = [], 0
    for md in sorted(files):
        text = strip_code(md.read_text(encoding="utf-8"))
        for m in list(LINK.finditer(text)) + list(IMG.finditer(text)):
            target = m.group(1)
            # Liens externes (http:, https:, mailto:) : non testés, pour rester hors ligne.
            if re.match(r"^[a-z]+:", target):
                continue
            total += 1
            path_part, _, frag = target.partition("#")
            # « #ancre » seule = ancre dans le même fichier.
            dest = md if not path_part else (md.parent / unquote(path_part)).resolve()
            if not dest.exists():
                broken.append(f"{md.relative_to(ROOT)} → {target} (fichier absent)")
                continue
            if frag and dest.is_file() and dest.suffix == ".md":
                if unquote(frag).lower() not in anchors(dest):
                    broken.append(f"{md.relative_to(ROOT)} → {target} (ancre absente)")
    for b in broken:
        print("CASSÉ ", b)
    print(f"{total} lien(s) relatif(s) vérifié(s) dans {len(files)} fichier(s) — {len(broken)} cassé(s)")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
