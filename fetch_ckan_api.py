import urllib.request
import json
import ssl

def fetch():
    url = "https://dados.gov.br/api/3/action/package_show?id=cadastro-nacional-da-pessoa-juridica---cnpj"
    print(f"Buscando metadados do dataset via CKAN API: {url}")
    
    # Desabilita verificação SSL caso haja problemas com certificados locais
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=20) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get("success"):
                result = data.get("result", {})
                resources = result.get("resources", [])
                print(f"[SUCESSO] Dataset encontrado: '{result.get('title')}'")
                print(f"Total de recursos listados: {len(resources)}")
                
                # Salva a lista de recursos estruturada
                with open("temp/ckan_resources.json", "w", encoding="utf-8") as f:
                    json.dump(resources, f, indent=4, ensure_ascii=False)
                print("Arquivo temp/ckan_resources.json salvo com sucesso.")
                
                for idx, r in enumerate(resources, 1):
                    print(f"Recurso #{idx}:")
                    print(f"  Nome: '{r.get('name')}'")
                    print(f"  URL: '{r.get('url')}'")
                    print(f"  Formato: '{r.get('format')}'")
                    print(f"  Descrição: '{r.get('description')}'")
                    print("-" * 40)
            else:
                print(f"[ERRO] A API retornou falha: {data}")
    except Exception as e:
        print(f"[ERRO] Falha ao consultar a API CKAN: {e}")

if __name__ == "__main__":
    fetch()
