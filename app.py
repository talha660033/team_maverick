import streamlit as st
import pandas as pd 
import numpy as np
import pydeck as pdk
import plotly.express as px
import base64
import time
import zipfile
# https://data.cityofnewyork.us/api/views/h9gi-nx95/rows.csv?accessType=DOWNLOAD
with zipfile.ZipFile('data_set.zip', 'r') as zip_ref:
    zip_ref.extractall('.')
DATA_URL=(
    "data_set.csv"
)

def streamlit_styling():
    st.set_page_config(
    page_title="EDA NYK City",
    page_icon="📊",
    initial_sidebar_state="expanded",
    layout="wide",
    )
    def add_bg_from_local(image_file):
        with open(image_file, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())
        st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url(data:image/{"png"};base64,{encoded_string.decode()});
            background-size: cover
        }}
        </style>
        """,
        unsafe_allow_html=True
        )
    add_bg_from_local('background.jpg')
    hide_st_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
    """

    st.markdown(hide_st_style,unsafe_allow_html=True)

@st.cache_data(persist=True) 
def load_data(nrows):
    st.title("Motor Vehicle Collision EDA 📊")
    st.markdown("This application is a Dashboard that can be used to analyze motor vehicle collisions in NYC.")
    data = pd.read_csv(DATA_URL, nrows = nrows, parse_dates=[['CRASH DATE', 'CRASH TIME']])
    data.dropna(subset=['LATITUDE',"LONGITUDE"], inplace=True)
    lowercase = lambda x:str(x).lower()
    data.rename(lowercase, axis='columns', inplace=True)
    data.rename(columns={'crash date_crash time':'date/time'}, inplace = True)
    data.rename(columns={'on street name':'on_street_name'}, inplace = True)
    data.rename(columns={'cross street name':'cross_street_name'}, inplace = True)
    data.rename(columns={'number of persons injured':'injured_people'}, inplace = True)
    data.rename(columns={'number of pedestrians injured':'injured_pedestrians'}, inplace = True)
    data.rename(columns={'number of cyclist injured':'injured_cyclists'}, inplace = True)
    data.rename(columns={'number of motorist injured':'injured_motorists'}, inplace = True)
    data.rename(columns={'number of persons killed':'killed_people'}, inplace = True)
    data.rename(columns={'number of pedestrians killed':'killed_pedestrians'}, inplace = True)
    data.rename(columns={'number of cyclist killed':'killed_cyclists'}, inplace = True)
    data.rename(columns={'number of motorist killed':'killed_motorists'}, inplace = True)
    return data

def most_people_injured():
    st.header("Where are the most people injured in NYC?")
    injured_people = st.slider("Number of persons injured in a crash",0,19)
    color1 = st.color_picker('Pick A Color for the dots for seeing injured people')
    st.map(data.query("injured_people >= @injured_people")[['latitude','longitude']].dropna(how="any"),color=color1)

def most_people_killed():
    st.header("Where are the most people killed in NYC?")
    killed_people = st.slider("Number of persons killed in a crash",1,3)
    color2 = st.color_picker('Pick A Color for the dots for seeing killed people')
    st.map(data.query("killed_people >= @killed_people")[['latitude','longitude']].dropna(how="any"),color=color2)

def collisions_during_given_time(data,hour):
    st.header("How many collissions occur during a given time of day?")
    data= data[data['date/time'].dt.hour==hour]
    st.markdown("Vehicle Collissions between %i:00 and %i:00" % (hour, (hour+1)%24) )
    midpoint = (np.average(data['latitude']), np.average(data['longitude']))
    st.write(
        pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            initial_view_state={
                "latitude":midpoint[0],
                "longitude":midpoint[1],
                "zoom":11,
                "pitch":50,

            },
            layers=[
                pdk.Layer(
                    "HexagonLayer",
                    data=data[['date/time','latitude','longitude']],
                    get_position= ['longitude','latitude'],
                    radius=100,
                    extruded=True,
                    pickable=True,
                    elevation_scale=4,
                    elevation_range=[0,1000]
                ),
            ],
        )
    )
    return data

