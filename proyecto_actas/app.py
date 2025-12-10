import streamlit as st
import tempfile
import pandas as pd
import os
import cv2
import pytesseract
from pdf2image import convert_from_path
import numpy as np
import re

# -------------------- TÍTULO Y DESCRIPCIÓN --------------------

st.title("Extractor de Datos – OCR para PDFs Escaneados (Simple)")

st.write("Sube un PDF escaneado. El sistema extraerá:")
st.write("• ID desde el nombre del archivo (por ejemplo, AY-0039-A01)")
st.write("• Nombre del responsable o firmante (si se detecta)")
st.write("• DNI (8 dígitos)")
st.write("Cada PDF procesado se agregará a la tabla acumulada.")

# -------------------- ESTADO GLOBAL --------------------

if "registros" not in st.session_state:
    st.session_state["registros"] = []  # lista de diccionarios


# -------------------- FUNCIONES OCR --------------------

def preprocess(img):
    """Mejora la imagen para OCR."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Escalado moderado para no consumir tanta memoria
    gray = cv2.resize(gray, None, fx=1.3, fy=1.3, interpolation=cv2.INTER_LINEAR)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    _, th = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return th


def ocr_last_page(pdf_path):
    """
    Hace OCR solo a la última página (donde normalmente está la firma y el DNI),
    con DPI moderado para no reventar la memoria.
    """
    try:
        pages = convert_from_path(pdf_path, dpi=120)  # menos DPI = menos RAM
        if not pages:
            return ""

        # Tomamos la última página
        last = cv2.cvtColor(np.array(pages[-1]), cv2.COLOR_RGB2BGR)

        # (Opcional) recortar solo la parte inferior de la página
        h, w = last.shape[:2]
        crop = last[int(h * 0.6):, :]  # 40% inferior

        pre = preprocess(crop)
        text = pytesseract.image_to_string(pre, lang="spa")
        return text
    except Exception as e:
        print("Error OCR:", e)
        return ""


def extract_id(filename):
    """
    ID = todo el nombre del archivo SIN extensión,
    hasta el primer espacio. Ejemplo:
    AY-0039-A01 HUAMBO.pdf -> AY-0039-A01
    """
    name = os.path.splitext(filename)[0]
    parts = name.split(" ")
    return parts[0]


def extract_dni(text):
    """Busca un DNI de 8 dígitos."""
    match = re.search(r"\b\d{8}\b", text)
    return match.group(0) if match else ""


def extract_responsable(text):
    """
    Busca una línea que parezca nombre debajo de palabras clave
    como 'responsable', 'firma', 'firmante', 'beneficiario', etc.
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    keys = ["responsable", "firma", "firmante", "beneficiario", "autoridad"]

    for i, line in enumerate(lines):
        low = line.lower()
        for k in keys:
            if k in low:
                # Intentar con la siguiente línea
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
    st.success("Tabla vaciada. Puedes comenzar de nuevo.")

if uploaded_pdf and procesar:
    with tempfile.TemporaryDirectory() as tmp:
        pdf_path = os.path.join(tmp, uploaded_pdf.name)

        # Guardar PDF temporalmente
        with open(pdf_path, "wb") as f:
            f.write(uploaded_pdf.read())

        st.info(f"Procesando: {uploaded_pdf.name}")

        # OCR solo en la última página (parte inferior)
        text = ocr_last_page(pdf_path)

        # Extraer datos
        data = {
            "ID": extract_id(uploaded_pdf.name),
            "Responsable": extract_responsable(text),
            "DNI": extract_dni(text),
        }

        st.session_state["registros"].append(data)
        st.success("PDF procesado y agregado a la tabla.")


# -------------------- MOSTRAR RESULTADOS Y DESCARGA --------------------

if st.session_state["registros"]:
    df = pd.DataFrame(st.session_state["registros"])
    st.subheader("Registros acumulados")
    st.dataframe(df)

    # Descargar como CSV (se abre en Excel sin problemas)
    csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Descargar archivo (CSV para Excel)",
        data=csv_bytes,
        file_name="resultado_actas.csv",
        mime="text/csv",
    )
else:
    st.info("Aún no hay registros. Sube un PDF y pulsa 'Procesar PDF'.")
