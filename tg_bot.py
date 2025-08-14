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
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
    CallbackContext,
)

from extenshion import (
    get_products,
    get_picture,
    get_or_create_cart,
    add_product_to_cart,
    get_cart_products,
)

_database = None

START, HANDLE_MENU, HANDLE_DESCRIPTION, HANDLE_CART = map(str, range(4))

logger = logging.getLogger("fish_bot")
logger.setLevel(logging.DEBUG)


def start(update: Update, context: CallbackContext):
    products = get_products()
    keyboard = [
        [InlineKeyboardButton(product["title"], callback_data=product["documentId"])]
        for product in products
    ] + [[InlineKeyboardButton("Моя корзина", callback_data="cart")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        text="Выберите интересующий товар:", reply_markup=reply_markup
    )
    return HANDLE_MENU


def cart_render(update: Update, context: CallbackContext):
    query = update.callback_query
    query.delete_message()
    chat_id = update.callback_query.message.chat_id
    cart_products = get_cart_products(str(chat_id))
    keyboard = [
        [
            InlineKeyboardButton(
                f"{product['title']} {product['price']}",
                callback_data=f"{product['documentId']}",
            )
        ]
        for product in cart_products
    ] + [[InlineKeyboardButton("Назад", callback_data="back")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(text=f"{cart_products}", reply_markup=reply_markup)
    return HANDLE_CART


def render_product(update: Update, context: CallbackContext):
    query = update.callback_query
    product_id = query.data
    product = get_products(product_id)
    picture_url = product["picture"]["url"]
    picture = get_picture(picture_url)
    keyboard = [
        [
            InlineKeyboardButton("Назад", callback_data="back"),
            InlineKeyboardButton(
                "Добавить в корзину 1 кг", callback_data=f"1$${product_id}"
            ),
            InlineKeyboardButton(
                "Добавить в корзину 2 кг", callback_data=f"2$${product_id}"
            ),
            InlineKeyboardButton(
                "Добавить в корзину 5 кг", callback_data=f"5$${product_id}"
            ),
            InlineKeyboardButton(
                "Добавить в корзину 10 кг", callback_data=f"10$${product_id}"
            ),
        ]
    ] + [[InlineKeyboardButton("Моя корзина", callback_data="cart")]]
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
        return cart_render(update, context)
    else:
        return render_product(update, context)


def handle_cart(update: Update, context: CallbackContext):
    query = update.callback_query
    if query.data == "back":
        query.delete_message()
        return start(query, context)
    else:
        print(f" delete message {query.data}")
    return HANDLE_CART


def handle_description(update: Update, context: CallbackContext):
    query = update.callback_query
    if query.data == "back":
        query.delete_message()
        return start(query, context)
    else:
        amount_kg, product_id = query.data.split("$$")
        chat_id = update.callback_query.message.chat_id
        cart_document_id = get_or_create_cart(str(chat_id))
        add_product_to_cart(cart_document_id, product_id, amount_kg ,chat_id)
        query.delete_message()
        return start(query, context)


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
        database_host = os.getenv("DATABASE_HOST")
        database_port = os.getenv("DATABASE_PORT")
        database_name = os.getenv("DATABASE_NAME")
        _database = redis.Redis(
            host=database_host,
            port=database_port,
            db=database_name,
            decode_responses=True,
        )
    return _database


if __name__ == "__main__":
    load_dotenv()
    token = os.getenv("TELEGRAM_TOKEN")
    updater = Updater(token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler("start", handle_users_reply))
    updater.start_polling()
    updater.idle()
