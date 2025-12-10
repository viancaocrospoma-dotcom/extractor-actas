import streamlit as st
import tempfile
import pandas as pd
import os
import cv2
import pytesseract
from pdf2image import convert_from_path
import numpy as np
import re

st.title("Extractor de Datos – OCR para PDFs Escaneados (Simple)")

st.write("Sube un PDF escaneado. El sistema extraerá:")
st.write("• ID desde el nombre del archivo")
st.write("• Nombre del responsable o firmante")
st.write("• DNI (8 dígitos)")
st.write("Cada PDF procesado se agregará a la tabla acumulada.")

# -------------------- ESTADO GLOBAL --------------------

if "registros" not in st.session_state:
    st.session_state["registros"] = []


# -------------------- FUNCIONES OCR --------------------

def preprocess(img):
    """Mejora la imagen para OCR."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=1.3, fy=1.3, interpolation=cv2.INTER_LINEAR)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    _, th = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return th


def ocr_last_page(pdf_path):
    """Hace OCR solo a la última página (donde está firma y DNI)."""
    try:
        pages = convert_from_path(pdf_path, dpi=120)
        last = cv2.cvtColor(np.array(pages[-1]), cv2.COLOR_RGB2BGR)
        pre = preprocess(last)
        text = pytesseract.image_to_string(pre, lang="spa")
        return text
    except Exception as e:
        print("Error OCR:", e)
        return ""


def extract_id(filename):
    """ID = todo antes del primer guion bajo o espacio."""
    name = os.path.splitext(filename)[0]
    parts = re.split(r"[_\- ]", name)
    return parts[0]


def extract_dni(text):
    match = re.search(r"\b\d{8}\b", text)
    return match.group(0) if match else ""


def extract_responsable(text):
    """Busca nombre debajo de 'responsable', 'firmante', 'beneficiario'."""
    lines = text.split("\n")
    keys = ["responsable", "firma", "firmante", "beneficiario", "autoridad"]

    for i, line in enumerate(lines):
        low = line.lower()
        for k in keys:
            if k in low:
                if i + 1 < len(lines):
                    cand = lines[i + 1].strip()
                    if len(cand.split()) >= 2:
                        return cand
    return ""


# -------------------- INTERFAZ --------------------

uploaded_pdf = st.file_uploader("Sube un PDF", type=["pdf"])

col1, col2 = st.columns(2)
procesar = col1.button("Procesar PDF")
limpiar = col2.button("Limpiar tabla")

if limpiar:
    st.session_state["registros"] = []
    st.success("Tabla vaciada.")

if uploaded_pdf and procesar:
    with tempfile.TemporaryDirectory() as tmp:
        pdf_path = os.path.join(tmp, uploaded_pdf.name)

        # guardar PDF
        with open(pdf_path, "wb") as f:
            f.write(uploaded_pdf.read())

        st.info(f"Procesando: {uploaded_pdf.name}")

        # OCR SOLO ULTIMA PAGINA
        text = ocr_last_page(pdf_path)

        # extraer datos
        data = {
            "ID": extract_id(uploaded_pdf.name),
            "Responsable": extract_responsable(text),
            "DNI": extract_dni(text)
        }

        st.session_state["registros"].append(data)
        st.success("PDF procesado y agregado a la tabla.")

# -------------------- MOSTRAR RESULTADOS --------------------

if st.session_state["registros"]:
    df = pd.DataFrame(st.session_state["registros"])
    st.dataframe(df)

    # descarga Excel
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_excel:
        df.to_excel(tmp_excel.name, index=False)
        tmp_excel.seek(0)
        st.download_button(
            "Descargar Excel",
            data=tmp_excel.read(),
            file_name="resultado_actas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
else:
    st.info("Aún no hay registros.")
