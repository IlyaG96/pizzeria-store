import requests
from environs import Env


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
    print(response.json())

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

    response = requests.delete(f'https://api.moltin.com/v2/files/{image_id}', headers=headers)
    response.raise_for_status()


def upload_image(token, image_url):
    headers = {
        'Authorization': f'Bearer {token}',
    }

    files = {
        'file_location': (None, f'{image_url}'),
    }

    response = requests.post('https://api.moltin.com/v2/files', headers=headers, files=files)
    response.raise_for_status()

    return response.json()


def get_all_images(token):
    headers = {
        'Authorization': f'Bearer {token}',
    }

    response = requests.get('https://api.moltin.com/v2/files', headers=headers)
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

    response = requests.post('https://api.moltin.com/v2/flows', headers=headers, json=json_data)
    response.raise_for_status()

    return response.json()


def delete_flow(token, flow_id):
    headers = {
        'Authorization': f'Bearer {token}',
    }

    response = requests.delete(f'https://api.moltin.com/v2/flows/{flow_id}', headers=headers)
    response.raise_for_status()


def get_flow(token, flow_id):
    headers = {
        'Authorization': f'Bearer {token}',
    }

    response = requests.get(f'https://api.moltin.com/v2/flows/{flow_id}', headers=headers)
    response.raise_for_status()

    return response.json()


def create_field(token, name, type, flow_id, description):
    headers = {
        'Authorization': f'{token}',
    }

    json_data = {
        'data': {
            'type': 'field',
            'name': name,
            'slug': f'{name}-field-slug',
            'field_type': type,
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

    response = requests.post('https://api.moltin.com/v2/fields', headers=headers, json=json_data)
    response.raise_for_status()


def get_all_fields(token):
    headers = {
        'Authorization': f'Bearer {token}',
    }

    response = requests.get('https://api.moltin.com/v2/fields', headers=headers)
    response.raise_for_status()

    return response.json()


def get_fields_by_flow(token, flow_slug):
    headers = {
        'Authorization': f'Bearer {token}',
    }

    response = requests.get(f'https://api.moltin.com/v2/flows/{flow_slug}/fields', headers=headers)
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
    response = requests.post(f'https://api.moltin.com/v2/flows/{flow_slug}/entries', headers=headers, json=json_data)
    response.raise_for_status()
    return response.json()


def get_flow_id_by_slug(token, flow_slug):
    headers = {
        'Authorization': f'Bearer {token}',
    }

    response = requests.get(f'https://api.moltin.com/v2/flows/{flow_slug}/fields', headers=headers)
    response.raise_for_status()

    return next(iter(response.json().get('data'))).get('relationships')['flow']['data']['id']


def add_addresses(token):
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
            print(f'Something in going wrong {e}')


def add_pizzas(token):
    menu = fetch_menu()
    for num, product in enumerate(menu):
        try:
            product_id = add_product(token, product, num)['data']['id']
            img_id = upload_image(token, product['product_image']['url'])['data']['id']
            bind_image_with_product(token, img_id, product_id)
        except Exception as e:
            print(f'Something in going wrong {e}')


def main():
    env = Env()
    env.read_env()

    client_secret = env.str('ELASTIC_CLIENT_SECRET')
    client_id = env.str('ELASTIC_CLIENT_ID')
    # get_client_auth(client_secret, client_id)
    token = ''
    add_addresses(token)


if __name__ == '__main__':
    main()
