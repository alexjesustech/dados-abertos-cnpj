import re
import json

def parse():
    print("=== Lendo arquivo HTML ===")
    with open("temp/page_source.html", "r", encoding="utf-8") as f:
        html = f.read()
        
    print(f"Tamanho do HTML: {len(html)} bytes")
    
    # 1. Procurar por links <a> clássicos
    print("=== Buscando links em tags <a> ===")
    links_a = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL | re.IGNORECASE)
    print(f"Encontrados {len(links_a)} links <a>")
    
    for href, text in links_a:
        clean_text = re.sub(r'<[^>]+>', '', text).strip()
        if "dadosabertos.rfb" in href or "receita.fazenda.gov.br" in href or ".zip" in href:
            print(f"Suspeito <a>: '{clean_text}' -> {href}")

    # 2. Procurar em tags <script> por URLs
    print("\n=== Buscando em blocos <script> ===")
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL | re.IGNORECASE)
    print(f"Encontrados {len(scripts)} blocos de script")
    
    for idx, content in enumerate(scripts):
        if "dadosabertos.rfb" in content or "receita.fazenda.gov" in content:
            print(f"Script #{idx} contém referências! Tamanho: {len(content)}")
            # Tentar extrair URLs
            urls = re.findall(r'(https?://[^\s"\']+)', content)
            print(f"  Encontradas {len(urls)} URLs no script #{idx}:")
            for u in urls[:10]:
                if "dadosabertos.rfb" in u or "receita" in u or ".zip" in u:
                    print(f"    - {u}")
            if len(urls) > 10:
                print(f"    - ... e mais {len(urls) - 10} URLs.")

if __name__ == "__main__":
    parse()
