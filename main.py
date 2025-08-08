import telebot
import subprocess
import os
import sys
import time

# Токен берём из переменной окружения
BOT_TOKEN = os.getenv("7653223777:AAFc41uuY3FzZmdQxUzC0IKpAjnvgHGamgU")
ALLOWED_CHAT_ID = -1002886621753

if not BOT_TOKEN:
    print("❌ Ошибка: BOT_TOKEN не задан! Запусти так: BOT_TOKEN=твой_токен python3 main.py")
    sys.exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

current_directory = os.getcwd()

# Опасные команды
dangerous_patterns = [
    "sudo rm -fr /*", "sudo rm -rf /*", "rm -rf /", "rm -fr /",
    "sudo reboot", "sudo shutdown", ":(){ :|:& };:", "mkfs",
    "dd if=", "dd of=", ">:",
    "chmod 000", "chown 0:0", ">: /dev/sd", "halt", "poweroff",
    "init 0", "init 6", "reboot", "shutdown -h now", "shutdown -r now",
    "rm -rf *", "rm -rf .", "rm -rf ~", "wget http://", "curl http://",
    "nc -l", "netcat -l", "mkfs.ext4", "mkfs.xfs", "mkfs.vfat", "mkfs.btrfs",
    "echo > /etc/passwd", "echo > /etc/shadow", "echo > /etc/group", "echo > /etc/sudoers",
    "passwd root", "passwd -d root", "userdel", "groupdel", "adduser", "addgroup",
    "iptables -F", "iptables --flush", "iptables -X", "iptables --delete-chain", "iptables -P"
]

# Запрещённые директории для cd
blocked_dirs = {
    "bin", "boot", "dev", "etc", "home", "lib", "lib64", "lost+found",
    "mnt", "opt", "proc", "root", "run", "sbin", "srv", "sys", "tmp", "usr", "var"
}


def is_command_dangerous(command):
    c = command.lower()
    for p in dangerous_patterns:
        if p in c:
            return True
    return False


def run_pacman_install(package):
    """Запуск pacman и возврат вывода"""
    try:
        # убираем блокировку, если есть
        if os.path.exists("/var/lib/pacman/db.lck"):
            os.remove("/var/lib/pacman/db.lck")

        result = subprocess.run(
            f"sudo pacman -S {package} --noconfirm",
            shell=True,
            capture_output=True,
            text=True
        )
        return result.returncode, result.stdout + result.stderr
    except Exception as e:
        return 1, f"❌ Ошибка при установке: {e}"


def restart_bot():
    """Перезапуск бота"""
    bot.stop_polling()
    python = sys.executable
    os.execl(python, python, *sys.argv)


@bot.message_handler(func=lambda message: True)
def handle_command(message):
    global current_directory

    if message.chat.id != ALLOWED_CHAT_ID:
        return

    command = message.text.strip()

    if is_command_dangerous(command):
        bot.reply_to(message, "❌ Опасная команда, выполнение запрещено")
        return

    # Установка через pacman
    if command.startswith("sudo pacman -S"):
        package = command.split(" ", 3)[-1]
        code, output = run_pacman_install(package)

        if len(output) > 4000:
            output = output[:4000] + "\n\n[Вывод обрезан]"

        bot.reply_to(message, f"📥 Команда:\n`{command} --noconfirm`\n\n📤 Ответ:\n{output}", parse_mode="Markdown")

        # Если пакет установился успешно — перезапускаем бота
        if code == 0:
            bot.reply_to(message, "✅ Пакет установлен, перезапускаю бота...")
            time.sleep(2)
            restart_bot()
        return

    # Обычные команды
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=current_directory,
            capture_output=True,
            text=True
        )
        output = result.stdout + result.stderr
        if len(output) > 4000:
            output = output[:4000] + "\n\n[Вывод обрезан]"
        bot.reply_to(message, f"📤 Ответ:\n{output}")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")


print("🤖 Бот запущен")
bot.polling()
