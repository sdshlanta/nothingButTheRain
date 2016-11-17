import argparse
import base64
import requests
import random
from multiprocessing import Process
from flask import Flask, request
import os
import time
import socket

#the remote bouncers that you want to hit
remoteHosts = ['192.168.0.254:8888','192.168.0.254:8889']
maxParts = 0
app = Flask(__name__)
@app.route('/setParts', methods=['POST'])
def setMaxParts():
	if not request.json:
		return abort(400)
	global maxParts
	maxParts = int(request.json['maxParts'])
	return 'ok'
parts = {}
@app.route('/', methods=['POST'])
def receive():
	if not request.json:
		return abort(400)
	else:
		global maxParts
		global parts
		parts[int(request.json['index'])] = base64.b64decode(request.json['data'])
		if len(parts) == maxParts+1:
			filename = request.json['filename']
			time.sleep(1)
			with open('reassembled.jpg','wb') as fp:
				for index in xrange(0,len(parts)):
					fp.write(parts[index])
		return 'ok'

def splitupFile(filename, blockSize):
	fp = file(filename)
	count = 0
	for filePart in iter(lambda: fp.read(blockSize), ''):
		filePart = base64.b64encode(filePart)
		yield (count,filePart)
		count+=1

def write(filename, blockSize=4096):
	data = {}
	print("Sending file")
	global maxParts
	for count, part in splitupFile(filename, blockSize):
		data = {'filename':filename, 'index':count, 'data':part}
		randomHost = random.choice(remoteHosts)
		r = requests.post("http://%s" % randomHost, json=data)
		print("Part %d sent to %s" % (count, random.choice(remoteHosts)))
		maxParts = count
	print("Sending finished")

def read(filename):
	randomHost = random.choice(remoteHosts)
	data = {'host':'%s:8887' % socket.gethostbyname(socket.gethostname()),'filename':filename, 'firstHop':'true'}
	r = requests.post("http://localhost:8887/setParts", json={'maxParts':maxParts})
	r = requests.post("http://%s/read" % randomHost, json=data)
	

def main():
	server = Process(target=app.run, args=("0.0.0.0", 8887, True))
	server.start()
	write(args.fileToSend, args.b)
	time.sleep(5)
	read(args.fileToSend)
	time.sleep(5)
	server.terminate()
	server.join()



if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='A quick and dirty Multi-Path TCP using remote proxy hosts.')
	parser.add_argument('fileToSend', metavar='F', type=str, help='The file you would like to send.')
	parser.add_argument('-b', type=int, default=4096, help='The size of the blocks you want to split the file into.' )
	args = parser.parse_args()
	main()
