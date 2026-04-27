"""Запуск одной команды на сервере с большим timeout."""
import sys, os
os.environ["PYTHONIOENCODING"] = "utf-8"
import paramiko

HOST, PORT, USER, PASSWORD = "77.110.96.77", 22, "root", "Ma9851H3pKIU"

def run(cmd, timeout=300):
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)
    print(f"$ {cmd}")
    _, stdout, stderr = c.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode(errors="replace").strip()
    err = stderr.read().decode(errors="replace").strip()
    c.close()
    if out: print(out)
    if err: print("[err]", err)
    return out

if __name__ == "__main__":
    cmd = " ".join(sys.argv[1:])
    run(cmd)
