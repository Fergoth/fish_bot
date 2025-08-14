# Чат бот для продажи Рыбы в ТГ



## Окружение
### Требования
Для запуска требуется python версии 3.10 и установленный [Redis](https://redis-docs.ru/operate/oss_and_stack/install/install-redis/). Или установленная утилита [uv](https://docs.astral.sh/uv/) 



### Установка зависимостей (если нет uv) 
```sh
pip install -r requirements.txt
```
### Переменные окружения

1. Создайте файл `.env` в папке проекта
2. Заполните файл `.env` следующим образом без кавычек:
```bash
TELEGRAM_TOKEN= токен для тг бота
STRAPI_TOKEN= токен для strapi
STRAPI_URL= урл для strapi
REDIS_HOST= хост редис
REDIS_PORT= порт редис
REDIS_NAME= номер базы данных редис
```
#### Как получить токены

* Токен для телеграм бота TELEGRAM_BOT_TOKEN(Бот для квиза)  можно получить при создании бота [ссылке](https://telegram.me/BotFather)
* STARAPI_TOKEN - токен для strapi, можно получить при создании проекта в [strapi](https://docs.strapi.io/cms/quick-start)
* STARAPI_URL - урл для strapi, можно получить при создании проекта в [strapi](https://docs.strapi.io/cms/quick-start)


### Запустите скрипт 
```sh
python tg_bot.py 
```
для запуска бота в телеграме,



### При наличии uv
- Просто запустите скрипт с помощью uv 
```sh
uv run tg_bot.py 
```

### Примечание

  Напишите телеграм боту чтобы он мог отправлять вам сообщения

### Пример использования

[tg](https://t.me/fish_shop_dvmn23423_bot)

