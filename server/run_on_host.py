"""Загружает скрипт на сервер и запускает напрямую на хосте (не в Docker)."""
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

    sftp = c.open_sftp()
    sftp.put(script, remote_path)
    sftp.close()
    print(f"Uploaded: {remote_path}")

    cmd = f"python3 {remote_path}"
    print(f"$ {cmd}\n")
    _, stdout, stderr = c.exec_command(cmd, timeout=120)
    for line in iter(stdout.readline, ""):
        print(line, end="", flush=True)
    err = stderr.read().decode(errors="replace").strip()
    if err:
        print("\n[stderr]", err)

    c.close()

if __name__ == "__main__":
    main()
