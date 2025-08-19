import logging
import os

import redis
from dotenv import load_dotenv
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Update,
)
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)

from star_api_requests import (
    add_product_to_cart,
    delete_from_cart,
    get_cart_products,
    get_or_create_cart,
    get_picture,
    get_products,
    add_client_email,
)

_database = None

START, HANDLE_MENU, HANDLE_DESCRIPTION, HANDLE_CART, WAITING_EMAIL = map(str, range(5))

logger = logging.getLogger("fish_bot")
logger.setLevel(logging.DEBUG)


def start(update: Update, context: CallbackContext):
    url = context.bot_data["url"]
    starapi_token = context.bot_data["starapi_token"]
    products = get_products(url, starapi_token)
    keyboard = [
        [InlineKeyboardButton(product["title"], callback_data=product["documentId"])]
        for product in products
    ] + [[InlineKeyboardButton("Моя корзина", callback_data="cart")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        text="Выберите интересующий товар:", reply_markup=reply_markup
    )
    return HANDLE_MENU


def render_cart(update: Update, context: CallbackContext):
    url = context.bot_data["url"]
    starapi_token = context.bot_data["starapi_token"]
    query = update.callback_query
    query.delete_message()
    chat_id = update.callback_query.message.chat_id
    cart_products = get_cart_products(url, starapi_token, str(chat_id))
    keyboard = [
        [
            InlineKeyboardButton(
                f"Удалить {product_in_cart['product']['title']} {product_in_cart['amount_kg']}",
                callback_data=f"{product_in_cart['documentId']}",
            )
        ]
        for product_in_cart in cart_products
    ] + [
        [InlineKeyboardButton("В главное меню", callback_data="back")],
        [InlineKeyboardButton("Оплатить", callback_data="pay")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    products = [
        f"""{product_in_cart["product"]["title"]}
            {product_in_cart["product"]["description"]}
            {product_in_cart["product"]["price"]} за кг
            {product_in_cart["amount_kg"]} кг в корзине
            {product_in_cart["product"]["price"] * product_in_cart["amount_kg"]} рублей
    """
        for product_in_cart in cart_products
    ]
    total_sum = sum(
        product_in_cart["product"]["price"] * product_in_cart["amount_kg"]
        for product_in_cart in cart_products
    )
    query.message.reply_text(
        text="\n".join(products) + f"\nВсего: {total_sum} рублей",
        reply_markup=reply_markup,
    )
    return HANDLE_CART


def render_product(update: Update, context: CallbackContext):
    url = context.bot_data["url"]
    starapi_token = context.bot_data["starapi_token"]
    query = update.callback_query
    product_id = query.data
    product = get_products(url, starapi_token, product_id)
    picture_url = product["picture"]["url"]
    picture = get_picture(url, starapi_token, picture_url)
    keyboard = [
        [
            InlineKeyboardButton(
                "Добавить в корзину 1 кг", callback_data=f"1$${product_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "Добавить в корзину 2 кг", callback_data=f"2$${product_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "Добавить в корзину 5 кг", callback_data=f"5$${product_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "Добавить в корзину 10 кг", callback_data=f"10$${product_id}"
            )
        ],
    ] + [
        [
            InlineKeyboardButton("Моя корзина", callback_data="cart"),
            InlineKeyboardButton("В главное меню", callback_data="back"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_media(
        media=InputMediaPhoto(
            picture,
            filename="picture.jpg",
            caption=f"{product['title']}\n{product['description']}\n{product['price']}",
        ),
        reply_markup=reply_markup,
    )
    return HANDLE_DESCRIPTION


def handle_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    if query.data == "cart":
        return render_cart(update, context)
    else:
        return render_product(update, context)


def handle_cart(update: Update, context: CallbackContext):
    url = context.bot_data["url"]
    starapi_token = context.bot_data["starapi_token"]
    query = update.callback_query
    if query.data == "back":
        query.delete_message()
        return start(query, context)
    elif query.data == "pay":
        query.delete_message()
        keyboard = [
            [InlineKeyboardButton("В главное меню", callback_data="back")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.message.reply_text("Введите ваш email:", reply_markup=reply_markup)
        return WAITING_EMAIL
    else:
        delete_from_cart(url, starapi_token, query.data)
        return render_cart(update, context)


def handle_description(update: Update, context: CallbackContext):
    url = context.bot_data["url"]
    starapi_token = context.bot_data["starapi_token"]
    query = update.callback_query
    if query.data == "back":
        query.delete_message()
        return start(query, context)
    else:
        amount_kg, product_id = query.data.split("$$")
        chat_id = update.callback_query.message.chat_id
        cart_document_id = get_or_create_cart(url, starapi_token, str(chat_id))
        add_product_to_cart(
            url, starapi_token, cart_document_id, product_id, amount_kg, chat_id
        )
        query.delete_message()
        return start(query, context)


def wait_for_email(update: Update, context: CallbackContext):
    url = context.bot_data["url"]
    starapi_token = context.bot_data["starapi_token"]
    query = update.callback_query
    if query and query.data == "back":
        query.delete_message()
        return start(query, context)
    email = update.message.text
    chat_id = update.message.chat_id
    add_client_email(url, starapi_token, email, chat_id)
    return start(update, context)


def handle_users_reply(update: Update, context: CallbackContext):
    db = get_database_connection()
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return
    if user_reply == "/start":
        user_state = START
    else:
        user_state = db.get(chat_id)
    states_functions = {
        START: start,
        HANDLE_MENU: handle_menu,
        HANDLE_DESCRIPTION: handle_description,
        HANDLE_CART: handle_cart,
        WAITING_EMAIL: wait_for_email,
    }
    state_handler = states_functions[user_state]
    try:
        next_state = state_handler(update, context)
        db.set(chat_id, next_state)
    except Exception as err:
        print(err)


def get_database_connection():
    global _database
    if _database is None:
        database_host = os.getenv("REDIS_HOST")
        database_port = os.getenv("REDIS_PORT")
        database_name = os.getenv("REDIS_NAME")
        _database = redis.Redis(
            host=database_host,
            port=database_port,
            db=database_name,
            decode_responses=True,
        )
    return _database


if __name__ == "__main__":
    load_dotenv()
    url = os.getenv("STRAPI_URL")
    starapi_token = os.getenv("STRAPI_TOKEN")
    token = os.getenv("TELEGRAM_TOKEN")
    updater = Updater(token)
    dispatcher = updater.dispatcher
    dispatcher.bot_data["url"] = url
    dispatcher.bot_data["starapi_token"] = starapi_token
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler("start", handle_users_reply))
    updater.start_polling()
    updater.idle()
