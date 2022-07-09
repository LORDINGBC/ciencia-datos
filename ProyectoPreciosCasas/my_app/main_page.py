import folium
import geopandas
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime 

from streamlit_folium import folium_static
from folium.plugins import MarkerCluster

st.set_page_config(page_title='Dashboard - Venta de casas',
                    layout="wide", 
                    page_icon=':rocket:',  
                    initial_sidebar_state="expanded")

st.title('Datos en inmobiliarios en King Country, USA')
st.write('#### Creado por Emilio Andres Arias M.')
st.write('El proposito de este dashboard es mostrar de manera sencilla estadisticas y localizacion de las propiedades en venta en King Count, (USA)')

### Inicio Dataset
@st.cache(allow_output_mutation=True)
def get_data(path):
    data = pd.read_csv(path)

    return data

@st.cache(allow_output_mutation=True)
def get_geofile(url):
    geofile = geopandas.read_file(url)

    return geofile
### Fin Dataset

### Inicio Columna Nueva 
def set_feature(data):
    #add new features
    data['price_m2'] = data['price']/data['sqft_lot']

    return data
### Fin Columna Nueva

### Inicio Parametros de busqueda
def slide_data(data):
    f_zipcode = st.sidebar.multiselect(
    'Código Postal',
    data['zipcode'].unique())

    if (f_zipcode !=[]):
        data = data.loc[data['zipcode'].isin(f_zipcode)]

    elif (f_zipcode != []):
        data = data.loc[data['zipcode'].isin(f_zipcode), :]

    elif (f_zipcode == []):
        data = data.loc[:,]

    else:
        data = data.copy()


    col1, col2 = st.columns((1, 1))

    # Metricas Promedio
    df1 = data[['id','zipcode']].groupby( 'zipcode' ).count().reset_index()
    df2 = data[['price','zipcode']].groupby( 'zipcode').mean().reset_index()
    df3 = data[['sqft_living','zipcode']].groupby( 'zipcode').mean().reset_index()
    df4 = data[['price_m2','zipcode']].groupby( 'zipcode').mean().reset_index()

    # Union
    m1 = pd.merge(df1, df2, on='zipcode', how='inner')
    m2 = pd.merge(m1, df3, on='zipcode', how='inner')
    df = pd.merge(m2, df4, on='zipcode', how='inner')

    df.columns = ['Código Postal', 'Total Casas', 'Precio', 'Pies Cuadrados', 'Precio / M2']

    col1.header('Valores Promedio por código postal')
    col1.dataframe(df, height = 600)

    # Estadisticas Desciptivas
    num_attributes = data.select_dtypes(include = ['int64','float64'])
    media = pd.DataFrame(num_attributes.apply(np.mean))
    mediana = pd.DataFrame(num_attributes.apply(np.median))
    std = pd.DataFrame(num_attributes.apply(np.std))
    max_ = pd.DataFrame(num_attributes.apply(np.max))
    min_ = pd.DataFrame(num_attributes.apply(np.min))

    df1 = pd.concat([max_, min_, media, mediana, std], axis = 1)
    df1.columns = ['Max', 'Min', 'Media', 'Mediana', 'STD']
    st.header('Análisis descriptivo')
    df1 = df1.drop(index =['id', 'lat', 'long','yr_built','yr_renovated'], axis = 0)
    df1.index = ['id','Precio','Habitaciones', 'Baños', 'Área construida (pies cuadrados)', 
                 'Área del terreno (pies cuadrados)', 'Pisos', 'Vista agua', 'Vista'
                 'Condición','Evaluación propiedad (1-13)','Área sobre tierra', 'Área sótano', 
                 'Código Postal', 'Área construída (15)', 
                 'Área del terreno (15)', 'Precio / M2']
    st.dataframe(df1, width = 1000)

    return None

def comercial_data(data):
    st.sidebar.title('Opciones Comerciales')
    st.title('Atributos Comerciales')

    data['date'] = pd.to_datetime(data['date']).dt.strftime('%Y-%m-%d')

    #Filtros
    min_year_built = int(data['yr_built'].min())
    max_year_built = int(data['yr_built'].max())

    st.sidebar.subheader('Año máximo de construcción')
    f_year_built = st.sidebar.slider('Año de construcción', min_year_built,
                                            max_year_built,
                                            min_year_built)

    st.header('Precio promedio por año construido')

    #Selección de datos
    df = data.loc[data['yr_built'] < f_year_built]
    df = df[['yr_built', 'price']].groupby('yr_built').mean().reset_index()

    fig = px.line(df, x='yr_built', y='price')
    st.plotly_chart( fig, use_container_width=True)

    st.header('Precio promedio por día')
    st.sidebar.subheader('Fecha máxima')

    #Filtros
    min_date = datetime.strptime(data['date'].min(), '%Y-%m-%d')
    max_date = datetime.strptime(data['date'].max(), '%Y-%m-%d')

    f_date = st.sidebar.slider('Fecha', min_date, max_date, min_date)

    #Filtrado de Datos
    data['date'] = pd.to_datetime(data['date'])
    df = data.loc[data['date'] < f_date]
    df= df[['date', 'price']].groupby('date').mean().reset_index()

    fig = px.line(df, x='date', y='price')

    st.plotly_chart( fig, use_container_width=True)

    #----------Histograma------------#
    st.header('Distribución de precios')
    st.sidebar.subheader('Precio Máximo')

    #Filtros
    min_price = int(data['price'].min())
    max_price = int(data['price'].max())
    avg_price = int(data['price'].mean())

    #Filtrado de Datos
    f_price = st.sidebar.slider('Precio', min_price, max_price, avg_price)
    df = data.loc[data['price'] < f_price]

    #Grafico
    fig = px.histogram( df, x='price', nbins=50)
    st.plotly_chart(fig, use_container_width=True)
    return None

