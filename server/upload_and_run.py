"""Загружает скрипт на сервер и запускает внутри Docker bot контейнера."""
import sys, os
os.environ["PYTHONIOENCODING"] = "utf-8"
import paramiko

HOST, PORT, USER, PASSWORD = "77.110.96.77", 22, "root", "Ma9851H3pKIU"

def main():
    script = sys.argv[1]
    remote_path = f"/tmp/{os.path.basename(script)}"

    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)

    # Загружаем файл
    sftp = c.open_sftp()
    sftp.put(script, remote_path)
    sftp.close()
    print(f"Загружен: {remote_path}")

    # Запускаем внутри контейнера бота
    cmd = f"docker cp {remote_path} mystbot-bot-1:/tmp/ && docker exec mystbot-bot-1 python /tmp/{os.path.basename(script)}"
    print(f"$ {cmd}\n")
    _, stdout, stderr = c.exec_command(cmd, timeout=300)

    # Стримим вывод
    for line in iter(stdout.readline, ""):
        print(line, end="")
    err = stderr.read().decode(errors="replace").strip()
    if err:
        print("\n[stderr]", err)

    c.close()

if __name__ == "__main__":
    main()
