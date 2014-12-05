#!/usr/bin/env python

import cmd
import socket
import thread
import threading
import time

log = []

#comm vars
IP = ["0.0.0.0", "54.67.122.117", "54.67.122.118"]
PORT = [12000, 12345, 12344]
pid = 0
mutex = threading.Lock()
OUT_SOCK = [None] * len(IP)
IN_SOCK = [None] * len(IP)
CONN = [None] * len(IP)

#Cross instance vars
BUFFER_SIZE = 2048
majority = 2
live = 0
liveness = [False] * len(IP)
halt = False
Sync = False

#PAXOS instance vars
BallotNum = (0, 0)
AcceptNum = (0, 0)
AcceptVal = 0
AckNum = 0
AccNum = 0
AckHighVal = 0
AckHighBal = (0, 0)
InitVal = 0
AccSent = False
DecSent = False

def queryServer(index):
    retry = 0
    global Sync, live, mutex
    while True:
        try:
    	    print ("Querying server %s" % IP[index])
	    OUT_SOCK[index].connect((IP[index], PORT[index]))
	    print ("Connect established with server %s" % IP[index])
	    liveness[index] = True
	    mutex.acquire()
	    live += 1
	    if ((Sync is False) and (index == pid%(len(IP) - 1) + 1)):
		Sync = True
	        mutex.release()
		print "SYNC: %s" % IP[index]
	        send2Server("syncreq", index)
	    else:	    
	        mutex.release()
	    break;
        except:
            retry += 1
	    print ("QueryServer Exception, retry %d" % retry)
	    time.sleep(1)

def waitForClient(index):
    global mutex, halt, liveness, BallotNum, AcceptNum, AcceptVal, AckNum, AccNum, AccSent, DecSent, AckHighBal, AckHighVal, AccepctVal
    IN_SOCK[index].setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print "binding socket %d to server %d" % (index, index)
    IN_SOCK[index].bind(('0.0.0.0', PORT[index]))
    while True:
	if halt:
	    IN_SOCK[index].close()
	    break
	print ("Waiting for client %d" % index)
	IN_SOCK[index].listen(0)
        CONN[index], addr = IN_SOCK[index].accept()
	liveness[index] = True
	CONN[index].setblocking(0)
	print addr
	while True:
	    while True:
		if halt:
		    break
		try:
	            data = CONN[index].recv(BUFFER_SIZE)
		    break
	        except:
		    time.sleep(0.1)
	    if halt:
		print "CLOSE %d" % index
                CONN[index].close()
		if liveness[index]:
		    OUT_SOCK[index].close()
                break
	    print "recieved data %s from server %s: " % (data.split('#'), index)
    	    mutex.acquire()
	    # if client dies
	    if not data:
	        CONN[index].close()
                OUT_SOCK[index] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		print "Server %s is dead!" % IP[index]
		liveness[index] = False
		thread.start_new_thread(queryServer, (index, ))
		mutex.release()
	        break
	    # if client asks for sync
	    elif data.split('#')[0] == 'syncreq':
		msg = 'syncack'
		for item in log:
		    if len(msg) + len(str(item)) + 1 > BUFFER_SIZE:
			send2Server(msg, index)
			msg = 'syncack'
		    msg += '#'
		    msg += str(item)
		send2Server(msg, index)
		mutex.release()
		continue
	    # if client answers for sync
	    elif data.split('#')[0] == 'syncack':
		for item in data.split('#'):
		    if item == 'syncack':
			continue
		    log.append(float(item))
		mutex.release()
		continue
	    # if the msg is stale
	    elif not data.split('#')[len(data.split('#'))-1] == str(len(log)):
		print "Sequence num %d not match %d! Aborting msg!" % (int(data.rsplit('#')[len(data.split('#'))-1]), len(log))
		mutex.release()
		continue
	    else:
		seqNum = int(data.split('#')[len(data.split('#'))-1])
	    # if PAXOS msg
	    if data.split('#')[0] == 'prepare':
		bal = data.split('#')[1]
		rid = data.split('#')[2]
		# if Ballot < bal, set ballot, join
		print "bal: %s, rid: %s" % (bal, rid)
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
		log.append(float(data.split('#')[1]))
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
	thread.start_new_thread(queryServer, (i, ))
    while (live < majority):
	print "live: %d" % live
	time.sleep(1)

def send2Server(msg, index):
    while liveness[index]:
        try:
	    if msg.split('#')[0] == 'syncreq' or msg.split('#')[0] == 'syncack':
                OUT_SOCK[index].send(msg)
            else:
                OUT_SOCK[index].send(msg + "#" + str(len(log)))
	    break
	except:
	    continue

def send2All(msg):
    for i in range(0, len(IP)):
	if liveness[i]:
	    print "sending msg to server %d" % i
	    send2Server(msg, i)

def reset_local_state():
    global AcceptNum, AcceptVal, AckNum, AccNum, AckHighVal, AckHighBal, InitVal, AccSent, DecSent
    print "reseting local state"
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
	global halt
	if not halt:
	    init_paxos(arg)

    def do_withdraw(self, arg):
	global halt
	if not halt:
	    init_paxos(-1.0*int(arg))
    
    def do_balance(self, arg):
	global halt
	if not halt:
	    get_balance()
    
    def do_print(self, arg):
	for item in log:
	    if float(item) >= 0:
		print "Deposit ", item
	    else:
		print "Withdraw", str(-1.0*float(item))

    def do_fail(self, arg):
	global halt
	if not halt:
	    halt = True
	    del log[:]
            print ("Oops! This server is not working!")	

    def do_unfail(self, arg):
	global halt, Sync
	if halt:
	    for i in liveness:
	        i = False
	    live = 0
	    Sync = False
	    reset_local_state()
	    halt = False
	    init_conn()
	    print ("Wala! The node recovers!")

    def do_EOF(self, arg):
	return (True)

    def postloop(self):
	print ("Goodbye!")

if __name__ == '__main__':
    #thread.start_new_thread(init_paxos, (20, ))
    init_conn()
    #send2Server("prepare#0#100", 0)
    CmdInterp = CmdInterpreter()
    CmdInterp.cmdloop("Please enter cmd: \n\tdeposit [number] \n\twithdraw [number] \n\tbalance \n\tfail \n\tunfail \n\tprint \npress CTRL+D to quit.")
