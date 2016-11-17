from flask import Flask, abort, request
import requests
import random
import sys
import threading
import time
app = Flask(__name__)

#other remote bouncers
hosts = ['192.168.0.254:8888','192.168.0.254:8889']
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
	toReadBack[json['filename']] = json['host']
	if json['firstHop'] == 'true':
		json['firstHop'] = 'false'
		for host in hosts:
			t = threading.Thread(target=nextbounce, args=(json, ))
			t.start()
	return 'ok'

@app.route('/', methods=['POST'])
def bounce():
	def nextbounce(json):
		time.sleep(1)
		requests.post("http://%s"%random.choice(hosts), json=json)
		return
	if not request.json:
		return abort(400)
	if request.json['filename'] in toReadBack.iterkeys():
		requests.post("http://%s"%toReadBack[request.json['filename']], json=request.json)
	else:
		t = threading.Thread(target=nextbounce, args=(request.json, ))
		t.start()
	return 'ok'

#you will need to supply the port number you want this to run on as an argument. 
if __name__ == "__main__":
	app.run(port=int(sys.argv[1]), host="0.0.0.0", debug=False)