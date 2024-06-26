Описание бота для Telegram:
Бот предназначен для управления заказами в таблице Google Sheets через Telegram. Он позволяет пользователям выбрать дату и строку для добавления или подтверждения заказа, а также вводить информацию о клиенте и заказе.
Функциональность бота:
1. При запуске бота пользователь получает приветственное сообщение с инструкциями.
2. Пользователь может отправить команду `/date` для выбора даты заказа.
3. Бот предлагает выбор месяца, а затем дня из календаря.
4. После выбора дня бот предлагает выбор строки для добавления заказа.
5. Пользователь может вводить информацию о клиенте и заказе, которую бот сохраняет в таблице Google Sheets.
6. Пользователь может отправить команду `/confirm` для подтверждения или отмены заказа.
7. Бот предлагает выбор месяца и дня для подтверждения или отмены заказа.
8. После выбора дня бот предлагает выбор строки для подтверждения или отмены заказа.
9. Бот изменяет цвет ячейки в таблице Google Sheets в зависимости от статуса заказа (подтвержден, отменен или ожидает подтверждения).
Технологии:
* Python
* Telegram API
* Google Sheets API
* gspread library for interacting with Google Sheets
* schedule library for running tasks at regular intervals
<img width="1142" alt="Снимок экрана 2024-05-04 в 3 45 26 PM" src="https://github.com/beliybear/googlesheets_bot/assets/95547886/62ed78f5-b876-4daf-9107-ede33ae8d671">

