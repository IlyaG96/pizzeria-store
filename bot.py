from textwrap import dedent
import redis
from enum import Enum, auto
from environs import Env
from telegram.ext import (Updater,
                          CallbackQueryHandler,
                          CommandHandler,
                          MessageHandler,
                          Filters,
                          ConversationHandler, PreCheckoutQueryHandler)
from telegram import (InlineKeyboardButton,
                      InlineKeyboardMarkup,
                      ReplyKeyboardRemove,
                      KeyboardButton,
                      ReplyKeyboardMarkup,
                      LabeledPrice)
from more_itertools import chunked
from elastic_api import (get_all_products,
                         get_product_info,
                         get_image_link,
                         get_cart,
                         add_product_to_cart,
                         create_cart,
                         get_cart_total_price,
                         remove_product_from_cart,
                         renew_token,
                         fetch_pizzerias_with_coordinates,
                         create_entry)

from bot_tools import (BidirectionalIterator,
                       format_cart,
                       format_product_description,
                       build_menu)
from geo_api import show_nearest_pizzeria, fetch_coordinates


class BotStates(Enum):
    START = auto()
    HANDLE_MENU = auto()
    HANDLE_PRODUCTS = auto()
    HANDLE_DESCRIPTION = auto()
    HANDLE_CART = auto()
    WAITING_GEO = auto()
    WAITING_EMAIL = auto()
    PROCESS_DELIVERY = auto()
    ACCEPT_PICKUP = auto()
    ACCEPT_DELIVERY = auto()
    ACCEPT_PAYMENT = auto()
    PRECHECKOUT = auto()
    SUCCESS_PAYMENT = auto()


def take_payment(update, context):
    context.user_data['delivery_type'] = update.callback_query.data
    if context.user_data['delivery_type'] == 'Самовывоз':
        context.user_data['delivery_price'] = 0

    price = context.user_data['delivery_price'] + float(context.user_data['order_price']) * 100
    price = int(price)
    user_id = update.effective_user.id
    context.bot.send_message(
        chat_id=user_id,
        text='Формирую счет...'
    )
    payment_token = context.bot_data['payment_token']
    title = 'Ваш заказ'
    description = f'Оплата заказа стоимостью {price} рублей'
    payload = 'Custom-Payload'
    currency = 'RUB'
    prices = [LabeledPrice('Стоимость', price * 100)]

    context.bot.send_invoice(
        user_id, title, description, payload, payment_token, currency, prices
    )
    return BotStates.PRECHECKOUT


def precheckout(update, _):
    query = update.pre_checkout_query
    if query.invoice_payload != 'Custom-Payload':
        query.answer(ok=False, error_message='Что-то пошло не так...')
    else:
        query.answer(ok=True)

    return BotStates.SUCCESS_PAYMENT


def cancel(update, context):
    text = 'Пока'

    update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def handle_menu(update, context):
    bot = context.bot
    redis_base = context.bot_data['redis_base']
    token = context.bot_data['token']
    user_id = update.effective_user.id

    products = get_all_products(token).get('data')
    pizzas_qty = 3
    chunked_products = list(chunked(products, pizzas_qty))
    iterable_products = BidirectionalIterator(chunked_products)
    context.user_data['iterable_products'] = iterable_products
    context.user_data['products_pack'] = next(iter(chunked_products))

    cart_id = redis_base.hget(user_id, 'cart')

    if not cart_id:
        cart_id = create_cart(token, str(user_id))['data']['id']
        redis_base.hset(user_id, 'cart', cart_id)
    context.user_data['cart_id'] = cart_id

    keyboard = build_menu(
        [InlineKeyboardButton(product.get('name'),
                              callback_data=product.get('id')) for product in context.user_data['products_pack']],
        n_cols=3,
        footer_buttons=[[InlineKeyboardButton('Назад', callback_data='Назад')],
                        [InlineKeyboardButton('Вперед', callback_data='Вперед')],
                        [InlineKeyboardButton('Корзина', callback_data='Корзина')]])

    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(text='Смотри, какая пицца!',
                     chat_id=user_id,
                     reply_markup=reply_markup)

    return BotStates.HANDLE_DESCRIPTION


