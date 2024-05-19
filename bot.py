import logging
import subprocess
import re
import paramiko
import os
import psycopg2
from psycopg2 import Error
from functools import partial
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

TOKEN = os.getenv('TOKEN')

# Подключаем логирование
logging.basicConfig(
    filename='/app/logfile.txt',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    encoding="utf-8"
)
logger = logging.getLogger(__name__)

def switch_command(argument):
    switcher = {
        "pnone": "SELECT * FROM Ph_number;",
        "email": "SELECT * FROM Email_add;",
        "release": "lsb_release -d",
        "uname": "uname -a",
        "uptime": "uptime",
        "df": "df -h",
        "free": "free -h",
        "mpstat": "mpstat",
        "w": "w",
        "auths": "last -n 10",
        "critical": "journalctl -p crit -n 5",
        "ps": "ps aux",
        "ss": "ss -tulwn",
        "services": "service --status-all",
	"repl": "tac /var/log/postgresql/$(ls -t /var/log/postgresql | head -n 1) | grep repl_user"
    }
    return switcher.get(argument, "Invalid command")

def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(
        f'Привет {user.full_name}! Введите /help для отображения списка команд.'
    )

def helpCommand(update: Update, context):
    help_text = (
        "Список доступных команд:\n"
        "/start - Начать диалог\n"
        "/help - Список команд\n"
        "/find_email - Найти email-адреса в тексте\n"
        "/find_phone_number - Найти телефонные номера в тексте\n"
        "/verify_password - Проверить сложность пароля\n"
        "/cancel - Отмена текущей команды"
    )
    help_text2 = (
        "Команды работы с Linux-машиной:\n"
        "/get_release - О релизе\n"
        "/get_uname - Об архитектуре процессора, имени хоста, системы и версии ядра\n"
        "/get_uptime - О времени работы\n"
        "/get_df - Сбор информации о состоянии файловой системы\n"
        "/get_free - Сбор информации о состоянии оперативной памяти\n"
        "/get_mpstat - Сбор информации о производительности системы\n"
        "/get_w - Сбор информации о работающих в данной системе пользователях\n"
        "/get_auths - Последние 10 входов в систему\n"
        "/get_critical - Последние 5 критических событий\n"
        "/get_ps - Сбор информации о запущенных процессах\n"
        "/get_ss - Сбор информации об используемых портах\n"
        "/get_apt_list - Сбор информации об установленных пакетах\n"
        "/get_services - Сбор информации о запущенных сервисах"
    )
    help_text3 = (
        "Команды для работы с БД:\n"
        "/get_emails - Получить список email адресов из базы данных\n"
        "/get_phone_numbers - Получить список телефонных номеров из базы данных\n"
        "/get_repl_logs - Получить логи репликации PostgreSQL"
    )
    update.message.reply_text(help_text)
    update.message.reply_text(help_text2)
    update.message.reply_text(help_text3)

def findEmailsCommand(update: Update, context):
    update.message.reply_text(
        'Введите текст для поиска email-адресов (/cancel для отмены):'
    )
    return 'findEmails'

def findEmails(update: Update, context):
    user_input = update.message.text

    if user_input == '/cancel':
        update.message.reply_text('Отмена действия')
        return ConversationHandler.END

    email_regex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    email_list = email_regex.findall(user_input)

    if not email_list:
        update.message.reply_text(
            'Email-адреса не найдены. Для повторного запроса введите команду ещё раз (/find_email)'
        )
        return ConversationHandler.END

    unique_emails = set(email_list)
    email_list = list(unique_emails)

    emails = '\n'.join(email_list)
    update.message.reply_text(emails)

    update.message.reply_text(
        'Введите цифру \n1-Записать данные в базу данных;\n2-Не записывать в базу данных\n (/cancel для отмены):'
    )

    context.user_data['emails'] = email_list
    return 'emailInsert'

