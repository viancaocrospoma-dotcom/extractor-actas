import streamlit as st
import zipfile
import tempfile
import pandas as pd
from utils import procesar_carpeta

st.title("Extractor Automático de Actas – DNI, Responsable, Institución")
st.write("Sube tu carpeta ZIP con las actas PDF.")

archivo_zip = st.file_uploader("Sube un ZIP con carpetas y PDFs", type=["zip"])

if archivo_zip:
    with tempfile.TemporaryDirectory() as tmp:
        zip_path = f"{tmp}/archivos.zip"
        
        with open(zip_path, "wb") as f:
            f.write(archivo_zip.read())

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(tmp)

        st.success("ZIP cargado y extraído correctamente.")

        registros = procesar_carpeta(tmp)

        df = pd.DataFrame(registros)
        st.dataframe(df)

        excel_path = f"{tmp}/resultado.xlsx"
        df.to_excel(excel_path, index=False)

        with open(excel_path, "rb") as f:
            st.download_button("Descargar Excel", f, "resultado.xlsx")