def handle_products(update, context):
    user_id = update.effective_user.id
    callback_query = update.callback_query
    iterable_products = context.user_data['iterable_products']

    if callback_query.data == 'Назад':
        products_pack = iterable_products.prev()
        context.user_data['products_pack'] = products_pack

    elif callback_query.data == 'Вперед':
        products_pack = iterable_products.next()
        context.user_data['products_pack'] = products_pack

    keyboard = build_menu(
        [InlineKeyboardButton(product.get('name'),
                              callback_data=product.get('id')) for product in context.user_data['products_pack']],
        n_cols=3,
        footer_buttons=[[InlineKeyboardButton('Назад', callback_data='Назад')],
                        [InlineKeyboardButton('Вперед', callback_data='Вперед')],
                        [InlineKeyboardButton('Корзина', callback_data='Корзина')]])
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.send_message(text=f'Смотри, какая пицца!',
                             chat_id=user_id,
                             reply_markup=reply_markup)
    context.bot.delete_message(chat_id=callback_query.message.chat_id,
                               message_id=callback_query.message.message_id)
    return BotStates.HANDLE_DESCRIPTION


def handle_description(update, context):
    bot = context.bot

    token = context.bot_data['token']
    callback_query = update.callback_query
    product_id = callback_query.data
    context.user_data['product_id'] = product_id

    product_description = get_product_info(token, product_id)
    product_image_id = product_description['data']['relationships']['main_image']['data']['id']
    image_link = get_image_link(token, product_image_id)
    formatted_product_description = format_product_description(product_description)

    keyboard = [[
        InlineKeyboardButton('В меню', callback_data='В меню'),
        InlineKeyboardButton('Добавить в корзину', callback_data='Добавить в корзину'),
        InlineKeyboardButton('Корзина', callback_data='Корзина')
    ]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    bot.send_photo(
        chat_id=callback_query.message.chat_id,
        photo=image_link,
        caption=formatted_product_description,
        reply_markup=reply_markup,
    )

    bot.delete_message(
        chat_id=callback_query.message.chat_id,
        message_id=callback_query.message.message_id,
    )

    return BotStates.HANDLE_DESCRIPTION


def update_cart(update, context):
    token = context.bot_data['token']
    cart_id = context.user_data['cart_id']
    product_id = context.user_data['product_id']
    add_product_to_cart(token, cart_id, product_id)

    return BotStates.HANDLE_DESCRIPTION


def handle_cart(update, context):
    bot = context.bot

    token = context.bot_data['token']
    cart_id = context.user_data['cart_id']
    callback_query = update.callback_query
    cart_items = get_cart(token, cart_id)

    context.user_data['cart_items'] = [item.get('id') for item in cart_items['data']]
    if callback_query.data in context.user_data.get('cart_items'):
        product_id = callback_query.data
        remove_product_from_cart(token, cart_id, product_id)
        cart_items = get_cart(token, cart_id)

    keyboard = build_menu(
        [InlineKeyboardButton(f"Убрать пиццу {item.get('name')}",
                              callback_data=item.get('id')) for item in cart_items['data']], n_cols=1,
        footer_buttons=[[InlineKeyboardButton('Оплатить',
                                              callback_data='Оплатить')],
                        [InlineKeyboardButton('В меню',
                                              callback_data='В меню')]])

    reply_markup = InlineKeyboardMarkup(keyboard)
    order_price = get_cart_total_price(token, cart_id)['data']['meta']['display_price']['with_tax']['formatted']

    context.user_data['order_price'] = order_price

    bot.delete_message(
        chat_id=callback_query.message.chat_id,
        message_id=callback_query.message.message_id,
    )
    bot.send_message(
        text=format_cart(cart_items, order_price),
        chat_id=update.callback_query.message.chat_id,
        reply_markup=reply_markup,
    )

    return BotStates.HANDLE_CART


def get_user_email(update, context):
    bot = context.bot
    callback_query = update.callback_query

    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Назад',
                                                           callback_data='Назад')]])

    if context.user_data['order_price'] == '0':
        bot.edit_message_text(
            text='Похоже, что в корзине нет товаров.',
            chat_id=callback_query.message.chat_id,
            message_id=callback_query.message.message_id,
            reply_markup=keyboard,
        )
        return BotStates.HANDLE_MENU

    bot.edit_message_text(
        text='Введите, пожалуйста, свой e-mail в формате username@email.com',
        chat_id=callback_query.message.chat_id,
        message_id=callback_query.message.message_id,
        reply_markup=keyboard,
    )

    return BotStates.WAITING_EMAIL


