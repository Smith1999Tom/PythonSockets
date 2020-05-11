#Code taken from https://pythonprogramming.net/client-chatroom-sockets-tutorial-python-3/
import socket
import select
import errno
import sys
import random
from datetime import date, datetime


index = 0 #index to keep track of how many times the nickname is rejected
IP = "10.0.42.17" #the ip to connect to
validserver = False 
while not validserver: #loops until a server the bot knows is entered
	server = input("Please enter the server you would like to connect to (miniircd/server.py).") # gets the users input
	if server == "miniircd":
		PORT = 6667 #sets the port to be for miniircd
		validserver = True
	elif server == "server.py": 
		PORT = 1234 #sets the port to be for server
		validserver = True
	else:
		print("unrecognized server") #informs the user that there choice was invalid

#connects to the ip
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((IP, PORT))
client_socket.setblocking(False)	

#handles joining the server
def join_server():
	global index #takes in the index variable
	if index == 0: #if its the first try
		nickname = "NICK ProBot\r" #sets nickname to be ProBot
	else:
		nickname = f"NICK ProBot{str(index)}\r" #sets nickname to be ProBot plus the number if trys
	index += 1 #increments the index
	
	username = "ProBot" # sets username
	client_socket.send(f"{nickname}\nUSER {username} {username} 127.0.0.1 bot\r\n".encode("utf-8"))#sends the message containing the info needed to join

	#asks to join the channel test
	channelmessage = "JOIN #test"
	client_socket.send(f"{channelmessage}\r\n".encode("utf-8"))



def output_message(message):
	print(f"{message}")	#Prints message
					

def do_bot_response(message):
	splitmessage = message.split(' ') #splits the message into parts
	#removes characters
	splitmessage[3] = splitmessage[3].replace('\r', '')
	splitmessage[3] = splitmessage[3].replace(':', '')
	splitmessage[3] = splitmessage[3].replace('\n', '')
	if splitmessage[3] == "!day": #handles the day command
		weekDays = ("Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday")
		response = weekDays[date.today().weekday()]
	elif splitmessage[3] == "!time": #handles the time command
		response = datetime.now().strftime("%H:%M:%S")
	else:
		num = random.randint(0, 5)#generates random number
		if num == 1:
			response = "RandomResponse1"
		elif num == 2:
			response = "RandomResponse2"
		elif num == 3:
			response = "RandomResponse3"
		elif num == 4:
			response = "RandomResponse4"
		else:
			response = "RandomResponse5"
	print(response)
	client_socket.send(f"PRIVMSG #test {response}\r\n".encode("utf-8")) #sends the response to the channel
	
def do_priv_response(message):
	splitmessage = message.split(' ') #splits the message into parts
	sender = splitmessage[0].split('!') #gets who sent the message
	#removes characters
	splitmessage[3] = splitmessage[3].replace('\r', '')
	splitmessage[3] = splitmessage[3].replace(':', '')
	splitmessage[3] = splitmessage[3].replace('\n', '')
	if splitmessage[3] == "!day": #handles the day command
		weekDays = ("Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday")
		response = weekDays[date.today().weekday()]
	elif splitmessage[3] == "!time": #handles the time command
		response = datetime.now().strftime("%H:%M:%S")
	else:
		num = random.randint(0, 5)#generates random number
		if num == 1:
			response = "RandomResponse1"
		elif num == 2:
			response = "RandomResponse2"
		elif num == 3:
			response = "RandomResponse3"
		elif num == 4:
			response = "RandomResponse4"
		else:
			response = "RandomResponse5"
	client_socket.send(f"PRIVMSG {sender[0][1:]} {response}\r\n".encode("utf-8")) #sends the response to the sender


join_server()

#Loop forever (until close connection)
while True:
	#When we have received all messages, an error will be thrown (see IO errors below)
	try:
		while True:	#Receive messages from server

			message = client_socket.recv(1024).decode("utf-8")	#Read in the message
			
			output_message(message) #prints the message
			
			try:
				splitmessage = message.split(' ') #splits the message into parts
				if splitmessage[1] == '433': # checks if the response is that the username is invalid
					join_server() #retries joining with a different username
				if splitmessage[1] == 'PRIVMSG': #checks if its a private message
					if splitmessage[2] == '#test': #checks if its from the channel
						do_bot_response(message) 
					else:
						do_priv_response(message)
			except Exception as e:
				print (e)

	except IOError as e:
		if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:	#All messages have been received, continue out of inner while loop and give control back to user
			print('Reading error', str(e))
			sys.exit()
		continue

	except Exception as e:
		print('General error', str(e))
		print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
		sys.exit()
		
