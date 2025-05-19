import streamlit as st
from PIL import Image
import openai
import os
import tempfile
from pdf2image import convert_from_bytes

# Load OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("❌ OPENAI_API_KEY manquante.")
    st.stop()

client = openai.OpenAI(api_key=api_key)

# Prompt complet avec variables pour type et contexte de diffusion
def build_prompt(support_type: str, diffusion_context: str):
    return f"""
# 🌟 Prompt expert conformité réglementaire (pharma)

Tu es un expert réglementaire dans un laboratoire pharmaceutique, spécialiste de la conformité des supports promotionnels destinés aux professionnels de santé. Tu maîtrises parfaitement la réglementation française, notamment :

- Le Code de la santé publique (articles L.5122-1 à L.5122-15)
- La Charte de l'information par démarchage ou prospection visant à la promotion des médicaments
- Le Référentiel de certification de la visite médicale
- Les recommandations de l’ANSM sur la publicité des médicaments
- Les exigences de l’EMA, lorsqu’elles s’appliquent

---

## 🧳 Contexte spécifique fourni par l’utilisateur

- **Type de support sélectionné** : {support_type}
- **Lieu ou mode de diffusion prévu** : {diffusion_context}

💡 *Adapte ton analyse réglementaire à ces éléments dès la première section. Sois particulièrement rigoureux si le support est destiné à un usage papier seul ou à une large audience HCP (congrès, mailing de masse, etc.).*

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
- autre (précisé)

[...]

### 2. 🔍 Effectuer un OCR complet de l’image

- Extraire **l’intégralité du texte visible**.
- Conserver la **mise en forme sémantique** : titres, encadrés, couleurs, tableaux, astérisques…
- Signaler toute **illisibilité**, **élément masqué**, **texte trop petit** ou **support partiel** (ex. une seule face d’un flyer recto/verso).

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

### 🧠 Conclusion réglementaire synthétique

**Avis final** :
✅ Conforme  
⚠️ À corriger avant diffusion  
❌ Non conforme – retour au marketing recommandé

> Recommandation : relire ce support avec le pharmacien responsable si des points critiques sont confirmés (ex. allégation sans source, données cliniques douteuses).

## 📌 Bonus (optionnel)

- Signale toute incohérence scientifique ou juridique critique.
- Précise s’il est recommandé d’effectuer une **validation interne finale** par le responsable conformité.
"""

# Fonction de conversion image -> PDF temporaire
def image_to_pdf_path(image: Image.Image):
    image = image.convert("RGB")
    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    image.save(temp_pdf.name, format="PDF")
    return temp_pdf.name

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

if uploaded_file:
    if uploaded_file.type == "application/pdf":
        pdf_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
        with open(pdf_path, "wb") as f:
            f.write(uploaded_file.read())
        pages = convert_from_bytes(open(pdf_path, "rb").read())
        for i, page in enumerate(pages):
            st.image(page, caption=f"Page {i+1}", use_container_width=True)
    else:
        image = Image.open(uploaded_file)
        st.image(image, caption="Image importée", use_container_width=True)
        pdf_path = image_to_pdf_path(image)

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
                                    {"type": "text", "text": build_prompt(support_type, diffusion_context)},
                                    {"type": "file", "file": {"file_id": file.id}}
                                ]
                            }
                        ],
                        max_tokens=1500
                    )
                st.success("✅ Analyse terminée - J’espère que ça va t’aider !")
                st.markdown(response.choices[0].message.content)
            except Exception as e:
                st.error(f"❌ Erreur OpenAI : {e}")
