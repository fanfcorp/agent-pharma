import streamlit as st
from PIL import Image
import openai
import os
import tempfile
from pdf2image import convert_from_bytes
from fpdf import FPDF
import pytesseract
import re
import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader

# Load OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("❌ OPENAI_API_KEY manquante.")
    st.stop()

client = openai.OpenAI(api_key=api_key)

# Prompt complet avec variables pour type, contexte de diffusion et AMM
def build_prompt(support_type: str, diffusion_context: str, amm_text: str = ""):
    return f"""
# 🎯 Prompt expert conformité réglementaire (pharma)

Tu es un expert réglementaire dans un laboratoire pharmaceutique, spécialiste de la conformité des supports promotionnels destinés aux professionnels de santé. Tu maîtrises parfaitement la réglementation française, notamment :

- Le Code de la santé publique (articles L.5122-1 à L.5122-15)
- La Charte de l'information par démarchage ou prospection visant à la promotion des médicaments
- Le Référentiel de certification de la visite médicale
- Les recommandations de l’ANSM sur la publicité des médicaments
- Les exigences de l’EMA, lorsqu’elles s’appliquent

---

## 🧾 Contexte spécifique fourni par l’utilisateur

- **Type de support sélectionné** : {support_type}
- **Lieu ou mode de diffusion prévu** : {diffusion_context}

💡 *Adapte ton analyse réglementaire à ces éléments dès la première section. Sois particulièrement rigoureux si le support est destiné à un usage papier seul ou à une large audience HCP (congrès, mailing de masse, etc.).*

---

## 📎 Texte extrait du RCP officiel (AMM)

{amm_text[:2000]}

*(seuls les premiers caractères sont affichés pour contexte)*

---

## 🧾 Étapes de l’analyse

### 1. 🗂️ Identifier le type de support

> L'utilisateur a indiqué que le support est un(e) **{support_type}**, prévu pour une diffusion via **{diffusion_context}**.

Indique parmi les options suivantes :
- bannière web
- diapositive PowerPoint
- affiche / kakemono
- page de magazine
- encart email
- prospectus / flyer
- plaquette produit
- autre (à préciser)

💡 *Adapte le niveau d’exigence réglementaire selon le type de support, en tenant compte des éléments suivants :*

| Type de support         | Mentions obligatoires exigées                                     | Format particulier ou dérogatoire                                     |
|-------------------------|--------------------------------------------------------------------|------------------------------------------------------------------------|
| **Bannière web**        | Nom du médicament, DCI, lien vers mentions complètes               | Les mentions peuvent être accessibles via un lien cliquable adjacent  |
| **Encart email**        | Nom du médicament, DCI, résumé AMM, effets indésirables            | L’email peut renvoyer via un lien vers le RCP ou mentions légales     |
| **Affiche / Kakemono**  | Nom, DCI, AMM, effets indésirables, laboratoire, mentions légales  | Doivent être visibles sans zoom, format lisible à distance            |
| **Page de magazine**    | Toutes mentions usuelles selon réglementation papier               | Idem qu’affiche : pas de lien hypertexte possible                     |
| **Flyer / Prospectus**  | Mention complète du médicament, DCI, AMM, effets indésirables      | S’il est à destination papier seule, toutes les mentions doivent figurer |
| **Plaquette produit**   | Toutes mentions complètes + sources si études citées              | Support souvent détaillé : exigence maximale de conformité             |
| **Diapositive PowerPoint** | Nom du médicament, DCI, résumé AMM (ou en annexe), effets indésirables | Vérifier lisibilité et équilibre à l’oral comme à l’écrit             |
| **Autre**               | À évaluer selon le format et la diffusion prévue                  | Si usage digital ou événementiel, adapter au canal                    |

🔎 En cas de **format court**, les mentions obligatoires peuvent figurer dans un lien (web) ou sur une page dédiée complémentaire, **mais doivent être accessibles immédiatement** (pas de démarche complexe pour y accéder).

---

### 2. 🔍 Effectuer un OCR complet de l’image

- Extraire **l’intégralité du texte visible**.
- Conserver la **mise en forme sémantique** : titres, encadrés, couleurs, tableaux, astérisques…
- Signaler toute **illisibilité**, **élément masqué**, **texte trop petit** ou **support partiel** (ex. une seule face d’un flyer recto/verso).

---

### 3. ✅ Vérifier la conformité réglementaire

#### A. Mentions obligatoires
- Nom du médicament
- DCI (Dénomination Commune Internationale)
- Informations AMM (titulaire, numéro, date)
- Mention obligatoire : *"Ce médicament est un produit de santé. Ne pas interrompre un traitement sans avis médical"* (si applicable)
- Prix et taux de remboursement (si applicable)

#### B. Équilibre bénéfices / risques
- Présentation objective des bénéfices
- Mention des effets indésirables
- Absence de banalisation ou minimisation des risques

#### C. Références scientifiques
- Présence de sources claires
- Publications accessibles, fiables, pertinentes, datées
- Fidélité des extraits aux publications originales

#### D. Caractère promotionnel
- Ton neutre, professionnel
- Absence de superlatifs non autorisés (ex : "le meilleur", "unique", "révolutionnaire")
- Formulations factuelles, non trompeuses

#### E. Publicité comparative
- Comparaison éventuelle avec d’autres produits
- Comparaison loyale, fondée, non dénigrante et complète

#### F. Spécificités de la cible
- Contenu adapté aux **professionnels de santé**
- Absence de confusion possible avec une cible **grand public**

#### G. Identification du laboratoire
- Nom du laboratoire clairement indiqué
- Coordonnées, mentions légales, site web, etc.

#### H. Lisibilité & ergonomie
- Mentions lisibles sans zoom
- Taille de police suffisante
- Hiérarchie visuelle claire
- Contraste suffisant entre texte et fond

---

## 📊 Rapport structuré

### A. Note globale de conformité

Attribue une note sur 100 avec cette échelle :
- ✅ **90 – 100** : Conforme
- ⚠️ **75 – 89** : À corriger
- ❌ **< 75** : Non conforme

### B. Résumé des points critiques

> Ex :  
> - Absence de mention de la DCI  
> - Données cliniques non sourcées  
> - Ton promotionnel avec superlatifs

### C. Tableau de conformité détaillé

| Axe                       | Statut     | Justification concise                               |
|--------------------------|------------|-----------------------------------------------------|
| Mentions obligatoires    |            |                                                     |
| Équilibre bénéfices/risques |            |                                                     |
| Références scientifiques |            |                                                     |
| Caractère promotionnel   |            |                                                     |
| Publicité comparative    |            |                                                     |
| Spécificité de la cible  |            |                                                     |
| Identification labo      |            |                                                     |
| Lisibilité/ergonomie     |            |                                                     |

### D. Propositions de reformulation

Exemples :
- ❌ “Le meilleur traitement disponible” → ✅ “Traitement recommandé par les recommandations actuelles”
- ❌ “Tolérance parfaite” → ✅ “Tolérance évaluée dans l’étude X, avec X % d’effets indésirables”

---

## 🧠 Conclusion réglementaire synthétique

**Avis final** :  
✅ Conforme  
⚠️ À corriger avant diffusion  
❌ Non conforme – retour au marketing recommandé

> Recommandation : relire ce support avec le pharmacien responsable si des points critiques sont confirmés (ex. allégation sans source, données cliniques douteuses).

---

## 📎 Bonus (optionnel)

- Signale toute incohérence scientifique ou juridique critique.
- Précise s’il est recommandé d’effectuer une **validation interne finale** par le responsable conformité.
"""

