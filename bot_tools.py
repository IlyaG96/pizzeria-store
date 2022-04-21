from textwrap import dedent


def format_product_description(product_description):
    product_description = product_description['data']
    print(product_description)

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
            raise StopIteration
        return result

    def prev(self):
        self.index -= 1
        if self.index < 0:
            raise StopIteration
        return self.collection[self.index]

    def __iter__(self):
        return self
