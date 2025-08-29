import time
import telebot
import os
import re
import json
import threading
import platform
from telebot import types
from threading import Lock
from config_parser import ConfigParser
from frontend import Bot_inline_btns
from backend import DbAct
from db import DB

config_name = 'secrets.json'
group_id = -1002969726752

last_bot_messages = {}
user_command_messages = {}

def delete_previous_bot_message(chat_id):
    if chat_id in last_bot_messages:
        try:
            bot.delete_message(chat_id, last_bot_messages[chat_id])
        except Exception as e:
            print(f"Не удалось удалить сообщение бота: {e}")
        finally:
            del last_bot_messages[chat_id]

def delete_user_command_message(chat_id):
    """Удаляет команду пользователя"""
    if chat_id in user_command_messages:
        try:
            bot.delete_message(chat_id, user_command_messages[chat_id])
        except Exception as e:
            print(f"Не удалось удалить команду пользователя: {e}")
        finally:
            del user_command_messages[chat_id]

def send_message_with_deletion(chat_id, text, reply_markup=None):
    delete_previous_bot_message(chat_id)
    delete_user_command_message(chat_id)
    sent_message = bot.send_message(chat_id, text, reply_markup=reply_markup)
    last_bot_messages[chat_id] = sent_message.message_id
    return sent_message