# Fonction de conversion image -> PDF temporaire
def image_to_pdf_path(image: Image.Image):
    image = image.convert("RGB")
    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    image.save(temp_pdf.name, format="PDF")
    return temp_pdf.name

# Fonction pour exporter du texte en PDF avec FPDF
def export_text_to_pdf(text: str, filename: str):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=10)
    for line in text.split('\n'):
        pdf.multi_cell(0, 10, line)
    pdf_path = os.path.join(tempfile.gettempdir(), filename)
    pdf.output(pdf_path)
    return pdf_path

# OCR pour extraire texte brut de l'image ou page PDF
def extract_text(image: Image.Image):
    return pytesseract.image_to_string(image)

# Détection du médicament via regex ou VISA
def detect_medicament_name(text: str):
    visa_match = re.search(r"Visa.*?(?P<name>[A-Z0-9\-]+)", text)
    if visa_match:
        return visa_match.group("name")
    candidates = re.findall(r"\b[A-ZÉÈÀÂÎÔÛÄËÏÖÜÇ0-9\-]{3,}\b", text)
    return candidates[0] if candidates else None

# Scraping BDPM pour obtenir le lien vers le RCP PDF
def find_rcp_url_from_bdpm(med_name: str):
    try:
        search_url = f"https://base-donnees-publique.medicaments.gouv.fr/index.php?search={med_name}"
        response = requests.get(search_url)
        soup = BeautifulSoup(response.content, "html.parser")
        link = soup.find("a", href=re.compile(r"\.pdf$"))
        if link:
            return "https://base-donnees-publique.medicaments.gouv.fr" + link["href"]
    except:
        return None

