import sqlite3
import pandas as pd
import plotly.graph_objects as go
import os
import streamlit as st

# Connect to database
connection = sqlite3.connect("covid_19.db")
daily_report = pd.read_sql("""SELECT * FROM daily_report;""", con=connection)
time_series = pd.read_sql("""SELECT * FROM time_series;""", con=connection)
connection.close()

# Convert 'reported_on' to datetime objects right after loading for accurate filtering and plotting
time_series["reported_on"] = pd.to_datetime(time_series["reported_on"])

total_cases = daily_report["confirmed"].sum()
total_deaths = daily_report["deaths"].sum()
# To get the total doses, find the latest (max) cumulative number for each country, then sum those values.
total_vaccinated = time_series.groupby('country')['doses_administered'].max().sum()
sum_confirmed_by_country = daily_report.groupby("country")["confirmed"].sum().sort_values(ascending=False)
top_confirmed = sum_confirmed_by_country.index[:30].to_list()

# Function to create map
def filter_global_map(country_names):
    filtered_daily_report = daily_report[daily_report["country"].isin(country_names)]
    
    # Extract values for hover
    countries = filtered_daily_report["country"].values
    provinces = filtered_daily_report["province"].values
    counties = filtered_daily_report["county"].values
    confirmed = filtered_daily_report["confirmed"].values
    deaths = filtered_daily_report["deaths"].values
    
    # Empty list to store country covid info when hover is on certain country
    information_when_hovered = []
    for country, province, county, c, d in zip(countries, provinces, counties, confirmed, deaths):
        if county is not None:
            marker_information = [(country, province, county), c, d]
        elif province is not None:
            marker_information = [(country, province), c, d]
        else:
            marker_information = [country, c, d]
        information_when_hovered.append(marker_information)

    fig = go.Figure(
        go.Scattermapbox(lat=filtered_daily_report["latitude"],
                            lon=filtered_daily_report["longitude"],
                            customdata=information_when_hovered,
                            hoverinfo="text",
                            hovertemplate="Location: %{customdata[0]}<br>Confirmed: %{customdata[1]}<br>Deaths: %{customdata[2]}",
                            mode="markers",
                            marker={"size": filtered_daily_report["confirmed"],
                                    "color": filtered_daily_report["confirmed"],
                                    "sizemin": 2,
                                    "sizeref": filtered_daily_report["confirmed"].max()/2500,
                                    "sizemode": "area"}
        )
    )
    fig.update_layout(mapbox_style="open-street-map",
                        mapbox=dict(zoom=2,
                                    center=go.layout.mapbox.Center(
                                    lat=0,
                                    lon=0),
                                    )
                        )
    return fig

# Streamlit app
st.title("Covid 19 Global Dashboard")

# Global Map Tab
st.header("Global Map")
st.write(f"Total cases: {total_cases:,}")
st.write(f"Total deaths: {total_deaths:,}")
st.write(f"Total doses administered: {total_vaccinated:,}")

country_names = st.multiselect(
    "Select countries:",
    options=daily_report["country"].unique().tolist(),
    default=top_confirmed
)

global_map = filter_global_map(country_names)
st.plotly_chart(global_map)

# Country Time Series Tab
st.header("Country Time Series")

country = st.selectbox(
    "Select a country:",
    options=time_series["country"].unique().tolist(),
    index=time_series["country"].unique().tolist().index("*Australia*") if "Australia*" in time_series["country"].unique() else 0
)

filtered_time_series = time_series[time_series["country"] == country]

st.subheader(f"Confirmed Cases in {country}")
st.line_chart(data=filtered_time_series, x="reported_on", y="confirmed")
st.subheader(f"Deaths in {country}")
st.line_chart(data=filtered_time_series, x="reported_on", y="deaths")
st.subheader(f"Doses Administered in {country}")
st.line_chart(data=filtered_time_series, x="reported_on", y="doses_administered")
