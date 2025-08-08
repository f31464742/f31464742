import telebot
import subprocess
import os

BOT_TOKEN = '7653223777:AAFc41uuY3FzZmdQxUzC0IKpAjnvgHGamgU'
ALLOWED_CHAT_ID = -1002886621753  # ID чата

bot = telebot.TeleBot(BOT_TOKEN)

current_directory = os.getcwd()

dangerous_patterns = [
    "sudo rm -fr /*", "sudo rm -rf /*", "rm -rf /", "rm -fr /", "sudo reboot", "sudo shutdown",
    ":(){ :|:& };:", "mkfs", "dd if=", "dd of=", ">:",
    "chmod 000", "chown 0:0", ">: /dev/sda", ">: /dev/sdb", ">: /dev/*",
    "halt", "poweroff", "init 0", "init 6", "reboot", "shutdown -h now", "shutdown -r now",
    "rm -rf *", "rm -rf .", "rm -rf ~", "rm -rf /*", "rm -rf /home", "rm -rf /root",
    "wget http://", "curl http://", "nc -l", "netcat -l",
    "mkfs.ext4", "mkfs.xfs", "mkfs.vfat", "mkfs.btrfs",
    "echo > /etc/passwd", "echo > /etc/shadow", "echo > /etc/group", "echo > /etc/sudoers",
    "passwd root", "passwd -d root", "userdel", "groupdel", "adduser", "addgroup",
    "iptables -F", "iptables --flush", "iptables -X", "iptables --delete-chain", "iptables -P"
]

blocked_dirs = {
    "bin", "boot", "dev", "etc", "home", "lib", "lib64", "lost+found",
    "mnt", "opt", "proc", "root", "run", "sbin", "srv", "sys", "tmp", "usr", "var"
}

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

    # обработка cd
    if command.startswith("cd"):
        parts = command.split(maxsplit=1)
        if len(parts) == 2:
            path = parts[1].strip()
            dir_name = os.path.normpath(path).split(os.sep)[0]
            if dir_name in blocked_dirs:
                bot.reply_to(message, "❌ Нет доступа к этой директории", parse_mode="Markdown")
                return
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
        # Автоматическая подстановка --noconfirm для pacman
        if command.startswith("sudo pacman -S") and "--noconfirm" not in command:
            command += " --noconfirm"

        # Для pacman увеличиваем таймаут
        cmd_timeout = 10
        if "pacman" in command:
            cmd_timeout = 300  # 5 минут

        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=cmd_timeout, cwd=current_directory)
        output = result.stdout + result.stderr

        # фильтруем ls
        if command.strip() == "ls":
            lines = output.splitlines()
            lines = [l for l in lines if l.strip() not in blocked_dirs]
            output = "\n".join(lines)

        if not output.strip():
            output = "Команда выполнена, но ничего не вывела."
        if len(output) > 4000:
            output = output[:4000] + "\n\n[Вывод обрезан]"

        bot.reply_to(
            message,
            f"📥 Команда:\n`{command}`\n\n📤 Ответ:\n```\n{output}\n```",
            parse_mode="Markdown"
        )
    except subprocess.TimeoutExpired:
        bot.reply_to(message, "❌ Ошибка: команда выполнялась слишком долго.")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка:\n`{str(e)}`", parse_mode="Markdown")

bot.polling()
