#!/usr/bin/env python3

import socket
import select
import sys
import time

#Set the servers IP and port
IP = "10.0.42.17"
PORT = 1234

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)	#Set up the socket
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)	#allow address to be reused

server_socket.bind((IP, PORT))	#Bind the socket to the server address

server_socket.listen()	#Listen for sockets connecting

hostname = socket.gethostname()	#Get the servers hostname
clienthostname = "10.0.42.19" #TODO make this dynamic

sockets_list = [server_socket] #List of all sockets

channel_list = {'Global': []} # Dict of all channels (channelName/channel). A channel is a list of users

nick_list = {}	#Dict of socket : nickname
user_list = {}	#Dict of socket : username
realname_list = {}	#Dict of socket : realname

#Add a socket to a channel
def add_socket_to_channel(socket, channel_name):
	try:
		channel = channel_list[channel_name]	#Get the channel from the channellist

		#Check if socket is already in the channel
		if channel.count(socket) > 0:
			#Send error message to client
			socket.send(f":{hostname}.home 443 :{nick_list[socket]} {channel_name} :is already on channel".encode('utf-8'))
			return False
		
		#Add socket to the channel
		channel.append(socket)
		return True

	#Channel is not in channel_list, create new channel
	except KeyError as e:

		channel = [socket]	#Create the channel, and add the socket
		channel_list[channel_name] = channel 	#Add the channel to the channel list
		return True

	except Exception as e:
		print("General error" + e)
		print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
		return False

#Remove a socket from a channel
def remove_socket_from_channel(socket, channel_name, message):
	try:
		channel = channel_list[channel_name]	#Get list of users on the channel
		channel.remove(socket) #Remove the socket
		for user in channel:	#Tell everyone on the server
			user.send(f":{nick_list[socket]}!{user_list[socket]}@{clienthostname} PART {channel_name} {message}\r\n".encode('utf-8'))

		#Remove channel if empty
		if not channel:
			if channel_name in channel_list:
				del channel_list[channel_name]
		return True

	except:
		print(f"Error removing {nick_list[socket]} from channel {channel_name}.")
		return False

#Return a socket based on its nickname
def get_socket_by_nickname(nickname):
	try:
		for socket in nick_list:	#Find the socket
			if nickname == nick_list[socket]:
				return socket
		return False
	except Exception as e:
		print(e)
		return False

#Sends a message to as user or a channel
def send_private_message(sender_socket, dest_nick, message):
	try:
		channel_message = False	#Whether message is for a channel or not
		channel = None	
		dest_socket = None #Socket to send message to
		if dest_nick in channel_list:	#Check if the nickname was a channel
			channel = channel_list[dest_nick]
			channel_message = True
		else:	#Send to a specific socket
			dest_socket = get_socket_by_nickname(dest_nick)
			if dest_socket == False:
				return False

		if channel_message:
			if sender_socket in channel:
				for user in channel:	#Send to each user in the channel
					if user != sender_socket:
						user.send(f":{nick_list[sender_socket]}!{user_list[sender_socket]}@{clienthostname} PRIVMSG {dest_nick} {message}\r\n".encode('utf-8'))
			else:	#Tell user they need to be on the channel
				sender_socket.send(f":{hostname} 442 :{dest_nick} :You're not on that channel\r\n".encode('utf-8'))
				return False
		else:
			dest_socket.send(f":{nick_list[sender_socket]}!{user_list[sender_socket]}@{clienthostname} PRIVMSG {dest_nick} {message}\r\n".encode('utf-8'))
	except Exception as e:
		print(e)
		print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
		return False

