import os
import re
from pathlib import Path
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By


class DadosAbertoCadastroNacionalPessoaJuridica:

    def __init__(self):
        self.dir_temp = "temp"

        if not os.path.isdir(self.dir_temp):
            os.makedirs(self.dir_temp)
            print(f'Criado o diretório temporário("{self.dir_temp}")')

        profile = webdriver.FirefoxProfile()
        profile.set_preference("browser.download.panel.shown", False)
        profile.set_preference("browser.download.animateNotifications", False)
        profile.set_preference("browser.download.dir", str(Path(self.dir_temp).absolute()))
        profile.set_preference("browser.download.folderList", 2)
        profile.set_preference("browser.helperApps.alwaysAsk.force", False)
        profile.set_preference("browser.download.manager.showWhenStarting", False)
        profile.set_preference("pdfjs.disabled", True)
        profile.set_preference(
            "browser.helperApps.neverAsk.saveToDisk",
            (
                "application/pdf, application/zip, application/octet-stream, "
                "text/csv, text/xml, application/xml, text/plain, "
                "text/octet-stream, application/x-gzip, application/x-tar "
                "application/"
                "vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
        )

        options = webdriver.FirefoxOptions()
        options.profile = profile
        options.add_argument("-headless")
        options.binary_location = str(Path("drivers/geckodriver.exe").absolute())

        self.driver = webdriver.Firefox(options=options)
        self.driver.install_addon(str(Path("drivers/selectorshub-4.6.8.xpi").absolute()))
        self.driver.implicitly_wait(10)
        self.driver.get(
            "https://dados.gov.br/dados/conjuntos-dados/cadastro-nacional-da-pessoa-juridica---cnpj")
        self.btn_collapse_recursos = (By.CLASS_NAME, "botao-collapse-Recursos")
        self.btns_acesso_recurso = (By.XPATH, '//button[text()=" Acessar o recurso "]')

    def download(self):
        btn_collapse_recursos = self.driver.find_element(*self.btn_collapse_recursos)
        btn_collapse_recursos.click()
        print(btn_collapse_recursos.text)

        sleep(5)

        links = self.driver.find_elements(*self.btns_acesso_recurso)
        num_download = 0
        for link in links:
            num_download += 1
            link.click()
            print(f'#{num_download} {link.text}')

            sleep(5)

        num_links = re.findall(r"\d", btn_collapse_recursos.text)
        if num_download != num_links:
            print(f'O número de links na página é {num_links} e o número de downloads é {num_download}.')

        self.driver.quit()


if __name__ == '__main__':
    dados = DadosAbertoCadastroNacionalPessoaJuridica()
    print("Início do download dos Dados Abertos do Cadastro Nacional de Pessoa Jurídica...")
    dados.download()
    print("Fim do download dos Dados Abertos do Cadastro Nacional de Pessoa Jurídica.")