# Télécharger le PDF RCP localement
def download_rcp_pdf(url, med_name):
    try:
        response = requests.get(url)
        rcp_path = os.path.join(tempfile.gettempdir(), f"{med_name}_rcp.pdf")
        with open(rcp_path, "wb") as f:
            f.write(response.content)
        return rcp_path
    except:
        return None

# Extraire texte du PDF RCP
def extract_pdf_text(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        text = "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
        return text.strip()
    except:
        return ""

# 🔹 Streamlit app
st.title("Pour ma Béné d'amour 💕 : Vérification ANSM avec GPT-4o")

uploaded_file = st.file_uploader("📁 Uploader une image ou un PDF", type=["pdf", "png", "jpg", "jpeg"])

support_type = st.selectbox(
    "📂 Quel est le type de support promotionnel ?",
    [
        "Bannière web",
        "Diapositive PowerPoint",
        "Affiche / Kakemono",
        "Page de magazine",
        "Encart email",
        "Prospectus / Flyer",
        "Plaquette produit",
        "Autre (préciser)"
    ]
)

diffusion_context = st.text_input(
    "🌍 Où ce support sera-t-il diffusé ? (ex : congrès, site web, cabinet médical...)"
)

ocr_text = ""
medicament_name = ""
ammpath = ""
amm_text = ""

if uploaded_file:
    if uploaded_file.type == "application/pdf":
        pdf_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
        with open(pdf_path, "wb") as f:
            f.write(uploaded_file.read())
        pages = convert_from_bytes(open(pdf_path, "rb").read())
        for i, page in enumerate(pages):
            st.image(page, caption=f"Page {i+1}", use_container_width=True)
        ocr_text = extract_text(pages[0])
    else:
        image = Image.open(uploaded_file)
        st.image(image, caption="Image importée", use_container_width=True)
        pdf_path = image_to_pdf_path(image)
        ocr_text = extract_text(image)

    medicament_name = detect_medicament_name(ocr_text)
    if medicament_name:
        st.info(f"🔍 Médicament détecté automatiquement : **{medicament_name}**")
        rcp_url = find_rcp_url_from_bdpm(medicament_name)
        if rcp_url:
            ammpath = download_rcp_pdf(rcp_url, medicament_name)
            if ammpath:
                amm_text = extract_pdf_text(ammpath)
                if amm_text:
                    st.success("📄 Texte du RCP intégré au contexte de l'analyse")

    if st.button("🔍 Analyser avec GPT-4o"):
        if not diffusion_context:
            st.warning("⚠️ Merci d’indiquer le contexte de diffusion.")
            st.stop()

        with st.spinner("📄 Conversion et envoi à OpenAI..."):
            try:
                with open(pdf_path, "rb") as f:
                    file = client.files.create(file=f, purpose="assistants")

                with st.spinner("🧠 Analyse réglementaire en cours..."):
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": build_prompt(support_type, diffusion_context, amm_text)},
                                    {"type": "file", "file": {"file_id": file.id}}
                                ]
                            }
                        ],
                        max_tokens=1500
                    )
                final_text = response.choices[0].message.content
                st.success("✅ Analyse terminée - J’espère que ça va t’aider !")
                st.markdown(final_text)

                if st.download_button("📥 Télécharger le rapport en PDF", data=open(export_text_to_pdf(final_text, "rapport_ansm.pdf"), "rb").read(), file_name="rapport_ansm.pdf"):
                    st.success("📄 Rapport PDF prêt à être téléchargé")

                if ammpath:
                    st.download_button("📥 Télécharger le RCP (AMM)", data=open(ammpath, "rb").read(), file_name=f"{medicament_name}_rcp.pdf")

            except Exception as e:
                st.error(f"❌ Erreur OpenAI : {e}")
