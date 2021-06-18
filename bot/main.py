# -*- coding: utf8 -*-
import sqlite3
import os
#
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, Message, ReplyKeyboardMarkup, KeyboardButton
#
import config.config as config
from db_requests import requestDB
from check_input_data import *
#
bot = telebot.TeleBot(config.BOT_TOKEN)
#


def createBD_FromDump(path_db, path_dump):
    cur = sqlite3.connect(path_db)
    f = open(path_dump, 'r', encoding='utf-8')
    dump = f.read()
    cur.executescript(dump)


@bot.message_handler(commands=['start'])
def start_handler(message):
    user_processing(message.from_user.id)
    main_menu(message.from_user.id)


@bot.message_handler(content_types=['text'])
def change_amount(message):
    check_command(message)


def send_message_to_admins_chat(text):
    'Отправка сообщения в чат администраторов.'
    bot.send_message(chat_id=config.ADMINS_GROUP_ID,
                     text=text
                     )


def send_message_to_admins_product_chat(text):
    'Отправка сообщения в чат для товара.'
    bot.send_message(chat_id=config.PRODUCTS_GROUP_ID,
                     text=text
                     )


def get_main_menu_keyboard(user_id):
    'Возвращает клавиатуру для главного меню.'
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    item1 = KeyboardButton('Сделать заказ')
    item2 = KeyboardButton('Корзина')
    markup.add(item1, item2)
    if check_user_is_admin(user_id) == True:
        item3 = KeyboardButton('Редактирование')
        markup.add(item3)
    return markup


def main_menu(user_id):
    'Главное меню'
    bot.send_message(chat_id=user_id,
                     text='Выберите...',
                     reply_markup=get_main_menu_keyboard(user_id)
                     )


def get_cancel_keyboard():
    'Возвращает клавиатуру с кнопкой "Отмена".'
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    item = KeyboardButton('Отмена')
    markup.add(item)
    return markup


def check_command(message):
    "Функция проверки комманд из главного меню."
    text = message.text
    if text == 'Сделать заказ':
        make_an_order(message)
    elif text == 'Корзина':
        shopping_cart(message)
    elif text == 'Редактирование':
        editing(message)
    elif 'админ' in text:
        add_admin(message)


def add_admin(message):
    msg = message.text.lower()
    msg = msg.replace(' ', '')
    user_id = message.from_user.id
    new_admin_id = msg.replace('админ', '')
    #
    if check_user_is_admin(user_id) and 'админ' in msg and new_admin_id != '' and new_admin_id.isdigit():
        db = requestDB(config.DB_PATH)
        if not check_user_is_admin(int(new_admin_id)):
            db.add_admin(int(new_admin_id))
            bot.send_message(chat_id=user_id,
                             text=f'Успешно! Новый администратор добавлен.'
                             )
        else:
            bot.send_message(chat_id=user_id,
                             text=f'Данный ID уже администратор.'
                             )
        db.close()
    elif check_user_is_admin(user_id) and 'админ' in msg and (new_admin_id == '' or not new_admin_id.isdigit()):
        bot.send_message(chat_id=user_id,
                         text=f'Ошибка формата команды.'
                         )


def make_an_order(message):
    'Начало сценария совершения заказа'
    user_id = message.from_user.id
    msg = 'Выберите производителя...'
    #
    manufacturers = get_manufacturers()
    if len(manufacturers) != 0:
        stack_for_uniqueness = []
        #
        inline_markup = InlineKeyboardMarkup()
        for manufacturer in manufacturers:
            # Чтобы не было inline кнопок с одинаковым текстом
            if manufacturer[0] in stack_for_uniqueness:
                continue
            else:
                stack_for_uniqueness.append(manufacturer[0])
            manufacturer_btn = InlineKeyboardButton(text=manufacturer[0],
                                                    callback_data='mnf_' +
                                                    manufacturer[0]
                                                    )
            inline_markup = inline_markup.add(manufacturer_btn)
        #
        cancel_btn = InlineKeyboardButton(text='Отмена',
                                          callback_data='cancel'
                                          )
        inline_markup.add(cancel_btn)
        #
        bot.send_message(chat_id=user_id,
                         text=msg,
                         reply_markup=inline_markup
                         )
    else:
        text = 'В продаже нет товаров.'
        bot.send_message(chat_id=user_id,
                         text=text,
                         reply_markup=get_main_menu_keyboard(user_id)
                         )


