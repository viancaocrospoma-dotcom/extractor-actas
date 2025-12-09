import streamlit as st
import zipfile
import tempfile
import pandas as pd
from utils import procesar_carpeta

st.title("Extractor Automático de Actas – DNI, Responsable, Institución")
st.write("Sube un ZIP con carpetas y PDFs o un archivo PDF individual.")

# Botón para limpiar
if st.button("Limpiar pantalla"):
    st.experimental_rerun()

# Uploader corregido
archivo = st.file_uploader("Sube tu archivo", type=["zip", "pdf"])

if archivo:
    temp_dir = tempfile.mkdtemp()

    # Si es PDF simple
    if archivo.type == "application/pdf":
        ruta_pdf = f"{temp_dir}/archivo.pdf"
        with open(ruta_pdf, "wb") as f:
            f.write(archivo.read())

        df = procesar_carpeta(temp_dir)
        st.dataframe(df)

    # Si es ZIP
    elif archivo.type == "application/zip":
        ruta_zip = f"{temp_dir}/archivo.zip"
        with open(ruta_zip, "wb") as f:
            f.write(archivo.read())

        with zipfile.ZipFile(ruta_zip, "r") as zip_ref:
            zip_ref.extractall(temp_dir)

        df = procesar_carpeta(temp_dir)
        st.dataframe(df)
