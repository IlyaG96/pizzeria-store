# Торговый бот для продажи пиццы

Учебный проект курсов веб-разработчиков [dvmn](https://dvmn.org).  

## Установка
Вам понадобится установленный Python 3.8+ и git.

Склонируйте репозиторий:
```bash
git clone git@github.com:IlyaG96/pizzeria-store.git
```

Создайте в этой папке виртуальное окружение:
```bash
cd pizzeria-store
python3 -m venv env
```

Активируйте виртуальное окружение и установите зависимости:
```bash
source env/bin/activate
pip install -r requirements.txt
```
Или запустите, используя Docker.
- Соберите контейнер
```shell
docker build -t pizzeria-bot .
```
- Запустите образ контейнера:
```shell
docker run -d --env-file ./.env pizzeria-bot
```
Или запустите, используя Docker compose:
```shell
docker compose up
```

## Настройка перед использованием

### Переменные окружения

Перед использованием вам необходимо заполнить .env.example файл или иным образом передать переменные среды:
* TG_TOKEN - токен бота Telegram. Можно получить у [@BotFather](https://t.me/BotFather).
* PAYMENT_TOKEN - платежный токен для бота. Поучать у [@BotFather](https://t.me/BotFather) --> payments
* REDIS_HOST - публичный адрес базы данных Redis
* REDIS_PORT - порт БД Redis
* REDIS_PASSWORD - пароль БД Redis
* ELASTIC_CLIENT_ID - id клиента [elasticpath.com](https://www.elasticpath.com)
* ELASTIC_CLIENT_SECRET - секретный ключ клиента [elasticpath.com](https://www.elasticpath.com)
* YANDEX_GEO_API - токен для работы с API Яндекс-геокодера [Инструкция по подключению](https://dvmn.org/encyclopedia/api-docs/yandex-geocoder-api/)

## Использование


### Телеграм-бот

Бот представляет из себя торговый автомат для заказа пиццы. На данный момент можно сформировать тестовый заказ и оформить доставку.
После успешной оплаты одной из [тестовых карт сбербанка](https://securepayments.sberbank.ru/wiki/doku.php/test_cards) 
Вам придет сообщение с предложением забрать пиццу по определенному адресу (при выборе самовывоза) или, если была выбрана курьерская доставка, 
бот отправит сообщение с уведомлением курьеру.

Для старта телеграм-бота, запустите скрипт:
```bash
$ python bot.py
```

### elastic_api.py
<details>
<summary>Открыть описание</summary>


* Используются для работы с API [elasticpath.com](https://www.elasticpath.com)
* [API](https://documentation.elasticpath.com)
</details>

### bot_tools.py
<details>
<summary>Открыть описание</summary>


Содержит в себе функции для:
* Формирования описаний корзины, товара.  
* Создания "красивого" меню для бота.
* Работы с геокодером.
* Отправки уведомлений пользователю.
* Нахождения ближайшей пиццерии.
</details>

