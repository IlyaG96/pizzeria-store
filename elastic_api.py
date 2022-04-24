import requests


def fetch_addresses():
    url = 'https://dvmn.org/media/filer_public/90/90/9090ecbf-249f-42c7-8635-a96985268b88/addresses.json'
    response = requests.get(url)
    response.raise_for_status()

    return response.json()


def fetch_menu():
    url = 'https://dvmn.org/media/filer_public/a2/5a/a25a7cbd-541c-4caf-9bf9-70dcdf4a592e/menu.json'
    response = requests.get(url)
    response.raise_for_status()

    return response.json()


def get_client_auth(client_secret, client_id):
    data = {
        f'client_id': {client_id},
        f'client_secret': {client_secret},
        'grant_type': 'client_credentials'
    }

    response = requests.post('https://api.moltin.com/oauth/access_token',
                             data=data)
    response.raise_for_status()

    return response.json()


def add_product(token, product, num):
    headers = {
        'Authorization': f'Bearer {token}',
    }

    json_data = {
        'data': {
            'type': 'product',
            'name': f'{product["name"]}',
            'slug': str(f'pizza-{num}'),
            'sku': str(f'pizza-{num}'),
            'description': f'{product["description"]}',
            'manage_stock': False,
            'price': [
                {
                    'amount': f'{product["price"]}',
                    'currency': 'RUB',
                    'includes_tax': True,
                },
            ],
            'status': 'live',
            'commodity_type': 'physical',
        },
    }

    response = requests.post('https://api.moltin.com/v2/products',
                             headers=headers,
                             json=json_data)

    response.raise_for_status()

    return response.json()


def get_all_products(token):
    headers = {
        'Authorization': f'Bearer {token}',
    }

    response = requests.get('https://api.moltin.com/v2/products',
                            headers=headers)
    response.raise_for_status()

    return response.json()


def get_product_info(elastic_token, product_id):
    headers = {
        'Authorization': f'Bearer {elastic_token}',
    }

    response = requests.get(f'https://api.moltin.com/v2/products/{product_id}',
                            headers=headers)
    response.raise_for_status()

    return response.json()


def delete_product(token, product_id):
    headers = {
        'Authorization': f'Bearer {token}',
    }

    response = requests.delete(f'https://api.moltin.com/v2/products/{product_id}',
                               headers=headers)
    response.raise_for_status()


def delete_image(token, image_id):
    headers = {
        'Authorization': f'Bearer {token}',
    }

    response = requests.delete(f'https://api.moltin.com/v2/files/{image_id}',
                               headers=headers)
    response.raise_for_status()


def upload_image(token, image_url):
    headers = {
        'Authorization': f'Bearer {token}',
    }

    files = {
        'file_location': (None, f'{image_url}'),
    }

    response = requests.post('https://api.moltin.com/v2/files',
                             headers=headers,
                             files=files)
    response.raise_for_status()

    return response.json()


def get_all_images(token):
    headers = {
        'Authorization': f'Bearer {token}',
    }

    response = requests.get('https://api.moltin.com/v2/files',
                            headers=headers)
    response.raise_for_status()

    return response.json()


def bind_image_with_product(token, image_id, product_id):
    headers = {
        'Authorization': f'Bearer {token}',
    }

    json_data = {
        'data': {
            'type': 'main_image',
            'id': f'{image_id}',
        },
    }

    response = requests.post(f'https://api.moltin.com/v2/products/{product_id}/relationships/main-image',
                             headers=headers,
                             json=json_data)
    response.raise_for_status()

    return response.json()


def create_currency(token, currency, default, enable):
    headers = {
        'Authorization': f'Bearer {token}',
    }

    json_data = {
        'data': {
            'type': 'currency',
            'code': currency,
            'exchange_rate': 1,
            'format': '{price}',
            'decimal_point': '.',
            'thousand_separator': ',',
            'decimal_places': 2,
            'default': default,
            'enabled': enable,
        },
    }

    response = requests.post('https://api.moltin.com/v2/currencies',
                             headers=headers,
                             json=json_data)
    response.raise_for_status()

    return response.json()


def get_all_currencies(token):
    headers = {
        'Authorization': f'Bearer {token}',
    }

    response = requests.get('https://api.moltin.com/v2/currencies',
                            headers=headers)
    response.raise_for_status()

    return response.json()


def delete_currency(token, currency_id):
    headers = {
        'Authorization': f'Bearer {token}',
    }

    response = requests.delete(f'https://api.moltin.com/v2/currencies/{currency_id}',
                               headers=headers)
    response.raise_for_status()

    return response.json()


