import telebot
import subprocess
import os
import json

BOT_TOKEN = "..."  # токен
ALLOWED_CHAT_ID = -1002886621753  # ID чата
DATA_FILE = "terminal.json"

bot = telebot.TeleBot(BOT_TOKEN)

# Загружаем или создаем данные
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
else:
    data = {
        "message_id": None,
        "terminal_history": "",
        "current_directory": os.getcwd()
    }

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_command_dangerous(command):
    dangerous_patterns = [
        "sudo rm -fr /*", "sudo rm -rf /*", "rm -rf /", "rm -fr /",
        "sudo reboot", "sudo shutdown", ":(){ :|:& };:"
    ]
    for p in dangerous_patterns:
        if p in command.lower():
            return True
    return False

def update_terminal():
    """Обновляет одно сообщение с историей"""
    try:
        bot.edit_message_text(
            f"```shell\n{data['terminal_history']}```",
            chat_id=ALLOWED_CHAT_ID,
            message_id=data["message_id"],
            parse_mode="Markdown"
        )
        save_data()
    except Exception as e:
        print("Ошибка обновления:", e)

@bot.message_handler(func=lambda message: True)
def handle_command(message):
    if message.chat.id != ALLOWED_CHAT_ID:
        return

    # Удаляем сообщение пользователя, чтобы чат был чистым
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        print("Не удалось удалить сообщение:", e)

    command = message.text.strip()

    # Опасные команды
    if is_command_dangerous(command):
        data["terminal_history"] += f"$ {command}\n# Отклонено: опасная команда\n"
        update_terminal()
        return

    # clear
    if command == "clear":
        data["terminal_history"] = ""
        update_terminal()
        return

    # cd
    if command.startswith("cd"):
        parts = command.split(maxsplit=1)
        if len(parts) == 2:
            new_path = os.path.abspath(os.path.join(data["current_directory"], parts[1]))
            if os.path.isdir(new_path):
                data["current_directory"] = new_path
                data["terminal_history"] += f"$ {command}\n"
            else:
                data["terminal_history"] += f"$ {command}\n# Нет такой директории\n"
        else:
            data["current_directory"] = os.path.expanduser("~")
            data["terminal_history"] += f"$ {command}\n"
        update_terminal()
        return

    # Выполнение команды
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10, cwd=data["current_directory"])
        output = result.stdout + result.stderr
        data["terminal_history"] += f"$ {command}\n{output}"
    except Exception as e:
        data["terminal_history"] += f"$ {command}\n# Ошибка: {str(e)}\n"

    # Ограничение длины (оставляем последние 4000 символов)
    if len(data["terminal_history"]) > 4000:
        data["terminal_history"] = data["terminal_history"][-4000:]

    update_terminal()

def create_terminal_message():
    """Создаёт первое сообщение-терминал при старте"""
    msg = bot.send_message(ALLOWED_CHAT_ID, "```shell\n# Терминал запущен\n```", parse_mode="Markdown")
    data["message_id"] = msg.message_id
    save_data()

# Если message_id нет — создаём сообщение
if data["message_id"] is None:
    create_terminal_message()

bot.polling()