@bot.callback_query_handler(func=lambda call: 'mnf_' in call.data)
def process_manufacturer(call):
    'Срабатывает после выбора производителя.'
    user_id = call.message.chat.id
    msg_id = call.message.message_id
    #
    manufacturer = call.data.replace('mnf_', '', 1)
    db = requestDB(config.DB_PATH)
    db.add_manufacturer_to_products_stack(user_id, manufacturer)
    db.close()
    #
    tastes = get_tastes(manufacturer)
    stack_for_uniqueness = []
    #
    inline_markup = InlineKeyboardMarkup()
    for taste in tastes:
        # Чтобы не было inline кнопок с одинаковым текстом
        if taste[0] in stack_for_uniqueness:
            continue
        else:
            stack_for_uniqueness.append(taste[0])
        manufacturer_btn = InlineKeyboardButton(text=taste[0],
                                                callback_data='tas_' + taste[0]
                                                )
        inline_markup = inline_markup.add(manufacturer_btn)
    #
    cancel_btn = InlineKeyboardButton(text='Отмена',
                                      callback_data='cancel'
                                      )
    inline_markup.add(cancel_btn)
    #
    bot.edit_message_text(text='Выберите вкус...',
                          chat_id=user_id,
                          message_id=msg_id
                          )
    bot.edit_message_reply_markup(chat_id=user_id,
                                  message_id=msg_id,
                                  reply_markup=inline_markup
                                  )


@bot.callback_query_handler(func=lambda call: 'tas_' in call.data)
def process_manufacturer(call):
    'Срабатывает после выбора вкуса.'
    user_id = call.message.chat.id
    msg_id = call.message.message_id
    #
    taste = call.data.replace('tas_', '', 1)
    db = requestDB(config.DB_PATH)
    manufacturer = (db.get_manufacturer_from_products_stack(user_id))[0]
    db.add_taste_to_products_stack(user_id, taste)
    db.close()
    #
    puffs_and_amounts = get_puffs_and_amount(manufacturer, taste)
    stack_for_uniqueness = []
    #
    inline_markup = InlineKeyboardMarkup()
    for puff_and_amount in puffs_and_amounts:
        # Чтобы не было inline кнопок с одинаковым текстом
        if puff_and_amount[0] in stack_for_uniqueness:
            continue
        else:
            stack_for_uniqueness.append(puff_and_amount[0])
        manufacturer_btn = InlineKeyboardButton(text=f'{puff_and_amount[0]} шт. - {puff_and_amount[1]} руб.',
                                                callback_data=f'paa_{puff_and_amount[0]}'
                                                )
        inline_markup = inline_markup.add(manufacturer_btn)
    #
    cancel_btn = InlineKeyboardButton(text='Отмена',
                                      callback_data='cancel'
                                      )
    inline_markup.add(cancel_btn)
    #
    bot.edit_message_text(text='Выберите количество тяг и цену...',
                          chat_id=user_id,
                          message_id=msg_id
                          )
    bot.edit_message_reply_markup(chat_id=user_id,
                                  message_id=msg_id,
                                  reply_markup=inline_markup
                                  )