def streets_where_most_injured():
    st.header("Top 5 dangerous streets by affected type")
    select = st.selectbox("where most of the people got injured", ['Pedestrians','Cyclists','Motorists'])
    if select=="Pedestrians":
        st.dataframe(original_data.query("injured_pedestrians >=1")[["on_street_name","injured_pedestrians"]].sort_values(by=['injured_pedestrians'],ascending=False).dropna(how="any")[:5],width=1600)    
    elif select=="Cyclists":
        st.dataframe(original_data.query("injured_cyclists >=1")[["on_street_name","injured_cyclists"]].sort_values(by=['injured_cyclists'],ascending=False).dropna(how="any")[:5],width=1600)
    else:
        st.dataframe(original_data.query("injured_motorists >=1")[["on_street_name","injured_motorists"]].sort_values(by=['injured_motorists'],ascending=False).dropna(how="any")[:5],width=1600)

def streets_where_most_killed():
    st.header("Top 5 dangerous streets by affected type")
    selectkilled = st.selectbox("where most of the people got killed", ['Pedestrians','Cyclists','Motorists'])
    if selectkilled=="Pedestrians":
        st.dataframe(original_data.query("killed_pedestrians >=1")[["on_street_name","killed_pedestrians"]].sort_values(by=['killed_pedestrians'],ascending=False).dropna(how="any")[:5],width=1600)
    elif selectkilled=="Cyclists":
        st.dataframe(original_data.query("killed_cyclists >=1")[["on_street_name","killed_cyclists"]].sort_values(by=['killed_cyclists'],ascending=False).dropna(how="any")[:5],width=1600)
    else:
        st.dataframe(original_data.query("killed_motorists >=1")[["on_street_name","killed_motorists"]].sort_values(by=['killed_motorists'],ascending=False).dropna(how="any")[:5],width=1600)

def best_commute_time():
    st.header("Commute Time Finder")
    destination1 = st.selectbox("Enter starting point", data['borough'].dropna(how="any").unique())
    destination2 = st.selectbox("Enter ending point", data['borough'].dropna(how="any").unique())
    original_data['date/time'] = pd.to_datetime(original_data['date/time'])
    original_data['hour'] = original_data['date/time'].dt.hour
    data['hour']=original_data['hour']
    borough_hour_crashes = original_data.groupby(['borough', 'hour']).size()
    least_crashes = borough_hour_crashes.groupby(level=0).idxmin()
    dest1_least_crash_hour = least_crashes[destination1][1] if destination1 in least_crashes else None
    dest2_least_crash_hour = least_crashes[destination2][1] if destination2 in least_crashes else None
    st.write(f"The hour with the least crashes in {destination1} is: {dest1_least_crash_hour}")
    st.write(f"The hour with the least crashes in {destination2} is: {dest2_least_crash_hour}")


def reasons_for_accidents(original_data):
    original_data.rename(columns={'contributing factor vehicle 1':'contributing_factors'}, inplace = True)
    st.header("Common reasons for accidents")
    common_reasons = original_data["contributing_factors"].value_counts()
    top_5_reasons_data = original_data[original_data["contributing_factors"].isin(common_reasons.index)]
    hist2 = top_5_reasons_data["contributing_factors"].value_counts()
    chart_data2 = pd.DataFrame({"Reasons of Accidents": hist2.index, "Number of Accidents": hist2.values})
    chart_data2.sort_values(by="Number of Accidents", ascending=False, inplace=True)
    fig =px.bar(chart_data2, x="Reasons of Accidents", y="Number of Accidents", height=600, width=1600)
    st.write(fig)

def show_row_data(data):
    if st.checkbox("Show Raw Data", False):
        with st.spinner(text='Data Manipulation in progress'):
            time.sleep(1)
            st.success('Showing updated data.')
            st.subheader('Raw Data')
            st.write(data)


streamlit_styling()
data =  load_data(100000)
original_data=data
most_people_injured()
most_people_killed()
hour = st.slider("Hour to look at",0,23)
data = collisions_during_given_time(data,hour)
reasons_for_accidents(original_data)
streets_where_most_injured()
streets_where_most_killed()
best_commute_time()
show_row_data(data)