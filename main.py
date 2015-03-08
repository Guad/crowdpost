import flask
import requests

from string import ascii_lowercase
from random import choice

app = flask.Flask(__name__) 


@app.route('/', methods=['GET', 'POST'])
def index():
    if flask.request.method == 'POST':
    	if flask.request.form['g-recaptcha-response']:
    		createPost(
    					'g',
    					flask.request.form['thread'],
    					flask.request.form['comment'],
    					str(flask.request.form['g-recaptcha-response'])
    				  )
    		print 'Post successful?'
        return flask.redirect(flask.url_for('index')) 
    else:
        return flask.render_template('index.html')

def getRandomPassword(length):
	alphanumeric = ascii_lowercase
	alphanumeric += choice.upper()
	alphanumeric += '0123456789'
	output = ''
	for n in range(length):
		output += choice(alphanumeric)
	return output

def createPost(board, threadid, message, captcha, debug=False):
	url = 'https://sys.4chan.org/%s/post'  % board
	form = {
		'MAX_FILE_SIZE':'4194304',
		'pwd': getRandomPassword(33),
		'mode':'regist',
		'resto':threadid,
		'email':'',
		'upfile':'',
		'name':'Anonymous',
		'com':'%s' % message,
		'g-recaptcha-response': str(captcha)
	}


	req = requests.post(url, data=form)
	if debug:
		print '[REQUEST DEBUG] STATUS CODE: ', str(req.status_code)
		print '[REQUEST DEBUG] HEADERS: ', str(req.headers)
		with open('debug.html', 'w') as file:
			file.write(req.text)

if __name__ == '__main__':
    #app.debug = True
    app.run(port=8080, host='0.0.0.0') 