@bot.callback_query_handler(func=lambda call: 'paa_' in call.data)
def process_manufacturer(call):
    'Срабатывает после выбора кол-во тяг и цены.'
    user_id = call.message.chat.id
    msg_id = call.message.message_id
    #
    puffs = call.data.replace('paa_', '', 1)
    #
    db = requestDB(config.DB_PATH)
    db.add_puffs_to_products_stack(user_id, puffs)
    db.close()
    #
    bot.delete_message(chat_id=user_id,
                       message_id=msg_id
                       )
    #
    msg = 'Введите количество...'
    msg = bot.send_message(chat_id=user_id,
                           text=msg,
                           reply_markup=get_cancel_keyboard()
                           )
    bot.register_next_step_handler(msg, process_count_step)


def process_count_step(message):
    'Срабатывает после указания количества.'
    if message.text == 'Отмена':
        db = requestDB(config.DB_PATH)
        db.delete_product_object_from_stack(message.from_user.id)
        db.close()
        main_menu(message.from_user.id)
        return
    user_id = message.from_user.id
    #
    if not message.text.isdigit():
        text = 'Напишите число!'
        msg = bot.send_message(chat_id=user_id,
                               text=text
                               )
        bot.register_next_step_handler(msg, process_count_step)
        return
    elif int(message.text) > 999999:
        text = 'Слишком большое количество.'
        msg = bot.send_message(chat_id=user_id,
                               text=text
                               )
        bot.register_next_step_handler(msg, process_count_step)
        return
    #
    count = int(message.text)
    #
    db = requestDB(config.DB_PATH)
    manufacturer = (db.get_manufacturer_from_products_stack(user_id))[0]
    taste = (db.get_taste_from_products_stack(user_id))[0]
    puffs = (db.get_puffs_from_products_stack(user_id))[0]
    product_id = int((db.get_product_id(manufacturer, taste, puffs))[0])
    db.delete_product_object_from_stack(user_id)  # удаление из стака
    db.add_product_to_shopping_cart(
        user_id, product_id, count)  # добавление в корзину
    db.close()
    #
    msg = 'Товар добавлен в корзину!'
    bot.send_message(chat_id=user_id,
                     text=msg,
                     reply_markup=get_main_menu_keyboard(user_id)
                     )


@bot.callback_query_handler(func=lambda call: call.data == 'cancel')
def cancel_make_an_order(call):
    'Срабатывает при нажатии на inline кнопку "Отмена".'
    msg_id = call.message.message_id
    user_id = call.message.chat.id
    bot.delete_message(chat_id=user_id,
                       message_id=msg_id
                       )
    db = requestDB(config.DB_PATH)
    db.delete_product_object_from_stack(user_id)
    db.close()
    main_menu(user_id)


def editing(message):
    'Начало сценария редактирования.'
    user_id = message.from_user.id
    msg = 'Выберите...'
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = KeyboardButton('Добавить товар')
    item2 = KeyboardButton('Удалить товар')
    item3 = KeyboardButton('Отмена')
    markup.add(item1)
    markup.add(item2)
    markup.add(item3)
    msg = bot.send_message(chat_id=user_id,
                           text=msg,
                           reply_markup=markup
                           )
    bot.register_next_step_handler(msg, check_editing_command)


def check_editing_command(message):
    'Срабатывает после выбора действия.'
    command = message.text
    user_id = message.from_user.id
    if command == 'Добавить товар':
        add_product(message)
    elif command == 'Удалить товар':
        delete_product_step(message)
    elif command == 'Отмена':
        main_menu(user_id)
    else:
        msg = 'Выберите...'
        msg = bot.send_message(chat_id=user_id,
                               text=msg
                               )
        bot.register_next_step_handler(msg, check_editing_command)


def add_product(message):
    'Начало сценария добавления товара.'
    user_id = message.from_user.id
    text = 'Введите название производителя...'
    #
    msg = bot.send_message(chat_id=user_id,
                           text=text,
                           reply_markup=get_cancel_keyboard()
                           )
    bot.register_next_step_handler(msg, process_manufacturer_step)


