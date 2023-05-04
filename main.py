#!/usr/bin/env python
# pylint: disable=unused-argument, wrong-import-position
# This program is dedicated to the public domain under the CC0 license.

import logging
import re
import os
import chardet
import shutil
import telnetlib
import configparser

from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    CallbackContext
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Stages
START_ROUTES, END_ROUTES, SHOW_USER_LIST_STATE, SHOW_USER_LIST_STATE_UNBAN= range(4)
# Callback data
ONE, TWO, THREE, FOUR, BANLIST, BAN, SHOW_USER_LIST, BAN_USER, UNBAN_USER, SHOW_USER_LIST_UNBAN, FAKESTART = range(11)

# чтение конфигурационного файла
config = configparser.ConfigParser()
config.read('config.ini')

# ID группы, в которой должен запускаться код
group_id = config.getint('group', 'group_id')

# создание словаря allowed_users
allowed_users = {}
for key, value in config.items('USERS'):
    if value.lower() == 'true':
        allowed_users[key] = True

token = config.get('TelegramBot', 'token')

def tim():
    from datetime import datetime
    now = datetime.now()
    date_string = datetime.strftime(now, "%m/%d/%Y, %H:%M:%S")
    return date_string

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Валидация запуска кода в определенной группе
    chat_id = update.effective_chat.id
    if chat_id != group_id:
        context.bot.send_message(chat_id=chat_id, text="Данный функционал доступен только в определенной группе.")
        return
    
    user = update.message.from_user
    logger.info("User %s started the conversation.", user.first_name)
    keyboard = [
        [InlineKeyboardButton("Список активных сертификатов", callback_data=str(ONE))],
        [InlineKeyboardButton("Список серверов", callback_data=str(TWO))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите сервер:", reply_markup=reply_markup)

    return START_ROUTES

async def fakestart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("Список активных сертификатов", callback_data=str(ONE))],
        [InlineKeyboardButton("Список серверов", callback_data=str(TWO))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text="Сервера профилей", reply_markup=reply_markup
    )

    return START_ROUTES

def get_users():
    users = []
    for file in os.listdir('/root/'):
        if file.endswith('.ovpn'):
            users.append(file[:-5])
    return users

async def one(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    # Получаем список пользователей и сортируем его по алфавиту
    users = get_users()
    users = sorted(users)

    # Создаем текст сообщения
    message_text = "Список активных сертификатов: " + ", ".join(users) + f" ({tim()})"

    # Создаем кнопки для перехода в главное меню
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Главное меню", callback_data=str(FAKESTART))]])

    # Отправляем сообщение с результатами
    await query.edit_message_text(
        text=message_text,
        reply_markup=reply_markup
    )

    return START_ROUTES

async def two(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    query = update.callback_query
    await query.answer()
    keyboard = [
        [
            InlineKeyboardButton("Пал", callback_data=str(THREE)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="Сервера профилей", reply_markup=reply_markup
    )
    return START_ROUTES

async def three(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    keyboard = [
        
            [InlineKeyboardButton("Список активных пользователей", callback_data=str(FOUR))],
            [InlineKeyboardButton("Список заблокированных пользователей", callback_data=str(BANLIST))],
            [InlineKeyboardButton("❌Заблокировать сертификат", callback_data=str(BAN))],
        
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="Выберите действие", reply_markup=reply_markup
    )
    return START_ROUTES
async def four(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query

    # Открываем файл с логом
    with open('/etc/openvpn/server/openvpn-status.log', 'r') as file:
        data = file.read()

        # Находим все строки, начинающиеся с "CLIENT_LIST"
        pattern = r'(?<=CLIENT_LIST,)[^,]*,[^,]*\b(?:\d{1,3}\.){3}\d{1,3}'
        text = re.findall(pattern, data)

        # Заменяем запятые на двоеточие и пробел
        ips = [re.sub(r',', ': ', line) for line in text]

        # Объединяем строки в одну с разделителем в виде пробела
        ips_str = '\n'.join(ips)

    await query.answer()
    keyboard = [
        [
            InlineKeyboardButton("Главное меню", callback_data=str(THREE)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Вывод списка юзеров для определенного сервера
    await query.edit_message_text(
        text=f"Список активных сертификатов:\n{ips_str}", reply_markup=reply_markup
    )
    return START_ROUTES

async def banlist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    await query.answer()
    keyboard = [
        [
            InlineKeyboardButton("Главное меню", callback_data=str(THREE)),
            InlineKeyboardButton("✔Разблокировать пользователя", callback_data=str(SHOW_USER_LIST_UNBAN)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Поиск заблокированных сертификатов в указанной папке
    blocked_certs = []
    for filename in os.listdir('/etc/openvpn/server/ccd'):
        with open(os.path.join('/etc/openvpn/server/ccd/', filename), 'rb') as f:
            encoding = chardet.detect(f.read())['encoding']
        with open(os.path.join('/etc/openvpn/server/ccd', filename), 'r', encoding=encoding) as f:
            if 'disable' in f.read():
                blocked_certs.append(filename)

    result_str = ', '.join(blocked_certs)
    await query.edit_message_text(
        text=f"Список заблокированных для определенного сервера:\n{result_str}",
        reply_markup=reply_markup
    )

    return START_ROUTES

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    await query.answer()
    keyboard = [
        [
            InlineKeyboardButton("Список для блокировки", callback_data=str(SHOW_USER_LIST)),
            InlineKeyboardButton("Главное меню", callback_data=str(FAKESTART)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Вывод списка юзеров для определенного сервера
    await query.edit_message_text(
        text="Кого заблокировать", reply_markup=reply_markup
    )

    return START_ROUTES

####################################################
async def show_user_list(update, context):
    """Вывод списка пользователей для бана"""
    query = update.callback_query

    if str(query.from_user.id) not in allowed_users:
        await query.answer(text='А всё, я вижу кто взаимодействует с ботом, забанить хотел, хитрюшка')
        return

    # Получаем список всех файлов в директории /root/
    files = os.listdir('/root/')
    # Отфильтровываем файлы по расширению ".ovpn"
    ovpn_files = [f for f in files if f.endswith('.ovpn')]
    ovpn_files.sort()

    # Разбиваем список на страницы по 10 файлов
    page_size = 10
    pages = [ovpn_files[i:i+page_size] for i in range(0, len(ovpn_files), page_size)]

    # Получаем текущую страницу из контекста
    current_page = context.user_data.get('current_page', 0)

    # Создаем список кнопок для каждого пользователя на текущей странице
    buttons = []
    for user in pages[current_page]:
        buttons.append([InlineKeyboardButton(user, callback_data=user)])

    # Добавляем кнопки для навигации по страницам
    prev_button = InlineKeyboardButton('Предыдущая', callback_data='prev_page')
    next_button = InlineKeyboardButton('Далее', callback_data='next_page')
    buttons.append([prev_button, next_button])

    # Создаем клавиатуру
    keyboard = InlineKeyboardMarkup(buttons)

    # Отображаем список пользователей на текущей странице
    await query.edit_message_text(text='Выберите пользователя для блокировки:', reply_markup=keyboard)

    return SHOW_USER_LIST_STATE

async def handle_callback(update, context):
    """Обработка callback-запросов"""
    query = update.callback_query
    data = query.data

    # Если нажата кнопка "Далее"
    if data == 'next_page':
        current_page = context.user_data.get('current_page', 0)
        context.user_data['current_page'] = current_page + 1

        # Показываем следующую страницу
        await show_user_list(update, context)

    # Если нажата кнопка "Предыдущая"
    elif data == 'prev_page':
        current_page = context.user_data.get('current_page', 0)
        context.user_data['current_page'] = current_page - 1

        # Показываем предыдущую страницу
        await show_user_list(update, context)

    # Если нажата кнопка с именем пользователя
    else:
        # Добавляем disable в сертификат пользователя
        await ban_user(update, context)

async def ban_user(update, context):
    """Добавление ключа disable в сертификат для блокировки пользователя и перемещение активного сертификата"""
    query = update.callback_query
    user = query.data

    # Отключаем клиента через telnet
    tn = telnetlib.Telnet("localhost", 7505)
    tn.write(f'kill {user[:-5]}\n'.encode())
    tn.write(b'exit\n')
    tn.read_all()

    # Перемещаем активный сертификат пользователя в директорию /etc/openvpn/server/ccd/ и переименовываем его
    cert_path = f'/root/{user}'
    cert_dest_path = f'/etc/openvpn/server/ccd/{user[:-5]}'
    shutil.move(cert_path, cert_dest_path)

    # Добавляем ключ disable в конец сертификата
    with open(cert_dest_path, 'a') as f:
        f.write('\n# User disabled\ndisable\n')

    # Отображаем сообщение об успешном добавлении файла
    await query.answer(text=f'Пользователь {user} заблокирован')

    # Отключаем кнопку пользователя
    keyboard = InlineKeyboardMarkup([])
    await query.edit_message_reply_markup(reply_markup=keyboard)

    return SHOW_USER_LIST

############################

async def show_user_list_unban(update, context):
    """Вывод списка пользователей для бана"""
    query = update.callback_query

    if str(query.from_user.id) not in allowed_users:
        await query.answer(text='А всё, я вижу кто взаимодействует с ботом, забанить хотел, хитрюшка')
        return

    # Получаем список всех файлов в директории /root/
    ovpn_files = []
    for file in os.listdir('/etc/openvpn/server/ccd/'):
        ovpn_files.append(file)

    ovpn_files.sort()

    # Разбиваем список на страницы по 10 файлов
    page_size = 10
    pages = [ovpn_files[i:i+page_size] for i in range(0, len(ovpn_files), page_size)]

    # Получаем текущую страницу из контекста
    current_page = context.user_data.get('current_page', 0)

    # Создаем список кнопок для каждого пользователя на текущей странице
    buttons = []
    for user in pages[current_page]:
        buttons.append([InlineKeyboardButton(user, callback_data=user)])

    # Добавляем кнопки для навигации по страницам
    prev_button = InlineKeyboardButton('Предыдущая', callback_data='prev_page')
    next_button = InlineKeyboardButton('Далее', callback_data='next_page')
    buttons.append([prev_button, next_button])

    # Создаем клавиатуру
    keyboard = InlineKeyboardMarkup(buttons)

    # Отображаем список пользователей на текущей странице
    await query.edit_message_text(text='Выберите пользователя для разблокировки:', reply_markup=keyboard)

    return SHOW_USER_LIST_STATE_UNBAN

async def handle_callbackk(update, context):
    """Обработка callback-запросов"""
    query = update.callback_query
    data = query.data

    # Если нажата кнопка "Далее"
    if data == 'next_page':
        current_page = context.user_data.get('current_page', 0)
        context.user_data['current_page'] = current_page + 1

        # Показываем следующую страницу
        await show_user_list_unban(update, context)

    # Если нажата кнопка "Предыдущая"
    elif data == 'prev_page':
        current_page = context.user_data.get('current_page', 0)
        context.user_data['current_page'] = current_page - 1

        # Показываем предыдущую страницу
        await show_user_list_unban(update, context)

    # Если нажата кнопка с именем пользователя
    else:
        # Добавляем disable в сертификат пользователя
        await unban_user(update, context)


async def unban_user(update, context):
    """Удаление ключа disable в сертификате для разблокировки пользователя"""
    query = update.callback_query
    user = query.data

    # Удаляем ключ disable из сертификата пользователя
    cert_path = f'/etc/openvpn/server/ccd/{user}'
    with open(cert_path, 'r') as f:
        lines = f.readlines()
    with open(cert_path, 'w') as f:
        for line in lines:
            if 'disable' not in line:
                f.write(line)

    # Перемещаем сертификат пользователя обратно в директорию /root/ и переименовываем его
    cert_dest_path = f'/root/{user}.ovpn'
    shutil.move(cert_path, cert_dest_path)

    # Отображаем сообщение об успешной разблокировке пользователя
    await query.answer(text=f'Пользователь {user} разблокирован')

    # Отключаем кнопку пользователя
    keyboard = InlineKeyboardMarkup([])
    await query.edit_message_reply_markup(reply_markup=keyboard)

    return SHOW_USER_LIST_UNBAN


#################################

async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="See you next time!")
    return ConversationHandler.END

def main() -> None:
    application = Application.builder().token(token).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("vpn", start)],
        states={
            START_ROUTES: [
                CallbackQueryHandler(one, pattern="^" + str(ONE) + "$"),
                CallbackQueryHandler(fakestart, pattern="^" + str(FAKESTART) + "$"),
                CallbackQueryHandler(two, pattern="^" + str(TWO) + "$"),
                CallbackQueryHandler(three, pattern="^" + str(THREE) + "$"),
                CallbackQueryHandler(four, pattern="^" + str(FOUR) + "$"),
                CallbackQueryHandler(banlist, pattern="^" + str(BANLIST) + "$"),
                CallbackQueryHandler(ban, pattern="^" + str(BAN) + "$"),
                CallbackQueryHandler(show_user_list, pattern=f"^{SHOW_USER_LIST}$"),
                CallbackQueryHandler(show_user_list_unban, pattern=f"^{SHOW_USER_LIST_UNBAN}$"),
                CallbackQueryHandler(ban_user, pattern='.*\.ovpn$'),
                CallbackQueryHandler(unban_user, pattern='.*\.ovpn$')
            ],
            END_ROUTES: [
                CallbackQueryHandler(end, pattern="^" + str(TWO) + "$"),
            ],
            SHOW_USER_LIST_STATE: [
                CallbackQueryHandler(handle_callback),  # Обработчик callback-запрос
            ],
            SHOW_USER_LIST_STATE_UNBAN: [
                CallbackQueryHandler(handle_callbackk),  # Обработчик callback-запрос
            ]
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True
    )
    
    application.add_handler(conv_handler)

    application.run_polling()
    
if __name__ == "__main__":
    main()
