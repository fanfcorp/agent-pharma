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
        for line in text.split('\\n'):
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
    except pytesseract.TesseractNotFoundError as e:
        st.error("❌ Tesseract OCR n'est pas installé sur le système.")
        return ""
    except Exception as e:
        st.error(f"❌ Erreur OCR : {e}")
        return ""

def detect_medicament_name(text: str):
    try:
        prompt = (
            f"Voici le texte extrait par OCR d'un support promotionnel :

"
            f"{text}

"
            f"Peux-tu détecter le nom du médicament (nom commercial) mentionné dans ce support ? Réponds uniquement par ce nom."
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

    if medicament_name:
        medicament_name = st.text_input("✏️ Nom du médicament détecté (modifiable) :", medicament_name)
        st.info(f"🔍 Médicament utilisé pour la recherche : **{medicament_name}**")
                        st.error("❌ Échec du résumé de l'AMM.")
                else:
                    st.error("❌ Échec d’extraction du texte du RCP.")
            else:
                st.error("❌ Téléchargement du RCP impossible.")
        else:
            st.warning("⚠️ Aucun lien RCP trouvé sur la BDPM.")
    else:
        st.warning("❓ Aucun médicament détecté dans l’image.")

    if st.button("🔍 Lancer l'analyse réglementaire complète"):
        with st.spinner("📊 Analyse réglementaire en cours..."):
            try:
                with open(pdf_path, "rb") as f:
                    file = client.files.create(file=f, purpose="assistants")

                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": build_prompt(support_type, diffusion_context, amm_summary)},
                                {"type": "file", "file": {"file_id": file.id}}
                            ]
                        }
                    ],
                    max_tokens=1500
                )
                final_text = response.choices[0].message.content
                st.success("✅ Analyse terminée")
                st.markdown(final_text)
                st.download_button("📥 Télécharger le rapport en PDF", data=open(export_text_to_pdf(final_text, "rapport_ansm.pdf"), "rb").read(), file_name="rapport_ansm.pdf")
                if ammpath:
                    st.download_button("📥 Télécharger le RCP (AMM)", data=open(ammpath, "rb").read(), file_name=f"{medicament_name}_rcp.pdf")
            except Exception as e:
                st.error(f"❌ Erreur OpenAI : {e}")
