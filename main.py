import os
import subprocess
import telebot


BOT_TOKEN = "7653223777:AAFc41uuY3FzZmdQxUzC0IKpAjnvgHGamgU"
CHAT_ID = -1002886621753
TERMINAL_MESSAGE_ID = 265
BASE_DIR = "/root/arch"
PROMPT = "archbot@chat:~$"


os.makedirs(BASE_DIR, exist_ok=True)

bot = telebot.TeleBot(BOT_TOKEN)
current_directory = BASE_DIR
terminal_log = [PROMPT]
last_terminal_text = ""



def load_dangerous_patterns(file_path="narch.txt"):
    """Reads blocked commands from file."""
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip().lower() for line in f if line.strip()]


dangerous_patterns = load_dangerous_patterns()


def is_command_dangerous(command):
    """Checks if command is blocked."""
    cmd = command.lower()
    return any(pattern in cmd for pattern in dangerous_patterns)


def is_inside_base(path):
    """Checks if path is inside BASE_DIR."""
    return os.path.abspath(path).startswith(BASE_DIR)


def update_terminal():
    """Updates terminal message in chat."""
    global last_terminal_text

    empty_top = "\n" * 10
    wide_line = " " * 100

    text_lines = terminal_log.copy()
    text_lines.append(wide_line)

    terminal_text = f"```shell\n{empty_top}" + "\n".join(text_lines) + "\n```"

    if terminal_text == last_terminal_text:
        return
    last_terminal_text = terminal_text

    try:
        bot.edit_message_text(
            terminal_text,
            chat_id=CHAT_ID,
            message_id=TERMINAL_MESSAGE_ID,
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"[Terminal update error]: {e}")


@bot.message_handler(func=lambda m: True)
def handle_command(message):
    global current_directory

    if message.chat.id != CHAT_ID:
        return

    command = message.text.strip()


    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

   
    if command in ("clear", "cls"):
        terminal_log.clear()
        terminal_log.append(PROMPT)
        update_terminal()
        return


    if is_command_dangerous(command):
        terminal_log.append(f"{PROMPT} {command}\n# Command blocked")
        update_terminal()
        return

   
    if command.startswith("cd"):
        parts = command.split(maxsplit=1)
        if len(parts) == 1:
            return
        new_path = os.path.abspath(os.path.join(current_directory, parts[1]))

        if not is_inside_base(new_path):
            terminal_log.append(f"{PROMPT} {command}\n# Path outside {BASE_DIR} is not allowed")
        elif os.path.abspath(current_directory) == BASE_DIR and parts[1] in ("..", "../"):
            terminal_log.append(f"{PROMPT} {command}\n# Already in root directory {BASE_DIR}")
        elif os.path.isdir(new_path):
            current_directory = new_path
        else:
            terminal_log.append(f"{PROMPT} {command}\n# Directory not found")

        update_terminal()
        return

   
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, cwd=current_directory
        )
        output = (result.stdout + result.stderr).strip()
        terminal_log.append(f"{PROMPT} {command}\n{output}")
        if len(terminal_log) > 30:
            terminal_log.pop(0)
        update_terminal()
    except Exception as e:
        terminal_log.append(f"{PROMPT} {command}\n# Error: {str(e)}")
        update_terminal()



bot.polling()
