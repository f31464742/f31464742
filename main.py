import telebot
import subprocess
import os

BOT_TOKEN = '7653223777:AAFc41uuY3FzZmdQxUzC0IKpAjnvgHGamgU'
ALLOWED_CHAT_ID = -1002886621753

bot = telebot.TeleBot(BOT_TOKEN)

current_directory = os.getcwd()

dangerous_patterns = [
    "sudo rm -fr /*",
    "sudo rm -rf /*",
    "rm -rf /",
    "rm -fr /",
    "sudo reboot",
    "sudo shutdown",
    ":(){ :|:& };:",
    "mkfs",
    "dd if=",
    "dd of=",
    ">:",
    "chmod 000",
    "chown 0:0",
    ">: /dev/sda",
    ">: /dev/sdb",
    ">: /dev/*",
    "halt",
    "poweroff",
    "init 0",
    "init 6",
    "reboot",
    "shutdown -h now",
    "shutdown -r now",
    "rm -rf *",
    "rm -rf .",
    "rm -rf ~",
    "rm -rf /*",
    "rm -rf /home",
    "rm -rf /root",
    "wget http://",
    "curl http://",
    "nc -l",
    "netcat -l",
    "mkfs.ext4",
    "mkfs.xfs",
    "mkfs.vfat",
    "mkfs.btrfs",
    "echo > /etc/passwd",
    "echo > /etc/shadow",
    "echo > /etc/group",
    "echo > /etc/sudoers",
    "passwd root",
    "passwd -d root",
    "userdel",
    "groupdel",
    "adduser",
    "addgroup",
    "iptables -F",
    "iptables --flush",
    "iptables -X",
    "iptables --delete-chain",
    "iptables -P",
]

def is_command_dangerous(command):
    c = command.lower()
    for p in dangerous_patterns:
        if p in c:
            print("Плохая команда обнаружена - неа фигушки")
            return True
    return False

@bot.message_handler(func=lambda message: True)
def handle_command(message):
    global current_directory

    if message.chat.id != ALLOWED_CHAT_ID:
        return

    command = message.text.strip()

    if is_command_dangerous(command):
        bot.reply_to(message, "неа фигушки")
        return

    if command.startswith("cd"):
        parts = command.split(maxsplit=1)
        if len(parts) == 2:
            path = parts[1]
            try:
                new_path = os.path.abspath(os.path.join(current_directory, path))
                if os.path.isdir(new_path):
                    current_directory = new_path
                    bot.reply_to(message, f"📁 Перешёл в директорию:\n`{current_directory}`", parse_mode="Markdown")
                else:
                    bot.reply_to(message, f"❌ Нет такой директории: `{path}`", parse_mode="Markdown")
            except Exception as e:
                bot.reply_to(message, f"❌ Ошибка при смене директории:\n`{str(e)}`", parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ Укажи путь после `cd`", parse_mode="Markdown")
        return

    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10, cwd=current_directory)
        output = result.stdout + result.stderr
        if not output.strip():
            output = "Команда выполнена, но ничего не вывела."
        if len(output) > 4000:
            output = output[:4000] + "\n\n[Вывод обрезан]"
        bot.reply_to(message, f"📥 Команда:\n`{command}`\n\n📤 Ответ:\n```\n{output}\n```", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка:\n`{str(e)}`", parse_mode="Markdown")

bot.polling()