def emailInsert(update: Update, context):
    user_input = update.message.text
    email_list = context.user_data['emails']

    if user_input == '/cancel':
        update.message.reply_text('Отмена действия')
        return ConversationHandler.END

    if user_input == '1':
        for email in email_list:
            if not record_exists('Email_add', 'EmailAddr', email):
                dbCommand = f"INSERT INTO Email_add (EmailAddr) VALUES ('{email}');"
                dbInsert(update, context, dbCommand)
        update.message.reply_text('Email-адреса записаны в базу данных.')
        return ConversationHandler.END

    elif user_input == '2':
        update.message.reply_text('Email-адреса не записаны в базу данных.')
        return ConversationHandler.END

    else:
        update.message.reply_text('Неверный ввод')
        return 'emailInsert'

def findPhoneNumbersCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров (/cancel для отмены):')
    return 'findPhoneNumbers'

def findPhoneNumbers(update: Update, context):
    user_input = update.message.text

    if user_input == '/cancel':
        update.message.reply_text('Отмена действия')
        return ConversationHandler.END

    phone_list = [
        re.sub(r'\D', '', m.group())
        for m in re.finditer(r"\+?7[ -]?\(?\d{3}\)?[ -]?\d{3}[ -]?\d{2}[ -]?\d{2}|\+?7[ -]?\d{10}|\+?7[ -]?\d{3}[ -]?\d{3}[ -]?\d{4}|8[ -]?\(?\d{3}\)?[ -]?\d{3}[ -]?\d{2}[ -]?\d{2}|8[ -]?\d{10}|8[ -]?\d{3}[ -]?\d{3}[ -]?\d{4}", user_input)
    ]

    unique_phones = set()
    for phone in phone_list:
        if phone.startswith('7'):
            phone = '8' + phone[1:]
        elif phone.startswith('+7'):
            phone = '8' + phone[2:]
        unique_phones.add(phone)

    phone_list = list(unique_phones)

    if not phone_list:
        update.message.reply_text('Телефонные номера не найдены. Для повторного запроса введите команду ещё раз(/find_phone_number)')
        return ConversationHandler.END

    phones = '\n'.join(phone_list)
    update.message.reply_text(phones)

    update.message.reply_text(
        'Введите цифру \n1-Записать данные в базу данных;\n2-Не записывать в базу данных\n (/cancel для отмены):'
    )

    context.user_data['phones'] = phone_list
    return 'phoneInsert'

def phoneInsert(update: Update, context):
    user_input = update.message.text
    phone_list = context.user_data['phones']

    if user_input == '/cancel':
        update.message.reply_text('Отмена действия')
        return ConversationHandler.END

    if user_input == '1':
        for phone in phone_list:
            if not record_exists('Ph_number', 'PhoneNumber', phone):
                dbCommand = f"INSERT INTO Ph_number (PhoneNumber) VALUES ('{phone}');"
                dbInsert(update, context, dbCommand)
        update.message.reply_text('Телефонные номера записаны в базу данных.')
        return ConversationHandler.END

    elif user_input == '2':
        update.message.reply_text('Телефонные номера не записаны в базу данных.')
        return ConversationHandler.END

    else:
        update.message.reply_text('Неверный ввод')
        return 'phoneInsert'

def verifyPasswordCommand(update: Update, context):
    update.message.reply_text(
        'Введите пароль для проверки (/cancel для отмены):'
    )
    return 'verifyPassword'

def verifyPassword(update: Update, context):
    user_input = update.message.text
    if user_input == '/cancel':
        update.message.reply_text('Отмена действия')
        return ConversationHandler.END
    password_regex = re.compile(
        r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()])[A-Za-z\d!@#$%^&*()]{8,}$'
    )
    if password_regex.match(user_input):
        update.message.reply_text(
            'Пароль сложный. Для повторного запроса введите команду ещё раз(/verify_password)'
        )
    else:
        update.message.reply_text(
            'Пароль простой. Для повторного запроса введите команду ещё раз(/verify_password)'
        )
        return ConversationHandler.END
    return ConversationHandler.END

def aptListCommand(update: Update, context):
    update.message.reply_text(
        'Введите цифру \n1-Вывод всех пакетов;\n2-Поиск информации о выбранном пакете\n (/cancel для отмены):'
    )
    return 'aptListChoice'

