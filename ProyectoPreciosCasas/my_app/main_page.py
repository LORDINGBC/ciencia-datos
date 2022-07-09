import json
import folium
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st
import matplotlib.pyplot as plt

from PIL                      import Image
from plotly                   import express as px
from folium.plugins           import MarkerCluster
from streamlit_folium         import folium_static
from matplotlib.pyplot        import figimage
from distutils.fancy_getopt   import OptionDummy

from functools import partial
from geopy.geocoders import Nominatim






st.set_page_config(page_title='App ',
                    layout="wide", 
                    page_icon=':house',  
                    initial_sidebar_state="expanded")


st.title('Dinámica Inmobiliaria en King County')
st.header('Propuesto por [Brayan Alexy Caballero Alvarez](https://www.linkedin.com/in/brayan-alexy-caballero-alvarez-36403b18b/)')



def get_data():
     url = 'https://raw.githubusercontent.com/sebmatecho/CienciaDeDatos/master/ProyectoPreciosCasas/data/kc_house_data.csv'
     return pd.read_csv(url)

data = get_data()
data_ref = data.copy()
data['date'] = pd.to_datetime(data['date'], format = '%Y-%m-%d').dt.date
data['yr_built']= pd.to_datetime(data['yr_built'], format = '%Y').dt.year

#llenar la columna anterior con new_house para fechas anteriores a 2015-01-01
data['house_age'] = 'NA'
data['name_ciudad'] = 'NA'
#llenar la columna anterior con new_house para fechas anteriores a 2015-01-01
data.loc[data['yr_built']>1990,'house_age'] = 'new_house' 
# geolocator = Nominatim(user_agent="brayan caballero")
# reverse = partial(geolocator.reverse, language="es")
# data.loc[data['yr_built']=98105,'name_ciudad'] 
# name_ciudad = reverse(
#      for lat, long in data['lat'], data['long']:
#           )
#llenar la columna anterior con old_house para fechas anteriores a 2015-01-01

data.loc[data['yr_built']<1990,'house_age'] = 'old_house'

data['zipcode'] = data['zipcode'].astype(str)


data.loc[data['yr_built']>=1990,'house_age'] = 'new_house' 
data.loc[data['yr_built']<1990,'house_age'] = 'old_house'

data.loc[data['bedrooms']<=1, 'dormitory_type'] = 'studio'
data.loc[data['bedrooms']==2, 'dormitory_type'] = 'apartment'
data.loc[data['bedrooms']>2, 'dormitory_type'] = 'house'

data.loc[data['condition']<=2, 'condition_type'] = 'bad'
data.loc[data['condition'].isin([3,4]), 'condition_type'] = 'regular'
data.loc[data['condition']== 5, 'condition_type'] = 'good'

data['price_tier'] = data['price'].apply(lambda x: 'Primer cuartil' if x <= 321950 else
                                                   'Segundo cuartil' if (x > 321950) & (x <= 450000) else
                                                   'Tercer cuartil' if (x > 450000) & (x <= 645000) else
                                                   'Cuarto cuartil')

data['price/sqft'] = data['price']/data['sqft_living']
st.write(data['zipcode'][1000], data['lat'][1000], data['long'][1000])

st.dataframe(data)
st.write('Este dashboard tiene por objevito presentar rápida y fácilmente la información derivada del estudio de la dinámica inmobiliaria en King Count, WA (USA). Los datos están disponibles [aquí](https://www.kaggle.com/datasets/harlfoxem/housesalesprediction) ')



## Filtros
st.subheader('Filtros Requeridos')
construccion = st.slider('Construcción después de:', int(data['yr_built'].min()),int(data['yr_built'].max()),1991)


st.markdown("""
Las casas han sido divididas en cuatro grupos de igual tañamo, basadas en su precio. 
-  El Primer Cuartil contendrá información de las propiedades que cuestan menos de \$321.950 
-  El Segundo Cuartil contendrá información de las propiedades que cuestan entre \$321.950 y \$450.000
-  El Tercer Cuartil contendrá información de las propiedades que cuestan entre \$450.000 y \$645.000
-  El Cuarto Cuartil contendrá información de las propiedades que cuestan más de \$645.000
    """)
tier = st.multiselect(
     'Cuartil de precios',
    list(data['price_tier'].unique()),
     list(data['price_tier'].unique()))


st.markdown("""
El código postal puede utilizarse como proxy para lo localización de un inmueble en King County. Por favor, consulte [aquí](https://www.zipdatamaps.com/king-wa-county-zipcodes) para más información. 
    """)

zipcod = st.multiselect(
     'Códigos postales',
      list(sorted(set(data['zipcode']))),
      list(sorted(set(data['zipcode']))))
data = data[(data['price_tier'].isin(tier))&(data['zipcode'].isin(zipcod))]
st.subheader('Filtros adicionales (Opcionales)')


OptFiltro = st.multiselect(
     'Variables a incluir en los filtros:',
     ['Habitaciones', 'Baños', 'Área construida (pies cuadrados)','Pisos','Vista al agua','Evaluación de la propiedad','Condición'],
     ['Habitaciones', 'Baños'])