def map_density(data, geofile):
    st.title('Descripción de región')

    col1, col2 = st.columns((1, 1))

    col1.header('Portafolio de cartera')
    #df = data.sample(10)
    df = data.copy()

    ##Mapa base -- Portafolio
    density_map = folium.Map(location=[data['lat'].mean(),
                  data['long'].mean()],
                  default_zoom_start=15)


    marker_cluster = MarkerCluster().add_to(density_map)
    for name, row in df.iterrows():
        folium.Marker([row['lat'], row['long']],
        popup='Vendido ${0} en: {1}. Características: {2} Pies Cuadrados, {3} Habitaciones, {4} Baños, Año construcción: {5}'.format(
                                                            row['price'],
                                                            row['date'],
                                                            row['sqft_living'],
                                                            row['bedrooms'],
                                                            row['bathrooms'],
                                                            row['yr_built'])).add_to(marker_cluster)

    with col1:
        folium_static(density_map)                                                    
########################################################################################################################################################
    col2.header('Densidad de Precio')
    df = data[['price', 'zipcode']].groupby('zipcode').mean().reset_index()
    df.columns = ['ZIP', 'PRICE']

    geofile = geofile[geofile['ZIP'].isin(df['ZIP'].tolist())]

    region_price_map = folium.Map(location=[data['lat'].mean(),
                       data['long'].mean()],
                       default_zoom_start=15)

    region_price_map.choropleth(data = df,
                                geo_data = geofile,
                                columns = ['ZIP', 'PRICE'],
                                key_on = 'feature.properties.ZIP',
                                fill_color = 'YlOrRd',
                                fill_opacity = 0.7,
                                line_opacity = 0.2,
                                legend_name = 'AVG PRICE')
    
    with col2:
        folium_static(region_price_map)

    return None

def attributes_distribution(data):
    st.sidebar.title( 'Atributos')
    st.title( 'Atributos de la casa')

    ##Filtros
    f_bedrooms = st.sidebar.selectbox('Número máximo de habitaciones',
                                  sorted(set(data['bedrooms'].unique())))

    f_bathrooms = st.sidebar.selectbox('Número máximo de baños',
                                   sorted(set(data['bathrooms'].unique())))


    c1, c2 = st.columns(2)

    # House per bedrooms
    c1.header('Casas por habitacion')
    df = data[data['bedrooms'] < f_bedrooms]
    fig = px.histogram(df, x='bedrooms', nbins=19)
    c1.plotly_chart(fig, use_container_width=True)

    # House per bathrooms
    c2.header('Casas por baño')
    df = data[data['bathrooms'] < f_bathrooms]
    fig = px.histogram(df, x='bathrooms', nbins=50)
    c2.plotly_chart(fig, use_container_width=True)

    #filters
    f_floors = st.sidebar.selectbox('Número máximo de pisos',
                                sorted(set(data['floors'].unique())))
    
    
    # House per floors
    st.header('Casas por No. de pisos')
    df = data[data['floors'] < f_floors]

    #plot
    fig = px.histogram(df, x='floors', nbins=50)
    st.plotly_chart(fig, use_container_width=True)
    return None

### Fin Parametros de busqueda

### Iniciacion de metodo principal, y este encapsula los metodos definidos
if __name__ == '__main__':

    ##DataSets (Archivo CSV, Archivo GeoJson)
    path = 'https://raw.githubusercontent.com/DarthShadow147/DataSetDiplomado/master/DataAccess/kc_house_data.csv'
    url = 'https://raw.githubusercontent.com/DarthShadow147/DataSetDiplomado/master/DataAccess/KingCountry.geojson'

    ##Metodos para obtener datos
    data = get_data(path)
    geofile = get_geofile(url)

    ## Metodo para transformar datos precio / M2
    data = set_feature(data)
    ## Metodos para obtener Analisis descriptivo y Parametros por codigo postal
    slide_data(data)
    ## Metodo para obtener graficos de precio promedio por año, por dia y distribucion de precios, adicionalmente de nuevos filtros
    comercial_data(data)
    ## Metodo para obtener mapas de ubicacion de las casas en venta y su densidad de precio
    map_density(data, geofile)
    ## Metodo para obtener graficos de casas por habitacion, baño y No pisos, adicionalmente nuevos filtros
    attributes_distribution(data)
### Fin de Iniciacion de metodo principal
