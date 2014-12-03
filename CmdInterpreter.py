#!/usr/bin/env python

import cmd
import socket
import thread
import threading
import time

log = []
IP = ["54.67.122.117", "54.67.122.118"]
PORT = [12345, 12344]
mutex = threading.Lock()
OUT_SOCK = [None] * len(IP)
IN_SOCK = [None] * len(IP)
CONN = [None] * len(IP)
BUFFER_SIZE = 2048
pid = 0
BallotNum = (0, 0)
AcceptNum = (0, 0)
AcceptVal = 0
#receivedVals = [None] * len(IP)
#AckNum = [None] * len(IP)
AckNum = 0
AccNum = 0
#AckHighVal = [None] * len(IP)
AckHighVal = 0
#AckHighBal = [None] * len(IP)
AckHighBal = (0, 0)
#AckHighId = [None] * len(IP)
majority = 1
InitVal = 0
AccSent = False
DecSent = False

def queryServer(index):
    retry = 0
    while True:
        try:
    	    print ("Querying server %d" % index)
	    OUT_SOCK[index].connect((IP[index], PORT[index]))
	    print ("Connect established with server %d" % index)
	    break;
        except:
            retry += 1
	    print ("QueryServer Exception, retry %d" % retry)
	    time.sleep(1)

def waitForClient(index):
    global BallotNum, AcceptNum, AcceptVal, AckNum, AccNum, AccSent, DecSent, AckHighBal, AckHighVal, AccepctVal
    IN_SOCK[index].setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print "binding socket %d to server %d" % (index, index)
    IN_SOCK[index].bind(('0.0.0.0', PORT[index]))
    while True:
	print ("Waiting for client %d" % index)
	IN_SOCK[index].listen(0)
        CONN[index], addr = IN_SOCK[index].accept()
	print addr
	while True:
            time.sleep(1)
	    print "receiving data:"
	    data = CONN[index].recv(BUFFER_SIZE)
	    print "recieved data %s from server %s: " % (data.split('#'), index)
    	    mutex.acquire()
	    # if client dies
	    if not data:
	        CONN[index].close()
		mutex.release()
	        break
	    elif not data.split('#')[len(data.split('#'))-1] == str(len(log)):
		print "Sequence num %d not match %d! Aborting msg!" % (int(data.rsplit('#')[0]), len(log))
		continue
	    else:
		seqNum = data.rsplit('#')[0]
	    if data.split('#')[0] == 'prepare':
		bal = data.split('#')[1]
		rid = data.split('#')[2]
		# if Ballot < bal, set ballot, join
		if (AcceptNum <= (bal, rid)):
                    AcceptNum = (bal, rid)
		    msg = "ack#" + bal + '#' + rid + '#' + str(AcceptNum[0]) + '#' + str(AcceptNum[1]) + '#' + str(AcceptVal)
		    print "ACK: %s to server %d" % (msg, index)
                    send2Server(msg, index)
            elif data.split('#')[0] == "ack":
		if not AccSent:
                    AckNum += 1
                    bal = data.split('#')[3]
                    rid = data.split('#')[4]
                    if (AckHighBal <= (bal, rid)):
                        AckHighVal = data.split('#')[5]
                    if (AckNum >= majority):
		        AcceptVal = AckHighVal
                        if (AcceptVal == str(0)):
                            AcceptVal = InitVal
			msg = "accept#" + str(BallotNum[0]) + '#' + str(BallotNum[1]) + '#' + str(AcceptVal)
			print "ACC: %s to all" % msg
                        send2All(msg)
		        AccSent = True
            elif data.split('#')[0] == "accept":
		if not DecSent:
		    AccNum += 1
                    bal = data.split('#')[1]
                    rid = data.split('#')[2]
                    if (AcceptNum <= (bal, rid)):
                        AcceptNum = (bal, rid)
                        AcceptVal = data.split('#')[3]
                        if not AccSent:
			    AccSent = True
                            send2All(data)
                    #if get accept from majority
		    if (AccNum >= majority):
		        msg = "decide#" + AcceptVal
		        print "DEC: %s to all" % msg
                        send2All(msg)
			DecSent = True
            elif data.split('#')[0] == "decide":
                log[int(seqNum)]= float(data.split('#')[1])
                reset_local_state()
	    else:
                print "Unknown Msg!"
		print data
    	    mutex.release()
                

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
    OUT_SOCK[index].send(msg + "#" + str(len(log)))

def send2All(msg):
    for i in range(0, len(IP)):
	print "sending msg to server %d" % i
	send2Server(msg, i)

def reset_local_state():
    global AcceptNum, AcceptVal, AckNum, AccNum, AckHighVal, AckHighBal, InitVal, AccSent, DecSent
    AcceptNum = (0, 0)
    AcceptVal = 0
    AckNum = 0
    AccNum = 0
    AckHighVal = 0
    AckHighBal = (0, 0)
    InitVal = 0
    AccSent = False
    DecSent = False 

def init_paxos(val):
    global BallotNum, InitVal
    BallotNum = (BallotNum[0] + 1, BallotNum[1])
    InitVal = val
    msg = "prepare#" + str(BallotNum[0]) + '#' + str(BallotNum[1])
    print msg
    send2All(msg)

def get_balance():
    global log
    curBallance = 0
    for item in log:
	curBallance += float(item)
    print curBallance

class CmdInterpreter(cmd.Cmd):

    def do_deposit(self, arg):
	print (arg)
	init_paxos(arg)

    def do_withdraw(self, arg):
	print ("withdraw")
    
    def do_balance(self, arg):
	get_balance()
    
    def do_fail(self, arg):
        print ("fail a node")

    def do_unfail(self, arg):
	print ("recover a node")

    def do_EOF(self, arg):
	return (True)

    def postloop(self):
	print ("Goodbye!")

if __name__ == '__main__':
    #thread.start_new_thread(init_paxos, (20, ))
    init_conn()
    #send2Server("prepare#0#100", 0)
    CmdInterp = CmdInterpreter()
    CmdInterp.cmdloop("Please enter cmd: \n\tdeposit [number] \n\twithdraw [number] \n\tbalance \n\tfail \n\tunfail \npress CTRL+D to quit.")