def get_user_address(update, context):
    context.user_data['email'] = update.message.text

    buttons = [
        [KeyboardButton('Определить мое местоположение', request_location=True)]
    ]

    reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)

    update.message.reply_text(
        'Пожалуйста, отправьте нам свой адрес или разрешите определить его автоматически',
        reply_markup=reply_markup
    )

    return BotStates.WAITING_GEO


def process_user_address(update, context):
    if update.message.location:
        context.user_data['coordinates'] = update.message.location['latitude'], update.message.location['longitude']

    elif update.message.text:
        address = update.message.text
        coordinates = fetch_coordinates(context.bot_data['yandex_geo_api'], address)
        if not coordinates:
            update.message.reply_text(
                'Адрес некорректен. Проверьте то, что вы ввели, или отправьте гео-точку'
            )
            return BotStates.WAITING_GEO

        context.user_data['coordinates'] = coordinates

    pizzerias = fetch_pizzerias_with_coordinates(context.bot_data['token'],
                                                 context.bot_data['flow_slug'])

    nearest_pizzeria = show_nearest_pizzeria(pizzerias, context.user_data['coordinates'])
    distance = nearest_pizzeria.get('distance')
    address = nearest_pizzeria.get('address')
    context.user_data['nearest_pizzeria'] = nearest_pizzeria

    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Назад', callback_data='Назад')],
                                     [InlineKeyboardButton('Самовывоз', callback_data='Самовывоз')],
                                     [InlineKeyboardButton('Доставка', callback_data='Доставка')]])

    if distance < 0.5:
        reply_text = dedent(f'''
        Может, заберете пиццу из нашей пиццерии неподалеку? Она всего в {round(distance * 1000, 1)} метрах от вас.
        Адрес пиццерии {address}.
        А можем и бесплатно доставить, нам не сложно :)
        ''')
        context.user_data['delivery_price'] = 0

    elif 0.5 < distance < 3:
        reply_text = dedent(f'''
        Похоже, до вас придется ехать на самокате. Доставка будет стоить 100 рублей. Или все-таки самовывоз? :)
        ''')
        context.user_data['delivery_price'] = 100

    elif 3 <= distance < 20:
        reply_text = dedent(f'''
        Похоже, до вас придется ехать на автомобиле. Доставка будет стоить 300 рублей. Или все-таки самовывоз? :)
        ''')
        context.user_data['delivery_price'] = 300

    else:
        reply_text = dedent(f'''
        Простите, но так далеко мы пиццу не доставляем. Ближайшая пиццерия аж в {round(distance, 1)} километрах от вас.
        <остроумная шутка, которую я не придумал>
        ''')
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('В корзину', callback_data='В корзину')]])

    context.bot.send_message(text=reply_text,
                             chat_id=update.effective_user.id,
                             reply_markup=keyboard)

    return BotStates.PROCESS_DELIVERY


def send_notification(context):
    text = "Приятного аппетита! *место для рекламы сообщение что делать если пицца не пришла"
    job = context.job
    context.bot.send_message(
        job.context, text=text
    )


def add_customer_to_cms(update, context):
    token = context.bot_data['token']
    chat_id = update.effective_user.id
    fields_slugs = ['longitude', 'latitude', 'email']
    values = *context.user_data['coordinates'], context.user_data['email']
    flow_slug = 'customer-address'
    create_entry(token, fields_slugs, values, flow_slug)
    send_message_after = 15
    context.job_queue.run_once(send_notification, send_message_after, context=chat_id)


def success_payment(update, context):
    if context.user_data['delivery_type'] == 'Доставка':
        accept_delivery(update, context)
    else:
        accept_pickup(update, context)


def accept_pickup(update, context):
    pickup_address = context.user_data['nearest_pizzeria'].get('address')
    reply_text = dedent(f'''
        Адрес пиццерии для самовывоза {pickup_address}        
        '''
                        )
    context.bot.send_message(text=reply_text,
                             chat_id=update.effective_user.id)

    return ConversationHandler.END


