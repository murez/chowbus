import sqlite3
import folium

# Database file name
db_file = 'chowbus.db'

# Your current location (latitude and longitude)
my_location = (40.730610, -73.935242)  # Example: New York City

# Function to fetch restaurant data from the database
def fetch_restaurants():
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    cursor.execute("SELECT name, latitude, longitude, telephone, url FROM restaurants")
    restaurants = cursor.fetchall()

    conn.close()
    return restaurants

# Create a map centered on your location
def create_map(restaurants):
    if not restaurants:
        print("No restaurant data available.")
        return

    # Create the map object centered on your location
    m = folium.Map(location=my_location, zoom_start=12)

    # Add markers for each restaurant
    for name, lat, lng, telephone, url in restaurants:
        google_maps_url = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}"
        popup_content = (
            f"<b>{name}</b><br><a href='{telephone}'>Phone: {telephone}<a><br>"
            f"<a href='{url}' target='_blank'>Website</a><br>"
            f"<a href='{google_maps_url}' target='_blank'>Get Directions</a>"
        )
        folium.Marker(
            location=[lat, lng],
            popup=folium.Popup(popup_content, max_width=300),
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(m)

    # Save the map to an HTML file
    map_file = 'index.html'
    m.save(map_file)
    print(f"Map created and saved to {map_file}")

if __name__ == '__main__':
    restaurants = fetch_restaurants()
    create_map(restaurants)
