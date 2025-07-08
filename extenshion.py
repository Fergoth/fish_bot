import requests
import os
from dotenv import load_dotenv
from io import BytesIO
from urllib.parse import urljoin


def get_products(documentId=None):
    url = os.getenv("STRAPI_URL")
    url = urljoin(url, "api/products/")
    params = {}
    if documentId is not None:
        url = urljoin(url, documentId)
        params["populate"] = "picture"
    token = os.getenv("STRAPI_TOKEN")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers, params=params)
    print(response.url)
    if response.status_code == 200:
        return response.json()["data"]
    else:
        raise Exception(f"Ошибка: {response.status_code, response.text}")


def get_picture(picture_url):
    url = urljoin(os.getenv("STRAPI_URL"), picture_url)
    token = os.getenv("STRAPI_TOKEN")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return BytesIO(response.content)
    else:
        raise Exception(f"Ошибка: {response.status_code, response.text}")


if __name__ == "__main__":
    load_dotenv()
    print(get_products("j269sqg0kjjjtqv90i6f5tu8"))
