from flask import Flask, abort, request
import requests
import random
import sys
import threading
import time
app = Flask(__name__)

#other remote bouncers
hosts = ['127.0.0.1:8888','127.0.0.1:8889']
toReadBack={}

@app.route('/read', methods=['POST'])
def read():
	def nextbounce(json):
		time.sleep(1)
		requests.post("http://%s/read"%random.choice(hosts), json=json)
		return
	json = request.json
	if not json:
		return abort(400)
	if json['firstHop'] == 'true':
		toReadBack[json['filename']] = request.remote_addr
		json['firstHop'] = 'false'
		json['host'] = request.remote_addr
		for host in hosts:
			t = threading.Thread(target=nextbounce, args=(json, ))
			t.start()
	else:
		toReadBack[json['filename']] = json['host']
	return 'ok'

@app.route('/', methods=['POST'])
def bounce():
	def nextbounce(json):
		time.sleep(1)
		requests.post("http://%s"%random.choice(hosts), json=json)
		return
	if not request.json:
		return abort(400)
	filename = request.json['filename']	
	# print(request.json)
	if filename in toReadBack.iterkeys():
		# print(toReadBack[filename])
		t = threading.Thread(target = lambda x, y: requests.post(x, json=y), args=("http://%s/"%toReadBack[filename], request.json))
		t.start()
	else:
		t = threading.Thread(target=nextbounce, args=(request.json, ))
		t.start()
	return 'ok'

@app.route('/fileRead', methods=['POST'])
def finishedRead():
	global toReadBack
	if not request.json:
		return abort(400)
	filename = request.json['filename']
	# print(toReadBack.iterkeys)
	# print(filename)
	if filename in toReadBack.iterkeys():
		print(filename)
		del toReadBack[filename]
	return 'ok'


#you will need to supply the port number you want this to run on as an argument. 
if __name__ == "__main__":
	app.run(port=int(sys.argv[1]), host="0.0.0.0", debug=False)