def aptListChoice(update: Update, context):
    user_input = update.message.text
    if user_input == '/cancel':
        update.message.reply_text('Отмена действия')
        return ConversationHandler.END
    if user_input == '1':
        linCommand = 'dpkg -l'
        return hostCheck(update, context, linCommand)
    elif user_input == '2':
        update.message.reply_text('Введите название нужного пакета')
        return 'aptPackageSearch'
    else:
        update.message.reply_text('Неверный ввод')
        return 'aptListChoice'

def aptPackageSearch(update: Update, context):
    user_input = update.message.text
    if user_input == '/cancel':
        update.message.reply_text('Отмена действия')
        return ConversationHandler.END
    if not re.match("^[a-zA-Z]+$", user_input):
        update.message.reply_text(
            'Название пакета должно содержать только буквы. Попробуйте снова.'
        )
        return
    linCommand = f'dpkg -l | grep {user_input}'
    return hostCheck(update, context, linCommand)


def hostCheckCommand(update: Update, context, typeCommand):
    linCommand = switch_command(typeCommand)
    return hostCheck(update, context, linCommand)

def hostCheck(update: Update, context, linCommand):
    host = os.getenv('RM_HOST')
    port = os.getenv('RM_PORT')
    username = os.getenv('RM_USER')
    password = os.getenv('RM_PASSWORD')
    image = os.getenv('DB_HOST')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)


    stdin, stdout, stderr = client.exec_command(linCommand)
    data = ''.join(stdout.readlines()[:10])
    data = data.replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    update.message.reply_text('Команда окончена')

    client.close()
    return ConversationHandler.END


def record_exists(table_name: str, column_name: str, value: str) -> bool:
    connection = None
    exists = False
    try:
        connection = psycopg2.connect(
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            database=os.getenv('DB_DATABASE')
        )
        cursor = connection.cursor()
        query = f"SELECT 1 FROM {table_name} WHERE {column_name} = %s"
        cursor.execute(query, (value,))
        exists = cursor.fetchone() is not None
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
            logging.info("Соединение с PostgreSQL закрыто")
    return exists

def dbSelect(update: Update, context, dbCommand):
    dbCommand = switch_command(dbCommand)
    connection = None
    try:
        connection = psycopg2.connect(user=os.getenv('DB_USER'),
                                      password=os.getenv('DB_PASSWORD'),
                                      host=os.getenv('DB_HOST'),
                                      port=os.getenv('DB_PORT'),
                                      database=os.getenv('DB_DATABASE'))
        cursor = connection.cursor()
        cursor.execute(f"{dbCommand}")
        data = cursor.fetchall()

        output = ""
        for row in data:
            output += str(row) + "\n"

        update.message.reply_text(output)
        logging.info("Команда успешно выполнена")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()

def dbInsert(update: Update, context, dbCommand: str):
    connection = None
    try:
        connection = psycopg2.connect(
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            database=os.getenv('DB_DATABASE')
        )
        cursor = connection.cursor()
        cursor.execute(dbCommand)
        connection.commit()
        logging.info("Команда успешно выполнена")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
            logging.info("Соединение с PostgreSQL закрыто")

def annoyingPerson(update: Update, context):
    update.message.reply_text('Я не понимать человеко-слова, понимать команда-список: /help')

def fallback_message(update: Update, context):
    update.message.reply_text('Текущая команда отменена, введите новую команду')
    return ConversationHandler.END

