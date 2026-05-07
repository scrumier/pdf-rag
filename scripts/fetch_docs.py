"""
Télécharge des fiches techniques réelles (Rockwool, Knauf) et génère des PDFs
synthétiques réalistes pour constituer un corpus de ~80 documents.
Usage: uv run python scripts/fetch_docs.py
"""
import os
import urllib.request
import urllib.error
import random
from fpdf import FPDF, XPos, YPos

DOCS_DIR = "demo_docs"
os.makedirs(DOCS_DIR, exist_ok=True)

# ─── PDFs réels à télécharger ───────────────────────────────────────────────

REAL_DOCS = [
    # Rockwool — fiches techniques (URLs stables siteassets)
    ("rockwool-rocksono-base.pdf",    "https://www.rockwool.com/siteassets/rw-bnl/downloads-fr/downloads/fiches-techniques/cloison/fiche-technique-rocksono-base-fr.pdf"),
    ("rockwool-rocksono-extra.pdf",   "https://www.rockwool.com/siteassets/rw-bnl/downloads-fr/downloads/fiches-techniques/cloison/fiche-technique-rocksono-extra-fr.pdf"),
    ("rockwool-rocksono-solid.pdf",   "https://www.rockwool.com/siteassets/rw-bnl/downloads-fr/downloads/fiches-techniques/cloison/fiche-technique-rocksono-solid-fr.pdf"),
    ("rockwool-rockfit-premium.pdf",  "https://www.rockwool.com/syssiteassets/rw-bnl/downloads-fr/downloads/fiches-techniques/facade/fiche-technique-rockfit-premium-silver-fr.pdf"),
    ("rockwool-rockfit-fulfill.pdf",  "https://www.rockwool.com/siteassets/rw-bnl/downloads-fr/downloads/fiches-techniques/laine-a-insuffler/fiche-technique-rockfit-fulfill-fr.pdf"),
    ("rockwool-rockroof-flexi.pdf",   "https://www.rockwool.com/syssiteassets/rw-bnl/downloads-fr/downloads/fiches-techniques/toiture-inclinee/fiche-technique-rockroof-flexi-plus-fr.pdf"),
    ("rockwool-klimarock.pdf",        "https://www.rockwool.com/syssiteassets/rw-bnl/downloads-fr/downloads/fiches-techniques/isolation-technique/fiche-technique-rockwool-klimarock-fr.pdf"),
    ("rockwool-810.pdf",              "https://www.rockwool.com/syssiteassets/rw-bnl/downloads-fr/downloads/fiches-techniques/isolation-technique/fiche-technique-rockwool-810-fr.pdf"),
    ("rockwool-rockfeu-rei120.pdf",   "https://www.rockwool.com/syssiteassets/rw-f/telechargements/fiches-produits/rockwool_fp_rockfeu_rei_120_rsd.pdf"),
    ("rockwool-rocksono-base-next.pdf","https://www.rockwool.com/syssiteassets/rw-bnl/downloads-fr/downloads/fiches-techniques/cloison/fiche-technique-rocksono-base-fr.pdf"),
]

def download_real_docs():
    downloaded = []
    failed = []
    headers = {"User-Agent": "Mozilla/5.0 (compatible; research-bot/1.0)"}
    for filename, url in REAL_DOCS:
        dest = os.path.join(DOCS_DIR, filename)
        if os.path.exists(dest):
            print(f"  [skip] {filename} (déjà présent)")
            downloaded.append(filename)
            continue
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
            if len(data) < 1000 or not data.startswith(b"%PDF"):
                raise ValueError(f"Contenu invalide ({len(data)} octets)")
            with open(dest, "wb") as f:
                f.write(data)
            print(f"  [OK] {filename} ({len(data)//1024} KB)")
            downloaded.append(filename)
        except Exception as e:
            print(f"  [FAIL] {filename}: {e}")
            failed.append(filename)
    return downloaded, failed


# ─── Génération synthétique ─────────────────────────────────────────────────

