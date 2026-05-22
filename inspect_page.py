import os
import sys
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service

def inspect():
    print("Inicializando scraper de inspeção...")
    dir_temp = str(Path("temp").absolute())
    
    options = webdriver.FirefoxOptions()
    options.add_argument("-headless")
    
    driver_path = "/snap/bin/firefox.geckodriver"
    if not os.path.exists(driver_path):
        driver_path = str(Path("drivers", "geckodriver").absolute())
        
    service = Service(executable_path=driver_path)
    driver = webdriver.Firefox(options=options, service=service)
    driver.implicitly_wait(10)
    
    try:
        print("Navegando até o portal...")
        driver.get("https://dados.gov.br/dados/conjuntos-dados/cadastro-nacional-da-pessoa-juridica---cnpj")
        time.sleep(5)
        
        print("Abrindo seção de recursos...")
        btn_collapse = driver.find_element(By.CLASS_NAME, "botao-collapse-Recursos")
        print(f"Texto do botão collapse: '{btn_collapse.text}'")
        btn_collapse.click()
        time.sleep(3)
        
        # Salva o screenshot e o HTML para depuração
        driver.save_screenshot("temp/page_screenshot.png")
        with open("temp/page_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
            
        print("Buscando recursos...")
        # Vamos ver a estrutura dos recursos
        # Geralmente os recursos ficam dentro de uma lista ou divs.
        recursos = driver.find_elements(By.XPATH, "//div[contains(@class, 'recurso-item') or contains(@class, 'card-recurso')]")
        print(f"Encontrados {len(recursos)} elementos de recurso diretamente")
        
        # Vamos buscar os botões de Acessar o recurso
        btns = driver.find_elements(By.XPATH, '//button[contains(text(), "Acessar o recurso")]')
        print(f"Encontrados {len(btns)} botões de 'Acessar o recurso'")
        
        for idx, btn in enumerate(btns, 1):
            try:
                # Tenta achar o título do recurso associado
                # Subindo o DOM a partir do botão para ver o texto do card
                parent = btn.find_element(By.XPATH, "./ancestor::div[contains(@class, 'card') or contains(@class, 'item') or @class][1]")
                title = parent.text.split("\n")[0] if parent else "Desconhecido"
            except Exception:
                title = "Erro ao obter título"
            print(f"Botão #{idx}: '{title}' | Visível: {btn.is_displayed()} | Habilitado: {btn.is_enabled()}")
            
        # Vamos verificar se existe um botão de paginação ou 'Ver mais'
        ver_mais_btns = driver.find_elements(By.XPATH, "//*[contains(text(), 'mais') or contains(text(), 'Mais') or contains(text(), 'carregar') or contains(text(), 'Carregar')]")
        for btn in ver_mais_btns:
            print(f"Botão suspeito de expansão: '{btn.text}' | Tag: '{btn.tag_name}' | Classe: '{btn.get_attribute('class')}'")

    finally:
        driver.quit()
        print("Fim da inspeção.")

if __name__ == "__main__":
    inspect()
