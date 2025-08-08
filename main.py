import telebot
import subprocess
import os

BOT_TOKEN = '7653223777:AAFc41uuY3FzZmdQxUzC0IKpAjnvgHGamgU'  # твой токен
ALLOWED_CHAT_ID = -1002886621753
MESSAGE_ID = 1  # айди твоего "терминала" в чате

bot = telebot.TeleBot(BOT_TOKEN)
current_directory = os.getcwd()
terminal_history = "archlog.txt"  # хранит все команды и вывод

def is_command_dangerous(command):
    dangerous_patterns = [
        "sudo rm -fr /*", "sudo rm -rf /*", "rm -rf /", "rm -fr /",
        "sudo reboot", "sudo shutdown", ":(){ :|:& };:"
    ]
    for p in dangerous_patterns:
        if p in command.lower():
            return True
    return False

@bot.message_handler(func=lambda message: True)
def handle_command(message):
    global current_directory, terminal_history

    if message.chat.id != ALLOWED_CHAT_ID:
        return

    command = message.text.strip()

    # Опасные команды
    if is_command_dangerous(command):
        terminal_history += f"$ {command}\n# Отклонено: опасная команда\n"
        update_terminal(message.chat.id)
        return

    # clear
    if command == "clear":
        terminal_history = ""
        update_terminal(message.chat.id)
        return

    # cd
    if command.startswith("cd"):
        parts = command.split(maxsplit=1)
        if len(parts) == 2:
            new_path = os.path.abspath(os.path.join(current_directory, parts[1]))
            if os.path.isdir(new_path):
                current_directory = new_path
                terminal_history += f"$ {command}\n"
            else:
                terminal_history += f"$ {command}\n# Нет такой директории\n"
        else:
            current_directory = os.path.expanduser("~")
            terminal_history += f"$ {command}\n"
        update_terminal(message.chat.id)
        return

    # Выполнение команды
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10, cwd=current_directory)
        output = result.stdout + result.stderr
        terminal_history += f"$ {command}\n{output}"
    except Exception as e:
        terminal_history += f"$ {command}\n# Ошибка: {str(e)}\n"

    # Ограничение длины
    if len(terminal_history) > 4000:
        terminal_history = terminal_history[-4000:]

    update_terminal(message.chat.id)

def update_terminal(chat_id):
    """Редактирует одно сообщение с историей"""
    try:
        bot.edit_message_text(
            f"```shell\n{terminal_history}```",
            chat_id=chat_id,
            message_id=MESSAGE_ID,
            parse_mode="Markdown"
        )
    except Exception as e:
        print("Ошибка обновления:", e)

bot.polling()
