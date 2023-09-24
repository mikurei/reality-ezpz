import os
import re
import subprocess

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
    TypeHandler,
    DispatcherHandlerStop,
)


SCRIPT = "bash <(curl -sL https://raw.githubusercontent.com/mikurei/reality-ezpz/master/reality-ezpz.sh) "


def get_users_ezpz() -> str:
    local_command = SCRIPT + "--list-users"
    return run_command(local_command).split("\n")[:-1]


def get_config_ezpz(username: str) -> str:
    local_command = SCRIPT + f"--show-user {username} | grep ://"
    return run_command(local_command)


def delete_user_ezpz(username: str) -> None:
    local_command = SCRIPT + f"--delete-user {username}"
    run_command(local_command)
    return


def add_user_ezpz(username: str) -> None:
    local_command = SCRIPT + f"--add-user {username}"
    run_command(local_command)
    return


def run_command(command: str) -> str:
    process = subprocess.Popen(
        ["/bin/bash", "-c", command],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    output, _ = process.communicate()
    return output.decode()


def pre_update(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    admin_list = admin.split(",")
    
    if user_id not in admin_list:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="You are not authorized to use this bot.",
        )
        raise DispatcherHandlerStop


def start(update: Update, context: CallbackContext) -> None:
    commands_text = "Reality-EZPZ User Management Bot\n\nChoose an option:"
    keyboard = [
        [InlineKeyboardButton("Show User", callback_data="show_user")],
        [InlineKeyboardButton("Add User", callback_data="add_user")],
        [InlineKeyboardButton("Delete User", callback_data="delete_user")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=commands_text,
        reply_markup=reply_markup,
    )


def users_list(
    update: Update, context: CallbackContext, text: str, callback: str
) -> None:
    keyboard = []
    for user in get_users_ezpz():
        keyboard.append(
            [InlineKeyboardButton(user, callback_data=f"{callback}!{user}")]
        )
    keyboard.append([InlineKeyboardButton("Back", callback_data="start")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(
        chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup
    )


def show_user(update: Update, context: CallbackContext, username: str) -> None:
    text = get_config_ezpz(username)
    keyboard = []
    keyboard.append([InlineKeyboardButton("Back", callback_data="show_user")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(
        chat_id=update.effective_chat.id, text=f'Config for "{username}":'
    )
    context.bot.send_message(
        chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup
    )


def delete_user(
    update: Update, context: CallbackContext, username: str
) -> None:
    keyboard = []
    if len(get_users_ezpz()) == 1:
        text = (
            "You cannot delete the only user.\n"
            "At least one user is needed.\n"
            "Create a new user, then delete this one."
        )
        keyboard.append([InlineKeyboardButton("Back", callback_data="start")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=reply_markup,
        )
        return
    text = f'Are you sure to delete "{username}"?'
    keyboard.append(
        [
            InlineKeyboardButton(
                "Delete", callback_data=f"approve_delete!{username}"
            )
        ]
    )
    keyboard.append(
        [InlineKeyboardButton("Cancel", callback_data="delete_user")]
    )
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(
        chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup
    )


def add_user(update: Update, context: CallbackContext) -> None:
    text = "Enter the username:"
    keyboard = []
    keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.user_data["expected_input"] = "username"
    context.bot.send_message(
        chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup
    )


def approve_delete(
    update: Update, context: CallbackContext, username: str
) -> None:
    delete_user_ezpz(username)
    text = f"User {username} has been deleted."
    keyboard = []
    keyboard.append([InlineKeyboardButton("Back", callback_data="start")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(
        chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup
    )


def cancel(update: Update, context: CallbackContext) -> None:
    if "expected_input" in context.user_data:
        del context.user_data["expected_input"]
    start(update, context)


def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    response = query.data.split("!")
    if len(response) == 1:
        if response[0] == "start":
            start(update, context)
        elif response[0] == "cancel":
            cancel(update, context)
        elif response[0] == "show_user":
            users_list(
                update, context, "Select user to view config:", "show_user"
            )
        elif response[0] == "delete_user":
            users_list(
                update, context, "Select user to delete:", "delete_user"
            )
        elif response[0] == "add_user":
            add_user(update, context)
        else:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Button pressed: {}".format(response[0]),
            )
    if len(response) > 1:
        if response[0] == "show_user":
            show_user(update, context, response[1])
        if response[0] == "delete_user":
            delete_user(update, context, response[1])
        if response[0] == "approve_delete":
            approve_delete(update, context, response[1])


def user_input(update: Update, context: CallbackContext) -> None:
    if "expected_input" in context.user_data:
        expected_input = context.user_data["expected_input"]
        del context.user_data["expected_input"]
        if expected_input == "username":
            username = update.message.text
            if username in get_users_ezpz():
                update.message.reply_text(
                    f'User "{username}" exists, try another username.'
                )
                add_user(update, context)
                return
            if not username_regex.match(username):
                update.message.reply_text(
                    "Username can only contains A-Z, a-z and 0-9, try another username."
                )
                add_user(update, context)
                return
            add_user_ezpz(username)
            update.message.reply_text(f'User "{username}" is created.')
            show_user(update, context, username)


token = os.environ["BOT_TOKEN"]
admin = os.environ["BOT_ADMIN_ID"]

username_regex = re.compile("^[a-zA-Z0-9]+$")

update_handler = TypeHandler(Update, pre_update)

start_handler = CommandHandler("start", start)
button_handler = CallbackQueryHandler(button)

updater = Updater(token)

updater.dispatcher.add_handler(update_handler, -1)
updater.dispatcher.add_handler(start_handler)
updater.dispatcher.add_handler(button_handler)
updater.dispatcher.add_handler(
    MessageHandler(Filters.text & ~Filters.command, user_input)
)

updater.start_polling()
updater.idle()