def update_currency(token, currency_id):
    headers = {
        'Authorization': f'Bearer {token}',
    }

    json_data = {
        'data': {
            'type': 'currency',
            'exchange_rate': 1.0,
            'format': '{price}',
        },
    }

    response = requests.put(f'https://api.moltin.com/v2/currencies/{currency_id}',
                            headers=headers,
                            json=json_data)
    response.raise_for_status()

    return response.json()


def create_flow(token, name, slug, description):
    headers = {
        'Authorization': f'{token}',
    }

    json_data = {
        'data': {
            'type': 'flow',
            'name': name,
            'slug': slug,
            'description': description,
            'enabled': True,
        },
    }

    response = requests.post('https://api.moltin.com/v2/flows',
                             headers=headers,
                             json=json_data)
    response.raise_for_status()

    return response.json()


def delete_flow(token, flow_id):
    headers = {
        'Authorization': f'Bearer {token}',
    }

    response = requests.delete(f'https://api.moltin.com/v2/flows/{flow_id}',
                               headers=headers)
    response.raise_for_status()


def get_flow(token, flow_id):
    headers = {
        'Authorization': f'Bearer {token}',
    }

    response = requests.get(f'https://api.moltin.com/v2/flows/{flow_id}',
                            headers=headers)
    response.raise_for_status()

    return response.json()


def create_field(token, name, field_type, flow_id, description):
    headers = {
        'Authorization': f'{token}',
    }

    json_data = {
        'data': {
            'type': 'field',
            'name': name,
            'slug': f'{name}-field-slug',
            'field_type': field_type,
            'description': description,
            'required': False,
            'enabled': True,
            'omit_null': False,
            'relationships': {
                'flow': {
                    'data': {
                        'type': 'flow',
                        'id': f'{flow_id}',
                    },
                },
            },
        },
    }

    response = requests.post('https://api.moltin.com/v2/fields',
                             headers=headers,
                             json=json_data)
    response.raise_for_status()


def get_all_fields(token):
    headers = {
        'Authorization': f'Bearer {token}',
    }

    response = requests.get('https://api.moltin.com/v2/fields',
                            headers=headers)
    response.raise_for_status()

    return response.json()


def get_fields_by_flow(token, flow_slug):
    headers = {
        'Authorization': f'Bearer {token}',
    }

    response = requests.get(f'https://api.moltin.com/v2/flows/{flow_slug}/fields',
                            headers=headers)
    response.raise_for_status()

    return response.json()


def create_entry(token, fields_slugs, values, flow_slug):
    headers = {
        'Authorization': f'Bearer {token}',
    }
    json_data = {
        'data': {'type': 'entry'}
    }
    for slug, value in zip(fields_slugs, values):
        json_data['data'].update({
            slug: value
        })
    response = requests.post(f'https://api.moltin.com/v2/flows/{flow_slug}/entries',
                             headers=headers,
                             json=json_data)
    response.raise_for_status()
    return response.json()


def update_entry(token, entry_id, field_slug, value, flow_slug):
    headers = {
        'Authorization': f'Bearer {token}',
    }

    json_data = {
        'data': {
            'id': entry_id,
            'type': 'entry',
            field_slug: value}
    }

    response = requests.put(f'https://api.moltin.com/v2/flows/{flow_slug}/entries/{entry_id}',
                            headers=headers,
                            json=json_data)
    print(response.json())
    response.raise_for_status()

    return response.json()


def get_all_entries(token, flow_slug):
    headers = {
        'Authorization': f'Bearer {token}',
    }

    params = {
        'page': 100,
    }

    response = requests.get(f'https://api.moltin.com/v2/flows/{flow_slug}/entries',
                            headers=headers,
                            params=params)
    response.raise_for_status()

    return response.json()


def get_flow_id_by_slug(token, flow_slug):
    headers = {
        'Authorization': f'Bearer {token}',
    }

    response = requests.get(f'https://api.moltin.com/v2/flows/{flow_slug}/fields',
                            headers=headers)
    response.raise_for_status()

    return next(iter(response.json().get('data'))).get('relationships')['flow']['data']['id']


def get_image_link(elastic_token, product_image_id):
    headers = {
        f'Authorization': f'Bearer {elastic_token}',
    }

    response = requests.get(f'https://api.moltin.com/v2/files/{product_image_id}',
                            headers=headers)
    response.raise_for_status()
    image_link = response.json()['data']['link']['href']

    return image_link


