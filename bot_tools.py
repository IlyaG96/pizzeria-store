from textwrap import dedent
import requests
from geopy.distance import distance as dist


def format_product_description(product_description):
    product_description = product_description['data']

    formatted_product_description = dedent(
        f'''
        Название : {product_description['name']}
        Описание : {product_description['description']}
        '''
    )

    return formatted_product_description


def format_cart(cart_items, total_price):
    cart = cart_items['data']
    formatted_cart = ''
    for item in cart:
        product = item['name']
        quantity = item['quantity']
        price = item['meta']['display_price']['without_tax']['value']['formatted']
        description = item['description']
        formatted_cart += dedent(
            f'''
        Товар {product} 
        {description}
        
        В количестве: {quantity} шт
        На сумму: {price}
        ''')

    return dedent(
        f'''
    {formatted_cart}
    Общая сумма: {total_price}
    ''')


class BidirectionalIterator(object):
    def __init__(self, collection):
        self.collection = collection
        self.index = 0

    def next(self):
        try:
            self.index += 1
            result = self.collection[self.index]
        except IndexError:
            self.index -= 1
            raise StopIteration
        return result

    def prev(self):
        self.index -= 1
        if self.index < 0:
            self.index = 0
            raise StopIteration
        return self.collection[self.index]

    def __iter__(self):
        return self


def build_menu(buttons, n_cols,
               header_buttons=None,
               footer_buttons=None):
    menu = [buttons[button:button + n_cols] for button in range(0, len(buttons), n_cols)]
    if header_buttons:
        for button in header_buttons:
            menu.insert(0, button)
    if footer_buttons:
        for button in footer_buttons:
            menu.append(button)
    return menu


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
