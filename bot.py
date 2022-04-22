import redis
from enum import Enum, auto
from environs import Env
from telegram.ext import Updater, CallbackQueryHandler, CommandHandler, MessageHandler, Filters, ConversationHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, ReplyKeyboardMarkup
from more_itertools import chunked
from elastic_api import (get_all_products,
                         get_product_info,
                         get_image_link,
                         get_cart,
                         add_product_to_cart,
                         create_cart,
                         get_cart_total_price,
                         remove_product_from_cart,
                         create_customer,
                         check_customer,
                         renew_token,
                         fetch_pizzerias_with_coordinates)

from bot_tools import (BidirectionalIterator,
                       format_cart,
                       format_product_description,
                       build_menu,
                       fetch_coordinates,
                       show_nearest_pizzeria)


class BotStates(Enum):
    START = auto()
    HANDLE_MENU = auto()
    HANDLE_PRODUCTS = auto()
    HANDLE_DESCRIPTION = auto()
    HANDLE_CART = auto()
    WAITING_GEO = auto()
    WAITING_EMAIL = auto()
    PROCESS_GEO = auto()


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

    products = get_all_products(token).get('data')
    pizzas_qty = 4
    chunked_products = list(chunked(products, pizzas_qty))
    iterable_products = BidirectionalIterator(chunked_products)
    context.bot_data['iterable_products'] = iterable_products
    context.bot_data['products_pack'] = next(iter(chunked_products))
    user_id = update.effective_user.id
    cart_id = redis_base.hget(user_id, 'cart')

    if not cart_id:
        cart_id = create_cart(token, str(user_id))['data']['id']
        redis_base.hset(user_id, 'cart', cart_id)
    context.user_data['cart_id'] = cart_id

    keyboard = build_menu(
        [InlineKeyboardButton(product.get('name'),
                              callback_data=product.get('id')) for product in context.bot_data['products_pack']],
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
    iterable_products = context.bot_data['iterable_products']

    if callback_query.data == 'Назад':
        products_pack = iterable_products.prev()
        context.bot_data['products_pack'] = products_pack

    elif callback_query.data == 'Вперед':
        products_pack = iterable_products.next()
        context.bot_data['products_pack'] = products_pack

    keyboard = build_menu(
        [InlineKeyboardButton(product.get('name'),
                              callback_data=product.get('id')) for product in context.bot_data['products_pack']],
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

    keyboard = [
        [InlineKeyboardButton('В меню',
                              callback_data='В меню')],
        [InlineKeyboardButton(f"Убрать {item.get('name')}",
                              callback_data=item.get('id')) for item in cart_items['data']],
        [InlineKeyboardButton('Оплатить',
                              callback_data='Оплатить')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    total_price = get_cart_total_price(token, cart_id)['data']['meta']['display_price']['with_tax']['formatted']

    context.user_data['total_price'] = total_price

    bot.delete_message(
        chat_id=callback_query.message.chat_id,
        message_id=callback_query.message.message_id,
    )
    bot.send_message(
        text=format_cart(cart_items, total_price),
        chat_id=update.callback_query.message.chat_id,
        reply_markup=reply_markup,
    )

    return BotStates.HANDLE_CART


def get_user_email(update, context):
    bot = context.bot
    callback_query = update.callback_query

    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Назад',
                                                           callback_data='Назад')]])

    if context.user_data['total_price'] == '0':
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

    buttons = [
        [KeyboardButton('Определеить мое местоположение', request_location=True)]
    ]

    reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)

    update.message.reply_text(
        'Пожалуйста, отправьте нам свой адрес или разрешите определить его автоматически',
        reply_markup=reply_markup
    )

    return BotStates.WAITING_GEO


def process_user_address(update, context):

    pizzerias = fetch_pizzerias_with_coordinates(context.bot_data['token'],
                                                 context.bot_data['flow_slug'])

    if update.message.location:
        context.user_data['location'] = update.message.location['latitude'], update.message.location['longitude']
        nearest_pizzeria = show_nearest_pizzeria(pizzerias, context.user_data['location'])
        print(nearest_pizzeria)

    elif update.message.text:
        address = update.message.text
        coordinates = fetch_coordinates(context.bot_data['yandex_geo_api'], address)
        if not coordinates:
            update.message.reply_text(
                'Адрес некорректен. Проверьте то, что вы ввели, или отправьте гео-точку'
            )
            return BotStates.WAITING_GEO

        context.user_data['location'] = coordinates
        nearest_pizzeria = show_nearest_pizzeria(pizzerias, context.user_data['location'])
        print(nearest_pizzeria)

    return BotStates.PROCESS_GEO


def add_client_to_cms(update, context):
    bot = context.bot

    token = context.bot_data['token']

    email = update.message.text

    customer_id = create_customer(token,
                                  user_id=update.message.chat_id,
                                  email=email)['data']['id']

    check_customer(token, customer_id)

    bot.send_message(
        text=f'Ваш заказ успешно создан, номер заказа: {customer_id}',
        chat_id=update.message.chat_id,
    )


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
            BotStates.PROCESS_GEO: [

            ],
        },

        per_user=True,
        per_chat=True,
        fallbacks=[
            CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(fish_shop)
    job_queue.run_once(renew_token, when=0.0)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