#Endless loop to listen for client messages
def listen_for_messages():
	#Broadcasts messages in global
	while True:		#Loop to receive messages from our clients, and send them to all other clients
		
		read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list) #Read list, write list, error list. Only really need read list

		for notified_socket in read_sockets:	#Get all the sockets in read_sockets (is assigned to notified_socket)
			
			if notified_socket == server_socket:	#Server socket has just connected to someone new
				client_socket, client_address = server_socket.accept()	#Accept new client, store data in client socket and address

				#Get input from the client
				message = client_socket.recv(1024).decode('utf-8', 'ignore')
				#message = message.replace('\r\n', '')	#Get rid of evil characters

				print(message)
				#If client tries a capability check, skip it
				captest = message.split(' ')
				if captest[0] == 'CAP':
					message = message = client_socket.recv(1024).decode('utf-8', 'ignore')

				print(message)
				messageArray = message.split('\n') #Split the messages across lines

				#For each message received
				for getinput in messageArray:
					splitmessage = getinput.split(' ')	#Split into words

					#Determine the command to handle
					if splitmessage[0] == 'NICK':
						print(splitmessage[1].encode())
						splitmessage[1] = splitmessage[1][:-1] #Removes trailing carriage return
						if splitmessage[1] in nick_list.values():	#Check if nick is taken
							print("user already exists")
							print(f":{hostname}.home 433 * {splitmessage[1]} :Nickname is already taken!\r\n".encode('utf-8'))
							client_socket.send(f":{hostname}.home 433 * {splitmessage[1]} :Nickname is already taken!\r\n".encode('utf-8'))
							break
						#Add nickname to the nickname list
						nick_list[client_socket] = splitmessage[1]
					if splitmessage[0] == 'USER':
						#Add user to user list
						user_list[client_socket] = splitmessage[1]
						print('Added user')
						realname = ""
						for i in range(4, len(splitmessage)):
							realname += splitmessage[i]
						#Add realname to realname list
						realname_list[client_socket] = realname
						returnmessage = f":{hostname}.home 001 {nick_list[client_socket]} :Welcome to the Internet Relay Network {nick_list[client_socket]}!{user_list[client_socket]}@{clienthostname}\r\n"
						client_socket.send(returnmessage.encode())	#Send message to socket
						sockets_list.append(client_socket) #Add socket to list of sockets
						
	
			else:	#If not server socket, a new message has been sent
			#Get message from client and split across lines
				message = notified_socket.recv(1024).decode('utf-8', 'ignore')
				messageArray = message.split('\n')
				print (message)

				#Loop through the messages
				for getinput in messageArray:
					#Split into words
					splitmessage = getinput.split(' ')
					if splitmessage[0] == 'JOIN':
						splitmessage[1] = splitmessage[1].rstrip() #Removes trailing characters
						channel_name = splitmessage[1] #Get channel name

						#Add the socket to the channel
						if add_socket_to_channel(notified_socket, channel_name):
							channel = channel_list[channel_name]
							nicks_in_channel = ""
							#Get a list of everyone else in the channel
							for user in channel:
								if user != notified_socket:
									user.send(f"{nick_list[client_socket]}!{user_list[client_socket]}@{clienthostname} JOIN {channel_name}\r\n".encode('utf-8'))
									nicks_in_channel += (nick_list[user] + " ")

							#Send join messages to client
							notified_socket.send(f":{nick_list[notified_socket]}!{user_list[notified_socket]}@{clienthostname} JOIN {channel_name}\r\n".encode('utf-8'))
							notified_socket.send(f":{hostname}.home 332 {nick_list[notified_socket]} {channel_name} :channel of tom\r\n".encode('utf-8'))
							notified_socket.send(f":{hostname}.home 353 {nick_list[notified_socket]} = {channel_name} :{nicks_in_channel}\r\n".encode('utf-8'))
							notified_socket.send(f":{hostname}.home 366 {nick_list[notified_socket]} {channel_name} :End of NAMES list\r\n".encode('utf-8'))
						else:
							print(f"Error when adding {nick_list[notified_socket]} to channel {channel_name}.")

					#SEND PRIVATE MESSAGE
					if splitmessage[0] == 'PRIVMSG':
						dnick = splitmessage[1] #Nickname to send message to
						privmsg = ''
						for i in range(2, len(splitmessage)): #Build the message
							privmsg += (splitmessage[i] + " ")
						send_private_message(notified_socket, dnick, privmsg)

					if splitmessage[0] == 'PART':
						channel_name = splitmessage[1]
						privmsg=""
						#Build leaving message
						for i in range(2, len(splitmessage)):
							privmsg += (splitmessage[i] + " ")
						#Remove \r
						privmsg = privmsg.replace('\r','')
						print(privmsg.encode('utf-8'))
						remove_socket_from_channel(notified_socket, channel_name, privmsg)

						notified_socket.send(f":{nick_list[notified_socket]}!{user_list[notified_socket]}@{clienthostname} PART {channel_name} {privmsg}\r\n".encode('utf-8'))

					if splitmessage[0] == 'QUIT':
						if notified_socket == server_socket: #Dont leave if server socket is trying to quit
							break
						#Remove user from all lists
						sockets_list.remove(notified_socket)
						nick_list.pop(notified_socket)
						user_list.pop(notified_socket)
						realname_list.pop(notified_socket)

					if splitmessage[0] == 'NICK':
						splitmessage[1] = splitmessage[1][:-1] #Gets rid of \r
						if splitmessage[1] in nick_list.values():#Nickname already exists
							notified_socket.send(f":{hostname}.home 433 * {splitmessage[1]} :Nickname is already taken!\r\n".encode('utf-8'))
							break
						nick_list[notified_socket] = splitmessage[1]
					if splitmessage[0] == 'USER':
						user_list[notified_socket] = splitmessage[1]
						realname = ""
						for i in range(4, len(splitmessage)): #Build realname
							realname += splitmessage[i]
						realname_list[notified_socket] = realname #Add realname to list
						returnmessage = f":{hostname}.home 001 {nick_list[notified_socket]} :Welcome to the Internet Relay Network {nick_list[client_socket]}!{user_list[client_socket]}@{clienthostname}\r\n"
						#returnmessage = f":{hostname} 433 * Tom :Nickname is already in use".rstrip()
						print(returnmessage)
						print("sent")
						notified_socket.send(returnmessage.encode())
						#sockets_list.append(notified_socket)
						





		#For exception, remove the client
		for notified_socket in exception_sockets:
			print("exception")
			sockets_list.remove(notified_socket)
			del clients[notified_socket]





listen_for_messages()