def main():
    load_dotenv()
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    conv_handler_find_emails = ConversationHandler(
        entry_points=[CommandHandler('find_email', findEmailsCommand)],
        states={
            'findEmails': [
                MessageHandler(
                    Filters.regex(r'^/cancel$') |
                    (Filters.text & ~Filters.command),
                    findEmails
                )
            ],
            'emailInsert': [
                MessageHandler(
                    Filters.regex(r'^/cancel$') |
                    (Filters.text & ~Filters.command),
                    emailInsert
                )
            ]
        },
        fallbacks=[MessageHandler(Filters.command, fallback_message)],
        allow_reentry=True
    )
    conv_handler_find_phone_numbers = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', findPhoneNumbersCommand)],
        states={
            'findPhoneNumbers': [
                MessageHandler(
                    Filters.regex(r'^/cancel$') |
                    (Filters.text & ~Filters.command),
                    findPhoneNumbers
                )
            ],
            'phoneInsert': [
                MessageHandler(
                    Filters.regex(r'^/cancel$') |
                    (Filters.text & ~Filters.command),
                    phoneInsert
                )
            ]
        },
        fallbacks=[MessageHandler(Filters.command, fallback_message)],
        allow_reentry=True
    )
    conv_handler_verify_password = ConversationHandler(
        entry_points=[CommandHandler('verify_password', verifyPasswordCommand)],
        states={
            'verifyPassword': [
                MessageHandler(
                    Filters.regex(r'^/cancel$') |
                    (Filters.text & ~Filters.command),
                    verifyPassword
                )
            ]
        },
        fallbacks=[MessageHandler(Filters.command, fallback_message)],
        allow_reentry=True
    )
    conv_handler_aptList = ConversationHandler(
        entry_points=[CommandHandler('get_apt_list', aptListCommand)],
        states={
            'aptListChoice': [
                MessageHandler(
                    Filters.regex(r'^/cancel$') |
                    (Filters.text & ~Filters.command),
                    aptListChoice
                )
            ],
            'aptPackageSearch': [
                MessageHandler(
                    Filters.regex(r'^/cancel$') |
                    (Filters.text & ~Filters.command),
                    aptPackageSearch
                )
            ]
        },
        fallbacks=[MessageHandler(Filters.command, fallback_message)],
        allow_reentry=True
    )
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(conv_handler_find_emails)
    dp.add_handler(conv_handler_find_phone_numbers)
    dp.add_handler(conv_handler_verify_password)
    dp.add_handler(conv_handler_aptList)
    dp.add_handler(
        CommandHandler(
            'get_release',
            partial(hostCheckCommand, typeCommand="release")
        )
    )
    dp.add_handler(
        CommandHandler('get_uname', partial(hostCheckCommand, typeCommand="uname"))
    )
    dp.add_handler(
        CommandHandler(
            'get_uptime',
            partial(hostCheckCommand, typeCommand="uptime")
        )
    )
    dp.add_handler(
        CommandHandler('get_df', partial(hostCheckCommand, typeCommand="df"))
    )
    dp.add_handler(
        CommandHandler('get_w', partial(hostCheckCommand, typeCommand="w"))
    )
    dp.add_handler(
        CommandHandler(
            'get_mpstat',
            partial(hostCheckCommand, typeCommand="mpstat")
        )
    )
    dp.add_handler(
        CommandHandler(
            'get_auths',
            partial(hostCheckCommand, typeCommand="auths")
        )
    )
    dp.add_handler(
        CommandHandler(
            'get_critical',
            partial(hostCheckCommand, typeCommand="critical")
        )
    )
    dp.add_handler(
        CommandHandler('get_ps', partial(hostCheckCommand, typeCommand="ps"))
    )
    dp.add_handler(
        CommandHandler('get_ss', partial(hostCheckCommand, typeCommand="ss"))
    )
    dp.add_handler(
        CommandHandler(
            'get_services',
            partial(hostCheckCommand, typeCommand="services")
        )
    )
    dp.add_handler(
        CommandHandler('get_free', partial(hostCheckCommand, typeCommand="free"))
    )

    dp.add_handler(
        CommandHandler('get_repl_logs', partial(hostCheckCommand, typeCommand="repl"))
    )

    dp.add_handler(
        CommandHandler(
            'get_emails',
            partial(dbSelect, dbCommand="email")
        )
    )
    dp.add_handler(
        CommandHandler(
            'get_phone_numbers',
            partial(dbSelect, dbCommand="pnone")
        )
    )

    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, annoyingPerson))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
