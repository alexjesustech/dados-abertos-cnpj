import urllib.request
import re

urls = [
    "https://dadosabertos.receita.fazenda.gov.br/CNPJ/",
    "http://dadosabertos.rfb.gov.br/CNPJ/"
]

for url in urls:
    print(f"Testando conexão com {url}...")
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8', errors='ignore')
            print(f"[OK] Conexão estabelecida com sucesso. Tamanho da resposta: {len(html)} bytes.")
            
            # Procura por links de arquivos ZIP na listagem Apache
            zip_files = re.findall(r'href="([^"]+\.zip)"', html, re.IGNORECASE)
            if zip_files:
                print(f"Encontrados {len(zip_files)} arquivos ZIP na listagem:")
                for z in zip_files[:5]:
                    print(f" - {z}")
                if len(zip_files) > 5:
                    print(f" - ... e mais {len(zip_files) - 5} arquivos.")
            else:
                print("Nenhum link .zip encontrado na página de listagem.")
    except Exception as e:
        print(f"[ERRO] Falha ao conectar: {e}")
    print("-" * 50)
