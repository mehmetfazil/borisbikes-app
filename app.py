import streamlit as st
import pandas as pd
from db import DB
from tfl import fetch_stations_info
import seaborn as sns
import matplotlib.pyplot as plt
from streamlit_echarts import st_echarts
import numpy as np


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
        # --- Assume you have your DataFrame "df" with a timestamp index ---
        # For example, df might look like:
        #                                   e_bikes  standard_bikes  empty_slots
        # timestamp                                                             
        # 2025-02-01 11:49:02.444169+00:00        2              16            7
        # 2025-02-01 12:00:06.614692+00:00        2              15            8
        # 2025-02-01 12:00:17.211748+00:00        2              16            7
        # ...

# --- 1. Prepare your data ---
# Assume your DataFrame "df" has a timestamp index and the following columns:
#                                   e_bikes  standard_bikes  empty_slots
# timestamp                                                             
# 2025-02-01 11:49:02.444169+00:00        2              16            7
# 2025-02-01 12:00:06.614692+00:00        2              15            8
# 2025-02-01 12:00:17.211748+00:00        2              16            7
# ...

# --- 1. Data Preparation ---
# Assume your DataFrame "df" has a timestamp index and the following columns:
#                                   e_bikes  standard_bikes  empty_slots
# timestamp                                                             
# 2025-02-01 11:49:02.444169+00:00        2              16            7
# 2025-02-01 12:00:06.614692+00:00        2              15            8
# 2025-02-01 12:00:17.211748+00:00        2              16            7
# ...


# --- 1. Data Preparation ---
# Assume your DataFrame "df" has a timestamp index and columns:
#                                   e_bikes  standard_bikes  empty_slots
# timestamp                                                             
# 2025-02-01 11:49:02.444169+00:00        2              16            7
# 2025-02-01 12:00:06.614692+00:00        2              15            8
# 2025-02-01 12:00:17.211748+00:00        2              16            7
# ...

        # Compute total bikes.
        df["total_bikes"] = df["e_bikes"] + df["standard_bikes"]

        # Resample to 15-minute intervals and forward-fill missing data.
        df_resampled = df.resample("15T").ffill()

        # Extract day name and time (15-minute slot in "HH:MM" format).
        df_resampled["day"] = df_resampled.index.day_name()       # e.g., "Monday"
        df_resampled["time"] = df_resampled.index.strftime("%H:%M")  # e.g., "12:00", "12:15", etc.

        # --- 2. Aggregate the Data ---
        # Group by day and time to compute the average total bikes in each 15-minute slot.
        pivot = df_resampled.groupby(["day", "time"])["total_bikes"].mean().unstack()

        # Define the desired order for days starting from Monday.
        days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        pivot = pivot.reindex(days_order, axis=0)

        # Generate a complete list of 15-minute intervals for a full day.
        times = pd.date_range("00:00", "23:45", freq="15T").strftime("%H:%M").tolist()
        pivot = pivot.reindex(times, axis=1)
        pivot = pivot.fillna(0)  # Fill missing values with 0

        # --- 3. Convert the Pivot Table to ECharts Format ---
        # ECharts expects data as a list of [x_index, y_index, value] points.
        data_points = []
        for y_idx, day in enumerate(days_order):
            for x_idx, time_label in enumerate(times):
                value = float(pivot.loc[day, time_label])
                data_points.append([x_idx, y_idx, value])

        # --- 4. Build the ECharts Option Dictionary ---
        option = {
            "tooltip": {"position": "top"},
            "grid": {"height": "50%", "top": "10%"},
            "xAxis": {
                "type": "category",
                "data": times,  # 15-minute intervals along x-axis
                "splitArea": {"show": True},
            },
            "yAxis": {
                "type": "category",
                "data": [day[:3] for day in days_order],  # Days starting from Monday
                "splitArea": {"show": True},
                "inverse": True,     # Inverse so that Monday appears at the top
            },
            "visualMap": {
                "min": 0,
                "max": float(np.nanmax(pivot.to_numpy())),
                "calculable": True,
                "orient": "horizontal",
                "left": "center",
                "bottom": "15%",
                # YlGnBu-like color palette (ColorBrewer 9-class)
                "inRange": {
                    "color": [
                        "#ffffd9",
                        "#edf8b1",
                        "#c7e9b4",
                        "#7fcdbb",
                        "#41b6c4",
                        "#1d91c0",
                        "#225ea8",
                        "#253494",
                        "#081d58",
                    ]
                },
            },
            "series": [
                {
                    "name": "Total Bikes",
                    "type": "heatmap",
                    "data": data_points,
                    "label": {"show": False},  # No annotations on cells
                    "emphasis": {
                        "itemStyle": {
                            "shadowBlur": 10,
                            "shadowColor": "rgba(0, 0, 0, 0.5)",
                        }
                    },
                }
            ],
        }

        # --- 5. Display the ECharts Heatmap in Streamlit ---
        st_echarts(options=option, height="500px")


if __name__ == "__main__":
    main()
