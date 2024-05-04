from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters
import gspread
import schedule
import time
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build

TOKEN = "#ВАШ_ТОКЕН"
CREDENTIALS_FILE = 'credentials.json'
SCOPE = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive.file','https://www.googleapis.com/auth/drive']
TABLE_NAME = '#НАЗВАНИЕ_ТАБЛИЦЫ'

event_data = {}

MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

MONTH_ROW_MAP = {'January': 3,'February': 11, 'March': 19, 'April': 27, 
'May': 35, 'June': 43, 'July': 51, 'August': 59, 'September': 67, 'October': 75, 'November': 83, 'December': 91}

credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPE)
client = gspread.authorize(credentials)
sheet = client.open(TABLE_NAME).sheet1

def update_internal_state():
    # Read updated data from spreadsheet using gspread
    sheet = client.open(TABLE_NAME).sheet1
    updated_data = sheet.get_all_records()
# Update event_data dictionary with new data
    for row in updated_data:
        chat_id = row['chat_id']
        event_data[chat_id] = {
        'month': row['month'],
        'date': row['date'],
        'row': row['row'],
        'column': row['column'],
        'info': row['info']
        }
schedule.every(1).minutes.do(update_internal_state) # Run every 1 minute

def check_if_row_empty(chat_id, row_index):
    cell_text = sheet.cell(MONTH_ROW_MAP[event_data[chat_id]['month']] + row_index - 1, 
                        2 + int(event_data[chat_id]['date'])).value
    return not bool(cell_text)

def get_order_info(chat_id, row_index):
    event_data[chat_id]["row"] = MONTH_ROW_MAP[event_data[chat_id]['month']] + row_index - 1
    cell_text = sheet.cell(event_data[chat_id]['row'], 
                        2 + int(event_data[chat_id]['date'])).value
    return cell_text.split('\n')[1].split(' - ')[1]  # extract address info

spreadsheet_id = sheet.spreadsheet.id
service = build('sheets', 'v4', credentials=credentials)

def start(update: Update, context: CallbackContext) -> None:
    user_name = update.message.from_user.first_name
    update.message.reply_text(f'Привет, {user_name}!\n'
                              f'Для выбора даты заказа отправьте /date. '
                              f'Для подтверждения или отмены заказа отправьте /confirm.\n')

def get_date(update: Update, context: CallbackContext) -> None:
    keyboard = []
    for i in range(12):
        keyboard.append([InlineKeyboardButton(MONTHS[i], callback_data="month|%s" %i)])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Выберите месяц:', reply_markup=reply_markup)

def confirm(update: Update, context: CallbackContext) -> None:
    keyboard = []
    for i in range(12):
        keyboard.append([InlineKeyboardButton(MONTHS[i], callback_data="confirm_month|%s" %i)])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Выберите месяц для подтверждения/отмены заказа:', reply_markup=reply_markup)

