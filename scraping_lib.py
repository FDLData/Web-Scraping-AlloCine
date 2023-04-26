import requests
from bs4 import BeautifulSoup

import numpy as np
import pandas as pd

import re 
from IPython.display import display

# Extraire le nombre de page à scraper
def extraire_nombre_pages(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    all_pages = soup.find_all('div', class_="pagination-item-holder")[0]
    nombre_pages = int(str(all_pages)[-12:][:2])
    return nombre_pages


# Scraper tous les films à l'affiche sur AlloCiné
def scraping_films_allociné():
    pages = extraire_nombre_pages(f"https://www.allocine.fr/film/aucinema/")
    movies_dict = { 'Title': [], 'Code': []}

    for i in range(1, pages+1):
        url = f"https://www.allocine.fr/film/aucinema/?page={i}"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        all_movies_i = soup.find_all('div', class_="card entity-card entity-card-list cf")

        for movie in all_movies_i:
            movie_info = movie.find('h2').find('a')
            movie_class = str(movie_info.attrs['class'][0])
            movie_href = str(movie_info.attrs['href']) 
            movie_title = str(movie_info).replace(movie_href,"").replace(movie_class,"").replace('class=',"").replace('href=',"")
            movie_title = re.sub("\"|\>|\<|\/","",movie_title)[1:-1].strip()
            movie_code = re.findall('\d', movie_href) 
            movie_code = int("".join(movie_code))
            movies_dict["Title"].append(movie_title)
            movies_dict["Code"].append(movie_code)   

    films_allociné = pd.DataFrame(movies_dict)
    films_allociné['Title'] = films_allociné['Title'].apply(lambda x: x.capitalize())
    
    #display(films_allociné)
    return films_allociné


#Importer fichier films 
def importer_fichier_films(fichier):
    films = pd.read_excel(fichier)
    films.rename(columns={'Nom':'Title'}, inplace=True)
    films['Title'] = films['Title'].apply(lambda x: x.capitalize())
    
    return films


# Films de la liste à l'affiche en ce moment dans un cinéma parisien
def trouver_films_commun(films):
    films_allociné = scraping_films_allociné()
    
    films_merge = pd.merge(left=films, right=films_allociné, on='Title', how='left') # Ca suppose d'avoir exactement le même titre
    films_merge.fillna(0,inplace=True)
    films_en_commun = films_merge[films_merge['Code'] != 0]
    films_en_commun.loc[:,'Code'] = films_en_commun.loc[:,'Code'].apply(lambda x: int(x))
    
    display(films_en_commun)
    return films_en_commun


# Séances films en commun
def séances_films_en_commun(films_en_commun):
    
    films_allociné = scraping_films_allociné()
    movies_code = list(films_en_commun['Code'].unique())

    toutes_les_séances = list()

    for code in movies_code:

        titre = films_allociné[films_allociné['Code'] == code].iloc[0,0]

        séances_film = {'Titre': titre, 'Cinéma': [], 'Adresse': [], 'Date&Version': [], 'Horaires': []}

        for d in range(0,7):
            url = f"https://www.allocine.fr/seance/film-{code}/pres-de-115767/d-{d}/"
            response = requests.get(url)
            soup = BeautifulSoup(response.content, "html.parser")
            séances = soup.find_all('div', class_="theater-card hred cf")

            for séance in séances:
                nom_cinéma = str(séance.find('h2').find('a')).replace(str(séance.find('h2').find('a').attrs['href']),"").replace('href', "")
                nom_cinéma = re.sub("\"|\>|\<|\/|\=","",nom_cinéma)[1:-1].strip()
                séances_film["Cinéma"].append(nom_cinéma)

                adresse_cinéma = str(séance.find('address')).replace('address',"").replace('class',"")
                adresse_cinéma = re.sub("\"|\>|\<|\/|\=","",adresse_cinéma)[1:]
                séances_film["Adresse"].append(adresse_cinéma)

                info_séances = séance.find_all('div', class_="showtimes-version")[0]

                date_séance = str(info_séances.find_all('div', class_='text')).replace('class', "").replace('text',"").replace('div',"")
                date_séance = re.sub("\"|\>|\<|\/|\=|\n|\-","",date_séance)[1:-1]
                séances_film["Date&Version"].append(date_séance)

                horaire_séance = str(info_séances.find_all('span', class_='showtimes-hour-item-value'))#.replace('class', "").replace('showtimes-hour-item-value', "").replace('span', "")
                #horaire_séance = re.sub("\"|\>|\<|\/|\=|\n|\-","",horaire_séance)[1:-1]
                séances_film["Horaires"].append(horaire_séance)

        toutes_les_séances.append(séances_film)
        
    if len(toutes_les_séances) == 0:
        return print("Aucun film de la liste à l'affiche en ce moment dans un cinéma parisien")
        
    elif len(toutes_les_séances) > 0:
        return toutes_les_séances
    

# Exporter tous les films à l'affiche
def exporter_films_allociné(df):
    df.to_excel("Films à l'affiche.xlsx") 


# Séance du film sélectionné  
def séances_film(code):
    films_allociné = scraping_films_allociné()
    titre = films_allociné[films_allociné['Code'] == code].iloc[0,0]
    séances_film = {'Titre': titre, 'Cinéma': [], 'Adresse': [], 'Infos': []}

    for d in range(0,7):
        url = f"https://www.allocine.fr/seance/film-{code}/pres-de-115767/d-{d}/"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        séances = soup.find_all('div', class_="theater-card hred cf card-thumb-large")

        for séance in séances:
                nom_cinéma = séance.find('h2').find('a').string
                séances_film["Cinéma"].append(nom_cinéma)

                adresse_cinéma = séance.find('address').string
                séances_film["Adresse"].append(adresse_cinéma)

                info_séances = séance.find_all('div', class_="showtimes-version")

                séances_infos = {'Date&Version': [], 'Horaires': []}

                for info in info_séances:
                    date_séance = str(info.find_all('div', class_='text')).replace('class', "").replace('text',"").replace('div',"")
                    date_séance = re.sub("\"|\>|\<|\/|\=|\n|\-","",date_séance)[1:-1]
                    séances_infos["Date&Version"].append(date_séance)

                    horaire_séance = str(info.find_all('span', class_='showtimes-hour-item-value')).replace('class', "").replace('showtimes-hour-item-value', "").replace('span', "")
                    horaire_séance = re.sub("\"|\>|\<|\/|\=|\n|\-","",horaire_séance)[1:-1]
                    séances_infos["Horaires"].append(horaire_séance)

                séances_film['Infos'].append(séances_infos)

    return pd.DataFrame(séances_film)


# Exporter séances du film choisi
def exporter_film(df):
    df.to_excel(f'Séances_{titre}.xlsx') 
    
    
    