def accept_delivery(update, context):
    deliveryman_telegram_id = context.user_data['nearest_pizzeria'].get('deliveryman-telegram-id')

    token = context.bot_data['token']
    cart_id = context.user_data['cart_id']
    cart_items = get_cart(token, cart_id)
    order_price = context.user_data['order_price']
    reply_text = format_cart(cart_items, order_price)
    latitude, longitude = context.user_data['coordinates']
    context.bot.send_location(longitude=longitude,
                              latitude=latitude,
                              chat_id=deliveryman_telegram_id)
    context.bot.send_message(
        text=reply_text,
        chat_id=deliveryman_telegram_id
    )

    add_customer_to_cms(update, context)

    return ConversationHandler.END


def main():
    env = Env()
    env.read_env()
    telegram_token = env.str('TG_TOKEN')
    redis_host = env.str('REDIS_HOST')
    redis_port = env.str('REDIS_PORT')
    redis_password = env.str('REDIS_PASSWORD')
    client_id = env.str('ELASTIC_CLIENT_ID')
    client_secret = env.str('ELASTIC_CLIENT_SECRET')
    yandex_geo_api = env.str('YANDEX_GEO_API')
    payment_token = env.str('PAYMENT_TOKEN')

    updater = Updater(telegram_token)

    redis_base = redis.Redis(host=redis_host,
                             port=redis_port,
                             password=redis_password,
                             decode_responses=True)

    dispatcher = updater.dispatcher
    job_queue = updater.job_queue
    dispatcher.bot_data['redis_base'] = redis_base
    dispatcher.bot_data['client_id'] = client_id
    dispatcher.bot_data['client_secret'] = client_secret
    dispatcher.bot_data['yandex_geo_api'] = yandex_geo_api
    dispatcher.bot_data['flow_slug'] = 'pizzeria'
    dispatcher.bot_data['payment_token'] = payment_token

    fish_shop = ConversationHandler(
        entry_points=[
            CommandHandler('start', handle_menu),
            CommandHandler('cancel', cancel)
        ],
        states={
            BotStates.HANDLE_MENU: [
                CallbackQueryHandler(handle_menu),
                CallbackQueryHandler(handle_cart, pattern='^Корзина$'),
            ],
            BotStates.HANDLE_DESCRIPTION: [
                CallbackQueryHandler(handle_products, pattern='^В меню$'),
                CallbackQueryHandler(handle_cart, pattern='^Корзина$'),
                CallbackQueryHandler(update_cart, pattern='^Добавить в корзину$'),
                CallbackQueryHandler(handle_products, pattern='^Назад$'),
                CallbackQueryHandler(handle_products, pattern='^Вперед$'),
                CallbackQueryHandler(handle_description)
            ],
            BotStates.HANDLE_CART: [
                CallbackQueryHandler(handle_products, pattern='^В меню$'),
                CallbackQueryHandler(get_user_email, pattern='^Оплатить$'),
                CallbackQueryHandler(handle_cart),
            ],
            BotStates.WAITING_EMAIL: [
                MessageHandler(Filters.regex('^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'), get_user_address),
                CallbackQueryHandler(handle_cart, pattern='^Назад$'),
                CallbackQueryHandler(get_user_email)
            ],
            BotStates.WAITING_GEO: [
                MessageHandler(Filters.location, process_user_address),
                MessageHandler(Filters.text, process_user_address)
            ],
            BotStates.PROCESS_DELIVERY: [
                CallbackQueryHandler(handle_cart, pattern='^В корзину$'),
                CallbackQueryHandler(take_payment, pattern='^Самовывоз$'),
                CallbackQueryHandler(take_payment, pattern='^Доставка$'),
            ],
            BotStates.PRECHECKOUT: [
                PreCheckoutQueryHandler(precheckout),
            ],
            BotStates.SUCCESS_PAYMENT: [
                MessageHandler(Filters.successful_payment, success_payment)
            ],
        },

        per_user=True,
        per_chat=False,
        allow_reentry=True,
        fallbacks=[
            CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(fish_shop)
    job_queue.run_once(renew_token, when=0.0)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
