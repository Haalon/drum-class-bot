import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)

from collections import OrderedDict


class LimitedSizeDict:
    def __init__(self, max_size):
        self.max_size = max_size
        self.dict = OrderedDict()

    def __setitem__(self, key, value):
        if key in self.dict:
            self.dict[key] = value
        elif len(self.dict) >= self.max_size:
            self.dict.popitem(last=False)  # remove oldest item
            self.dict[key] = value
        else:
            self.dict[key] = value

    def __getitem__(self, key):
        return self.dict[key]

    def __delitem__(self, key):
        del self.dict[key]

    def __len__(self):
        return len(self.dict)

    def __iter__(self):
        return iter(self.dict)


RECENT_REQUESTS = LimitedSizeDict(100_000)


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)


GOAL, AGE, NAME, PHONE = range(4)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks the user about their goal."""

    reply_keyboard = [
        ["Стать увереннее", "Выплеснуть эмоции"],
        ["Обрести новое хобби для разгрузки", "Выступить на сцене"],
    ]

    await update.message.reply_text(
        "Привет. Я бот школы барабанов в Тбилиси\n" "Какую цель вы хотите достичь с помощью барабанов?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, is_persistent=True, input_field_placeholder="Цель?"
        ),
    )

    return GOAL


async def goal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the user's goal and asks for their age."""

    reply_keyboard = [
        ["18-25", "26-35"],
        ["36-45", "46+"],
    ]

    if RECENT_REQUESTS[update.message.chat_id]:
        await update.message.reply_text("Вы уже отправили заявку. Мы с вами обязательно свяжемся")
        return ConversationHandler.END

    text = update.message.text
    context.user_data["goal"] = text
    await update.message.reply_text(
        "Отлично! Теперь сколько вам лет?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, is_persistent=True, input_field_placeholder="Возраст?"
        ),
    )

    return AGE


async def age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the user's age and asks for their NAME."""

    text = update.message.text
    context.user_data["age"] = text
    await update.message.reply_text(
        "Отлично! Как вас зовут?",
        reply_markup=ReplyKeyboardRemove(),
    )

    return NAME


async def name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the user's name and asks for their phone."""

    text = update.message.text
    context.user_data["name"] = text
    await update.message.reply_text(
        "Отлично! Какой у вас номер телефона?",
        reply_markup=ReplyKeyboardRemove(),
    )

    return PHONE


async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the user's phone and saves the user's data."""

    text = update.message.text
    context.user_data["phone"] = text
    await update.message.reply_text("Спасибо!:\n\n" "Ваша заявка передана и с вами скоро свяжутся")

    await context.bot.send_message(
        -4868445940,
        f"Цель: {context.user_data['goal']}\n"
        f"Возраст: {context.user_data['age']}\n"
        f"Имя: {context.user_data['name']}\n"
        f"Телефон: {context.user_data['phone']}",
    )

    RECENT_REQUESTS[update.message.chat_id] = True

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""

    # user = update.message.from_user

    # logger.info("User %s canceled the conversation.", user.first_name)

    await update.message.reply_text("Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove())

    # context.bot.send_message(chat_id)

    return ConversationHandler.END


async def id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Returns chat id"""
    await update.message.reply_text(update.message.chat_id)


def main() -> None:
    """Run the bot."""

    # Create the Application and pass it your bot's token.

    application = Application.builder().token("8041054213:AAHSY7S6pB-Q-TZqzcb6JLPHSXOOyrEFuwY").build()

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start, filters=filters.ChatType.PRIVATE)],
        states={
            GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, goal)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, age)],
            NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, name),
                # CommandHandler("skip", skip_location),
            ],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    id_handler = CommandHandler("id", id)
    application.add_handler(id_handler)

    # Run the bot until the user presses Ctrl-C

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":

    main()
