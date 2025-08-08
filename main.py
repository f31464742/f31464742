import telebot
import subprocess
import os
import json

BOT_TOKEN = "7653223777:AAFc41uuY3FzZmdQxUzC0IKpAjnvgHGamgU"  # токен
ALLOWED_CHAT_ID = -1002886621753  # ID чата
DATA_FILE = "terminal.json"

bot = telebot.TeleBot(BOT_TOKEN)

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

# Загружаем или создаём данные
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
else:
    data = {
        "message_id": None,
        "history": [],
        "current_directory": os.getcwd()
    }

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_command_dangerous(command):
    c = command.lower()
    for p in dangerous_patterns + network_leak_patterns:
        if p in c:
            return True
    return False

def update_terminal():
    """Обновляет одно сообщение с последними 50 строками и делает его широким"""
    visible_lines = data["history"][-50:]
    big_terminal = "\n".join(visible_lines)

    # Добавляем пустые строки сверху и снизу
    big_terminal = "\n" * 2 + big_terminal + "\n" * 2

    # Делаем широкую строку с невидимыми символами
    big_terminal += "\n" + ("\u200b" * 150)

    bot.edit_message_text(
        f"```shell\n{big_terminal}```",
        chat_id=ALLOWED_CHAT_ID,
        message_id=data["message_id"],
        parse_mode="Markdown"
    )
    save_data()

@bot.message_handler(func=lambda message: True)
def handle_command(message):
    if message.chat.id != ALLOWED_CHAT_ID:
        return

    # Удаляем сообщение пользователя
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

    command = message.text.strip()

    # Запрет опасных команд
    if is_command_dangerous(command):
        data["history"].append(f"$ {command}")
        data["history"].append("# Отклонено: опасная команда")
        update_terminal()
        return

    # clear
    if command == "clear":
        data["history"].clear()
        update_terminal()
        return

    # cd
    if command.startswith("cd"):
        parts = command.split(maxsplit=1)
        if len(parts) == 2:
            path = parts[1].strip()
            dir_name = os.path.normpath(path).split(os.sep)[0]
            if dir_name in blocked_dirs:
                data["history"].append(f"$ {command}")
                data["history"].append("# Нет доступа к этой директории")
                update_terminal()
                return
            try:
                new_path = os.path.abspath(os.path.join(data["current_directory"], path))
                if os.path.isdir(new_path):
                    data["current_directory"] = new_path
                    data["history"].append(f"$ {command}")
                else:
                    data["history"].append(f"$ {command}")
                    data["history"].append("# Нет такой директории")
            except Exception as e:
                data["history"].append(f"$ {command}")
                data["history"].append(f"# Ошибка: {str(e)}")
        else:
            data["history"].append(f"$ {command}")
            data["history"].append("# Укажи путь после cd")
        update_terminal()
        return

    # Выполнение команды
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10, cwd=data["current_directory"])
        output = result.stdout + result.stderr

        # Фильтруем ls
        if command.strip() == "ls":
            lines = output.splitlines()
            lines = [l for l in lines if l.strip() not in blocked_dirs]
            output = "\n".join(lines)

        data["history"].append(f"$ {command}")
        if output.strip():
            data["history"].extend(output.strip().split("\n"))
    except Exception as e:
        data["history"].append(f"$ {command}")
        data["history"].append(f"# Ошибка: {str(e)}")

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
