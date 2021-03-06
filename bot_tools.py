from textwrap import dedent


def format_product_description(product_description):
    product_description = product_description['data']

    formatted_product_description = dedent(
        f'''
        Пицца "{product_description['name']}"
        Состава : {product_description['description']}
        Цена: {next(iter(product_description['price']))['amount']} руб.
        '''
    )

    return formatted_product_description


def format_cart(cart_items, total_price):
    cart = cart_items['data']
    formatted_cart = 'В корзине:'
    for item in cart:
        product = item['name']
        quantity = item['quantity']
        price = item['meta']['display_price']['without_tax']['value']['formatted']
        formatted_cart += dedent(
            f'''
        Пицца {product}
        В количестве: {quantity} шт
        На сумму: {float(price) * 100} руб.
        ''')

    return dedent(
        f'''
    {formatted_cart}
    Общая сумма: {float(total_price) * 100} руб.
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