import streamlit as st
import requests
from requests.structures import CaseInsensitiveDict
import pandas as pd
import gdown
from streamlit_geolocation import streamlit_geolocation

# Function to download the CSV from Google Drive
@st.cache
def download_data_from_drive():
    # Google Drive link for the dataset (convert to direct download link)
    url = 'https://drive.google.com/uc?id=1Tc3Hequ5jVjamAfuPhpBv8JvsOp7LSJY'
    output = 'restaurant_reviews.csv'
    
    # Download the file without printing progress (quiet=True)
    gdown.download(url, output, quiet=True)
    
    # Load the dataset
    return pd.read_csv(output)

# Load the dataset of restaurant reviews
reviews_df = download_data_from_drive()

# Geoapify API keys
GEOAPIFY_API_KEY = "1b8f2a07690b4cde9b94e68770914821"

# Display the title
st.title("Restaurant Recommendation System")

# Use streamlit_geolocation to capture the location
location = streamlit_geolocation()

# Automatically set the latitude and longitude if geolocation is available
if location:
    lat, lon = location['lat'], location['lon']
    coords = f"{lat},{lon}"
    st.write(f"Detected Coordinates: Latitude {lat}, Longitude {lon}")
else:
    # Input for manual entry of geolocation data
    coords = st.text_input("Enter your coordinates (latitude,longitude):")

# Allow the user to change the search radius and category of the restaurant
radius = st.slider("Select search radius (meters):", min_value=1000, max_value=10000, value=5000, step=500)
category = st.selectbox("Select restaurant category:", 
                        ["catering.restaurant", "catering.fast_food", "catering.cafe", "catering.bar"])

# If either geolocation was found or the user has inputted coordinates, proceed
if coords:
    lat, lon = map(float, coords.split(","))
    st.write(f"Using Coordinates: (Latitude: {lat}, Longitude: {lon})")
    
    # Function to fetch restaurant recommendations
    def get_restaurant_recommendations(lat, lon, radius, category):
        url = f"https://api.geoapify.com/v2/places?categories={category}&filter=circle:{lon},{lat},{radius}&limit=10&apiKey={GEOAPIFY_API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            restaurants = data["features"]
            restaurant_list = [
                {
                    "name": place["properties"].get("name", "Unknown name"),
                    "address": place["properties"].get("formatted", "No address available"),
                    "category": place["properties"]["categories"][0]
                }
                for place in restaurants
            ]
            return restaurant_list
        else:
            st.error("Failed to retrieve restaurant data.")
            return []

    # Display restaurant recommendations
    st.header("Nearby Restaurant Recommendations:")
    restaurants = get_restaurant_recommendations(lat, lon, radius, category)

    if restaurants:
        for restaurant in restaurants:
            st.write(f"**{restaurant['name']}**")
            st.write(f"Address: {restaurant['address']}")
            st.write(f"Category: {restaurant['category']}")
            st.write("---")

            # Extract reviews for the recommended restaurant
            restaurant_reviews = reviews_df[reviews_df["Restaurant"].str.contains(restaurant['name'], case=False, na=False)]
            
            if not restaurant_reviews.empty:
                st.write("**Reviews:**")
                for _, review_row in restaurant_reviews.iterrows():
                    st.write(f"- {review_row['Review']} (Rating: {review_row['Rating']})")
            else:
                st.write("No reviews found.")
            st.write("---")
    else:
        st.write("No restaurants found nearby.")
else:
    st.write("Waiting for coordinates...")
