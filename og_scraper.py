# ==================================================
# PROYECTO 1: OG SCRAPER - OSINT Open Graph + Meta
# Escrito 100% por: Daniel Toro
# ==================================================
import os
import sys
from datetime import date
import urllib.request
import urllib.error
from html.parser import HTMLParser
import json

# -------- BASE_DIR + CHDIR SIEMPRE ARRIBA --------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

# -------- CREAR CARPETAS SALIDA --------
os.makedirs("datos_osint", exist_ok=True)
os.makedirs("imagenes_og", exist_ok=True)
os.makedirs("informes_pdf", exist_ok=True)


# ==================================================
# CLASE OGParser: Extrae title, meta, og: del HTML
# ==================================================
class OGParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.en_title = False
        self.resultado = {
            "title": None,
            "meta_description": None,
            "meta_keywords": None,
            "og_title": None,
            "og_image": None,
            "og_url": None,
        }

    # -------- HOOK 1: empieza un tag --------
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        # Tag <TITLE>: activar bandera
        if tag.lower() == "title":
            self.en_title = True
            return

        # Tag <META>: extraer name/property/content
        if tag.lower() == "meta":
            # meta description / keywords (name=...)
            if attrs_dict.get("name") == "description":
                self.resultado["meta_description"] = attrs_dict.get("content", None)
            elif attrs_dict.get("name") == "keywords":
                self.resultado["meta_keywords"] = attrs_dict.get("content", None)
            # Open Graph property=og:xxx
            elif attrs_dict.get("property") == "og:title":
                self.resultado["og_title"] = attrs_dict.get("content", None)
            elif attrs_dict.get("property") == "og:image":
                self.resultado["og_image"] = attrs_dict.get("content", None)
            elif attrs_dict.get("property") == "og:url":
                self.resultado["og_url"] = attrs_dict.get("content", None)

    # -------- HOOK 2: texto DENTRO de tags --------
    def handle_data(self, data):
        if self.en_title and self.resultado["title"] is None:
            self.resultado["title"] = data.strip()

    # -------- HOOK 3: cierra un tag --------
    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self.en_title = False
            
    
# ==================================================
# FUNCIÓN analizar_url: Hace HTTP GET, pasa HTML al parser OGParser
# ==================================================
def analizar_url(url: str) -> dict:
    """
    Analiza 1 URL individual:
      1. GET HTTP con User-Agent Mozilla (evitar 403)
      2. Decode UTF-8 errors=replace (evitar UnicodeDecodeError)
      3. Pasa html_str al OGParser.feed()
      4. Devuelve dict con URL + fecha + status + datos parser + error
    """
    resultado_base = {
        "url": url,
        "fecha_analisis": str(date.today()),
        "status_code": None,
        "title": None,
        "meta_description": None,
        "meta_keywords": None,
        "og_title": None,
        "og_image": None,
        "og_url": None,
        "error": None,
    }

    try:
        # ----- (1) HTTP Request con User-Agent navegador -----
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            resultado_base["status_code"] = response.getcode()
            html_bytes = response.read()

        # ----- (2) Decode UTF-8 (replace por bytes raros) -----
        html_str = html_bytes.decode("utf-8", errors="replace")

        # ----- (3) Parsear con OGParser -----
        parser = OGParser()
        parser.feed(html_str)

        # ----- (4) Mezclar resultado parser + base -----
        for k, v in parser.resultado.items():
            resultado_base[k] = v

        return resultado_base

    # ----- Manejo errores POR URL INDIVIDUAL -----
    except urllib.error.URLError as e:
        resultado_base["error"] = f"URLError: {str(e)}"
        return resultado_base
    except urllib.error.HTTPError as e:
        resultado_base["error"] = f"HTTPError {e.code}: {str(e.reason)}"
        resultado_base["status_code"] = e.code
        return resultado_base
    except Exception as e:
        resultado_base["error"] = f"Error inesperado: {type(e).__name__}: {str(e)}"
        return resultado_base
    
    # ==================================================
# FUNCIÓN procesar_lote_urls: Itera N URLs, llama analizar_url
# ==================================================
def procesar_lote_urls(lista_urls: list[str]) -> list[dict]:
    """
    Recibe lista de URLs y procesa UNA por UNA.
    try/except DENTRO del for: 1 URL fallida NO rompe lote completo.
    Devuelve lista con diccionarios resultado (1 por URL).
    """
    resultados = []
    total = len(lista_urls)

    print("=" * 70)
    print(f"🚀 PROYECTO 1 OG SCRAPER — PROCESANDO LOTE DE {total} URLs")
    print("=" * 70)

    for idx, url in enumerate(lista_urls, start=1):
        print(f"\n[{idx}/{total}] Analizando URL: {url}")
        try:
            resultado = analizar_url(url)
            resultados.append(resultado)
            if resultado["error"]:
                print(f"   [⚠️] ERROR: {resultado['error']}")
            else:
                titulo = resultado.get("title") or resultado.get("og_title") or "SIN TÍTULO"
                print(f"   [✅] OK - Status: {resultado.get('status_code')}")
                print(f"   [📜] Título: {titulo[:80]}")
        except Exception as e:
            print(f"   [❌] ERROR GRANDERO: {type(e).__name__}: {str(e)}")
            resultados.append({
                "url": url,
                "fecha_analisis": str(date.today()),
                "status_code": None,
                "title": None, "meta_description": None,
                "meta_keywords": None, "og_title": None,
                "og_image": None, "og_url": None,
                "error": f"Excepción global procesador: {type(e).__name__}: {str(e)}",
            })

    print("\n" + "=" * 70)
    print(f"📊 LOTE TERMINADO: {len(resultados)} URLs procesadas.")
    print("=" * 70)
    return resultados

# ==================================================
# BLOQUE MAIN: Punto de entrada al hacer `python3 og_scraper.py`
# ==================================================
if __name__ == "__main__":

    # --------- LOTE DE PRUEBA (4 URLs reales conocidas) ---------
    lote_prueba = [
        "https://www.paypal.com/es/home",
        "https://es.wikipedia.org/wiki/Inteligencia_artificial",
        "https://github.com/dayucri12",
        "https://httpstat.us/404",
    ]

    # --------- (1) Procesar lote ---------
    resultados = procesar_lote_urls(lote_prueba)

    # --------- (2) Guardar JSON en datos_osint/ ---------
    fecha_hoy = date.today().strftime("%Y-%m-%d")
    ruta_json = os.path.join("datos_osint", f"og_resultados_{fecha_hoy}.json")

    # ensure_ascii=False → guardar ñ/tildes UTF-8 no \uXXXX
    # default=str → si hay tipos no serializables (datetime), str()
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n[💾] Resultados guardados en JSON: {ruta_json}")

    # --------- (3) Resumen final por consola ---------
    ok_count  = sum(1 for r in resultados if r["error"] is None)
    err_count = sum(1 for r in resultados if r["error"] is not None)
    print(f"\n[📊] RESUMEN FINAL: OK={ok_count} / ERRORES={err_count} / TOTAL={len(resultados)}")
    print("[🏆] OG SCRAPER TERMINADO 100%\n")