if 'Habitaciones' in OptFiltro: 
     if data['bedrooms'].min() < data['bedrooms'].max():
          min_habs, max_habs = st.sidebar.select_slider(
          'Número de Habitaciones',
          options=list(sorted(set(data['bedrooms']))),
          value=(data['bedrooms'].min(),data['bedrooms'].max()))
          data = data[(data['bedrooms']>= min_habs)&(data['bedrooms']<= max_habs)]
     else:
          st.markdown("""
               El filtro **Habitaciones** no es aplicable para la selección actual de valores
               """)
if 'Baños' in OptFiltro: 
     if data['bathrooms'].min() < data['bathrooms'].max():
          min_banhos, max_banhos = st.sidebar.select_slider(
          'Número de baños ',
          options=list(sorted(set(data['bathrooms']))),
          value=(data['bathrooms'].min(), data['bathrooms'].max()))
          data = data[(data['bathrooms']>= min_banhos)&(data['bathrooms']<= max_banhos)]
     else:
          st.markdown("""
               El filtro **Baños** no es aplicable para la selección actual de valores
               """)
if 'Área construida (pies cuadrados)' in OptFiltro: 
     if data['sqft_living'].min() < data['sqft_living'].max():
          area = st.sidebar.slider('Área construida menor a', int(data['sqft_living'].min()),int(data['sqft_living'].max()),2000)
          data = data[data['sqft_living']<area]
     else:  
          st.markdown("""
               El filtro **Área construida (pies cuadrados)** no es aplicable para la selección actual de valores
               """)

if 'Pisos' in OptFiltro: 
     if data['floors'].min() < data['floors'].max():
          min_pisos, max_pisos = st.sidebar.select_slider(
          'Número de Pisos',
          options=list(sorted(set(data['floors']))),
          value=(data['floors'].min(),data['floors'].max()))
          data = data[(data['floors']>= min_pisos)&(data['floors']<= max_pisos)]
     else:
          st.markdown("""
               El filtro **Pisos** no es aplicable para la selección actual de valores
               """)

if 'Vista al agua' in OptFiltro: 
     if data['view'].min() < data['view'].max():
          min_vista, max_vista = st.sidebar.select_slider(
          'Puntaje de vista al agua',
          options=list(sorted(set(data['view']))),
          value=(data['view'].min(),data['view'].max()))
          data = data[(data['view']>= min_vista)&(data['view']<= max_vista)]
     else:
          st.markdown("""
               El filtro **Vista al agua** no es aplicable para la selección actual de valores
               """)
if 'Evaluación de la propiedad' in OptFiltro:
     if data['grade'].min() < data['grade'].max():
          min_cond, max_cond = st.sidebar.select_slider(
          'Índice de evaluación de la propiedad',
          options=list(sorted(set(data['grade']))),
          value=(data['grade'].min(),data['grade'].max()))
          data = data[(data['grade']>= min_cond)&(data['grade']<= max_cond)]
     else:
          st.markdown("""
               El filtro **Evaluación de la propiedad** no es aplicable para la selección actual de valores
               """)

if 'Condición' in OptFiltro:
     if data['condition'].min() < data['condition'].max():
          min_condi, max_condi = st.sidebar.select_slider(
          'Condición de la propiedad',
          options=list(sorted(set(data['condition']))),
          value=(data['condition'].min(),data['condition'].max()))
          data = data[(data['condition']>= min_condi)&(data['condition']<= max_condi)]
     else:
          st.markdown("""
               El filtro **Condición** no es aplicable para la selección actual de valores
               """)












# Mapas 

# info geojson
url2 = 'https://raw.githubusercontent.com/sebmatecho/CienciaDeDatos/master/ProyectoPreciosCasas/data/KingCount.geojson'
col1, col2 = st.columns(2)
with col1:
     st.header("Densidad de casas disponibles por código postal")
     data_aux = data[['id','zipcode']].groupby('zipcode').count().reset_index()
     custom_scale = (data_aux['id'].quantile((0,0.2,0.4,0.6,0.8,1))).tolist()

     mapa = folium.Map(location=[data['lat'].mean(), data['long'].mean()], zoom_start=8)
     folium.Choropleth(geo_data=url2, 
                    data=data_aux,
                    key_on='feature.properties.ZIPCODE',
                    columns=['zipcode', 'id'],
                    threshold_scale=custom_scale,
                    fill_color='YlOrRd',
                    highlight=True).add_to(mapa)
     folium_static(mapa)

     

geolocator = Nominatim(user_agent="brayan caballero")
reverse = partial(geolocator.reverse, language="es")
st.write(reverse("47.6593 , -122.327"))


# i = 0
# for x,y in data['lat'][i], data['long'][i]:
     
#      st.write(x,y)
     



i = 0
while i <= 5:
     i+=1
     geolocator = Nominatim(user_agent="brayan caballero")
     reverse = partial(geolocator.reverse, language="es")
     # st.write(reverse(data['lat'][i], data['long'][i]))
     # console.log(reverse(data['lat'][i], data['long'][i]))
     #  data['lat'][i],  data['long'][i]
     st.write(data['lat'][i], data['long'][i])
else:
     st.write("Se ha completado toda la iteración y c vale")










                    


