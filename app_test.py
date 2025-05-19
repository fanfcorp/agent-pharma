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

# Fonctions utilitaires

def image_to_pdf_path(image: Image.Image):
    try:
        image = image.convert("RGB")
        temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        image.save(temp_pdf.name, format="PDF")
        return temp_pdf.name
    except Exception as e:
        st.error(f"❌ Erreur lors de la conversion image en PDF : {e}")
        return ""

def export_text_to_pdf(text: str, filename: str):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", size=10)
        for line in text.split('\n'):
            pdf.multi_cell(0, 10, line)
        pdf_path = os.path.join(tempfile.gettempdir(), filename)
        pdf.output(pdf_path)
        return pdf_path
    except Exception as e:
        st.error(f"❌ Erreur lors de l'export PDF : {e}")
        return ""

def extract_text(image: Image.Image):
    try:
        return pytesseract.image_to_string(image)
    except pytesseract.TesseractNotFoundError:
        st.error("❌ Tesseract OCR n'est pas installé sur le système.")
        return ""
    except Exception as e:
        st.error(f"❌ Erreur OCR : {e}")
        return ""

def detect_medicament_name(text: str):
    try:
        prompt = (
            "Voici le texte extrait par OCR d'un support promotionnel :\n\n"
            f"{text}\n\n"
            "Peux-tu détecter le nom du médicament (nom commercial) mentionné dans ce support ? Réponds uniquement par ce nom."
        )
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=20
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"❌ Erreur pendant la détection du médicament via GPT : {e}")
        return ""

def build_prompt(support_type: str, diffusion_context: str, amm_summary: str):
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

---

## 📎 Résumé du RCP (AMM)

{amm_summary}

---

## 🧾 Étapes de l’analyse

1. Identifier le type de support et adapter le niveau d'exigence réglementaire
2. Vérifier les mentions obligatoires (nom, DCI, AMM, effets indésirables...)
3. Évaluer l'équilibre bénéfices/risques
4. Vérifier les références scientifiques, le caractère promotionnel, la publicité comparative
5. Vérifier la spécificité de la cible, l'identification du laboratoire et la lisibilité
6. Générer un rapport noté, un tableau de conformité, et des suggestions de reformulation si nécessaire
"""

def main():
    st.title("🔍 Vérification réglementaire ANSM avec GPT-4o")

    support_type = st.selectbox("📂 Type de support promotionnel :", [
        "Bannière web", "Diapositive PowerPoint", "Affiche / Kakemono",
        "Page de magazine", "Encart email", "Prospectus / Flyer",
        "Plaquette produit", "Autre (préciser)"
    ])

    diffusion_context = st.text_input("🌍 Contexte ou lieu de diffusion :")

    manual_override = st.checkbox("✍️ Entrer manuellement le nom du médicament")
    manual_name = st.text_input("💊 Nom du médicament (si connu)", "") if manual_override else ""

    uploaded_file = st.file_uploader("📁 Uploader une image ou un PDF", type=["pdf", "png", "jpg", "jpeg"])

    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            pdf_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
            with open(pdf_path, "wb") as f:
                f.write(uploaded_file.read())
            pages = convert_from_bytes(open(pdf_path, "rb").read())
            image = pages[0]
        else:
            image = Image.open(uploaded_file)
            pdf_path = image_to_pdf_path(image)

        st.image(image, caption="🖼️ Aperçu du support")

        ocr_text = extract_text(image)
        st.subheader("📝 Texte extrait par OCR")
        st.code(ocr_text[:2000] if ocr_text else "(aucun texte extrait)", language="text")

        medicament_name = manual_name or detect_medicament_name(ocr_text)

        if medicament_name:
            medicament_name = st.text_input("✏️ Nom du médicament détecté (modifiable) :", medicament_name)
            st.info(f"🔍 Médicament utilisé pour la recherche : **{medicament_name}**")

        if st.button("🔍 Lancer l'analyse réglementaire complète"):
            prompt = build_prompt(support_type, diffusion_context, "(résumé de l'AMM à insérer ici)")
            try:
                with open(pdf_path, "rb") as f:
                    file = client.files.create(file=f, purpose="assistants")

                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "user", "content": [
                            {"type": "text", "text": prompt},
                            {"type": "file", "file": {"file_id": file.id}}
                        ]}
                    ],
                    max_tokens=1500
                )
                final_text = response.choices[0].message.content
                st.success("✅ Analyse terminée")
                st.markdown(final_text)
                st.download_button("📥 Télécharger le rapport en PDF", data=open(export_text_to_pdf(final_text, "rapport_ansm.pdf"), "rb").read(), file_name="rapport_ansm.pdf")
            except Exception as e:
                st.error(f"❌ Erreur OpenAI : {e}")

if __name__ == "__main__":
    main()