def process_manufacturer_step(message):
    'Срабатывает после указания имени производителя.'
    if message.text == 'Отмена':
        cancel_add_product(message.from_user.id)
        return
    user_id = message.from_user.id
    #
    if check_manufacturer_text(message.text) == False:
        text = 'Слишком большое название производителя!'
        msg = bot.send_message(chat_id=user_id,
                               text=text
                               )
        bot.register_next_step_handler(msg, process_manufacturer_step)
        return
    #
    manufacturer = message.text
    db = requestDB(config.DB_PATH)
    db.add_manufacturer_to_products_stack(user_id, manufacturer)
    db.close()
    #
    text = 'Введите вкус...'
    msg = bot.send_message(chat_id=user_id,
                           text=text,
                           reply_markup=get_cancel_keyboard()
                           )
    bot.register_next_step_handler(msg, process_taste_step)


def process_taste_step(message):
    'Срабатывает после указания вкуса.'
    if message.text == 'Отмена':
        cancel_add_product(message.from_user.id)
        return
    user_id = message.from_user.id
    #
    if check_taste_text(message.text) == False:
        text = 'Слишком большое название вкуса!'
        msg = bot.send_message(chat_id=user_id,
                               text=text
                               )
        bot.register_next_step_handler(msg, process_taste_step)
        return
    #
    taste = message.text
    db = requestDB(config.DB_PATH)
    db.add_taste_to_products_stack(user_id, taste)
    db.close()
    #
    text = 'Введите количество затяжек...'
    msg = bot.send_message(chat_id=user_id,
                           text=text,
                           reply_markup=get_cancel_keyboard()
                           )
    bot.register_next_step_handler(msg, process_puffs_step)


def process_puffs_step(message):
    'Срабатывает после указания кол-ва затяжек.'
    if message.text == 'Отмена':
        cancel_add_product(message.from_user.id)
        return
    user_id = message.from_user.id
    #
    if not message.text.isdigit():
        text = 'Введите число!'
        msg = bot.send_message(chat_id=user_id,
                               text=text
                               )
        bot.register_next_step_handler(msg, process_puffs_step)
        return
    elif int(message.text) > 999999:
        text = 'Слишком большое число.'
        msg = bot.send_message(chat_id=user_id,
                               text=text
                               )
        bot.register_next_step_handler(msg, process_puffs_step)
        return
    #
    number_of_puffs = int(message.text)
    db = requestDB(config.DB_PATH)
    db.add_puffs_to_products_stack(user_id, number_of_puffs)
    db.close()
    #
    text = 'Введите цену товара...'
    msg = bot.send_message(chat_id=user_id,
                           text=text,
                           reply_markup=get_cancel_keyboard()
                           )
    bot.register_next_step_handler(msg, process_amount_step)


def process_amount_step(message):
    'Срабатывает после указания цены товара.'
    if message.text == 'Отмена':
        cancel_add_product(message.from_user.id)
        return
    user_id = message.from_user.id
    #
    if not message.text.isdigit():
        text = 'Введите число!'
        msg = bot.send_message(chat_id=user_id,
                               text=text
                               )
        bot.register_next_step_handler(msg, process_amount_step)
        return
    elif int(message.text) > 999999:
        text = 'Слишком большое число.'
        msg = bot.send_message(chat_id=user_id,
                               text=text
                               )
        bot.register_next_step_handler(msg, process_amount_step)
        return
    #
    amount = int(message.text)
    db = requestDB(config.DB_PATH)
    db.add_amount_to_products_stack(user_id, amount)
    db.close()
    #
    add_product_to_db(message)


