"""
Live AQI Feature Pipeline
Fetches AQICN data, engineers features, and uploads to Hopsworks Feature Store.
Stable version (no read dependency, no Kafka issues).
"""

import requests
import json
import pandas as pd
from datetime import datetime
import os
import hopsworks
from dotenv import load_dotenv

load_dotenv()

CITY = "A540745"
AQICN_TOKEN = os.getenv("AQICN_TOKEN")

HOPSWORKS_API_KEY = os.getenv("HOPSWORKS_API_KEY")
PROJECT_NAME = "ShineProject"

LOCAL_FILE = "dummy_data.json"



def fetch_and_save_data(city, token):
    url = f"https://api.waqi.info/feed/{city}/?token={token}"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"API Error: {response.status_code}")
        return None

    data = response.json()

    if data["status"] != "ok":
        print("API returned error")
        return None

    with open(LOCAL_FILE, "w") as f:
        json.dump(data, f)

    print("Live data fetched and saved")
    return data["data"]


def load_local_data():
    if not os.path.exists(LOCAL_FILE):
        return None

    with open(LOCAL_FILE, "r") as f:
        return json.load(f)["data"]



def generate_features(raw):
    if not raw:
        return None

    now = datetime.now()
    iaqi = raw.get("iaqi", {})

    df = pd.DataFrame([{
        "timestamp": now,
        "target_aqi": raw.get("aqi", 0),
        "pm25": iaqi.get("pm25", {}).get("v", 0),
        "pm10": iaqi.get("pm10", {}).get("v", 0),
        "temp": iaqi.get("t", {}).get("v", 0),
        "humidity": iaqi.get("h", {}).get("v", 0),
        "wind_speed": iaqi.get("w", {}).get("v", 0),
        "hour": now.hour,
        "day": now.day,
        "month": now.month,
        "day_of_week": now.weekday(),
    }])


    for col in df.columns:
        if col == "temp":
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype("float64")
        elif col != "timestamp":
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype("int64")

    return df


def upload_to_hopsworks(df):
    print("Connecting to Hopsworks...")

    project = hopsworks.login(
        project=PROJECT_NAME,
        api_key_value=HOPSWORKS_API_KEY,
        host="eu-west.cloud.hopsworks.ai",
        port=443
    )

    fs = project.get_feature_store()

    fg = fs.get_or_create_feature_group(
        name="lahore_aqi_features",
        version=2,
        primary_key=["timestamp"],
        description="AQI features for Lahore"
    )


    df["aqi_change_rate"] = 0
    df["aqi_change_rate"] = df["aqi_change_rate"].astype("int64")

    fg.insert(df)

    print("Upload successful")


if __name__ == "__main__":

    FETCH_LIVE = os.getenv("FETCH_LIVE", "true").lower() == "true"

    raw = fetch_and_save_data(CITY, AQICN_TOKEN) if FETCH_LIVE else load_local_data()

    df = generate_features(raw)

    if df is not None:
        upload_to_hopsworks(df)
    else:
        print("No data to process")
