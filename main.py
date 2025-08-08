import telebot
import subprocess
import os

BOT_TOKEN = "7653223777:AAFc41uuY3FzZmdQxUzC0IKpAjnvgHGamgU"
CHAT_ID = -1002886621753  # твой чат
MESSAGE_ID = 265  # ID сообщения-терминала

bot = telebot.TeleBot(BOT_TOKEN)
current_directory = os.getcwd()

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

@bot.message_handler(func=lambda message: True)
def handle_cmd(message):
    global current_directory

    if message.chat.id != CHAT_ID:
        return

    # Удаляем команду пользователя
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

    command = message.text.strip()

    # Проверка опасных команд
    if is_command_dangerous(command):
        bot.edit_message_text(
            f"```shell\n$ {command}\n# Неа, фигушки```" + "\u200b" * 150,
            chat_id=CHAT_ID,
            message_id=MESSAGE_ID,
            parse_mode="Markdown"
        )
        return

    # Обработка cd
    if command.startswith("cd"):
        parts = command.split(maxsplit=1)
        if len(parts) == 2:
            path = parts[1].strip()
            dir_name = os.path.normpath(path).split(os.sep)[0]
            if dir_name in blocked_dirs:
                output = "# Нет доступа к этой директории"
            else:
                try:
                    new_path = os.path.abspath(os.path.join(current_directory, path))
                    if os.path.isdir(new_path):
                        current_directory = new_path
                        output = ""
                    else:
                        output = "# Нет такой директории"
                except Exception as e:
                    output = f"# Ошибка: {str(e)}"
        else:
            output = "# Укажи путь после cd"

        bot.edit_message_text(
            f"```shell\n$ {command}\n{output}```" + "\u200b" * 150,
            chat_id=CHAT_ID,
            message_id=MESSAGE_ID,
            parse_mode="Markdown"
        )
        return

    # Выполняем команду
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=10, cwd=current_directory
        )
        output = result.stdout + result.stderr

        # Фильтруем ls
        if command.strip() == "ls":
            lines = output.splitlines()
            lines = [l for l in lines if l.strip() not in blocked_dirs]
            output = "\n".join(lines)

        if len(output) > 4000:
            output = output[:4000] + "\n# [Вывод обрезан]"

    except Exception as e:
        output = f"# Ошибка: {str(e)}"

    # Делаем широкое сообщение
    bot.edit_message_text(
        f"```shell\n$ {command}\n{output}```" + "\u200b" * 150,
        chat_id=CHAT_ID,
        message_id=MESSAGE_ID,
        parse_mode="Markdown"
    )

bot.polling()
