#!/usr/bin/env python3
"""Vuelca la tabla de seguimiento ABM a la Google Sheet del usuario."""
import csv, os, sys
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession

# Configuración por variables de entorno (la clave NUNCA se versiona):
#   GOOGLE_SA_KEY  → ruta al JSON de la cuenta de servicio de Google
#   ABM_SHEET_ID   → ID de la Google Sheet destino
KEY = os.environ.get("GOOGLE_SA_KEY")
SHEET_ID = os.environ.get("ABM_SHEET_ID")
if not KEY or not SHEET_ID:
    sys.exit("Faltan variables de entorno: define GOOGLE_SA_KEY (ruta al JSON) y "
             "ABM_SHEET_ID (ID de la hoja). Ej.:\n"
             "  GOOGLE_SA_KEY=/ruta/clave.json ABM_SHEET_ID=1AbC... python3 scripts/volcar_a_sheet.py")

# Ángulo conciso por cuenta (las 10 con dossier+secuencia generados)
ANGULOS = {
    "GrúasTorre y Elevación Levante S.A.": "Maximizar la ocupación de una flota de elevación de alto valor con demanda B2B nacional, fuera del mercado local de Alicante.",
    "Alquileres Maquinaria Ibérica S.L.": "Canal digital de captación nacional que da alcance sin más estructura (interlocución a Dirección General).",
    "Excavaciones y Alquileres del Levante S.A.": "Rellenar los periodos valle de la flota de movimiento de tierras frente a la estacionalidad de la obra civil.",
    "Movitierra Andalucía Alquiler S.L.": "Subir la tasa de utilización de la flota de tierras con demanda nacional (mensaje al Director de Flota).",
    "Alquiler Industrial Norte S.L.": "Capturar la demanda irregular de energía temporal (eventos, paradas industriales, obra) a nivel nacional.",
    "RentMaq Cataluña S.L.": "Conectar la flota de manutención con el auge logístico catalán y los picos de campaña.",
    "Maquinaria del Sur Alquiler S.L.": "Captación digital con alcance nacional que una empresa media no construiría sola.",
    "Plataformas Elevadoras Aragón S.L.": "Alcance nacional para un especialista de elevación de tamaño contenido (eje del Ebro).",
    "Compactación y Obra Civil Galicia S.L.": "Acceso a obra civil por proyecto de toda la cornisa y del resto de España.",
    "Maquinaria Agrícola y Forestal Castilla S.L.": "Llenar flota por proyecto; verificar antes el catálogo real (obra civil vs. agrícola/forestal).",
}

# 1) Datos base del CSV de cuentas (decisor, contacto, especialidad, etc.)
cuentas = {}
with open("data/cuentas.csv", newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        cuentas[r["empresa"]] = r

# 2) Orden y score desde el CSV priorizado
filas = []
with open("output/cuentas_priorizadas.csv", newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        emp = r["empresa"]
        c = cuentas.get(emp, {})
        angulo = ANGULOS.get(emp, "")
        estado = "Secuencia lista — pendiente de lanzar" if angulo else "Pendiente dossier/secuencia"
        filas.append([
            emp, r["score_total"], r["tier"],
            c.get("especialidad", ""), c.get("region", ""), c.get("ciudad", ""),
            c.get("contacto", ""), c.get("cargo", ""), c.get("email", ""), c.get("telefono", ""),
            angulo, estado,
        ])

CAB = ["Empresa", "Score", "Tier", "Especialidad", "Región", "Ciudad",
       "Decisor", "Cargo", "Email", "Teléfono", "Ángulo de mensaje", "Estado"]
valores = [CAB] + filas

# 3) Autenticación y escritura (vía REST + requests, que respeta REQUESTS_CA_BUNDLE)
creds = service_account.Credentials.from_service_account_file(
    KEY, scopes=["https://www.googleapis.com/auth/spreadsheets"])
sess = AuthorizedSession(creds)
BASE = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}"

def chk(r):
    if not r.ok:
        sys.exit(f"ERROR {r.status_code}: {r.text}")
    return r

# Nombre de la primera pestaña
meta = chk(sess.get(BASE, params={"fields": "sheets.properties"})).json()
sheet0 = meta["sheets"][0]["properties"]
title, gid = sheet0["title"], sheet0["sheetId"]

# Limpiar y escribir valores
chk(sess.post(f"{BASE}/values/{title}!A1:Z1000:clear"))
chk(sess.put(f"{BASE}/values/{title}!A1",
             params={"valueInputOption": "RAW"}, json={"values": valores}))

# Formato: cabecera en negrita + fila fijada + ajuste de columnas
ncols = len(CAB)
chk(sess.post(f"{BASE}:batchUpdate", json={"requests": [
    {"repeatCell": {
        "range": {"sheetId": gid, "startRowIndex": 0, "endRowIndex": 1},
        "cell": {"userEnteredFormat": {"textFormat": {"bold": True},
                 "backgroundColor": {"red": 0.85, "green": 0.92, "blue": 0.83}}},
        "fields": "userEnteredFormat(textFormat,backgroundColor)"}},
    {"updateSheetProperties": {
        "properties": {"sheetId": gid, "gridProperties": {"frozenRowCount": 1}},
        "fields": "gridProperties.frozenRowCount"}},
    {"autoResizeDimensions": {
        "dimensions": {"sheetId": gid, "dimension": "COLUMNS",
                       "startIndex": 0, "endIndex": ncols}}},
]}))

print(f"OK: escritas {len(filas)} cuentas en la pestaña '{title}' (gid {gid}).")
