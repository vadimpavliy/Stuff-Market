# Stuff Market Bot

Stuff Market Bot - это Telegram-бот для интернет-магазина, который позволяет пользователям просматривать товары, добавлять их в корзину и оформлять заказы. Бот также предоставляет административные функции для управления товарами и рассылки сообщений пользователям.

## Описание

Бот включает в себя следующие функции:

- Регистрация пользователей и управление корзиной.
- Просмотр каталога товаров и их категорий.
- Добавление товаров в корзину и оформление заказов.
- Административные команды для добавления новых товаров и рассылки сообщений.

## Технологии

Проект разработан с использованием следующих технологий:

- **Python**: основной язык программирования.
- **aiogram**: библиотека для работы с Telegram Bot API.
- **aiohttp**: библиотека для асинхронных HTTP-запросов.
- **MongoDB**: база данных для хранения информации о пользователях и товарах.

## Установка

Чтобы запустить проект локально, выполните следующие шаги:

1. Клонируйте репозиторий:

```
git clone https://github.com/vadimpavliy/Stuff-Market.git
```
2. Перейдите в директорию проекта:
```
cd Stuff-Market
 ```
3. Установите зависимости:
  ```
pip install -r requirements.txt
   ```
4. Настройте файл конфигурации config.pyнеобходимые параметры.
  ``` 
    TOKEN=
    ENGINE=
    ECHO=True
    SHOP_ID = 
    SECRET_KEY = 
  ```
5. Запустите бота:
  ```
python run.py
   ```