def _safe(text: str) -> str:
    return text.replace("°", " deg").replace("µ", "mu").replace("²", "2").replace("³", "3")


def pdf(filename, title, sections):
    p = FPDF()
    p.add_page()
    p.set_font("Helvetica", "B", 14)
    p.cell(0, 10, _safe(title), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    p.ln(2)
    for heading, lines in sections:
        p.set_font("Helvetica", "B", 11)
        p.cell(0, 8, _safe(heading), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        p.set_font("Helvetica", size=9)
        for line in lines:
            p.multi_cell(190, 5, _safe(line))
        p.ln(2)
    out = os.path.join(DOCS_DIR, filename)
    p.output(out)


ISOLANTS = [
    ("Laine de verre",    "LV",  8.50,  "A1",  "Combles, murs, planchers"),
    ("Laine de roche",    "LR", 10.20,  "A1",  "Murs, toiture, acoustique"),
    ("PSE graphite",      "PSE", 12.00, "E",   "ITE, planchers"),
    ("Polyurethane PIR",  "PIR", 18.50, "F",   "Toiture plate, ITE"),
    ("Ouate de cellulose","OC",  11.00, "D",   "Combles perdus, soufflage"),
    ("Chanvre naturel",   "CH",  14.00, "D",   "Murs ossature bois, bio-source"),
    ("Laine de mouton",   "LM",  16.00, "C",   "Bio-source, murs ossature"),
    ("Verre cellulaire",  "VC",  32.00, "A1",  "Toiture-terrasse, sous-sol"),
]

EPAISSEURS = [40, 60, 80, 100, 120, 140, 160, 200]
REGIONS = ["Ile-de-France", "Auvergne-Rhone-Alpes", "Provence-Alpes-Cote-Azur",
           "Occitanie", "Nouvelle-Aquitaine", "Grand-Est", "Hauts-de-France"]
FOURNISSEURS = ["Isover Saint-Gobain", "Rockwool France", "Knauf Insulation",
                "Ursa France", "Soprema", "Weber Saint-Gobain"]

def gen_product_sheets():
    count = 0
    for mat, code, prix_base, classe_feu, applications in ISOLANTS:
        for ep in EPAISSEURS:
            r = ep / 0.04 if "verre" in mat.lower() or "roche" in mat.lower() else ep / 0.035
            prix = round(prix_base * (ep / 100) * 1.2, 2)
            ref = f"REF-{code}-{ep:03d}"
            filename = f"fiche-produit-{code.lower()}-{ep}mm.pdf"
            pdf(filename, f"Fiche Produit - {mat} {ep}mm", [
                ("Description", [
                    f"Reference: {ref}",
                    f"Materiau: {mat}",
                    f"Epaisseur: {ep} mm",
                    f"Resistance thermique: R = {r:.2f} m2.K/W",
                    f"Classe au feu: {classe_feu}",
                    f"Applications: {applications}",
                    f"Prix indicatif: {prix} EUR/m2 HT",
                    f"Conditionnement: rouleaux ou panneaux selon epaisseur",
                ]),
                ("Performances", [
                    f"Conductivite thermique lambda: 0.032 a 0.040 W/m.K selon densite",
                    f"Resistance a la diffusion de vapeur mu: 1 a 5",
                    f"Indice d'affaiblissement acoustique Rw: 45 a 62 dB selon configuration",
                    f"Certification ACERMI obligatoire pour travaux subventionnes (MaPrimeRenov)",
                ]),
                ("Conditions d'utilisation", [
                    f"Plage de temperature: -50°C a +300°C (selon produit)",
                    f"Humidite relative: utiliser pare-vapeur si HR > 60%",
                    f"Mise en oeuvre par professionnel RGE recommandee pour CEE",
                    f"Stockage a l'abri de l'humidite, duree max 24 mois",
                ]),
                ("Livraison SAMSE", [
                    f"Delai standard: 48h pour commandes passees avant 14h",
                    f"Livraison palette complete offerte a partir de 500 EUR HT",
                    f"Retrait possible dans toutes les agences SAMSE",
                ]),
            ])
            count += 1
    print(f"  Fiches produits isolants: {count} PDFs")
    return count


def gen_procedures():
    procs = [
        ("procedure-commande-urgente", "Procedure Commande Urgente", [
            ("Criteres d'urgence", [
                "Chantier arrete faute de materiau: delai max 4h pour traitement",
                "Intemperies imprevisibles: commande derogee sans validation direction",
                "Validation par responsable agence ou directeur region suffisante",
            ]),
            ("Process", [
                "1. Appel direct au depot central: 04.XX.XX.XX.XX",
                "2. Reference produit + quantite + adresse livraison + code client",
                "3. Accord verbal enregistre, bon de commande a regulariser sous 24h",
                "4. Transport urgent: facturation majoree 25% du cout standard",
            ]),
        ]),
        ("procedure-retour-marchandises", "Procedure Retour et Avoir Marchandises", [
            ("Conditions de retour", [
                "Produit non conforme: retour accepte sans delai sur presentation du BL",
                "Erreur de commande client: retour sous 30 jours, etat neuf obligatoire",
                "Produit endommage a la livraison: reserve sur BL + photos obligatoires",
                "Produits coupes ou entames: aucun retour accepte",
            ]),
            ("Process avoir", [
                "Demande de retour via espace client ou agence",
                "Accord ecrit du responsable commercial sous 48h",
                "Avoir emis sous 5 jours ouvrables apres reception au depot",
                "Avoir deductible sur prochaine commande ou remboursement sur RIB",
            ]),
        ]),
        ("procedure-credit-client", "Procedure Ouverture et Gestion Credit Client", [
            ("Eligibilite", [
                "Entreprise immatriculee depuis > 12 mois",
                "Kbis de moins de 3 mois + derniers bilans comptables",
                "Pas d'incident bancaire sur les 24 derniers mois",
                "Encours initial: 5 000 EUR, extensible sur historique de paiement",
            ]),
            ("Delais de paiement", [
                "Standard: 30 jours fin de mois date de facture",
                "Grands comptes (> 1M EUR/an): negociable 45 jours",
                "Depassement encours: blocage automatique, deblocage par directeur",
            ]),
        ]),
        ("procedure-gestion-non-conformites", "Procedure Gestion Non-Conformites Fournisseurs", [
            ("Detection", [
                "A reception: controle visuel + comparaison bon de commande",
                "Non-conformite quantitative: ecart > 2% ou > 1 unite",
                "Non-conformite qualitative: produit endommage, ref incorrecte",
                "Reserve sur CMR obligatoire pour non-conformite transport",
            ]),
            ("Traitement", [
                "Declaration fournisseur sous 72h par ecrit (email tracable)",
                "Photo systématique, reference lot et date fabrication",
                "Fournisseur propose solution sous 5 jours: remplacement ou avoir",
                "Litige non resolu: escalade direction achats + penalite contractuelle",
            ]),
        ]),
        ("procedure-appel-offres", "Procedure Reponse aux Appels d'Offres", [
            ("Qualification", [
                "Verifier les criteres d'eligibilite: CA, references, certifications",
                "Analyse du DCE sous 48h pour decider de repondre ou non",
                "Seuil de rentabilite minimum: marge brute > 12% sur estimation",
            ]),
            ("Constitution du dossier", [
                "Memoire technique: presentation SAMSE + references projets similaires",
                "Certificats: Kbis, assurance decennale, attestations fiscales et sociales",
                "Planning d'execution et plan d'installation de chantier",
                "Devis detaille avec sous-detail de prix sur demande",
            ]),
        ]),
        ("procedure-securite-depot", "Reglement Securite et Surete Depots SAMSE", [
            ("Acces et controle", [
                "Badge obligatoire pour tout acces zone stockage",
                "Visiteurs: escorte permanente par agent SAMSE",
                "Cameras de surveillance 24h/24, images conservees 30 jours",
                "Portail automatique: fermeture 19h, ouverture 6h30",
            ]),
            ("Securite incendie", [
                "Extincteurs: controle annuel, renouvellement automatique",
                "RIA (Robinet d'Incendie Arme) tous les 25m de galerie",
                "Interdiction de fumer: perimetre 50m autour des batiments",
                "Exercice evacuation: 2 fois par an, rapport obligatoire",
            ]),
        ]),
        ("procedure-inventaire-annuel", "Procedure Inventaire Annuel des Stocks", [
            ("Organisation", [
                "Date: premiere semaine de janvier, depot ferme au public",
                "Equipes: 2 agents par zone, 1 responsable de secteur",
                "Comptage double obligatoire pour articles > 500 EUR unitaire",
                "ERP mis en mode inventaire: blocage mouvements de stock",
            ]),
            ("Ecarts", [
                "Ecart < 0.5% en valeur: acceptable, regularisation automatique",
                "Ecart 0.5-2%: investigation obligatoire sous 48h",
                "Ecart > 2%: audit interne + rapport direction dans les 5 jours",
            ]),
        ]),
        ("politique-achats-responsables", "Politique Achats Responsables SAMSE", [
            ("Criteres fournisseurs", [
                "Empreinte carbone: preference fournisseurs avec bilan carbone certifie",
                "Proximite: priorite aux fabricants europeens (< 1500 km)",
                "Social: zero tolerance travail non declare, audit possible",
                "Produits biosources: objectif 15% du CA en 2026",
            ]),
            ("Engagements 2026", [
                "100% des emballages recyclables ou reutilisables",
                "Reduction de 30% des emballages plastique vs 2022",
                "Bilan carbone scope 1+2 certifie d'ici fin 2025",
                "Formation acheteurs RSE: 2 jours minimum par an",
            ]),
        ]),
    ]
    for fname, title, sections in procs:
        pdf(f"{fname}.pdf", title, sections)
    print(f"  Procedures internes: {len(procs)} PDFs")
    return len(procs)


def gen_price_lists():
    count = 0
    categories = {
        "Isolation thermique": [
            ("Laine de verre 100mm R2.6", "REF-LV-100", 8.50),
            ("Laine de verre 120mm R3.15", "REF-LV-120", 10.20),
            ("Laine de verre 160mm R4.2", "REF-LV-160", 13.50),
            ("Laine de roche 100mm R2.5", "REF-LR-100", 10.80),
            ("Laine de roche 120mm R3.0", "REF-LR-120", 12.90),
            ("PSE graphite 80mm R2.4", "REF-PSE-080", 11.00),
            ("PSE graphite 100mm R3.0", "REF-PSE-100", 13.50),
            ("PIR 80mm R3.7", "REF-PIR-080", 18.50),
        ],
        "Etancheite": [
            ("Membrane EPDM 1.2mm", "REF-EPDM-12", 15.00),
            ("Membrane EPDM 1.5mm", "REF-EPDM-15", 18.00),
            ("Bitume SBS 3mm", "REF-SBS-030", 7.50),
            ("Bitume APP 4mm", "REF-APP-040", 9.80),
            ("Ecran HPV 115g", "REF-HPV-115", 0.85),
            ("Film pare-vapeur 200mu", "REF-PV-200", 0.60),
        ],
        "Plaques et cloisons": [
            ("BA13 standard 2.5m", "REF-BA13-250", 6.20),
            ("BA13 hydrofuge H2 2.5m", "REF-BAH-250", 8.10),
            ("BA13 coupe-feu F30 2.5m", "REF-BAF-250", 9.50),
            ("Rail R48 3m", "REF-R48-300", 1.80),
            ("Montant M48 2.5m", "REF-M48-250", 2.10),
            ("Vis TF 25mm (boite 500)", "REF-VIS-025", 4.50),
        ],
        "Mortiers et enduits": [
            ("Mortier colle C2 Weber 25kg", "REF-MC2-025", 18.50),
            ("Enduit facade monocouche 30kg", "REF-EFM-030", 24.00),
            ("Enduit de rebouchage 5kg", "REF-ERB-005", 9.80),
            ("Colle carrelage sol 25kg", "REF-CCS-025", 16.50),
            ("Joint epoxy 2kg", "REF-JEP-002", 28.00),
        ],
    }
    for region in REGIONS:
        rows = []
        for cat, products in categories.items():
            rows.append((f"Categorie: {cat}", [
                f"{name} | {ref} | {prix:.2f} EUR/m2 ou Unite | Stock: {'Disponible' if random.random() > 0.15 else 'Sur commande'}"
                for name, ref, prix in products
            ]))
        pdf(
            f"tarif-{region.lower().replace(' ', '-').replace('-', '-')}.pdf",
            f"Tarif Agences SAMSE - {region} - 2025",
            [("Conditions generales", [
                "Tarifs HT, TVA 20% applicable sauf materiaux sous TVA 10%",
                f"Region: {region} - Mise a jour: janvier 2025",
                "Tarifs valables sous reserve de disponibilite stock",
                "Remise volume: 2% de 5K a 20K EUR/mois, 5% au-dela",
            ])] + rows
        )
        count += 1
    print(f"  Tarifs regionaux: {count} PDFs")
    return count


def gen_supplier_contracts():
    count = 0
    for fournisseur in FOURNISSEURS:
        slug = fournisseur.lower().replace(" ", "-").replace("'", "")
        pdf(f"contrat-{slug}-2025.pdf", f"Contrat Cadre - {fournisseur} - 2025", [
            ("Parties", [
                f"Acheteur: SAMSE Distribution SAS - 38 Chemin des Basses Rives - 38130 Echirolles",
                f"Vendeur: {fournisseur}",
                "Duree: 12 mois du 1er janvier au 31 decembre 2025, tacite reconduction",
            ]),
            ("Conditions tarifaires", [
                "Prix base: selon tarif fournisseur en vigueur au 1er janvier 2025",
                "Remise commerciale: 8 a 14% selon volumes et categories",
                "Remise de fin d'annee (RFA): 1.5% si objectif CA atteint",
                "Revision prix: notification 60 jours avant application, accord ecrit requis",
                "Frais de port offerts: commandes > 3 000 EUR HT livrees en 48h",
            ]),
            ("Qualite et service", [
                "Taux de service minimum: 96% (livraisons dans les delais)",
                "Taux de non-conformite maximum accepte: 0.5%",
                "Penaite non-livraison: 0.5% du montant commande par jour de retard",
                "Audit qualite annuel: preavis 15 jours, rapport sous 30 jours",
            ]),
            ("Paiement", [
                "Delai: 30 jours fin de mois date de facture",
                "Escompte paiement comptant: 1%",
                "Penalites de retard: taux BCE + 10 points (loi LME)",
                "Indemnite forfaitaire de recouvrement: 40 EUR par facture",
            ]),
            ("Responsabilite et assurances", [
                f"Assurance RC: {fournisseur} fournit attestation annuelle",
                "Plafond de garantie: 3 000 000 EUR par sinistre",
                "Garantie produit: conformite aux normes NF, CE, DTU applicables",
                "Clause de reserve de propriete jusqu'au paiement integral",
            ]),
        ])
        count += 1
    print(f"  Contrats fournisseurs: {count} PDFs")
    return count


# ─── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Telechargement fiches techniques reelles...")
    downloaded, failed = download_real_docs()

    print("\nGeneration PDFs synthetiques...")
    n1 = gen_product_sheets()
    n2 = gen_procedures()
    n3 = gen_price_lists()
    n4 = gen_supplier_contracts()

    all_pdfs = [f for f in os.listdir(DOCS_DIR) if f.endswith(".pdf")]
    print(f"\nCorpus total: {len(all_pdfs)} PDFs dans {DOCS_DIR}/")
    print(f"  Reels telechargés: {len(downloaded)}")
    if failed:
        print(f"  Echecs téléchargement: {len(failed)} (remplacés par synthétiques)")
    print(f"  Synthetiques: {n1 + n2 + n3 + n4}")
