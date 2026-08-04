import signal
import threading
import time


def handler(signum, frame):
    print("Signal received")


def worker():
    time.sleep(1)
    print("Worker attempting to get signal...")
    try:
        s = signal.getsignal(signal.SIGINT)
        print(f"Worker got signal: {s}")
    except ValueError as e:
        print(f"Worker failed to get signal: {e}")

    print("Worker attempting to set signal...")
    try:
        signal.signal(signal.SIGINT, handler)
        print("Worker successfully set signal")
    except ValueError as e:
        print(f"Worker failed to set signal: {e}")


threading.Thread(target=worker).start()
time.sleep(2)
