TOKEN = ""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

ADMINS = [869488169]

class UserOrder:
    def __init__(self):
        self.state = {}
        self.data = {}

    def start_order(self, user_id):
        self.state[user_id] = 'waiting_for_format'
        self.data[user_id] = {}

    def set_state(self, user_id, state):
        self.state[user_id] = state

    def get_state(self, user_id):
        return self.state.get(user_id)

    def set_data(self, user_id, key, value):
        if user_id not in self.data:
            self.data[user_id] = {}
        self.data[user_id][key] = value

    def get_data(self, user_id):
        return self.data.get(user_id)

    def clear_user_data(self, user_id):
        if user_id in self.state:
            del self.state[user_id]
        if user_id in self.data:
            del self.data[user_id]


class Admin:
    @staticmethod
    def is_admin(user_id):
        return user_id in ADMINS

    @staticmethod
    async def send_message_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not Admin.is_admin(update.message.from_user.id):
            await update.message.reply_text('У вас нет доступа к этой команде.')
            return

        if len(context.args) < 2:
            await update.message.reply_text('Использование: /send_message_to_user <user_id> <message>')
            return

        user_id = int(context.args[0])
        message = ' '.join(context.args[1:])

        try:
            await context.bot.send_message(chat_id=user_id, text=message)
            await update.message.reply_text(f'Сообщение отправлено пользователю {user_id}.')
        except Exception as e:
            await update.message.reply_text(f'Ошибка при отправке сообщения: {e}')


class Menu:
    @staticmethod
    def get_main_menu():
        keyboard = [
            [InlineKeyboardButton("Просмотреть портфолио", callback_data='view_portfolio')],
            [InlineKeyboardButton("Оставить заказ", callback_data='leave_order')],
            [InlineKeyboardButton("Написать отзыв", callback_data='write_review')],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_portfolio_menu():
        portfolio_link = "https://t.me/+UBBDbCnxFzQyMjM6"
        keyboard = [
            [InlineKeyboardButton("Перейти к портфолио", url=portfolio_link)],
            [InlineKeyboardButton("Назад", callback_data='back_to_menu')]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_order_format_menu():
        keyboard = [
            [InlineKeyboardButton("Горизонтальный", callback_data='format_horizontal'),
             InlineKeyboardButton("Вертикальный", callback_data='format_vertical')]
        ]
        return InlineKeyboardMarkup(keyboard)


class Handler:
    def __init__(self, user_order: UserOrder):
        self.user_order = user_order

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        gif_path = "D:/#НаПроект/Музыка/logo_tg_33 (1).gif"
        with open(gif_path, 'rb') as gif:
            await update.message.reply_animation(animation=gif, caption="Добро пожаловать! Ознакомьтесь с меню.")
        reply_markup = Menu.get_main_menu()
        await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)

    async def portfolio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        reply_markup = Menu.get_portfolio_menu()
        await update.message.reply_text("Просмотр портфолио:", reply_markup=reply_markup)



    async def write_review(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.user_order.set_state(update.message.from_user.id, 'review')
        await update.message.reply_text("Мы будем предельно благодарны, если Вы оставите свой отзыв!\nТак мы сможем улучшить свою работу <3")

    async def leave_order(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.message.from_user.id
        self.user_order.start_order(user_id)
        reply_markup = Menu.get_order_format_menu()
        await update.message.reply_text("Выберите формат видео:", reply_markup=reply_markup)

    async def button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id

        if query.data == 'view_portfolio':
            reply_markup = Menu.get_portfolio_menu()
            await query.edit_message_text(text="Просмотр портфолио:", reply_markup=reply_markup)

        elif query.data == 'write_review':
            self.user_order.set_state(user_id, 'review')
            await query.edit_message_text("Мы будем предельно благодарны, если Вы оставите свой отзыв!\nТак мы сможем улучшить свою работу <3")

        elif query.data == 'leave_order':
            self.user_order.start_order(user_id)
            reply_markup = Menu.get_order_format_menu()
            await query.edit_message_text("Выберите формат видео:", reply_markup=reply_markup)

        elif query.data == 'format_horizontal':
            self.user_order.set_data(user_id, 'format', "Горизонтальный")
            self.user_order.set_state(user_id, 'waiting_for_duration')
            await query.edit_message_text("Формат записан: Горизонтальный.\nТеперь напишите, какой должна быть продолжительность видео?")

        elif query.data == 'format_vertical':
            self.user_order.set_data(user_id, 'format', "Вертикальный")
            self.user_order.set_state(user_id, 'waiting_for_duration')
            await query.edit_message_text("Формат записан: Вертикальный.\nТеперь напишите, какой должна быть продолжительность видео?")

        elif query.data == 'back_to_menu':
            reply_markup = Menu.get_main_menu()
            await query.edit_message_text("Выберите действие:", reply_markup=reply_markup)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.message.from_user
        text = update.message.text
        user_id = user.id

        if user_id not in self.user_order.state:
            await update.message.reply_text("Пожалуйста, начните с команды /start.")
            return

        state = self.user_order.get_state(user_id)

        if state == 'waiting_for_duration':
            self.user_order.set_data(user_id, 'duration', text)
            self.user_order.set_state(user_id, 'waiting_for_concept')
            await update.message.reply_text("Продолжительность ролика записана.\nНемного расскажите о видео: что нужно сделать в ролике и как вы его видите?")

        elif state == 'waiting_for_concept':
            self.user_order.set_data(user_id, 'concept', text)
            self.user_order.set_state(user_id, 'waiting_for_price')
            await update.message.reply_text("Отлично! Какой у Вас бюджет на монтаж? Введите сумму.")

        elif state == 'waiting_for_price':
            self.user_order.set_data(user_id, 'price', text)
            self.user_order.set_state(user_id, None)
            await update.message.reply_text("Спасибо, что обратились ко мне! Я свяжусь с Вами как можно скорее!")



            order_details = self.user_order.get_data(user_id)
            order_summary = (
                f"Заявка от пользователя @{user.username if user.username else 'Без username'} (ID: {user_id}):\n"
                f"Формат видео: {order_details.get('format')}\n"
                f"Продолжительность: {order_details.get('duration')}\n"
                f"Концепция: {order_details.get('concept')}\n"
                f"Оценка: {order_details.get('price')}\n"
            )
            await context.bot.send_message(chat_id=ADMINS[0], text=order_summary)

            self.user_order.clear_user_data(user_id)

        elif state == 'review':
            username = user.username if user.username else "Без username"
            await context.bot.send_message(
                chat_id=ADMINS[0],
                text=f"Получен отзыв от @{username} (ID: {user.id}):\n{text}"
            )
            self.user_order.set_state(user_id, None)


class Bot:
    def __init__(self, token: str):
        self.application = ApplicationBuilder().token(token).build()
        self.user_order = UserOrder()
        self.handler = Handler(self.user_order)

    def run(self):
        self.application.add_handler(CommandHandler("start", self.handler.start))
        self.application.add_handler(CommandHandler("help", self.handler.start))
        self.application.add_handler(CommandHandler("portfolio", self.handler.portfolio))
        self.application.add_handler(CommandHandler("leave_order", self.handler.leave_order))
        self.application.add_handler(CommandHandler("write_review", self.handler.write_review))
        self.application.add_handler(CallbackQueryHandler(self.handler.button))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handler.handle_message))
        self.application.add_handler(CommandHandler("send_message_to_user", Admin.send_message_to_user))
        self.application.run_polling()


if __name__ == '__main__':
    bot = Bot(TOKEN)
    bot.run()
