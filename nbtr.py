import argparse
import base64
import requests
import random
from multiprocessing import Process
from flask import Flask, request
import os
import time
import threading

#the remote bouncers that you want to hit
remoteHosts = []
app = Flask(__name__)
@app.route('/', methods=['POST'])
def receive():
	def writePart(fileName, buffer, offset):
		with open(fileName,'r+b') as fp:
			fp.seek(int(offset))
			fp.write(buffer)
			fp.flush()
	if not request.json:
		return abort(400)
	else:
		print(request.json[u'index'])
		t = threading.Thread(target=writePart, args=(request.json[u'filename'], base64.b64decode(request.json[u'data']), request.json[u'index']))
		t.start()
		return 'ok'

def splitupFile(filename, blockSize):
	with open(filename, 'r+b') as fp:
		for count, filePart in enumerate(iter(lambda: fp.read(blockSize), '')):
			filePart = base64.b64encode(filePart)
			yield (count*blockSize, filePart)

def write(filename, blockSize=4096):
	data = {}
	print('Sending file')
	global maxParts
	for offset, part in splitupFile(filename, blockSize):
		data = {'filename':filename, 'index':offset, 'data':part}
		randomHost = random.choice(remoteHosts)
		r = requests.post('http://%s' % randomHost, json=data)
		print('Part %d sent to %s' % (offset, randomHost))
	print('Sending finished')

def read(filename):
	randomHost = random.choice(remoteHosts)
	data = {'filename':filename, 'firstHop':'true'}
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
		if args.hosts.strip() != 'hosts.txt':
	 		print('File "%s" not found.' % args.hosts)
	 	else:
	 		print('File "hosts.txt" not found, perhaps you forgot to use the --hosts flag?')
	 	return

	server = Process(target=app.run, args=('0.0.0.0', 80, False))
	server.start()
	write(args.fileToSend, args.b)
	raw_input('Press Enter to read...')
	read(args.fileToSend)
	raw_input('Press Enter to exit...')
	server.terminate()
	server.join()



if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='A quick and dirty implmentation of latency based file storage using remote proxy hosts.')
	parser.add_argument('fileToSend', metavar='F', type=str, help='The file you would like to send.')
	parser.add_argument('-b', type=int, default=4096, help='The size of the blocks you want to split the file into.' )
	parser.add_argument('--hosts', type=str, default='hosts.txt', help='Specify a specfic file to draw remote bouncers from.  Default is hosts.txt')
	args = parser.parse_args()
	main()
