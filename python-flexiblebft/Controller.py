from Protocol import Protocol
import random
from threading import Thread
from time import sleep

protocol = Protocol(4)


def create_cmd(cmd):
    protocol.add_command([cmd])


def run():
    protocol.run()

run_thread = Thread(target=run, args=())
run_thread.start()

for i in range(0, 400):
    cmd_thread = Thread(target=create_cmd, args=(random.randint(0, 1),))
    cmd_thread.start()
    sleep(random.random())


