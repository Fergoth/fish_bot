from io import BytesIO
from urllib.parse import urljoin

import requests


def get_products(url, token, documentId=None):
    url = urljoin(url, "api/products/")
    params = {}
    if documentId is not None:
        url = urljoin(url, documentId)
        params["populate"] = "picture"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()["data"]


def get_picture(url, token, picture_url):
    url = urljoin(url, picture_url)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return BytesIO(response.content)


def get_cart(url, token, tg_user_id):
    url = urljoin(url, "api/carts/")
    headers = {"Authorization": f"Bearer {token}"}
    params = {"filters[tg_user_id][$eq]": tg_user_id}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()["data"]


def create_cart(url, token, tg_user_id):
    url = urljoin(url, "api/carts/")
    headers = {"Authorization": f"Bearer {token}"}
    data = {"data": {"tg_user_id": tg_user_id}}
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()["data"]["documentId"]


def add_product_to_cart(
    url, token, cart_document_id, product_document_id, amount_kg=1, chat_id=None
):
    current_products_cart = get_cart_products(url, token, chat_id)
    current_product_id_for_update = None
    for product_in_cart in current_products_cart:
        if product_in_cart["product"]["documentId"] == product_document_id:
            current_product_id_for_update = product_in_cart
    if current_product_id_for_update:
        url = urljoin(
            url,
            f"api/product-carts/{current_product_id_for_update['documentId']}",
        )
        headers = {"Authorization": f"Bearer {token}"}
        data = {
            "data": {
                "amount_kg": int(current_product_id_for_update["amount_kg"])
                + int(amount_kg),
            }
        }

        response = requests.put(url, headers=headers, json=data)
        response.raise_for_status()
    else:
        url = urljoin(url, "api/product-carts/")
        headers = {"Authorization": f"Bearer {token}"}
        data = {
            "data": {
                "cart": {"connect": cart_document_id},
                "product": {"connect": product_document_id},
                "amount_kg": amount_kg,
            }
        }

        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["data"]["documentId"]


def get_cart_products(url, token, user_tg_id):
    url = urljoin(url, "api/product-carts/")
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "filters[cart][tg_user_id][$eq]": user_tg_id,
        "populate[0]": "product",
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()["data"]


def delete_from_cart(url, token, product_cart_document_id):
    url = urljoin(url, f"api/product-carts/{product_cart_document_id}")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(url, headers=headers)
    response.raise_for_status()


def add_client_email(url, token, email, tg_user_id):
    url = urljoin(url, "api/clients/")
    headers = {"Authorization": f"Bearer {token}"}
    data = {"data": {"email": email, "tg_user_id": str(tg_user_id)}}
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