def add_addresses(client_secret, client_id):
    token = get_client_auth(client_secret, client_id).get('access_token')

    fields = get_fields_by_flow(token, flow_slug='pizzeria')
    fields_slugs = [field['slug'] for field in fields['data']]
    addresses = fetch_addresses()
    for address in addresses:
        try:
            values = [
                address.get('address').get('full'),
                address.get('alias'),
                float(address.get('coordinates').get('lon')),
                float(address.get('coordinates').get('lat')),
            ]
            create_entry(token, fields_slugs, values, flow_slug='pizzeria')
        except Exception as e:
            print(f'Something is going wrong {e}')


def add_pizzas(client_secret, client_id):
    token = get_client_auth(client_secret, client_id).get('access_token')

    menu = fetch_menu()
    for num, product in enumerate(menu):
        try:
            product_id = add_product(token, product, num)['data']['id']
            img_id = upload_image(token, product['product_image']['url'])['data']['id']
            bind_image_with_product(token, img_id, product_id)
        except Exception as e:
            print(f'Something is going wrong {e}')


def add_product_to_cart(token, cart_id, product_id):
    headers = {
        'Authorization': f'Bearer {token}',
        'X-MOLTIN-CURRENCY': 'RUB'
    }

    json_data = {
        'data': {
            'id': product_id,
            'type': 'cart_item',
            'quantity': 1,
        },
    }

    response = requests.post(f'https://api.moltin.com/v2/carts/{cart_id}/items', headers=headers, json=json_data)
    response.raise_for_status()

    return response.json()


def remove_product_from_cart(token, cart_id, product_id):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    response = requests.delete(f'https://api.moltin.com/v2/carts/{cart_id}/items/{product_id}', headers=headers)
    response.raise_for_status()

    return response.json()


def create_cart(token, tg_id):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    json_data = {
        'data': {
            'name': tg_id,
            'description': f'cart of user {tg_id}',
        }
    }
    response = requests.post('https://api.moltin.com/v2/carts', headers=headers, json=json_data)
    response.raise_for_status()

    return response.json()


def get_cart(token, cart_id):
    headers = {
        'Authorization': f'Bearer {token}',
    }

    response = requests.get(f'https://api.moltin.com/v2/carts/{cart_id}/items', headers=headers)
    response.raise_for_status()

    return response.json()


def get_cart_total_price(token, cart_id):
    headers = {
        'Authorization': f'Bearer {token}',
    }

    response = requests.get(f'https://api.moltin.com/v2/carts/{cart_id}', headers=headers)
    response.raise_for_status()

    return response.json()


def create_customer(token, user_id, email):
    headers = {
        'Authorization': f'Bearer {token}',
    }

    json_data = {
        'data': {
            'type': 'customer',
            'name': f'{user_id}',
            'email': f'{email}',
            'password': 'mysecretpassword',
        },
    }

    response = requests.post('https://api.moltin.com/v2/customers', headers=headers, json=json_data)
    response.raise_for_status()

    return response.json()


def check_customer(elastic_token, client_id):
    headers = {
        'Authorization': f'Bearer {elastic_token}',
    }

    response = requests.get(f'https://api.moltin.com/v2/customers/{client_id}', headers=headers)
    response.raise_for_status()

    return response.json()


def renew_token(bot_context):
    """
    :param bot_context: this is a context object passed to the callback called by :class:`telegram.ext.Handler`
    or by the :class:`telegram.ext.Dispatcher`
    :return: None
    """
    client_secret = bot_context.bot_data['client_secret']
    client_id = bot_context.bot_data['client_id']
    elastic_auth = get_client_auth(client_secret, client_id)
    bot_context.bot_data['token'] = elastic_auth.get('access_token')
    bot_context.bot_data['token_expires_in'] = elastic_auth.get('expires_in')
    bot_context.job_queue.run_once(renew_token, when=bot_context.bot_data['token_expires_in'])


def fetch_pizzerias_with_coordinates(token, flow_slug):
    pizzerias = get_all_entries(token, flow_slug)['data']
    pizzerias_with_coordinates = []
    for pizzeria in pizzerias:
        pizzerias_with_coordinates.append({
            'address': pizzeria['address'],
            'coordinates': (pizzeria['latitude'], pizzeria['longitude']),
            'deliveryman-telegram-id': pizzeria['deliveryman-telegram-id']
        })
    return pizzerias_with_coordinates