def add_product_to_db(message):
    'Добавление товара в БД.'
    user_id = message.from_user.id
    #
    db = requestDB(config.DB_PATH)
    manufacturer = (db.get_manufacturer_from_products_stack(user_id))[0]
    taste = (db.get_taste_from_products_stack(user_id))[0]
    number_of_puffs = (db.get_puffs_from_products_stack(user_id))[0]
    amount = (db.get_amount_from_products_stack(user_id))[0]
    res = db.add_product(manufacturer, taste, number_of_puffs, amount)
    db.delete_product_object_from_stack(user_id)
    product_id = (db.get_product_id(manufacturer, taste, number_of_puffs))[0]
    db.close()
    #
    if res != False:
        msg = 'Товар добавлен!'
        bot.send_message(chat_id=user_id,
                         text=msg,
                         reply_markup=get_main_menu_keyboard(user_id)
                         )
        #
        product_text = create_product_text(product_id,
                                           manufacturer,
                                           taste,
                                           number_of_puffs,
                                           amount
                                           )
        text = 'Новый товар!\n\n' + product_text
        # Отправляем оповещение о добавлении нового товара в чат с товарами
        send_message_to_admins_product_chat(text)
    else:
        msg = 'Такой товар уже есть в БД.'
        bot.send_message(chat_id=user_id,
                         text=msg,
                         reply_markup=get_main_menu_keyboard(user_id)
                         )


def cancel_add_product(user_id):
    db = requestDB(config.DB_PATH)
    db.delete_product_object_from_stack(user_id)
    db.close()
    main_menu(user_id)


def delete_product_step(message):
    'Начало сценария удаления товара.'
    user_id = message.from_user.id
    #
    text = 'Введите ID товара...'
    message = bot.send_message(chat_id=user_id,
                               text=text,
                               reply_markup=get_cancel_keyboard()
                               )
    bot.register_next_step_handler(message, delete_product)


def delete_product(message):
    'Удаление товара.'
    user_id = message.from_user.id
    #
    if not message.text.isdigit():
        text = 'Неверный формат ID.'
        bot.send_message(chat_id=user_id,
                         text=text,
                         reply_markup=get_main_menu_keyboard(user_id)
                         )
        return
    elif int(message.text) > 999999:
        text = 'Слишком большое ID.'
        bot.send_message(chat_id=user_id,
                         text=text,
                         reply_markup=get_main_menu_keyboard(user_id)
                         )
        return
    #
    product_id = int(message.text)
    #
    db = requestDB(config.DB_PATH)
    result = db.delete_product(product_id)
    if result != False:
        db.delete_product_from_shopping_cart_everyone_has(product_id)
        text = 'Товар удалён.'
        bot.send_message(chat_id=user_id,
                         text=text,
                         reply_markup=get_main_menu_keyboard(user_id)
                         )
    else:
        text = 'Товара с указанным ID не существует.'
        bot.send_message(chat_id=user_id,
                         text=text,
                         reply_markup=get_main_menu_keyboard(user_id)
                         )
    db.close()


def shopping_cart(message):
    'Высылает сообщение с товарами в корзине у пользователя.'
    user_id = message.from_user.id
    orders = get_orders(user_id)
    if len(orders) != 0:
        msg = 'Список товаров в корзине:\n\n'
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        item = KeyboardButton('Оплатить')
        item_1 = KeyboardButton('Главное меню')
        markup.add(item)
        markup.add(item_1)
        message = bot.send_message(chat_id=user_id,
                                   text=msg,
                                   reply_markup=markup
                                   )
        #
        for num, order in enumerate(orders):
            product_id = order[0]
            count = order[1]
            msg = f'Товар №{num + 1}:\n' + \
                create_product_text_by_id(product_id, count) + '\n\n'
            delete_from_shippint_cart_btn = InlineKeyboardButton(text='Убрать',
                                                                 # delete from shopping cart
                                                                 callback_data=f'del_from_sh_c_{product_id}'
                                                                 )
            inline_markup = InlineKeyboardMarkup().add(delete_from_shippint_cart_btn)
            bot.send_message(chat_id=user_id,
                             text=msg,
                             reply_markup=inline_markup
                             )
        bot.register_next_step_handler(message, process_shopping_cart)
    else:
        msg = 'Корзина пуста.'
        bot.send_message(chat_id=user_id,
                         text=msg,
                         reply_markup=get_main_menu_keyboard(user_id)
                         )


