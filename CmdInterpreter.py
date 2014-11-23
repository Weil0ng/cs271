#!/usr/bin/env python

import cmd
import socket
import thread
import time

log = []
IP = ["128.111.46.83"]
PORT = [12345]
OUT_SOCK = [None] * len(IP)
IN_SOCK = [None] * len(IP)
CONN = [None] * len(IP)
BUFFER_SIZE = 2048
pid = 0
BallotNum = (0, 0)
AcceptNum = (0, 0)
AcceptVal = 0
receivedVals = [None] * len(IP)
AckNum = [None] * len(IP)
AckHighVal = [None] * len(IP)
AckHighBal = [None] * len(IP)
AckHighId = [None] * len(IP)
majority = 3

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
    IN_SOCK[index].bind(('0.0.0.0', 12345))
    while True:
	print ("Waiting for client %d" % index)
	IN_SOCK[index].listen(1)
        CONN[index], addr = IN_SOCK[index].accept()
	print addr
	while True:
            time.sleep(1)
	    print "receiving data:"
	    data = CONN[index].recv(BUFFER_SIZE)
	    print "recieved data: ", data.split('#')
	    if not data:
	        CONN[index].close()
	        break;
	    if data.split('#')[0] == 'prepare':
		bal = data.split('#')[1]
		rid = data.split('#')[2]
		global BallotNum
		if ((BallotNum[0] < bal) or (BallotNum[0] == bal) and (BallotNum[0] < rid)):
                    BallotNum = (bal, rid)
                    send2server("ack#" + str(BallotNum[0]) + '#' + str(BallotNum[1]) + '#' + str(AcceptNum[0]) + '#' + str(AcceptNum[1]) + '#' + str(AcceptVal), index)
            if data.split('#')[0] == "ack":
                AckNum[index] += 1
                bal = data.split('#')[3]
                rid = data.split('#')[4]
                if ((AckHighBal[index] < bal) or (AckHighBal[index] == bal) and (AckHighId[index] == rid)):
                    AckHighVal[index] = data.split('#')[5]
                if (AckNum[index] >= majority):
                    receivedVal[index] = AckHighVal[index]
                send2all("accept#" + str(BallotNum[0]) + '#' + str(BallotNum[1]) + '#' + str(AcceptVal))
            if data.split('#')[0] == "accept":
                bal = data.split('#')[1]
                rid = data.split('#')[2]
		global BallotNum, AcceptNum, AcceptVal
                if ((BallotNum[0] < bal) or (BallotNum[0] == bal) and (BallotNum[0] < rid)):
                    AcceptNum = (bal, rid)
                    AcceptVal = data.split('#')[3]
                    if #first time
                        send2all(data)
                #if get accept from majority
                    log.append(data.split('#')[3])
                    send2all("decide#" + data.split('#')[3])
            if data.split('#')[0] == "decide":
                log.append(data.split('#')[3])
                

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
    OUT_SOCK[index].send(msg)

def send2all(msg):
    for i in range(0, len(IP)):
	send2Server(msg, i)

def init_paxos(val):
    global Ballot
    Ballot += 1
    send2all("prepare#" + str(Ballot) + '#' + str(pid)) 

class CmdInterpreter(cmd.Cmd):

    def do_deposit(self, arg):
	print (arg)
	init_paxos(arg)

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
    send2Server("prepare#0#100", 0)
    cmdInterp = CmdInterpreter()
    cmdInterp.cmdloop("Please enter cmd: \n\tdeposit [number] \n\twithdraw [number] \n\tbalance \n\tfail \n\tunfail \npress CTRL+D to quit.")
