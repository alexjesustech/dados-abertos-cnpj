import os
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service

def search():
    print("Inicializando scraper de busca de datasets...")
    options = webdriver.FirefoxOptions()
    options.add_argument("-headless")
    
    driver_path = "/snap/bin/firefox.geckodriver"
    if not os.path.exists(driver_path):
        driver_path = str(Path("drivers", "geckodriver").absolute())
        
    service = Service(executable_path=driver_path)
    driver = webdriver.Firefox(options=options, service=service)
    driver.implicitly_wait(10)
    
    try:
        url = "https://dados.gov.br/dados/conjuntos-dados?q=CNPJ"
        print(f"Acessando busca: {url}")
        driver.get(url)
        time.sleep(5)
        
        # Tirar print e salvar HTML
        driver.save_screenshot("temp/search_screenshot.png")
        with open("temp/search_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
            
        print("Buscando elementos de resultados...")
        # Cada dataset na lista costuma ter um link ou título
        # No portal dados.gov.br moderno, os cards de conjunto de dados têm tags h3 ou links específicos
        cards = driver.find_elements(By.XPATH, "//a[contains(@href, '/conjuntos-dados/')]")
        print(f"Encontrados {len(cards)} links contendo /conjuntos-dados/")
        
        datasets = set()
        for card in cards:
            href = card.get_attribute("href")
            text = card.text.strip().replace("\n", " ")
            if href and "/conjuntos-dados/" in href:
                # Filtrar links repetidos ou que não sejam o próprio dataset (ex: links de tags)
                # O formato do link do dataset é: https://dados.gov.br/dados/conjuntos-dados/<nome-do-dataset>
                # Evitar links de recursos que têm sub-caminhos ou parâmetros
                datasets.add((text, href))
                
        print("\n=== Datasets Encontrados ===")
        for idx, (text, href) in enumerate(datasets, 1):
            print(f"Dataset #{idx}: '{text}' -> {href}")
            
    finally:
        driver.quit()
        print("Busca finalizada.")

if __name__ == "__main__":
    search()