def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    data = query.data.split('|')
    chat_id = query.message.chat_id

    if data[0] == "month":
        event_data[chat_id] = {"month": MONTHS[int(data[1])]}
        keyboard = []
        for i in range(1, 32):
            keyboard.append([InlineKeyboardButton("%s" %i, callback_data="date|%s" %i)])
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text('Выберите день:', reply_markup=reply_markup)
    elif data[0] == "date":
        event_data[chat_id]["date"] = data[1]
        keyboard = []
        for i in range(1, 7):
            if check_if_row_empty(chat_id, i):
                keyboard.append([InlineKeyboardButton("%s" %i, callback_data="line|%s" %i)])
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text('Выберите строку:', reply_markup=reply_markup)
    elif data[0] == "line":
        event_data[chat_id]["row"] = MONTH_ROW_MAP[event_data[chat_id]['month']] + int(data[1])-1
        event_data[chat_id]["column"] = 2 + int(event_data[chat_id]['date'])
        event_data[chat_id]['info'] = []
        query.edit_message_text("Введите клиента:")
    elif data[0] == "no":
        event_data[chat_id]["color"] = "yellow"
        save_event(chat_id)
        query.edit_message_text("Заказ добавлен!")
    elif data[0] == "yes":
        event_data[chat_id]["color"] = "red"
        save_event(chat_id)
        query.edit_message_text("Заказ добавлен!")

    elif data[0] == "confirm_month":
        event_data[chat_id] = {"month": MONTHS[int(data[1])]}
        keyboard = []
        for i in range(1, 32):
            keyboard.append([InlineKeyboardButton("%s" %i, callback_data="confirm_date|%s" %i)])
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text('Выберите день:', reply_markup=reply_markup)
    elif data[0] == "confirm_date":
        event_data[chat_id]["date"] = data[1]
        keyboard = []
        for i in range(1, 7):
            if not check_if_row_empty(chat_id, i):
                cell_text = sheet.cell(MONTH_ROW_MAP[event_data[chat_id]['month']] + i - 1, 2 + int(event_data[chat_id]['date'])).value
                first_line = cell_text.split('\n')[0]
                keyboard.append([InlineKeyboardButton(first_line, callback_data="confirm_line|{}".format(i))])
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text('Выберите заказ для подтверждения/отмены:', reply_markup=reply_markup)
    elif data[0] == "confirm_line":
        event_data[chat_id]["row"] = MONTH_ROW_MAP[event_data[chat_id]['month']] + int(data[1])-1
        event_data[chat_id]["column"] = 2 + int(event_data[chat_id]['date'])
        keyboard = [[InlineKeyboardButton("Подтвердить", callback_data="confirm_yes"), InlineKeyboardButton("Отменить", callback_data="confirm_no")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text("Вы хотите подтвердить или отменить этот заказ?", reply_markup=reply_markup)
    elif data[0] == "confirm_no":
        event_data[chat_id]["color"] = "gray"
        event_data[chat_id]['info'] = sheet.cell(event_data[chat_id]['row'], event_data[chat_id]['column']).value
        save_event(chat_id)
        query.edit_message_text("Заказ был отменен!")
    elif data[0] == "confirm_yes":
        event_data[chat_id]["color"] = "red"
        event_data[chat_id]['info'] = sheet.cell(event_data[chat_id]['row'], event_data[chat_id]['column']).value
        save_event(chat_id)
        query.edit_message_text("Заказ подтвержден!")

def message(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    if chat_id in event_data and "info" in event_data[chat_id]:
        event_data[chat_id]['info'].append(update.message.text)
        if len(event_data[chat_id]['info']) < 5:
            questions = ["Введите адрес", "Введите количество артистов:", "Какие костюмы?", "Введите время заказа:"]
            update.message.reply_text(questions[len(event_data[chat_id]['info']) - 1])
        else:
            info_data = event_data[chat_id]['info']
            event_data[chat_id]['info'] = f"{info_data[0]}\nАдрес - {info_data[1]}\nКол-во арт - {info_data[2]}\nКостюмы - {info_data[3]}\nВремя - {info_data[4]}"
            keyboard = [[InlineKeyboardButton("Да", callback_data="yes"), InlineKeyboardButton("Нет", callback_data="no")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text("Подтвержден ли заказ?", reply_markup=reply_markup)
    else:
        update.message.reply_text("Не найдена дата заказа, введите /date")

def save_event(chat_id):
    credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPE)
    client = gspread.authorize(credentials)
    sheet = client.open(TABLE_NAME).sheet1

    cell = sheet.cell(event_data[chat_id]['row'], event_data[chat_id]['column'])
    cell.value = event_data[chat_id]['info']
    sheet.update_cells([cell])

    service = build('sheets', 'v4', credentials=credentials)
    requests = []
    if event_data[chat_id]['color'] == "red":
        color = {
            "red": 1,
            "green": 0,
            "blue": 0
        }
    elif event_data[chat_id]['color'] == "yellow":
        color = {
            "red": 1,
            "green": 1,
            "blue": 0
        }
    elif event_data[chat_id]['color'] == "gray":
        color = {
            "red": 0.5,
            "green": 0.5,
            "blue": 0.5
        }

    requests.append({
        'repeatCell': {
            'range': {
                'sheetId': 0,
                'startRowIndex': event_data[chat_id]['row']-1,
                'endRowIndex': event_data[chat_id]['row'],
                'startColumnIndex': event_data[chat_id]['column']-1,
                'endColumnIndex': event_data[chat_id]['column'],
            },
            'cell': {
                'userEnteredFormat': {
                    'backgroundColor': color,
                    'wrapStrategy': 'WRAP'  # Adding wrapStrategy to enable text wrap
                }
            },
            'fields': 'userEnteredFormat(backgroundColor,wrapStrategy)',
        }
    })

    body = {
        'requests': requests
    }

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=body).execute()

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("date", get_date))
    dp.add_handler(CommandHandler("confirm", confirm))
    dp.add_handler(MessageHandler(Filters.text, message))
    dp.add_handler(CallbackQueryHandler(button))

    updater.start_polling()
    updater.idle()
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    main()