def process_shopping_cart(message):
    text = message.text
    user_id = message.from_user.id
    if text == 'Оплатить':
        start_payment(message)
    elif text == 'Главное меню':
        main_menu(message.from_user.id)
    else:
        text = 'Выберите действие...'
        msg = bot.send_message(chat_id=user_id,
                               text=text
                               )
        bot.register_next_step_handler(msg, process_shopping_cart)


def start_payment(message):
    'Начало сценария оплаты.'
    user_id = message.from_user.id
    text = 'Введите ваше имя...'
    message = bot.send_message(chat_id=user_id,
                               text=text,
                               reply_markup=get_cancel_keyboard()
                               )
    bot.register_next_step_handler(message, process_name_step)


def process_name_step(message):
    'Срабатывает после указания имени.'
    if message.text == 'Отмена':
        cancel_make_an_order(message.from_user.id)
        return
    user_id = message.from_user.id
    #
    if check_name_text(message.text) == False:
        text = 'Слишком длинное имя, введите имя короче.'
        msg = bot.send_message(chat_id=user_id,
                               text=text
                               )
        bot.register_next_step_handler(msg, process_name_step)
        return
    #
    name = message.text
    db = requestDB(config.DB_PATH)
    db.add_name_to_castomer(user_id, name)
    db.close()
    #
    text = 'Введите ваш номер телефона...'
    message = bot.send_message(chat_id=user_id,
                               text=text,
                               reply_markup=get_cancel_keyboard()
                               )
    bot.register_next_step_handler(message, process_phone_step)


def process_phone_step(message):
    'Срабатывает после номера телефона.'
    if message.text == 'Отмена':
        cancel_make_an_order(message.from_user.id)
        return
    user_id = message.from_user.id
    #
    if not message.text.isdigit():
        text = 'Введите число!'
        msg = bot.send_message(chat_id=user_id,
                               text=text
                               )
        bot.register_next_step_handler(msg, process_phone_step)
        return
    #
    phone = message.text
    db = requestDB(config.DB_PATH)
    db.add_phone_to_castomer(user_id, phone)
    db.close()
    #
    text = 'Введите ваш адресс...'
    message = bot.send_message(chat_id=user_id,
                               text=text,
                               reply_markup=get_cancel_keyboard()
                               )
    bot.register_next_step_handler(message, process_address_step)


def process_address_step(message):
    'Срабатывает после указания адреса.'
    if message.text == 'Отмена':
        cancel_make_an_order(message.from_user.id)
        return
    user_id = message.from_user.id
    #
    if check_address_text(message.text) == False:
        text = 'Слишком длинный адресс, введите адресс короче.'
        msg = bot.send_message(chat_id=user_id,
                               text=text
                               )
        bot.register_next_step_handler(msg, process_address_step)
        return
    #
    address = message.text
    db = requestDB(config.DB_PATH)
    db.add_address_to_castomer(user_id, address)
    db.close()
    #
    text = 'Выберите время доставки...'
    #
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = KeyboardButton('Ближайшее время')
    item2 = KeyboardButton('Назначить конкретное')
    item3 = KeyboardButton('Отмена')
    markup.add(item1)
    markup.add(item2)
    markup.add(item3)
    message = bot.send_message(chat_id=user_id,
                               text=text,
                               reply_markup=markup
                               )
    bot.register_next_step_handler(message, process_delivery_step)


def process_delivery_step(message):
    'Срабатывает после указания способы доставки.'
    text = message.text
    user_id = message.from_user.id
    if text == 'Ближайшее время':
        db = requestDB(config.DB_PATH)
        db.add_delivery_time_to_castomer(user_id, 'Ближайшее время')
        db.close()
        send_payment_q(user_id)
    elif text == 'Назначить конкретное':
        text = 'Напишите желаемое время доставки...'
        message = bot.send_message(chat_id=user_id,
                                   text=text,
                                   reply_markup=get_cancel_keyboard()
                                   )
        bot.register_next_step_handler(
            message, process_specific_delivery_time_step)
    elif message.text == 'Отмена':
        cancel_make_an_order(message.from_user.id)
    else:
        text = 'Выберите время доставки...'
        message = bot.send_message(chat_id=user_id,
                                   text=text
                                   )
        bot.register_next_step_handler(message, process_delivery_step)


