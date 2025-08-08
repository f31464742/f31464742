import telebot
import subprocess
import os

# === НАСТРОЙКИ ===
BOT_TOKEN = "7653223777:AAFc41uuY3FzZmdQxUzC0IKpAjnvgHGamgU"
CHAT_ID = -1002886621753  # id чата
TERMINAL_MESSAGE_ID = 265  # id "терминального" сообщения

bot = telebot.TeleBot(BOT_TOKEN)

current_directory = os.getcwd()
terminal_log = ["$ "]  # История "экрана" терминала

# Опасные команды
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

# Сетевые команды
network_leak_patterns = [
    "ip a", "ip addr", "ip link", "ip route", "ip neigh",
    "ifconfig",
    "hostname -i", "hostname -I", "hostname",
    "whoami",
    "curl ifconfig.me", "wget ifconfig.me", "curl icanhazip.com", "wget icanhazip.com",
    "ping", "traceroute", "nslookup",
    "netstat", "ss -tuln", "ss -tulnp", "arp -a"
]

# Системные директории, куда нельзя лезть
blocked_dirs = {
    "bin", "boot", "dev", "etc", "home", "lib", "lib64", "lost+found",
    "mnt", "opt", "proc", "root", "run", "sbin", "srv", "sys", "tmp", "usr", "var"
}


def is_command_dangerous(command):
    c = command.lower()
    for p in dangerous_patterns + network_leak_patterns:
        if p in c:
            return True
    return False


def update_terminal():
    """Обновляет сообщение-терминал"""
    text = "```shell\n" + "\n".join(terminal_log) + "\n```" + "‎‎‎‎‎‎‎‎‎‎‎‎‎‎‎‎‎‎‎‎‎‎‎‎"  # невидимые символы для ширины
    try:
        bot.edit_message_text(
            text,
            chat_id=CHAT_ID,
            message_id=TERMINAL_MESSAGE_ID,
            parse_mode="Markdown"
        )
    except Exception as e:
        print("Ошибка обновления:", e)


@bot.message_handler(func=lambda message: True)
def handle_command(message):
    global current_directory

    if message.chat.id != CHAT_ID:
        return

    command = message.text.strip()

    # Удаляем сообщение пользователя, чтобы чат был чистый
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

    # Запрещённые команды
    if is_command_dangerous(command):
        terminal_log.append(f"$ {command}\n# неа фигушки")
        update_terminal()
        return

    # cd
    if command.startswith("cd"):
        parts = command.split(maxsplit=1)
        if len(parts) == 2:
            path = parts[1].strip()
            dir_name = os.path.normpath(path).split(os.sep)[0]
            if dir_name in blocked_dirs:
                terminal_log.append(f"$ {command}\n# Нет доступа к этой директории")
            else:
                try:
                    new_path = os.path.abspath(os.path.join(current_directory, path))
                    if os.path.isdir(new_path):
                        current_directory = new_path
                    else:
                        terminal_log.append(f"$ {command}\n# Нет такой директории")
                except Exception as e:
                    terminal_log.append(f"$ {command}\n# Ошибка: {str(e)}")
        else:
            terminal_log.append(f"$ {command}\n# Укажи путь после cd")
        update_terminal()
        return

    # Выполнение команды
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10, cwd=current_directory)
        output = result.stdout + result.stderr

        # Фильтруем ls
        if command.strip() == "ls":
            lines = output.splitlines()
            lines = [l for l in lines if l.strip() not in blocked_dirs]
            output = "\n".join(lines)

        terminal_log.append(f"$ {command}\n{output.strip()}")
        if len(terminal_log) > 30:  # ограничиваем историю
            terminal_log.pop(0)

        update_terminal()

    except Exception as e:
        terminal_log.append(f"$ {command}\n# Ошибка: {str(e)}")
        update_terminal()


print("Бот запущен!")
bot.polling()
