import streamlit as st
import pandas as pd
from db import DB
from tfl import fetch_stations_info

stations_info = fetch_stations_info()
station_names = tuple([s[0] for s in stations_info])
station_ids = tuple([s[1] for s in stations_info])

def main():
    selected_station = st.selectbox(
        "Station",
        station_names,
        index=None,
        placeholder="Select a station..."
    )

    if selected_station:
        # Find the index of the selected station name
        selected_index = station_names.index(selected_station)

        # Get the corresponding station_id
        station_id = station_ids[selected_index]

        # Connect to the DB and query
        db = DB()
        data = db.get_station_data(station_id)[10:]
        latest_info = db.get_latest_station_data(station_id)
        db.close()

        if latest_info:
            # Extract the latest station information
            timestamp, e_bikes, standard_bikes, empty_slots = latest_info

            # Display the latest info as KPI cards in one row
            st.subheader("Station Overview")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("E-Bikes", e_bikes)

            with col2:
                st.metric("Standard Bikes", standard_bikes)

            with col3:
                st.metric("Empty Docks", empty_slots)

        # Convert to a pandas DataFrame
        df = pd.DataFrame(data, columns=["timestamp", "e_bikes", "standard_bikes", "empty_slots"])

        # Parse timestamps for time-based charts
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # Set 'timestamp' as index for time-series data
        df.set_index("timestamp", inplace=True)

        # Display separate line charts
        st.subheader("E-Bikes Over Time")
        st.line_chart(df["e_bikes"])

        st.subheader("Standard Bikes Over Time")
        st.line_chart(df["standard_bikes"])

if __name__ == "__main__":
    main()
