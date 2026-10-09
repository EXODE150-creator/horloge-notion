"""Construit le dossier PDF : couverture + corps numéroté, sommaire rempli automatiquement.
Usage : python3 construire.py   (nécessite Playwright/Chromium, pypdf, pdfplumber)"""
import os, re, subprocess, tempfile
import pdfplumber
from pypdf import PdfReader, PdfWriter

ICI = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(ICI, "La-Table-Commune-dossier-maire.pdf")
NODE_ENV = dict(os.environ, NODE_PATH=subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip())

# Titre de chaque section tel qu'il apparaît en tête de page (sec-num), pour retrouver sa page.
REPERES = {
    "s1": "01 · LE PROJET EN UNE PAGE", "s2": "02 · POURQUOI CE PROJET", "s3": "03 · SAINT-JEAN-D'HEURS AUJOURD'HUI",
    "s4": "04 · COMMENT ÇA MARCHE", "s5": "05 · LES SIX PRODUCTIONS", "s6": "06 · LES TERRES NÉCESSAIRES",
    "s7": "07 · LE TRAVAIL NÉCESSAIRE", "s8": "08 · QUELLE ORGANISATION JURIDIQUE", "s9": "09 · LES RÈGLES À RESPECTER",
    "s10": "10 · BUDGET ET FINANCEMENT", "s11": "11 · LE CALENDRIER", "s12": "12 · GOUVERNANCE ET PARTICIPATION",
    "s13": "13 · RISQUES ET RÉPONSES", "s14": "14 · ILS L'ONT DÉJÀ FAIT", "s15": "15 · CE QUE NOUS DEMANDONS AU MAIRE",
    "aA": "ANNEXE A · CALCULS", "aB": "ANNEXE B · INVENTAIRE", "aC": "ANNEXE C · SIGLES",
}

def rendre(html, pdf, pied=False):
    cmd = ["node", os.path.join(ICI, "render.js"), html, pdf] + (["--pied"] if pied else [])
    subprocess.run(cmd, check=True, env=NODE_ENV)

def norm(t):
    return re.sub(r"\s+", " ", t.replace(" ", " ").replace("’", "'")).upper()

with tempfile.TemporaryDirectory() as tmp:
    source = open(os.path.join(ICI, "dossier.html"), encoding="utf-8").read()
    brouillon = os.path.join(ICI, "_brouillon.html")
    # 1er passage : numéros provisoires de même largeur pour ne pas changer la mise en page
    open(brouillon, "w", encoding="utf-8").write(re.sub(r"__P_\w+__", "00", source))
    rendre(brouillon, os.path.join(tmp, "corps1.pdf"), pied=True)
    pages = {}
    with pdfplumber.open(os.path.join(tmp, "corps1.pdf")) as doc:
        textes = [norm(p.extract_text() or "") for p in doc.pages]
    # La synthèse (s1) suit le sommaire ; on ne cherche les autres sections qu'à partir d'elle.
    debut = next(i for i, t in enumerate(textes) if norm(REPERES["s1"]) in t)
    for i, texte in enumerate(textes[debut:], start=debut + 1):
        for cle, rep in REPERES.items():
            if cle not in pages and norm(rep) in texte:
                pages[cle] = i
    manquants = [k for k in REPERES if k not in pages]
    if manquants:
        raise SystemExit(f"Sections introuvables : {manquants}")
    # 2e passage avec les vrais numéros
    final = re.sub(r"__P_(\w+)__", lambda m: str(pages[m.group(1)]), source)
    open(brouillon, "w", encoding="utf-8").write(final)
    rendre(brouillon, os.path.join(tmp, "corps.pdf"), pied=True)
    os.remove(brouillon)
    rendre(os.path.join(ICI, "couverture.html"), os.path.join(tmp, "couv.pdf"))

    w = PdfWriter()
    for f in ("couv.pdf", "corps.pdf"):
        for p in PdfReader(os.path.join(tmp, f)).pages:
            w.add_page(p)
    w.add_metadata({"/Title": "La Table Commune — Dossier de présentation", "/Subject": "Projet d'alimentation communautaire gratuite, Saint-Jean-d'Heurs (63190)"})
    with open(SORTIE, "wb") as fh:
        w.write(fh)
    print("Pages des sections :", pages)
    print("PDF :", SORTIE, "-", len(PdfReader(SORTIE).pages), "pages")
