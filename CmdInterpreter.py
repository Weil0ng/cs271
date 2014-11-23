#!/usr/bin/env python

import cmd
import readline
import socket
import thread
import time

log = []
IP = ["169.231.6.155"]
PORT = [12345]
OUT_SOCK = [None] * len(IP)
IN_SOCK = [None] * len(IP)
CONN = [None] * len(IP)

def queryServer(index):
    while True:
        try:
    	    print ("Querying server %d" % index)
	    OUT_SOCK[index].connect((IP[index], PORT[index]))
	    print ("Connect established")
	    break;
        except:
	    print ("QueryServer Exception")
	    time.sleep(1)

def waitForClient(index):
	print ("Waiting for client %d" % index)
	IN_SOCK[index].bind(('0.0.0.0', 42709))
	IN_SOCK[index].listen(1)
        CONN[index], addr = IN_SOCK[index].accept()
	print addr

def init_conn():
    print ("Initializing connection...")
    index = 0
    while index < len(IP):
    	OUT_SOCK[index] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	IN_SOCK[index] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	index += 1
    for i in range(0, len(IP)):
	thread.start_new_thread(waitForClient, (i, ))
    for i in range(0, len(IP)):
	queryServer(i)

def send2Server(msg, index):
    print ("sending $s" % msg)
    OUT_SOCK[index].send(msg)

class CmdInterpreter(cmd.Cmd):

    def do_deposit(self, arg):
	print (arg)

    def do_withdraw(self, arg):
	print ("withdraw")
    
    def do_balance(self, arg):
	print ("balance")
    
    def do_fail(self, arg):
        print ("fail a node")

    def do_unfail(self, arg):
	print ("recover a node")

    def do_EOF(self, arg):
	return (True)

    def postloop(self):
	print ("Goodbye!")

if __name__ == '__main__':
    init_conn()
    send2Server("hello", 0)
    cmdInterp = CmdInterpreter()
    cmdInterp.cmdloop("Please enter cmd: \n\tdeposit [number] \n\twithdraw [number] \n\tbalance \n\tfail \n\tunfail \npress CTRL+D to quit.")