def process_specific_delivery_time_step(message):
    'Срабатывает после указания желаемого времени доставки.'
    if message.text == 'Отмена':
        cancel_make_an_order(message.from_user.id)
        return
    user_id = message.from_user.id
    #
    if check_some_text(message.text) == False:
        text = 'Слишком большой текст. Напишите текст короче.'
        msg = bot.send_message(chat_id=user_id,
                               text=text,
                               reply_markup=get_main_menu_keyboard(user_id)
                               )
        bot.register_next_step_handler(
            message, process_specific_delivery_time_step)
        return
    #
    specific_delivery_time = message.text
    #
    db = requestDB(config.DB_PATH)
    db.add_delivery_time_to_castomer(user_id, specific_delivery_time)
    db.close()
    #
    send_payment_q(user_id)


def send_payment_q(user_id):
    text = 'Выберите способ оплаты...'
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = KeyboardButton('Картой онлайн')
    item2 = KeyboardButton('Наличными')
    item3 = KeyboardButton('Отмена')
    markup.add(item1)
    markup.add(item2)
    markup.add(item3)
    message = bot.send_message(chat_id=user_id,
                               text=text,
                               reply_markup=markup
                               )
    bot.register_next_step_handler(message, process_payment_method_step)


def process_payment_method_step(message):
    'Срабатывает после указания способа оплаты.'
    text = message.text
    user_id = message.from_user.id
    username = message.from_user.username
    if text == 'Картой онлайн':
        db = requestDB(config.DB_PATH)
        db.add_payment_method_to_castomer(user_id, 'Картой онлайн')
        db.close()
        create_an_order(user_id, username)
    elif text == 'Наличными':
        db = requestDB(config.DB_PATH)
        db.add_payment_method_to_castomer(user_id, 'Наличными')
        db.close()
        create_an_order(user_id, username)
    elif message.text == 'Отмена':
        cancel_make_an_order(message.from_user.id)
    else:
        text = 'Выберите способ оплаты...'
        message = bot.send_message(chat_id=user_id,
                                   text=text
                                   )
        bot.register_next_step_handler(message, process_payment_method_step)


def create_an_order(user_id, username):
    'Формирование текста нового заказа и отсылка его в чат админов.'
    msg = 'Новый заказ!\n\n'
    #
    db = requestDB(config.DB_PATH)
    castomer = db.get_castomer(user_id)
    name = castomer[1]
    phone = castomer[2]
    address = castomer[3]
    delivery_time = castomer[4]
    payment_method = castomer[5]
    castomer = f'TG-username: @{username}\nИмя: {name}\nТелефон: {phone}\nАдресс: {address}\nВремя доставки: {delivery_time}\nСумма: {get_total(user_id)} руб.\nСпособ оплаты: {payment_method}\n\n'
    products = 'Заказанные товары:\n'
    text = msg + castomer + products
    send_message_to_admins_chat(text)
    #
    orders = db.get_orders(user_id)
    for num, order in enumerate(orders):
        product_id = order[0]
        count = order[1]
        product = f'Товар №{num+1}:\n' + \
            create_product_text_by_id(product_id, count) + '\n\n'
        send_message_to_admins_chat(product)
    #
    db.clear_shopping_cart_for_user(user_id)
    db.delete_castomer(user_id)
    db.close()
    #
    text_for_user = 'Ваш заказ принят. Благодарим, что выбрали наш магазин!'
    bot.send_message(chat_id=user_id,
                     text=text_for_user,
                     reply_markup=get_main_menu_keyboard(user_id)
                     )


def cancel_make_an_order(user_id):
    db = requestDB(config.DB_PATH)
    db.delete_castomer(user_id)
    db.close()
    main_menu(user_id)


