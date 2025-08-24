from telebot import types


class Bot_inline_btns:
    def __init__(self):
        super(Bot_inline_btns, self).__init__()
        self.__markup = types.InlineKeyboardMarkup(row_width=1)

    def start_buttons(self):
        one = types.InlineKeyboardButton('✨ Заказать рекламу', callback_data="order_ad")
        two = types.InlineKeyboardButton('✨ Предложить публикацию', callback_data="offer_post")
        three = types.InlineKeyboardButton('✨ Предложить рекламу', callback_data="offer_ad")
        self.__markup.add(one, two, three)
        return self.__markup
    
    def admin_buttons(self):
        one = types.InlineKeyboardButton("Добавить сообщение", callback_data="update_message")
        self.__markup.add(one)
        return self.__markup