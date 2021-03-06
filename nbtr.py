import argparse
import base64
import requests
import random
from multiprocessing import Process
from flask import Flask, request
import os
import time
import socket
import threading
import sys
import logging

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
remoteHosts = []
maxParts = 0
parts = {}

def printProgress(i, count, prefix="", size=40):
	x = int(size*i/count)
	sys.stdout.write("%s[%s%s] %i/%i\r" % (prefix, "#"*x, "."*(size-x), i, count))
	sys.stdout.flush()

app = Flask(__name__)
@app.route('/setParts', methods=['POST'])
def setMaxParts():
	if not request.json:
		return abort(400)
	global maxParts
	maxParts = int(request.json['maxParts'])
	return 'ok'

@app.route('/', methods=['POST'])
def receive():
	def readFinished(filename):
		json = {'filename':filename}
		random.shuffle(remoteHosts)
		for host in remoteHosts:
			requests.post("http://%s/fileRead" % host, json=json)
	if not request.json:
		return abort(400)
	else:
		try:
			global maxParts
			global parts
			parts[int(request.json['index'])] = base64.b64decode(request.json['data'])
			# print(list(parts.iterkeys()))
			printProgress(len(parts), maxParts + 1)
			if len(parts) == maxParts+1:
				filename = request.json['filename']
				time.sleep(1)
				t = threading.Thread(target=readFinished, args=(filename,))
				with open('reassembled.%s' % filename.split('.')[1], 'wb') as fp:
					for index in xrange(0,len(parts)):
						fp.write(parts[index])
				t.start()
		except Exception as e:
			print(str(e))
			
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
	print('writing file')
	global maxParts
	for count, part in splitupFile(filename, blockSize):
		data = {'filename':filename, 'index':count, 'data':part}
		randomHost = random.choice(remoteHosts)
		r = requests.post('http://%s/' % randomHost, json=data)
		print('Part %d sent to %s' % (count, random.choice(remoteHosts)))
		maxParts = count
	print('writing finished')

def read(filename):
	randomHost = random.choice(remoteHosts)
	data = {'host':'%s:8887' % socket.gethostbyname(socket.gethostname()),'filename':filename, 'firstHop':'true'}
	# print(data)
	r = requests.post('http://localhost:8887/setParts', json={'maxParts':maxParts})
	r = requests.post('http://%s/read' % randomHost, json=data)

def loadHostsFromFile(fp):
	global remoteHosts
	remoteHosts = []
	for host in fp:
		remoteHosts.append(host.strip())

def main():
	if os.path.isfile(args.hosts):
		loadHostsFromFile(open(args.hosts, 'r'))
	else:
		if args.hosts.strip() == 'hosts.txt':
			print('File "%s" not found.' % args.hosts)
		else:
			print('File "hosts.txt" not found, perhaps you forgot to use the --hosts flag?')
		return

	server = Process(target=app.run, args=('0.0.0.0', 8887, False))
	server.start()
	write(args.fileToSend, args.b)
	raw_input("Press ENTER to receive.")
	read(args.fileToSend)
	raw_input("Press ENTER to terminate.")
	server.terminate()
	server.join()



if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='A quick and dirty implmentation of latency based file storage using remote proxy hosts.')
	parser.add_argument('fileToSend', metavar='F', type=str, help='The file you would like to send.')
	parser.add_argument('-b', type=int, default=4096, help='The size of the blocks you want to split the file into.' )
	parser.add_argument('--hosts', type=str, default='hosts.txt', help='Specify a specfic file to draw remote bouncers from.  Default is hosts.txt')
	args = parser.parse_args()
	main()
