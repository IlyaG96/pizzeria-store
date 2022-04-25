import requests
from geopy.distance import distance as dist


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(' ')
    return lat, lon


def get_distance(pizzeria):
    return pizzeria['distance']


def show_nearest_pizzeria(pizzerias, user_location):

    for pizzeria in pizzerias:
        distance = dist(
            pizzeria['coordinates'], user_location,
        ).km
        pizzeria['distance'] = distance
    nearest_pizzeria = min(pizzerias, key=get_distance)

    return nearest_pizzeria
