import os
import sys
import subprocess
import time
import telebot

# === Конфигурация ===
BOT_TOKEN = '7653223777:AAFc41uuY3FzZmdQxUzC0IKpAjnvgHGamgU'
ALLOWED_CHAT_ID = -1002886621753
blocked_dirs = {
    "bin", "boot", "dev", "etc", "home", "lib", "lib64", "lost+found",
    "mnt", "opt", "proc", "root", "run", "sbin", "srv", "sys", "tmp", "usr", "var"
}
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

# === Глобальная переменная для директории ===
current_directory = os.getcwd()

# === Проверка опасных команд ===
def is_command_dangerous(command):
    c = command.lower()
    for p in dangerous_patterns:
        if p in c:
            return True
    return False

# === Режим установки пакета (BOT_MODE=install) ===
if os.environ.get("BOT_MODE") == "install":
    pkg_command = sys.argv[1:]
    os.system("sudo rm -f /var/lib/pacman/db.lck")  # снимаем лок
    try:
        subprocess.run(["sudo", "pacman", "-S", "--noconfirm"] + pkg_command, check=True)
        print("✅ Пакет установлен:", " ".join(pkg_command))
    except subprocess.CalledProcessError as e:
        print("❌ Ошибка установки:", e)
    # Перезапуск бота
    subprocess.Popen(["python3", __file__])
    sys.exit(0)

# === Обычный режим работы бота ===
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(func=lambda message: True)
def handle_command(message):
    global current_directory

    if message.chat.id != ALLOWED_CHAT_ID:
        return

    command = message.text.strip()

    # Проверка опасных команд
    if is_command_dangerous(command):
        bot.reply_to(message, "неа фигушки")
        return

    # Перехват pacman-команд
    if command.startswith("sudo pacman -S"):
        pkg_list = command.split()[3:]
        bot.reply_to(message, f"⏳ Перезапускаюсь для установки пакета: {' '.join(pkg_list)}")
        subprocess.Popen(
            ["BOT_MODE=install", "python3", __file__] + pkg_list,
            env={**os.environ, "BOT_MODE": "install"}
        )
        sys.exit(0)
        return

    # Обработка cd
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

    # Выполнение команды
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10, cwd=current_directory)
        output = result.stdout + result.stderr

        # Фильтрация ls
        if command.strip() == "ls":
            lines = output.splitlines()
            lines = [l for l in lines if l.strip() not in blocked_dirs]
            output = "\n".join(lines)

        if not output.strip():
            output = "Команда выполнена, но ничего не вывела."
        if len(output) > 4000:
            output = output[:4000] + "\n\n[Вывод обрезан]"

        bot.reply_to(message, f"📥 Команда:\n`{command}`\n\n📤 Ответ:\n```\n{output}\n```", parse_mode="Markdown")
    except subprocess.TimeoutExpired:
        bot.reply_to(message, "❌ Ошибка: команда выполнялась слишком долго.")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка:\n`{str(e)}`", parse_mode="Markdown")

# Запуск бота
bot.polling()
