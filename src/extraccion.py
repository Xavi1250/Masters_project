import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import random
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import datetime
import chromedriver_autoinstaller
import numpy as np

"""
CONDICIONES INICIALES CHROME
"""
chromedriver_autoinstaller.install()
chrome_options = webdriver.ChromeOptions() 
chrome_options.add_argument("--disable-blink-features=AutomationControlled") 
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option("useAutomationExtension", False) 

driver = webdriver.Chrome(options=chrome_options)
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

headers = {
'Access-Control-Allow-Origin': '*',
'Access-Control-Allow-Methods': 'GET',
'Access-Control-Allow-Headers': 'Content-Type',
'Access-Control-Max-Age': '3600',
'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
}




""" 
-- FUNCIONES SECUNDARIAS ---
Vamos a crear varias funciones secundarias que posteriormente servirán para crear una función primaria que llame a esas funciones secundarias
"""

"""
SOUP OPCIÓN 1: Intentamos hacerlo de manera simple con beautifullsoup y no funcionó (nos detectaba como bot)
"""

"""
SOUP OPCIÓN 2: Código todo junto.
Usamos selenium para conseguir el soup:
"""
def tarjetas_masters(url):
    driver.get(url)
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    lista_tarjetas1 = soup.find_all("a", attrs={"class":"SearchStudyCard"})
    time.sleep(3)
    new_url = f"{url}/page-2"
    driver.get(new_url)
    new_html = driver.page_source
    new_soup = BeautifulSoup(new_html, "html.parser")
    lista_tarjetas2 = lista_tarjetas1.append(new_soup.find_all("a", attrs={"class":"SearchStudyCard"}))
    time.sleep(3)

    for i in range (3,5):
        new_url = f"{url}?page={i}"
        driver.get(new_url)
        new_html = driver.page_source
        new_soup = BeautifulSoup(new_html, "html.parser")
        lista_tarjetas_completa = lista_tarjetas2.append(new_soup.find_all("a", attrs={"class":"SearchStudyCard"}))
        time.sleep(3)

    return lista_tarjetas_completa

"""
OPCIÓN 3: Usamos Selenium y separamos el código de soup en varios pasos para que no nos detecten como bot.
"""
def lista_tarjetas_1(url):
    driver.get(url)
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    lista_tarjetas1 = soup.find_all("a", attrs={"class":"SearchStudyCard"})
    return lista_tarjetas1

def lista_tarjetas_2(url):
    new_url = f"{url}/page-2"
    html = requests.get(new_url)
    soup = BeautifulSoup(html.content, "html.parser")
    lista_tarjetas2 = soup.find_all("a", attrs={"class":"SearchStudyCard"})
    return lista_tarjetas2

def lista_otras_tarjetas(url):
    for i in range (3,5):
        new_url_2 = f"{url}?page={i}"
        html = requests.get(new_url_2)
        soup = BeautifulSoup(html, "html.parser")
        lista_tarjetas_3 = soup.find_all("a", attrs={"class":"SearchStudyCard"})
    return lista_tarjetas_3

def lista_tarjetas_completa(url):
    return lista_tarjetas_1(url)+lista_tarjetas_2(url)+lista_otras_tarjetas(url)

"""
DICCIONARIO
Tanto si usamos el método de soup todo junto como el método separado, funciona:
"""
def diccionario(lista_tarjetas_completa):
    dict_list = []
    for i in lista_tarjetas_completa:
        dict_ = {}
        dict_["ID"] = i.find("div", attrs={"data-study-id":True})["data-study-id"]
        dict_["Titulo"] = i.find("h2", attrs={"class":"StudyName"}).getText()
        dict_["Lugar"] = i.find("strong", attrs={"class":"OrganisationLocation"}), 
        dict_["Universidad"] = i.find("strong", attrs={"class":"OrganisationName"}).getText()
        dict_["Tipo"] = i.find("span", attrs={"class":"SecondaryFacts DesktopOnlyBlock"}).getText().split("/")[1].strip()
        dict_["Presencial"] = i.find("span", attrs={"class":"SecondaryFacts DesktopOnlyBlock"}).getText().split("/")[2].strip()
        precio = dict_["Precio"] = i.find("div", attrs={"class":"TuitionValue"})
        if precio: 
            dict_["Precio"] = precio.getText().split("/")[0].strip().split(" ")[0].replace(",","")
        else:
            dict_["Precio"] = np.nan
        dict_["Tiempo"] = i.find("div", attrs={"class":"DurationValue"}).getText()
        dict_["Descripcion"] = i.find("h2", attrs={"class":"StudyName"}).getText()
        dict_["Enlaces"] = i.get("href")
        dict_list.append(dict_)
    return dict_list

"""EXTRA: Para cada tarjeta de máster, accedemos a su link para obtener más información:
        - Fecha de inscripción
        - Fecha de inicio
        - Rating (falta el código ya que el de fecha no ha funcionado, detecta bot)
"""
def fechas(dict_list):
    for i in dict_list:
        master_web = i["Enlaces"]
        driver.get(master_web)
        html_2 = driver.page_source
        soup2 = BeautifulSoup(html_2, "html.parser")
        lista_fechas = soup2.find_all("div", attrs={"class":"TimingContainer"})
    
        list_dates = []
        for j in lista_fechas:
            if j.find("time"):
                list_dates.append(j.find("time").get("datetime"))
            else:
                list_dates.append("Unknown")

            apply_date_bad = list_dates[0]
            start_date_bad = list_dates[1]

            apply_obj = datetime.datetime.strptime(apply_date_bad, "%Y-%m-%d")
            start_obj = datetime.datetime.strptime(start_date_bad, "%Y-%m-%d")

            apply_date = apply_obj.strftime("%d/%m/%Y")
            start_date = start_obj.strftime("%d/%m/%Y")

            i["Fecha_inscripcion"] = apply_date
            i["Fecha_inicio"] = start_date

    return "fechas añadidas para cada master"


"""
--- FUNCIONES PRIMARIAS ---
Vamos a crear una función primaria que llamará de forma anidada las secundarias creadas anteriormente.
Así, con una única función tendremos todo el proceso anterior.
"""

"""
OPCIÓN 1: Este primer caso es sin la función de fecha que no funcionaba
"""
def obtencion_masters_basico(url):
    list_dicts = diccionario(tarjetas_masters(url))
    df = pd.DataFrame(list_dicts)
    return df

"""
OPCIÓN 2: Este segundo caso es como quedaría si todas las funciones funcionaran y no nos detectaran como bot.
"""
def obtencion_masters_completo(url):
    list_dicts = fechas(diccionario(tarjetas_masters(url)))
    df = pd.DataFrame(list_dicts)
    return df
