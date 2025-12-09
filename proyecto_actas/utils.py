import pdfplumber
import re
import os

def extraer_datos_pdf(ruta_pdf):
    institucion = ""
    responsable = ""
    dni = ""

    try:
        with pdfplumber.open(ruta_pdf) as pdf:
            texto = ""
            for pagina in pdf.pages:
                texto += pagina.extract_text() or ""

        primera_linea = texto.split("\n")[0]
        institucion = primera_linea.strip()

        patron_nombre = r"(?i)(responsable|firmante|beneficiario)[:\s]*([A-ZÁÉÍÓÚÑ ]{5,})"
        match_nombre = re.search(patron_nombre, texto)
        if match_nombre:
            responsable = match_nombre.group(2).strip()

        patron_dni = r"\b([0-9]{8})\b"
        match_dni = re.search(patron_dni, texto)
        if match_dni:
            dni = match_dni.group(1)

    except Exception as e:
        print("Error leyendo PDF:", ruta_pdf, e)

    return institucion, responsable, dni


def procesar_carpeta(base_path):
    registros = []

    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.lower().endswith(".pdf"):
                ruta_pdf = os.path.join(root, file)

                inst, resp, dni = extraer_datos_pdf(ruta_pdf)

                registros.append({
                    "Institución": inst,
                    "Responsable": resp,
                    "DNI": dni,
                    "Archivo": file
                })

    return registros
