import socket
import threading
import time

TARGETS = {
    10899: ('193.233.138.42', 443),
    10900: ('193.233.138.42', 2053),
}


def frag_send(sock, data):
    i = 0
    for off in range(0, min(len(data), 24), 4):
        sock.sendall(data[off:off + 4])
        time.sleep(0.008)
        i = off + 4
    if data[i:]:
        sock.sendall(data[i:])


def pump(src, dst, first_frag):
    first = True
    try:
        while True:
            d = src.recv(65536)
            if not d:
                break
            if first and first_frag:
                first = False
                frag_send(dst, d)
            else:
                dst.sendall(d)
    except OSError:
        pass
    finally:
        try:
            dst.shutdown(socket.SHUT_WR)
        except OSError:
            pass


def handle(conn, target):
    try:
        dst = socket.create_connection(target, timeout=10)
    except OSError:
        try:
            conn.close()
        except OSError:
            pass
        return
    threading.Thread(target=pump, args=(conn, dst, True), daemon=True).start()
    pump(dst, conn, False)
    for s in (conn, dst):
        try:
            s.close()
        except OSError:
            pass


def serve(listener, target):
    while True:
        conn, _ = listener.accept()
        threading.Thread(target=handle, args=(conn, target), daemon=True).start()


def main():
    listeners = []
    for port, target in TARGETS.items():
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('127.0.0.1', port))
        s.listen(128)
        listeners.append((s, target))
    print('fragment relay ready on 10899/10900', flush=True)
    for s, target in listeners:
        threading.Thread(target=serve, args=(s, target), daemon=True).start()
    while True:
        time.sleep(3600)


if __name__ == '__main__':
    main()