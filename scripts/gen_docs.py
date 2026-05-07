from fpdf import FPDF
from fpdf.enums import XPos, YPos
import os

def make_pdf(filename, title, sections):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 12, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)
    for heading, lines in sections:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, heading, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", size=10)
        for line in lines:
            pdf.multi_cell(0, 6, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(3)
    out = os.path.join("demo_docs", filename)
    pdf.output(out)
    print(f"Generated: {out}")

make_pdf("catalogue-produits.pdf", "Catalogue Produits SAMSE 2025", [
    ("Isolation thermique", [
        "REF-ISO-001 - Laine de verre ISOVER 100mm - R=2.6 m2K/W - Prix: 8.50 EUR/m2",
        "REF-ISO-002 - Panneau PSE graphite 80mm - R=2.8 m2K/W - Prix: 12.00 EUR/m2",
        "REF-ISO-003 - Laine de roche ROCKWOOL 120mm - R=3.45 m2K/W - Prix: 10.20 EUR/m2",
        "Application: murs, combles, planchers. Classe feu: A1 (laine), B (PSE).",
    ]),
    ("Etancheite toiture", [
        "REF-ETA-001 - Membrane EPDM 1.2mm - duree de vie 50 ans - Prix: 15.00 EUR/m2",
        "REF-ETA-002 - Bitume SBS APP 4kg - Prix: 9.80 EUR/m2",
        "Pose par professionnel certifie RGE obligatoire pour travaux subventionnes.",
    ]),
    ("Cloisons et plaques", [
        "REF-CLO-001 - Plaque BA13 standard 2.5m - Prix: 6.20 EUR/plaque",
        "REF-CLO-002 - Plaque hydrofuge BA13 H2 2.5m - Prix: 8.10 EUR/plaque",
        "REF-CLO-003 - Rail R48 3m acier galvanise - Prix: 1.80 EUR/piece",
        "Garantie produit: 10 ans defaut fabrication.",
    ]),
    ("Mortiers et enduits", [
        "REF-MOR-001 - Mortier colle C2 Weber 25kg - Prix: 18.50 EUR/sac",
        "REF-MOR-002 - Enduit de facade monocouche 30kg - Prix: 24.00 EUR/sac",
        "Delai de livraison standard: 48h pour commandes avant 14h.",
    ]),
])

make_pdf("procedures-achats.pdf", "Procedures Internes - Service Achats", [
    ("1. Processus de commande fournisseur", [
        "Toute commande superieure a 5 000 EUR doit etre validee par le directeur achats.",
        "Les bons de commande sont emis via le logiciel SAP uniquement.",
        "Delai de reglement standard: 30 jours fin de mois a date de facture.",
        "Tout nouveau fournisseur doit etre reference dans le systeme avant premiere commande.",
    ]),
    ("2. Reception et controle marchandises", [
        "Un bon de livraison signe est obligatoire pour toute reception.",
        "Les non-conformites doivent etre declarees sous 72h par ecrit au fournisseur.",
        "Les retours marchandises necessitent un avoir emis par le fournisseur.",
    ]),
    ("3. Gestion des litiges fournisseurs", [
        "Litige < 500 EUR: resolution par le gestionnaire compte.",
        "Litige 500-5000 EUR: escalade responsable achats sous 5 jours ouvrables.",
        "Litige > 5000 EUR: comite direction, delai maximum 15 jours ouvrables.",
    ]),
    ("4. Fournisseurs strategiques", [
        "Saint-Gobain, Rockwool, Weber, Knauf: contrats cadres annuels.",
        "Conditions de remise negociees sur volume annuel.",
        "Revue annuelle des conditions en novembre pour application janvier N+1.",
    ]),
])

make_pdf("contrat-fournisseur-type.pdf", "Contrat Cadre Fournisseur - Modele Type", [
    ("Article 1 - Objet", [
        "Le present contrat definit les conditions generales d'achat entre SAMSE Distribution (Acheteur) et le Fournisseur.",
        "Duree: 12 mois renouvelables par tacite reconduction avec preavis de 3 mois.",
    ]),
    ("Article 2 - Conditions tarifaires", [
        "Les prix sont fixes pour la duree du contrat sauf evenement exceptionnel (variation matieres > 15%).",
        "Remise de volume: 2% de 50K a 100K EUR/an, 4% au-dela de 100K EUR/an.",
        "Frais de port offerts pour commandes superieures a 2 000 EUR HT.",
    ]),
    ("Article 3 - Qualite et conformite", [
        "Le Fournisseur garantit la conformite de ses produits aux normes NF, CE et DTU applicables.",
        "Taux de service minimum exige: 95% (livraisons dans les delais convenus).",
        "Audit qualite possible une fois par an avec preavis de 15 jours.",
    ]),
    ("Article 4 - Responsabilite", [
        "En cas de defaut produit, le Fournisseur prend en charge le remplacement sous 5 jours.",
        "Plafond de responsabilite: 150% du montant de la commande concernee.",
        "Assurance RC professionnelle obligatoire, attestation fournie chaque annee.",
    ]),
])

print("Done. 3 PDFs generated in demo_docs/")
