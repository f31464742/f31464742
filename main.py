import telebot
import subprocess
import os

BOT_TOKEN = '7653223777:AAFc41uuY3FzZmdQxUzC0IKpAjnvgHGamgU'
ALLOWED_CHAT_ID = -1002886621753  # ID чата

bot = telebot.TeleBot(BOT_TOKEN)

home_directory = os.getcwd()
current_directory = home_directory

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

# Запрещённые директории
blocked_dirs = {
    "bin", "boot", "dev", "etc", "home", "lib", "lib64", "lost+found",
    "mnt", "opt", "proc", "root", "run", "sbin", "srv", "sys", "tmp", "usr", "var"
}

def is_command_dangerous(command):
    c = command.lower()
    for p in dangerous_patterns + network_leak_patterns:
        if p in c:
            print("неа фигушки")  # единственный лог
            return True
    return False

def get_prompt():
    rel_path = os.path.relpath(current_directory, home_directory)
    if rel_path == ".":
        rel_path = "~"
    else:
        rel_path_parts = rel_path.split(os.sep)
        rel_path_parts = [p for p in rel_path_parts if p not in blocked_dirs]
        rel_path = "~" if not rel_path_parts else "~/" + "/".join(rel_path_parts)
    return f"archbot@chat:{rel_path}$"

@bot.message_handler(func=lambda message: True)
def handle_command(message):
    global current_directory

    if message.chat.id != ALLOWED_CHAT_ID:
        return

    command = message.text.strip()

    if is_command_dangerous(command):
        bot.reply_to(message, "неа фигушки")
        return

    # Обработка cd
    if command.startswith("cd"):
        parts = command.split(maxsplit=1)
        if len(parts) == 2:
            path = parts[1].strip()
            dir_name = os.path.normpath(path).split(os.sep)[0]
            if dir_name in blocked_dirs:
                bot.reply_to(message, f"```shell\n{get_prompt()} cd {path}\nНет доступа к этой директории\n```", parse_mode="Markdown")
                return
            try:
                new_path = os.path.abspath(os.path.join(current_directory, path))
                new_dir_name = os.path.normpath(new_path).split(os.sep)[0]
                if new_dir_name in blocked_dirs:
                    bot.reply_to(message, f"```shell\n{get_prompt()} cd {path}\nНет доступа к этой директории\n```", parse_mode="Markdown")
                    return
                if os.path.isdir(new_path):
                    current_directory = new_path
                    bot.reply_to(message, f"```shell\n{get_prompt()} cd {path}\n```", parse_mode="Markdown")
                else:
                    bot.reply_to(message, f"```shell\n{get_prompt()} cd {path}\nНет такой директории\n```", parse_mode="Markdown")
            except Exception as e:
                bot.reply_to(message, f"```shell\n{get_prompt()} cd {path}\nОшибка: {str(e)}\n```", parse_mode="Markdown")
        else:
            bot.reply_to(message, f"```shell\n{get_prompt()} cd\nУкажи путь после cd\n```", parse_mode="Markdown")
        return

    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10, cwd=current_directory)
        output = result.stdout + result.stderr

        # Фильтруем ls
        if command.strip() == "ls":
            lines = output.splitlines()
            lines = [l for l in lines if l.strip() not in blocked_dirs]
            output = "\n".join(lines)

        if len(output) > 4000:
            output = output[:4000] + "\n[Вывод обрезан]"

        bot.reply_to(
            message,
            f"```shell\n{get_prompt()} {command}\n{output}```" if output.strip() else f"```shell\n{get_prompt()} {command}\n```",
            parse_mode="Markdown"
        )
    except Exception as e:
        bot.reply_to(message, f"```shell\n{get_prompt()} {command}\nОшибка: {str(e)}\n```", parse_mode="Markdown")

bot.polling()
