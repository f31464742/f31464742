import telebot
import subprocess
import os

BOT_TOKEN = '7653223777:AAFc41uuY3FzZmdQxUzC0IKpAjnvgHGamgU'
ALLOWED_CHAT_ID = -1002886621753  # ID чата

bot = telebot.TeleBot(BOT_TOKEN)

home_directory = os.getcwd()
current_directory = home_directory

dangerous_patterns = [
    # опасные команды
    "sudo rm -fr /*", "sudo rm -rf /*", "rm -rf /", "rm -fr /", "sudo reboot", "sudo shutdown",
    ":(){ :|:& };:", "mkfs", "dd if=", "dd of=", ">:",
    "chmod 000", "chown 0:0", ">: /dev/sda", ">: /dev/sdb", ">: /dev/*",
    "halt", "poweroff", "init 0", "init 6", "reboot", "shutdown -h now", "shutdown -r now",
    "rm -rf *", "rm -rf .", "rm -rf ~", "rm -rf /*", "rm -rf /home", "rm -rf /root",
    "wget http://", "curl http://", "nc -l", "netcat -l",
    "mkfs.ext4", "mkfs.xfs", "mkfs.vfat", "mkfs.btrfs",
    "echo > /etc/passwd", "echo > /etc/shadow", "echo > /etc/group", "echo > /etc/sudoers",
    "passwd root", "passwd -d root", "userdel", "groupdel", "adduser", "addgroup",
    "iptables -F", "iptables --flush", "iptables -X", "iptables --delete-chain", "iptables -P",
    # сетевые команды
    "ip a", "ip addr", "ip link", "ip route",
    "ifconfig", "hostname -i", "hostname -I", "hostname",
    "whoami", "curl ifconfig.me", "wget ifconfig.me",
    "ping", "traceroute", "nslookup", "netstat", "ss -tuln"
]

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

def get_prompt():
    rel_path = os.path.relpath(current_directory, home_directory)
    if rel_path == ".":
        rel_path = "~"
    else:
        rel_parts = []
        for part in rel_path.split(os.sep):
            if part in blocked_dirs or part == "..":
                continue
            rel_parts.append(part)
        rel_path = "~" if not rel_parts else "~/" + "/".join(rel_parts)
    return f"archbot@chat:{rel_path}$"

@bot.message_handler(func=lambda message: True)
def handle_command(message):
    global current_directory

    if message.chat.id != ALLOWED_CHAT_ID:
        return

    command = message.text.strip()

    # блокируем опасные
    if is_command_dangerous(command):
        bot.reply_to(message, "неа фигушки")
        return

    # обработка cd
    if command.startswith("cd"):
        parts = command.split(maxsplit=1)
        if len(parts) == 2:
            path = parts[1].strip()
            try:
                new_path = os.path.abspath(os.path.join(current_directory, path))
                parts_new = os.path.normpath(new_path).split(os.sep)
                if len(parts_new) > 1 and parts_new[1] in blocked_dirs:
                    bot.reply_to(message, "неа фигушки")
                    return
                if os.path.isdir(new_path):
                    current_directory = new_path
                else:
                    bot.reply_to(message, "неа фигушки")
            except:
                bot.reply_to(message, "неа фигушки")
        return

    # выполнение команды
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10, cwd=current_directory)
        output = result.stdout + result.stderr

        # фильтруем ls
        if command.strip() == "ls":
            lines = output.splitlines()
            lines = [l for l in lines if l.strip() not in blocked_dirs]
            output = "\n".join(lines)

        if len(output) > 4000:
            output = output[:4000] + "\n\n[Вывод обрезан]"

        # просто выводим prompt + вывод команды (даже если пусто)
        bot.reply_to(
            message,
            f"```\n{get_prompt()} {command}\n{output}\n```",
            parse_mode="Markdown"
        )
    except:
        bot.reply_to(message, "неа фигушки")

bot.polling()
