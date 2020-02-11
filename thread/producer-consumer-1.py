import queue
import signal
import threading


PRODUCE_CYCLE = 4
CONSUME_DURATION = 2


def log(msg, *args):
    if args:
        print(msg % args)
    else:
        print(msg)


class Producer(threading.Thread):
    def __init__(self, que, period):
        threading.Thread.__init__(self)
        self.que = que
        self.period = period
        self.stop = threading.Event()

    def run(self):
        log("Produce thread start")
        data = 1
        while not self.stop.is_set():
            self.que.put(data)
            data += 1
            log("Produce ->")
            self.stop.wait(self.period)

        log("Produce thread end")

    def terminate(self):
        self.stop.set()
        self.join()


class Consumer(threading.Thread):
    def __init__(self, que):
        threading.Thread.__init__(self)
        self.worker = Worker()
        self.que = que
        self.stop = threading.Event()

    def run(self):
        log("consume thread start")

        while not self.stop.is_set():
            try:
                data = self.que.get(timeout=1)
            except queue.Empty:
                continue

            if self.que.qsize() > 0:
                log("skip queued work in consumer")
                continue

            log("-> Consume")
            self.worker.do(data)

        log("consume thread end")

    def terminate(self):
        self.worker.terminate()
        self.stop.set()
        self.join()


class Worker(object):
    def __init__(self):
        self.stop = threading.Event()

    def do(self, data):
        log("Worker: %d working...", data)
        self.stop.wait(CONSUME_DURATION)
        log("Worker: %d done...", data)

    def terminate(self):
        self.stop.set()


def init_signals(stop, pro, con):
    """Catch signals in order to stop..."""

    # pylint: disable=unused-argument
    def signal_action(signum, frame):
        """To be executed upon exit signal."""
        log("signal: %d\n"
            "frame: %s\n"
            "Gracefully stopping... (press Ctrl+C again to force)", signum, frame)

        stop.set()
        pro.terminate()
        con.terminate()

    # Catch SIGINT and SIGTERM so that we can clean up
    for sig in [signal.SIGINT, signal.SIGTERM]:
        signal.signal(sig, signal_action)

    log('Press ctrl + c to terminate...')


def main():
    q = queue.Queue()
    stop = threading.Event()

    pro = Producer(q, PRODUCE_CYCLE)
    con = Consumer(q)
    init_signals(stop, pro, con)

    con.start()
    pro.start()

    try:
        while not stop.is_set():
            stop.wait(1)
    except Exception as e:
        log(e)
        raise

    log("Main thread end")


if __name__ == '__main__':
    main()
