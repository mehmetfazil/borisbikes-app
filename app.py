import streamlit as st
import pandas as pd
from db import DB
from tfl import fetch_stations_info
import seaborn as sns
import matplotlib.pyplot as plt

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

        st.subheader("Total Bikes Over Days")
        # --- 1. Create a "total_bikes" column ---
        df["total_bikes"] = df["e_bikes"] + df["standard_bikes"]

        # --- 2. Resample the DataFrame to 15-minute intervals with forward fill ---
        df_resampled = df.resample("15T").ffill()

        # --- 3. Extract the day of week and time-of-day ---
        df_resampled["day"] = df_resampled.index.day_name()          # e.g., "Monday"
        df_resampled["time"] = df_resampled.index.strftime("%H:%M")     # e.g., "12:00"

        # --- 4. Group by 'day' and 'time' and pivot so that:
        #       - Rows represent days
        #       - Columns represent time-of-day ---
        heatmap_data = df_resampled.groupby(["day", "time"])["total_bikes"].mean().unstack()

        # --- 5. Reindex the rows so that all days appear in order ---
        days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        heatmap_data = heatmap_data.reindex(days_order)

        # --- 6. Ensure time columns are sorted chronologically ---
        # The "HH:MM" format sorts correctly if times are zero-padded.
        heatmap_data = heatmap_data.reindex(
            sorted(heatmap_data.columns, key=lambda t: pd.to_datetime(t, format="%H:%M")), axis=1
        )

        # --- 7. Plot the heatmap without annotating individual cells ---
        plt.figure(figsize=(14, 8))
        sns.heatmap(heatmap_data, cmap="YlGnBu", cbar=True, annot=False)
        plt.tight_layout()

        # --- 8. Display the plot in Streamlit ---
        st.pyplot(plt)

if __name__ == "__main__":
    main()
