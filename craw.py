import requests
from bs4 import BeautifulSoup
import json
from geopy.geocoders import Nominatim
from typing import Dict
import sqlite3
import re

geolocator = Nominatim(user_agent="chowbus")
address_keys = ["streetAddress", "addressLocality", "addressRegion", "postalCode"]

def extract_json_containing_key(data, key):
    # Find the nearest { and } around the key
    match = re.search(r'\{[^{}]*' + re.escape(key) + r'[^{}]*\}', data)
    if match:
        json_str = match.group()
        try:
            json_str = json_str.replace("\\", "")
            # Attempt to parse the JSON string
            parsed_json = json.loads(json_str)
            return parsed_json
        except json.JSONDecodeError:
            return f"Invalid JSON: {json_str}"
    else:
        print(data)
        raise Exception(f"Key '{key}' not found in the data")


def scrape_chowbus(id: int) -> Dict:
    url = f"https://pos.chowbus.com/online-ordering/store/{id}/"

    # Send HTTP GET request to fetch the web page
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"}
    
    response = requests.get(url, headers=headers, timeout=10)

    if response.status_code != 200:
        print(f"Failed to fetch the page. Status code: {response.status_code}")
        return

    # Parse the page content using BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    script_tag = soup.find("script")

    # if script_tag is json:
    script_is_json = False

    try:
        json.loads(script_tag.get_text())
        script_is_json = True
    except json.JSONDecodeError:
        pass

    if script_is_json:
        json_data = json.loads(script_tag.get_text())
        restaurant_name = json_data["name"]
        address = ", ".join([json_data["address"][key] for key in address_keys if key in json_data["address"]])
        lat = json_data["geo"]["latitude"]
        long = json_data["geo"]["longitude"]
        telephone = "tel:" + json_data["telephone"]
        

    else:
    # Find the restaurant name
        try:
            restaurant_name_tag = soup.find(class_=lambda c: c and ("restaurant_name" in c or "restaurantName" in c))
            restaurant_name = restaurant_name_tag.get_text(strip=True) if restaurant_name_tag else "Restaurant name not found"

    # Find the restaurant address HTML
            script_list = soup.find_all("script")
            for script in script_list:
                # find  if "address_1" in script
                if "address_1" in script.get_text():
                    address_script = script.get_text()
                    break
            address_json = extract_json_containing_key(address_script.replace('"])', "}").replace("self.__next_f.push([1,", "{id: "), "address_1")
            print(address_json)

            address = address_json["address_1"] + "," + address_json["city"] + "," + address_json["state"] + "," + address_json["zip_code"]

            lat, long = address_json["latitude"], address_json["longitude"]

            telephone_tag = soup.find(class_=lambda c: c and "BrandSection_telephone" in c) 
            # get a tag and get href attribute
            telephone = telephone_tag.find("a").get("href") if telephone_tag else "Telephone not found"

            
        except Exception as e:
            print(f"Failed to scrape restaurant with ID {id}")
            print(e)
            return
    return {
            "id": id,
            "name": restaurant_name,
            "address": address,
            "latitude": lat,
            "longitude": long,
            "telephone": telephone,
            "url": url,
        }

if __name__ == "__main__":
    conn = sqlite3.connect("chowbus.db")
    cursor = conn.cursor()

    cursor.execute("CREATE TABLE IF NOT EXISTS restaurants (id INTEGER PRIMARY KEY, name TEXT, address TEXT, latitude REAL, longitude REAL, telephone TEXT, url TEXT)")

    for id in range(1, 20000):
        print(f"Scraping restaurant with ID: {id}")
        restaurant = scrape_chowbus(id)
        if restaurant:
            print(restaurant)
            # overwrite the existing data
            cursor.execute("INSERT OR REPLACE INTO restaurants VALUES (?, ?, ?, ?, ?, ?, ?)", (restaurant["id"], restaurant["name"], restaurant["address"], restaurant["latitude"], restaurant["longitude"], restaurant["telephone"], restaurant["url"]))
            conn.commit()
    
    conn.close()