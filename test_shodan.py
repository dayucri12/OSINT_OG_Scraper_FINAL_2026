from dotenv import load_dotenv
import os
load_dotenv()

import shodan
SHODAN_KEY = os.getenv("SHODAN_API_KEY")
print("Clave Shodan cargada:", "✅" if len(SHODAN_KEY or "") > 10 else "❌")

api = shodan.Shodan(SHODAN_KEY)
ip_prueba = "8.8.8.8"  # Google DNS

print(f"\n🛰️ Probando Shodan con IP:", ip_prueba)
try:
    host = api.host(ip_prueba)
    print(f"✅ Shodan ¡EXITO!")
    print(f"IP: {ip_prueba}")
    print(f"ORG: {host.get('org')}")
    print(f"PAÍS: {host.get('country_name')}")
    print(f"PUERTOS ABIERTOS (primeros 10): {host.get('ports', [])[:10]}")
    print(f"CVEs (vulns encontradas: {len(host.get('vulns', []))}")
    if host.get('vulns'):
        print("  · Las primeras 3 CVEs:", host['vulns'][:3])
except Exception as e:
    print(f"❌ Shodan error: {e}")
    print("ℹ️ Si sale 'Invalid API key' → comprueba que la clave en .env")
    print("ℹ️ Si sale 'Rate limit' → eres free y has superaste, inténtalo en 1 minuto")