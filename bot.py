import redis
from enum import Enum, auto
from environs import Env
from telegram.ext import Updater, CallbackQueryHandler, CommandHandler, MessageHandler, Filters, ConversationHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
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
                         renew_token)

from bot_tools import BidirectionalIterator, format_cart, format_product_description


class BotStates(Enum):
    START = auto()
    HANDLE_MENU = auto()
    HANDLE_PRODUCTS = auto()
    HANDLE_DESCRIPTION = auto()
    HANDLE_CART = auto()
    WAITING_EMAIL = auto()


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
    access_token = context.bot_data['access_token']

    products = get_all_products(access_token).get('data')
    pizzas_qty = 5
    chunked_products = list(chunked(products, pizzas_qty))
    chunked_products2 = BidirectionalIterator(chunked_products)
    context.bot_data['chunked_products'] = chunked_products2

    user_id = update.effective_user.id
    cart_id = redis_base.hget(user_id, 'cart')

    if not cart_id:
        cart_id = create_cart(access_token, str(user_id))['data']['id']
        redis_base.hset(user_id, 'cart', cart_id)
    context.user_data['cart_id'] = cart_id

    keyboard = [
        [InlineKeyboardButton(product.get('name'), callback_data=product.get('id')) for product in chunked_products[0]],
        [InlineKeyboardButton('Назад', callback_data='Назад')],
        [InlineKeyboardButton('Вперед', callback_data='Вперед')],
        [InlineKeyboardButton('Корзина', callback_data='Корзина')]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(text='Смотри, какая пицца!',
                     chat_id=user_id,
                     reply_markup=reply_markup)

    return BotStates.HANDLE_DESCRIPTION


def handle_products(update, context):
    user_id = update.effective_user.id
    callback_query = update.callback_query
    chunked_products = context.bot_data['chunked_products']

    if callback_query.data == 'Назад':
        products_pack = chunked_products.prev()
        context.bot_data['chunked_products'] = chunked_products

    elif callback_query.data == 'Вперед':
        products_pack = chunked_products.next()
        context.bot_data['chunked_products'] = chunked_products

    keyboard = [
        [InlineKeyboardButton(product.get('name'), callback_data=product.get('id')) for product in products_pack],
        [InlineKeyboardButton('Назад', callback_data='Назад')],
        [InlineKeyboardButton('Вперед', callback_data='Вперед')],
        [InlineKeyboardButton('Корзина', callback_data='Корзина')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.edit_message_text(text='Смотри, какая пицца!',
                                  chat_id=user_id,
                                  message_id=callback_query.message.message_id,
                                  reply_markup=reply_markup)

    return BotStates.HANDLE_DESCRIPTION


def handle_description(update, context):
    bot = context.bot

    access_token = context.bot_data['access_token']
    callback_query = update.callback_query
    product_id = callback_query.data
    context.user_data['product_id'] = product_id

    product_description = get_product_info(access_token, product_id)
    product_image_id = product_description['data']['relationships']['main_image']['data']['id']
    image_link = get_image_link(access_token, product_image_id)
    formatted_product_description = format_product_description(product_description)

    keyboard = [[
        InlineKeyboardButton('В меню', callback_data='В меню'),
        InlineKeyboardButton('+ 1 кг', callback_data='1'),
        InlineKeyboardButton('+ 5 кг', callback_data='5'),
        InlineKeyboardButton('+ 10 кг', callback_data='10'),
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
    access_token = context.user_data['access_token']
    cart_id = context.user_data['cart_id']
    product_id = context.user_data['product_id']

    callback_query = update.callback_query
    quantity = int(callback_query.data)

    add_product_to_cart(access_token, cart_id, product_id, quantity)

    return BotStates.HANDLE_DESCRIPTION


def handle_cart(update, context):
    bot = context.bot

    access_token = context.bot_data['access_token']
    cart_id = context.user_data['cart_id']
    callback_query = update.callback_query
    cart_items = get_cart(access_token, cart_id)

    context.user_data['cart_items'] = [item.get('id') for item in cart_items['data']]
    if callback_query.data in context.user_data.get('cart_items'):
        product_id = callback_query.data
        remove_product_from_cart(access_token, cart_id, product_id)
        cart_items = get_cart(access_token, cart_id)

    keyboard = [
        [InlineKeyboardButton('В меню',
                              callback_data='В меню')],
        [InlineKeyboardButton(f"Убрать {item.get('name')}",
                              callback_data=item.get('id')) for item in cart_items['data']],
        [InlineKeyboardButton('Оплатить',
                              callback_data='Оплатить')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    total_price = get_cart_total_price(access_token, cart_id)['data']['meta']['display_price']['with_tax']['formatted']

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


def add_client_to_cms(update, context):
    bot = context.bot

    access_token = context.bot_data['access_token']

    email = update.message.text

    customer_id = create_customer(access_token,
                                  user_id=update.message.chat_id,
                                  email=email)['data']['id']

    check_customer(access_token, customer_id)

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

    fish_shop = ConversationHandler(
        entry_points=[
            CommandHandler('start', handle_menu),
            CommandHandler('cancel', cancel)
        ],
        states={
            BotStates.HANDLE_MENU: [
                CallbackQueryHandler(handle_menu),
                CallbackQueryHandler(handle_cart, pattern='^Корзина'),
            ],
            BotStates.HANDLE_DESCRIPTION: [
                CallbackQueryHandler(handle_menu, pattern='^В меню'),
                CallbackQueryHandler(handle_cart, pattern='^Корзина'),
                CallbackQueryHandler(update_cart, pattern='^[0-9]+$'),
                CallbackQueryHandler(handle_products, pattern='^Назад$'),
                CallbackQueryHandler(handle_products, pattern='^Вперед'),
            ],
            BotStates.HANDLE_CART: [
                CallbackQueryHandler(handle_menu, pattern='^В меню$'),
                CallbackQueryHandler(get_user_email, pattern='^Оплатить$'),
                CallbackQueryHandler(handle_cart),
            ],
            BotStates.WAITING_EMAIL: [
                MessageHandler(Filters.regex('^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'), add_client_to_cms),
                CallbackQueryHandler(handle_cart, pattern='^Назад$'),
                CallbackQueryHandler(get_user_email)
            ]

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
