import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException, ElementNotVisibleException

from selenium.webdriver.chrome.options import Options
from unidecode import unidecode
from urllib.parse import urlparse, parse_qs
import urllib.request
import json
import re
import requests
import logging
import time

# Configurar o logger
logging.basicConfig(filename='log.txt', level=logging.ERROR,
                    format='%(asctime)s [%(levelname)s]: %(message)s')


class WebScraping:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.title = ""
        self.link = ""
        self.post_date = ""
        self.author = ""
        self.post_context_ps = []
        self.post_comments_ps = []
        self.post_comments = []
        self.author_list = []
        self.global_data = []
        self.GoodReacts = 0
        self.BadReacts = 0
        self.data_update = 1
        logging.basicConfig(filename='log.txt', level=logging.ERROR,
                            format='%(asctime)s [%(levelname)s]: %(message)s')

    def init_driver(self,):
        options = Options()
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--window-size=426,240')

        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 5)
        self.driver.maximize_window()

    def login(self, email, senha):
        self.driver.get('https://www.blackrat.pro/login/')
        try:
            fechar_anuncio = self.wait.until(EC.visibility_of_element_located(
                (By.XPATH, '/html/body/div[5]/div/span/a/i')))
            fechar_anuncio.click()
        except TimeoutException:
            return False

        try:
            self.wait.until(EC.visibility_of_element_located(
                (By.XPATH, '/html/body/main/div/div/div/form')))
            email_field = self.driver.find_element(
                By.XPATH, './/ul/li[1]/div/input')
            email_field.send_keys(email)
            senha_field = self.driver.find_element(
                By.XPATH, './/ul/li[2]/div/input')
            senha_field.send_keys(senha)
            envia_formulario = self.driver.find_element(
                By.XPATH, '//*[@id="elSignIn_submit"]')
            envia_formulario.click()
        except TimeoutException:
            return False
        return True

    def getReacts(self):
        try:
            abrir_reacts = self.wait.until(EC.visibility_of_element_located(
                (By.XPATH, '//*[@data-ipsdialog-title="Veja quem reagiu a isso"]')))
            abrir_reacts.click()
        except TimeoutException:
            return False
        try:
            self.wait.until(EC.visibility_of_element_located(
                (By.XPATH, '//*[@role="tablist"]')))
            ReactsNumber = self.wait.until(EC.presence_of_all_elements_located(
                (By.XPATH, '//*[@role="tablist"]/li/a/span')))
            for index, item in enumerate(ReactsNumber):
                item_text = item.get_attribute('textContent')
                text_formatado = unidecode(item_text)
                padrao = r"\((\d+)\)"
                resultado = re.search(padrao, text_formatado)
                numero = resultado.group(1)
                if index >= 1 and index < 6:
                    self.GoodReacts += int(numero)
                elif index >= 6:
                    self.BadReacts += int(numero)
        except TimeoutException:
            return False
        try:
            fechar_reacts = self.wait.until(EC.visibility_of_element_located(
                (By.XPATH, '//*[@data-action="dialogClose"]')))
            fechar_reacts.click()
        except TimeoutException:
            return True

    def getAuthorComments(self):
        try:
            authorElement = self.wait.until(EC.presence_of_all_elements_located(
                (By.XPATH, '//*/aside/h3/strong/a[2]')))
            for index, item in enumerate(authorElement):
                if index > 0:
                    item_text = item.get_attribute('textContent')
                    text_formatado = unidecode(item_text)
                    self.author_list.append(text_formatado)
        except TimeoutException:
            return False

    def formatComent(self, autorIndex):
        post_comments_lista_filtrada = [item for item in self.post_comments_ps if item.strip(
        ) != '' and item != 'Valor nao especificado']
        post_comments = ' '.join(
            post_comments_lista_filtrada)
        if self.author_list[autorIndex-1]:
            obj = {
                "author": self.author_list[autorIndex-1],
                "comment": post_comments
            }
            self.post_comments.append(obj)
            self.post_comments_ps = []
        else:
            return

    def pesquisar(self,):
        url_pesquisa = f'https://www.blackrat.pro/discover/unread/?&stream_read=all&stream_date_type=relative&stream_classes[IPS%5Cforums%5CTopic]=T%C3%B3picos&stream_classes_type=1&stream_date_relative_days[val]=100000000000&stream_date_relative_days[unit]=w'
        self.driver.get(url_pesquisa)
        while True:
            try:
                next_button = self.wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@data-action="loadMore"]')))
                next_button.click()
                self.escanear_posts()
            except TimeoutException:
                break
            

    def salvar_json(self):
        post_context_lista_filtrada = [item for item in self.post_context_ps if item.strip(
        ) != '' and item != 'Valor nao especificado']
        post_context = ' '.join(
            post_context_lista_filtrada)
        dados = {
            "Title": self.title,
            "Date": self.post_date,
            "Link": self.link,
            "Content": {
                "Author": self.author,
                "Reacts": {
                    "Good": self.GoodReacts,
                    "Bad": self.BadReacts
                },
                "context": post_context,
                "comments": self.post_comments,
            }
        }
        self.global_data = dados
        self.save()
        self.data_update += 1
        print('post', self.data_update)

    def save(self):
        os.makedirs(
            f"Data/Post-{self.data_update}", exist_ok=True)

        filename = f"Data/Post-{self.data_update}/data.json"
        with open(filename, "w") as arquivo:
            json.dump(self.global_data, arquivo, indent=2)

    def get_data_from_elements(self, xpath):
        time.sleep(1)
        try:
            elements = self.wait.until(
                EC.presence_of_all_elements_located((By.XPATH, xpath)))
            self.getAuthorComments()
            cauntAuthor = len(self.author_list)

            for index, item in enumerate(elements):
                time.sleep(1)
                ps = item.find_elements(By.XPATH, './/p')
                for p in ps:
                    text = p.get_attribute('textContent')
                    text_formatado = unidecode(text)

                    if index == 0:
                        self.post_context_ps.append(text_formatado)
                        imagens = p.find_elements(By.XPATH, './/a/img')
                        for i, imagem in enumerate(imagens):
                            alt_imagem = imagem.get_attribute('alt')
                            self.post_context_ps.append(
                                f"-IMG-{alt_imagem}-/IMG-")
                    else:
                        self.post_comments_ps.append(text_formatado)
                if index == 0:
                    self.getReacts()
                    os.makedirs(
                        f"Data/Post-{self.data_update}/Imgs", exist_ok=True)
                    imagens = item.find_elements(By.XPATH, './/p/a/img')
                    for i, imagem in enumerate(imagens):
                        url_imagem = imagem.get_attribute('data-src')
                        alt_imagem = imagem.get_attribute('alt')
                        padrao_image_name = r"[<>:\"/\\|?*]"
                        resultado = re.sub(padrao_image_name, "", alt_imagem)
                        nome_arquivo = f"Data/Post-{self.data_update}/Imgs/{resultado}.png"
                        try:
                            response = requests.get(url_imagem)
                            response.raise_for_status()
                            with open(nome_arquivo, 'wb') as file:
                                file.write(response.content)
                        except requests.HTTPError as e:
                            logging.error(
                                f"Erro ao baixar a imagem {url_imagem}: {e}")
                        except Exception as e:
                            logging.error(
                                f"Ocorreu um erro inesperado ao baixar a imagem {url_imagem}: {e}")
                elif index > 0:
                    self.formatComent(index)
        except TimeoutException:
            logging.error(f'No elements found for xpath: {xpath}')

    def extract_post_data(self, post):
        try:
            titulo_element = post.find_element(
                By.XPATH, './/a[@data-linktype="link"]')
            titulo = titulo_element.text
            titulo_formatado = unidecode(titulo)
            self.title = titulo_formatado
        except (TimeoutException, StaleElementReferenceException, NoSuchElementException):
            return False
        try:
            author_element = post.find_element(
                By.XPATH, './/a[@class="ipsType_break"]/span')
            author = author_element.text
            author_formatado = unidecode(author)
            self.author = author_formatado
        except (TimeoutException, StaleElementReferenceException, NoSuchElementException):
            author = "Não identificado"
            self.author = unidecode(author)
        try:
            post_date = post.find_element(By.XPATH, './/*/*/*/*/time')
            post_date_text = post_date.get_attribute('title')
            post_date_text_formatado = unidecode(post_date_text)
            self.post_date = post_date_text_formatado
        except (TimeoutException, StaleElementReferenceException):
            post_date_text = "Não identificado"
            self.post_date = unidecode(author)
            return False
        try:
            link = titulo_element.get_attribute('href')
            # Remover "?do=getNewComment" da URL
            nova_url = re.sub(r"\?do=getNewComment", "", link)
            # Substituir a parte "page/{number}" por "page/1"
            nova_url = re.sub(r"(page\/)\d+", r"\g<1>1", nova_url)
            self.link = nova_url
        except (TimeoutException, StaleElementReferenceException):
            return False
        try:
            time.sleep(1)
            self.driver.execute_script(f"window.open('{nova_url}', '_blank');")
            self.driver.switch_to.window(self.driver.window_handles[-1])
            self.get_data_from_elements(
                '//*[@data-role="commentContent"]')
            self.salvar_json()
            self.post_context_ps = []
            self.post_comments = []
            self.driver.close()
            time.sleep(1)
            self.driver.switch_to.window(self.driver.window_handles[0])
        except (TimeoutException, StaleElementReferenceException):
            return False
        
        return True

    def escanear_posts(self):
        self.wait.until(EC.presence_of_all_elements_located(
            (By.XPATH, '/html/body/main/div/div/div/section/div[2]/div/div/ol[1]')))
        posts = self.wait.until(EC.presence_of_all_elements_located(
            (By.XPATH, '//*[@data-role="activityItem"]')))
        for post in posts:
            success = self.extract_post_data(post)
            if not success:
                return

    def fechar_navegador(self):
        self.driver.quit()
        self.driver = None
        self.wait = None
