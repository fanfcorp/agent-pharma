
import streamlit as st
from PIL import Image
import openai
import io
import os
from pdf2image import convert_from_bytes

# Load OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("❌ OPENAI_API_KEY manquante.")
    st.stop()

client = openai.OpenAI(api_key=api_key)

# Extended prompt for ANSM compliance
def build_prompt():
    return """
# 🎯 Prompt expert conformité réglementaire (pharma)

Tu es un expert réglementaire dans un laboratoire pharmaceutique, spécialiste de la conformité des supports promotionnels destinés aux professionnels de santé. Tu maîtrises parfaitement la réglementation française, notamment :

- Le Code de la santé publique (articles L.5122-1 à L.5122-15)
- La Charte de l'information par démarchage ou prospection visant à la promotion des médicaments
- Le Référentiel de certification de la visite médicale
- Les recommandations de l’ANSM sur la publicité des médicaments
- Les exigences de l’EMA, lorsqu’elles s’appliquent

Ton objectif est de **vérifier la conformité réglementaire** d’un support promotionnel fourni sous forme **d’image**, destiné aux professionnels de santé.

---

## 🧾 Étapes de l’analyse

### 1. 🗂️ Identifier le type de support

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

---

### B. Résumé des points critiques

> Ex :  
> - Absence de mention de la DCI  
> - Données cliniques non sourcées  
> - Ton promotionnel avec superlatifs

---

### C. Tableau de conformité détaillé

| Axe                       | Statut     | Justification concise                               |
|--------------------------|------------|-----------------------------------------------------|
| Mentions obligatoires    | ⚠️          | AMM incomplète, DCI absente                         |
| Équilibre bénéfices/risques | ✅       | Effets indésirables mentionnés                      |
| Références scientifiques | ❌          | Absence de sources, pas de publication identifiée  |
| Caractère promotionnel   | ⚠️          | Formulation ambiguë : “efficacité remarquable”      |
| Publicité comparative    | ✅          | Aucune comparaison                                  |
| Spécificité de la cible  | ✅          | Ton réservé aux professionnels                      |
| Identification labo      | ✅          | Nom et contact présents                             |
| Lisibilité/ergonomie     | ⚠️          | Mention légale trop petite, illisible sans zoom     |

---

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

# Convert image to PDF
def image_to_pdf_path(image: Image.Image):
    image = image.convert("RGB")
    pdf_path = "/tmp/input_as_pdf.pdf"
    image.save(pdf_path, format="PDF")
    return pdf_path

# Streamlit app
st.title("Pour ma Béné d'amour: Vérification ANSM avec GPT-4o")

uploaded_file = st.file_uploader("Uploader une image ou un PDF", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file:
    if uploaded_file.type == "application/pdf":
        pdf_path = "/tmp/uploaded_doc.pdf"
        with open(pdf_path, "wb") as f:
            f.write(uploaded_file.read())
        pages = convert_from_bytes(open(pdf_path, "rb").read())
        st.image(pages[0], caption="Page 1 du PDF", use_container_width=True)
    else:
        image = Image.open(uploaded_file)
        st.image(image, caption="Image importée", use_container_width=True)
        pdf_path = image_to_pdf_path(image)

    if st.button("Analyser avec GPT-4o"):
        with st.spinner("📄 Je convertis ton image pour l'envoyer à OpenAI..."):
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
                                    {"type": "text", "text": build_prompt()},
                                    {"type": "file", "file": {"file_id": file.id}}
                                ]
                            }
                        ],
                        max_tokens=1500
                    )
                st.success("✅ Analyse terminée - J'espère que ça va t'aider!")
                st.markdown(response.choices[0].message.content)
            except Exception as e:
                st.error(f"❌ Erreur OpenAI : {e}")