@bot.callback_query_handler(func=lambda call: 'del_from_sh_c_' in call.data)
def delete_product_from_shopping_cart(call):
    msg_id = call.message.message_id
    user_id = call.message.chat.id
    bot.delete_message(chat_id=user_id,
                       message_id=msg_id
                       )
    #
    product_id = call.data.replace('del_from_sh_c_', '', 1)
    #
    db = requestDB(config.DB_PATH)
    db.delete_product_from_shopping_cart(user_id, product_id)
    orders = db.get_orders(user_id)
    db.close()
    #
    if len(orders) == 0:
        text = 'В корзине больше ничего нет.'
        message = bot.send_message(chat_id=user_id,
                                   text=text
                                   )
        main_menu(user_id)
        bot.register_next_step_handler(message, check_command)


def create_product_text(id, manufacturer, taste, number_of_puffs, amount):
    text = f'ID: {id}\nПроизводитель: {manufacturer}\nВкус: {taste}\nКоличество затяжек: {number_of_puffs}\nЦена: {amount} руб.'
    return text


def create_product_text_by_id(product_id, count):
    db = requestDB(config.DB_PATH)
    product = db.get_product_by_product_id(product_id)
    db.close()
    #
    manufacturer = product[0]
    taste = product[1]
    number_of_puffs = product[2]
    amount = product[3]
    #
    text = f'ID товара: {product_id}\nПроизводитель: {manufacturer}\nВкус: {taste}\nКоличество затяжек: {number_of_puffs}\nЦена: {amount} руб.\nКоличество: {count} шт.'
    return text


def user_processing(user_id: int):
    """Обработка пользователя, запустившего бота."""
    db = requestDB(config.DB_PATH)
    check = db.check_user(user_id)
    db.close()
    if check == False:
        db = requestDB(config.DB_PATH)
        db.add_user(user_id)
        db.close()


def get_admins() -> list:
    """Получает всех операторов бота и сохраняет их возвращает их."""
    db = requestDB(config.DB_PATH)
    admins = db.get_admins()
    db.close()
    return admins


def check_user_is_admin(user_id: int) -> bool:
    """Проверяет является ли пользователь администратором."""
    admins = get_admins()
    for admin in admins:
        if user_id in admin:
            return True
    return False


def get_manufacturers():
    'Возвращает всех производителей из БД.'
    db = requestDB(config.DB_PATH)
    mnfctrrs = db.get_manufacturers()
    db.close()
    return mnfctrrs


def get_tastes(manufacturer):
    'Возвращает все вкусы из БД.'
    db = requestDB(config.DB_PATH)
    tastes = db.get_tastes(manufacturer)
    db.close()
    return tastes


def get_puffs_and_amount(manufacturer, taste):
    'Возвращает все вариации тяг и цен из БД.'
    db = requestDB(config.DB_PATH)
    puffs_and_amount = db.get_puffs_and_amount(manufacturer, taste)
    db.close()
    return puffs_and_amount


def get_orders(user_id):
    'Возвращает все заказы пользователя из БД.'
    db = requestDB(config.DB_PATH)
    orders = db.get_orders(user_id)
    db.close()
    return orders


def get_total(user_id):
    'Возвращает итоговую цену заказов из БД.'
    db = requestDB(config.DB_PATH)
    orders = db.get_orders(user_id)
    #
    total = 0
    for order in orders:
        product_id = order[0]
        count = order[1]
        total += db.get_amount(product_id)[0] * count
    db.close()
    return total


# RUN
if __name__ == '__main__':
    # Create a Data Base from a dump file if db.db isn't exists
    if not os.path.isfile(config.DB_PATH):
        createBD_FromDump(path_db=config.DB_PATH,
                          path_dump=config.DUMP_PATH
                          )
    #
    get_users()
    #
    bot.enable_save_next_step_handlers(delay=0)
    bot.load_next_step_handlers()
    bot.polling(none_stop=True)
