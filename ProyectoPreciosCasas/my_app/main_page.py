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
                    page_icon='🐔',  
                    initial_sidebar_state="expanded")


st.title('Dinámica Inmobiliaria en King County')
st.header('Propuesto por [Brayan Alexy Caballero Alvarez](https://www.linkedin.com/in/brayan-alexy-caballero-alvarez-36403b18b/)')



def get_data():
     url = 'https://raw.githubusercontent.com/LORDINGBC/ciencia-datos/main/ProyectoPreciosCasas/data/kc_house_data.csv'
     return pd.read_csv(url)

data = get_data()
data_ref = data.copy()
data['date'] = pd.to_datetime(data['date'], format = '%Y-%m-%d').dt.date
data['yr_built']= pd.to_datetime(data['yr_built'], format = '%Y').dt.year

#llenar la columna anterior con new_house para fechas anteriores a 2015-01-01
data['house_age'] = 'NA'
# data['name_ciudad'] = 'NA'
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
# st.write(data['zipcode'][1000], data['lat'][1000], data['long'][1000])

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

# Mapas 

# info geojson
url2 = 'https://raw.githubusercontent.com/LORDINGBC/ciencia-datos/main/ProyectoPreciosCasas/data/KingCount.geojson'
col1, col2 = st.columns(2)
with col1:
     st.header("Densidad de casas disponibles por código postal")
     
     st.markdown("""
     Puede filtrar por un solo codigo postal y en la parte inferior del mapa le saldra informacion de este lugar. 
      """)


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
st.write(reverse(mapa.location))




# graficos
#  data = pd.read_csv('basededatos/data.csv')

st.title('Cual es el valor promedio de los inmuebles por año de construccion')

habitaciones = st.multiselect(
'cuantas habitaciones',
list(set(data['bedrooms'])),
[1,2,3]
)

banhos = st.multiselect(
'cuantas bañoss',
list(set(data['bathrooms'])),
[1,2,3]
)

sns.set(style="darkgrid")
sns.axes_style("whitegrid")

aux = data[data['bedrooms'].isin(habitaciones) &(data['bathrooms'].isin(banhos))]

df = aux[['sqft_living','yr_built']].groupby('yr_built').mean().reset_index()
fig = sns.lineplot(x= 'yr_built', y='sqft_living', data = df)
fig.set_xlabel('Año de Construcción')
fig.set_ylabel('Precio (USD)')
st.pyplot(fig.figure)









                    


