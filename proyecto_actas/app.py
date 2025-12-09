import streamlit as st
import zipfile
import tempfile
import pandas as pd
import os
import cv2
import pytesseract
from pdf2image import convert_from_path
import numpy as np

st.title("Extractor Automático de Datos – OCR para PDFs Escaneados")

st.write("Sube un archivo ZIP con carpetas que contengan PDFs escaneados. El sistema extraerá:")
st.write("• ID desde el nombre del archivo")
st.write("• Nombre del responsable o firmante")
st.write("• DNI")
st.write("• Nombre de la institución (si aparece en la primera página)")


# -------------------- FUNCIONES OCR --------------------

def preprocess(img):
    """Mejora la imagen para OCR."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_LINEAR)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    _, th = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return th


def extract_text_from_pdf(pdf_path):
    """Convierte PDF escaneado a texto usando OCR (última página y primera página)."""
    try:
        pages = convert_from_path(pdf_path, dpi=300)
        text_all = ""

        # OCR PRIMERA PÁGINA (Institución)
        first_img = cv2.cvtColor(np.array(pages[0]), cv2.COLOR_RGB2BGR)
        first_pre = preprocess(first_img)
        text_all += pytesseract.image_to_string(first_pre, lang="spa")

        # OCR ÚLTIMA PÁGINA (Firmas y DNI)
        last_img = cv2.cvtColor(np.array(pages[-1]), cv2.COLOR_RGB2BGR)
        last_pre = preprocess(last_img)
        text_all += pytesseract.image_to_string(last_pre, lang="spa")

        return text_all

    except Exception as e:
        return ""


def extract_dni(text):
    """Busca DNI de 8 dígitos."""
    import re
    match = re.search(r"\b\d{8}\b", text)
    return match.group(0) if match else ""


def extract_name(text):
    """Busca nombres cerca de palabras clave."""
    keywords = ["responsable", "autoridad", "nombre", "yo", "firma", "suscriben"]

    lines = text.split("\n")
    for i, line in enumerate(lines):
        low = line.lower()
        for key in keywords:
            if key in low:
                if i + 1 < len(lines):
                    cand = lines[i + 1].strip()
                    if len(cand.split()) >= 2:
                        return cand
    return ""


def extract_institution(text):
    """Toma la primera línea significativa del OCR."""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if len(lines) > 0:
        return lines[0]
    return ""


def extract_id_from_filename(filename):
    """Extrae ID (todo antes del primer guion bajo)."""
    try:
        name = os.path.splitext(filename)[0]
        return name.split("_")[0]
    except:
        return ""


# -------------------- INTERFAZ STREAMLIT --------------------

file = st.file_uploader("Sube el archivo ZIP", type=["zip"])

if file:
    with tempfile.TemporaryDirectory() as tmp:
        zip_path = os.path.join(tmp, "upload.zip")

        with open(zip_path, "wb") as f:
            f.write(file.read())

        # Extraer ZIP
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(tmp)

        st.success("ZIP cargado exitosamente. Procesando PDFs...")

        resultados = []

        # Recorrer PDFs dentro del ZIP
        for root, dirs, files in os.walk(tmp):
            for pdf in files:
                if pdf.lower().endswith(".pdf"):
                    pdf_path = os.path.join(root, pdf)

                    text = extract_text_from_pdf(pdf_path)

                    data = {
                        "Archivo": pdf,
                        "ID": extract_id_from_filename(pdf),
                        "Institución": extract_institution(text),
                        "Responsable": extract_name(text),
                        "DNI": extract_dni(text)
                    }

                    resultados.append(data)

        df = pd.DataFrame(resultados)
        st.dataframe(df)

        # Descargar Excel
        excel_path = os.path.join(tmp, "resultado.xlsx")
        df.to_excel(excel_path, index=False)

        with open(excel_path, "rb") as f:
            st.download_button("Descargar Excel", f, "resultado.xlsx")
