import telebot
import subprocess
import os

# === НАСТРОЙКИ ===
BOT_TOKEN = "7653223777:AAFc41uuY3FzZmdQxUzC0IKpAjnvgHGamgU"
CHAT_ID = -1002886621753  # id чата
TERMINAL_MESSAGE_ID = 265  # id "терминала"
BASE_DIR = "/root/arch"  # директория, в которой работаем

bot = telebot.TeleBot(BOT_TOKEN)
current_directory = BASE_DIR
terminal_log = ["$ "]

# Опасные команды
dangerous_patterns = [
    "sudo rm -fr /*", "sudo rm -rf /*", "rm -rf /", "rm -fr /",
    "sudo reboot", "sudo shutdown", ":(){ :|:& };:", "mkfs", "dd if=",
    "halt", "poweroff", "init 0", "init 6", "reboot", "shutdown -h now",
    "shutdown -r now", "iptables -F", "iptables --flush"
]

def is_command_dangerous(command):
    c = command.lower()
    for p in dangerous_patterns:
        if p in c:
            return True
    return False

def is_inside_base(path):
    """Проверка, что путь внутри BASE_DIR"""
    abs_path = os.path.abspath(path)
    return abs_path.startswith(BASE_DIR)

def update_terminal():
    """Обновляет терминал в одном сообщении"""
    text = "```shell\n" + "\n".join(terminal_log) + "\n```" + "‎‎‎‎‎‎‎‎‎‎‎‎‎‎‎‎‎‎‎‎‎‎‎"
    bot.edit_message_text(
        text,
        chat_id=CHAT_ID,
        message_id=TERMINAL_MESSAGE_ID,
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: True)
def handle_command(message):
    global current_directory

    if message.chat.id != CHAT_ID:
        return

    command = message.text.strip()

    # Удаляем сообщение пользователя
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

    # clear
    if command in ["clear", "cls"]:
        terminal_log.clear()
        terminal_log.append("$ ")
        update_terminal()
        return

    # Опасные команды
    if is_command_dangerous(command):
        terminal_log.append(f"$ {command}\n# запрещено")
        update_terminal()
        return

    # cd
    if command.startswith("cd"):
        parts = command.split(maxsplit=1)
        if len(parts) == 1:
            return
        new_path = os.path.join(current_directory, parts[1])
        if not is_inside_base(new_path):
            terminal_log.append(f"$ {command}\n# нельзя выйти за {BASE_DIR}")
        elif os.path.isdir(new_path):
            current_directory = os.path.abspath(new_path)
        else:
            terminal_log.append(f"$ {command}\n# нет такой директории")
        update_terminal()
        return

    # Выполнение команд
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, cwd=current_directory
        )
        output = result.stdout + result.stderr
        terminal_log.append(f"$ {command}\n{output.strip()}")
        if len(terminal_log) > 30:
            terminal_log.pop(0)
        update_terminal()
    except Exception as e:
        terminal_log.append(f"$ {command}\n# ошибка: {str(e)}")
        update_terminal()

print("Бот запущен!")
bot.polling()