def main():
    @bot.message_handler(commands=['start', 'admin'])
    def start(message):
        user_command_messages[message.chat.id] = message.message_id
        
        command = message.text.replace('/', '')
        user_id = message.from_user.id
        buttons = Bot_inline_btns()
        
        if db_actions.user_is_admin(user_id):
            if command == "admin":
                send_message_with_deletion(user_id, "Добро пожаловать в админ-панель ✅\n\n"
                "Выберите пункт", reply_markup=buttons.admin_buttons())
        
        if command == "start":
            db_actions.add_user(user_id, message.from_user.first_name, message.from_user.last_name,
                    f'@{message.from_user.username}')
            send_message_with_deletion(user_id, "👋 Добро пожаловать!\n\n"
            "Это бот для сотрудничества с PulseNews. Здесь вы можете предложить интересный контент для публикации или обсудить условия размещения рекламы.\n\n"
            "Выберите, пожалуйста, подходящую опцию ниже:\n"
            "✨ Заказать рекламу — узнать актуальные цены и условия размещения рекламных материалов.\n"
            "✨ Предложить публикацию — прислать новость, статью или пост для нашего канала.\n"
            "✨ Предложить рекламу — отправить ваше коммерческое предложение на рассмотрение.\n\n"
            "Мы рады продуктивному сотрудничеству!", reply_markup=buttons.start_buttons())

    @bot.message_handler(content_types=['text', 'photo'])
    def text_message(message):
        user_id = message.chat.id
        user_input = message.text
        buttons = Bot_inline_btns()
        code = db_actions.get_user_system_key(user_id, "index")
        if message.text and not message.text.startswith('/'):
            delete_user_command_message(user_id)
        
        if db_actions.user_is_existed(user_id):
            if code == 1:
                try:
                    topic_id = telebot.TeleBot.create_forum_topic(bot, chat_id=group_id,
                                                                name=f'{message.from_user.first_name} '
                                                                    f'{message.from_user.last_name} РЕКЛАМА',
                                                                icon_color=0x6FB9F0).message_thread_id
                    
                    if message.photo:
                        photo_id = message.photo[-1].file_id
                        caption = message.caption if message.caption else ''
                        bot.send_photo(chat_id=group_id, photo=photo_id, caption=caption,
                                     message_thread_id=topic_id)
                    else:
                        bot.send_message(chat_id=group_id, text=user_input,
                                       message_thread_id=topic_id)
                    
                    db_actions.update_topic_id(user_id, topic_id)
                    bot.send_message(chat_id=group_id, message_thread_id=topic_id, 
                                   text=f'Получена заявка "Предложение рекламы", от пользователя: @{message.from_user.username}')
                    
                    send_message_with_deletion(user_id, 'Спасибо! Ваше предложение получено, ожидайте! ⌛\n' \
                    'Обратная связь будет предоставлена в кратчайшие сроки.👋')
                    db_actions.set_user_system_key(user_id, "index", None)
                    
                except Exception as e:
                    print(f"Ошибка при создании темы: {e}")
                    send_message_with_deletion(user_id, "Произошла ошибка. Попробуйте позже.")
            
            elif code == 2:
                try:
                    topic_id = telebot.TeleBot.create_forum_topic(bot, chat_id=group_id,
                                                name=f'{message.from_user.first_name} '
                                                    f'{message.from_user.last_name} ПОСТ',
                                                icon_color=0x6FB9F0).message_thread_id
                    
                    if message.photo:
                        bot.forward_message(chat_id=group_id, from_chat_id=message.chat.id, 
                                          message_id=message.id, message_thread_id=topic_id)
                    else:
                        # Если только текст
                        bot.send_message(chat_id=group_id, text=user_input,
                                       message_thread_id=topic_id)
                    
                    db_actions.update_topic_id(user_id, topic_id)
                    bot.send_message(chat_id=group_id, message_thread_id=topic_id, 
                                   text=f'Получена заявка "Предложение публикации", от пользователя: @{message.from_user.username}')
                    
                    send_message_with_deletion(user_id, 'Спасибо! Ваше предложение получено, ожидайте! ⌛\n' \
                    'Обратная связь будет предоставлена в кратчайшие сроки.👋')
                    db_actions.set_user_system_key(user_id, "index", None)
                    
                except Exception as e:
                    print(f"Ошибка при создании темы: {e}")
                    send_message_with_deletion(user_id, "Произошла ошибка. Попробуйте позже.")
            
            elif code == 3:
                if message.photo:
                    photo_id = message.photo[-1].file_id
                    caption = message.caption if message.caption else ''
                    
                    if db_actions.get_order_message():
                        db_actions.update_order_message(f"PHOTO:{photo_id}:{caption}")
                    else:
                        db_actions.set_order_message(f"PHOTO:{photo_id}:{caption}")
                    
                    send_message_with_deletion(user_id, "Сообщение с фото установлено ✅")
                else:
                    if db_actions.get_order_message():
                        db_actions.update_order_message(user_input)
                        send_message_with_deletion(user_id, "Сообщение установлено ✅")
                    else:
                        db_actions.set_order_message(user_input)
                        send_message_with_deletion(user_id, "Сообщение обновлено ✅")

    @bot.callback_query_handler(func=lambda call: True)
    def callback(call):
        user_id = call.message.chat.id
        buttons = Bot_inline_btns()
        try:
            bot.delete_message(user_id, call.message.message_id)
        except Exception as e:
            print(f"Не удалось удалить callback сообщение: {e}")
        
        if db_actions.user_is_existed(user_id):
            if call.data == "order_ad":
                order_message = db_actions.get_order_message()
                if order_message:
                    message_content = order_message[0][0]
                    if message_content.startswith("PHOTO:"):
                        parts = message_content.split(":", 2)
                        if len(parts) >= 3:
                            photo_id = parts[1]
                            caption = parts[2]
                            bot.send_photo(user_id, photo_id, caption=caption)
                        else:
                            send_message_with_deletion(user_id, "Ошибка формата сообщения")
                    else:
                        send_message_with_deletion(user_id, f"{message_content}")
                else:
                    send_message_with_deletion(user_id, "Сообщение не найдено")
            
            elif call.data == "offer_ad":
                send_message_with_deletion(user_id, "🤝 Предложить рекламу\n\n" \
                "Спасибо за интерес к сотрудничеству! Для рассмотрения вашего коммерческого предложения нам потребуется следующая информация:\n" \
                "Пожалуйста, заполните по пунктам и отправьте одним сообщением:\n" \
                "• Название компании/проекта\n" \
                "• Ссылка на сайт/соцсети\n" \
                "• Какой среднесуточный охват аудитории?\n" \
                "• Контактные данные для дальнейшей связи\n\n" \
                "Вы можете отправить текст или текст с одной фотографией.\n\n" \
                "Это ускорит обработку вашей заявки. Мы свяжемся с вами для обсуждения деталей.\n\n")
                db_actions.set_user_system_key(user_id, "index", 1)
            
            elif call.data == "offer_post":
                send_message_with_deletion(user_id, "📝 Предложить публикацию\n\n" \
                "Отлично! Мы всегда рамы интересным новостям и авторским материалам.\n" \
                "Чтобы рассмотреть вашу заявку быстрее, прикрепите текст и/или фото в сообщении.\n" \
                "Мы рассмотрим ваше предложение в ближайшее время.\n\n" \
                "Спасибо за ваше предложение! ✨")
                db_actions.set_user_system_key(user_id, "index", 2)
            
            if db_actions.user_is_admin(user_id):
                if call.data == "update_message":
                    send_message_with_deletion(user_id, "Отправьте текст сообщения или текст с одной фотографией для пункта 'Заказать рекламу'")
                    db_actions.set_user_system_key(user_id, "index", 3)

    bot.polling(none_stop=True)

if '__main__' == __name__:
    os_type = platform.system()
    work_dir = os.path.dirname(os.path.realpath(__file__))
    config = ConfigParser(f'{work_dir}/{config_name}', os_type)
    db = DB(config.get_config()['db_file_name'], Lock())
    db_actions = DbAct(db, config)
    bot = telebot.TeleBot(config.get_config()['tg_api'])
    main()