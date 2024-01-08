import os
import re
import shutil
import time
from pathlib import Path
import logging

from selenium import webdriver
from selenium.webdriver.common.by import By


class DadosAbertoCadastroNacionalPessoaJuridica:
    logging.basicConfig(filename="dados_aberto_cpnj.log", level=logging.INFO)
    logging.info("Início do download dos Dados Abertos do Cadastro Nacional de Pessoa Jurídica...")

    def __init__(self):

        self.dir_temp = str(Path("temp").absolute())

        # caso exista, exclui o diretório temporário.
        if os.path.isdir(self.dir_temp):
            print(f'Excluindo o diretório temporário("{self.dir_temp}")')
            shutil.rmtree(self.dir_temp)

        # cria o diretório temporário.
        os.makedirs(self.dir_temp)
        print(f'Diretório temporário("{self.dir_temp}") recriado.')

        profile = webdriver.FirefoxProfile()
        profile.set_preference("browser.download.panel.shown", False)
        profile.set_preference("browser.download.animateNotifications", False)
        profile.set_preference("browser.download.dir", self.dir_temp)
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

        self.btn_collapse_recursos = (By.CLASS_NAME, "botao-collapse-Recursos")
        self.btns_acesso_recurso = (By.XPATH, '//button[text()=" Acessar o recurso "]')

    def wait_for_downloads(self):
        print("Aguardando downloads", end="")
        while any([filename.endswith(".part") for filename in os.listdir(self.dir_temp)]):
            time.sleep(2)
            print(".", end="")
        print("Feito!")
        logging.info("Finalizando o driver.")
        profile_name = driver.capabilities.get('moz:profile').replace('\\', '/').split('/')[-1]
        logging.info(f"profile_name: {profile_name}")
        self.driver.quit()

    def download(self):
        self.driver.get(
            "https://dados.gov.br/dados/conjuntos-dados/cadastro-nacional-da-pessoa-juridica---cnpj")

        btn_collapse_recursos = self.driver.find_element(*self.btn_collapse_recursos)
        btn_collapse_recursos.click()

        try:
            links = self.driver.find_elements(*self.btns_acesso_recurso)
            num_download = 0
            for link in links:
                num_download += 1
                time.sleep(5)
                print(f'#{num_download} {link.text}')
                link.click()
        finally:
            self.wait_for_downloads()

        # retorna uma lista dos números retirados da frase/texto.
        num_links = re.findall(r"\d", btn_collapse_recursos.text)
        # junta todos os números da lista em uma única string.
        num_links = ''.join([str(num_link) for num_link in num_links])
        print(f'O número de links na página é {num_links} e o número de downloads é {num_download}.')

        if num_download != num_links:
            # TODO: Criar log e alerta via e-mail/discord sobre o erro.
            print("Falta implementar o alerta...")

        logging.info("Fim do download dos Dados Abertos do Cadastro Nacional de Pessoa Jurídica.")


if __name__ == '__main__':
    dados = DadosAbertoCadastroNacionalPessoaJuridica()
    print("Início do download dos Dados Abertos do Cadastro Nacional de Pessoa Jurídica...")
    dados.download()
    print("Fim do download dos Dados Abertos do Cadastro Nacional de Pessoa Jurídica.")
    '''
        TODO:
            1- Criar log e alerta via e-mail/discord sobre o erro;
            1.1 Informar cada extração bem ou mal sucedida;
            2- Criar rotina para descompactar os arquivos;
            2.1 unzip file.zip
            3- Criar rotina para guardar as informações em uma base de dados;
    '''
