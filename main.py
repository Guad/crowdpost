import requests
import flask
import re

from string import ascii_lowercase, ascii_uppercase
from threading import Timer
from waitress import serve
from random import choice
from os import environ

app = flask.Flask(__name__) 

# Globals
criminalList = []
shotDownCriminals = []
updateInProgress = False
interjection = r"""
I'd jus[code][/code]t like to inte[code][/code]rject for moment. What you're refer[code][/code]ing to as Linux, is in fact, GNU/[code][/code]Linux, or as I've recently taken to call[code][/code]ing it, GNU pl[code][/code]us Linux. Linux is not an operating system unto itself, but rather another free component of a fully functioning GNU system made useful by the GNU corelibs, shell util[code][/code]ities and vital system components comprising a full OS as defined by POSIX.

Ma[code][/code]ny comput[code][/code]er users run a modified version of the GN[code][/code]U system ev[code][/code]ery day, without realizing it. Through a peculiar turn of events, the version of GNU which is widely used today is often called Linux, and many of its users are not aware that it is basically the GNU system, developed by the GNU Project.

There rea[code][/code]lly is a Linux, and these peop[code][/code]le are using it, but it is just a part of the system they use. Linux is the kernel: the program in the system that allocates the machine's resources to the other programs that you run. The kernel is an essential part of an operating system, but useless by itself; it can only function in the context of a complete operating system. Linux is normally used in combination with the GNU operating system: the whole system is basically GNU with Linux added, or GNU/Linux. All the so-called Linux distributions are really distributions of GNU/Linux!
"""
# Note that the code tags are used to avoid spam detection.

@app.route('/', methods=['GET', 'POST'])
def index():
    if flask.request.method == 'POST':
    		arrestCriminal(flask.request.form['g-recaptcha-response'])
		return flask.redirect(flask.url_for('index')) 
    else:
    	lastFive = shotDownCriminals[:-6:-1]
    	if not criminalList: # The criminal list is empty, gotta update it.
    		if not updateInProgress:
    			Timer(0, updateCriminalPosts, ()).start()
        	return flask.render_template('index.html', unavailable=True, interjections=lastFive)
        else:
        	return flask.render_template('index.html', interjections=lastFive)

def getRandomPassword(length):
	alphanumeric = ascii_lowercase
	alphanumeric += ascii_uppercase
	alphanumeric += '0123456789'
	output = ''
	for n in range(length):
		output += choice(alphanumeric)
	return output

def validatePost(post):
	post = flask.Markup(post).striptags()
	linuxRule = re.compile(r'(/|\\|\+)?L(u|i|o+)n(u|i)x', re.IGNORECASE)
	gnuRule = re.compile(r'gnu', re.IGNORECASE)
	if(linuxRule.search(post) and not gnuRule.search(post)): # Incorrect use spotted
		return True
	else:
		return False

def scanBoardForPosts(board):
	detectedPosts = []
	threads = []
	# 1. Get all threads
	# 2. Loop through all threads scanning for posts
	# 3. Return a dictionary with all detected posts

	boardApiURL = 'http://a.4cdn.org/%s/threads.json' % board
	boardRequest = requests.get(boardApiURL)
	mainJSON = boardRequest.json()
	# First is a list []
	# Inside the list there are dicts {}
	# In the dics are stored the page and a list
	# named threads
	# Inside that list there are multiple dicts with 
	# the thread information
	# [{[{}]}]

	for page in mainJSON: # 1. Get all thread ids from the board
		for thread in page['threads']:
			threads.append(thread['no'])
	
	for thread in threads: # 2. Loop through the threads to get the posts
		threadApiURL = 'http://a.4cdn.org/%s/thread/%s.json' % (board, thread)
		threadRequest = requests.get(threadApiURL)
		threadJSON = threadRequest.json()
		for post in threadJSON['posts']:
			try:
				if validatePost(post['com']):
					detectedPosts.append({
												'op':thread,
												'id':post['no'],
												'com':flask.Markup(post['com']).striptags()
												})
			except KeyError: # Comment-less post, just a picture.
				pass
	return detectedPosts

def createPost(board, threadid, message, captcha):
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
	if app.debug:
		print '[REQUEST DEBUG] STATUS CODE: ', str(req.status_code)
		print '[REQUEST DEBUG] HEADERS: ', str(req.headers)
		with open('debug.html', 'w') as file:
			file.write(req.text)

def updateCriminalPosts():
	global criminalList
	global shotDownCriminals
	global updateInProgress
	updateInProgress = True
	tempPosts = scanBoardForPosts('g')
	for post in tempPosts:
		if not post in criminalList and not post in shotDownCriminals:
			criminalList.append(post)
	print 'Criminals updated.'
	updateInProgress = False

def arrestCriminal(captcha):
	global criminalList
	global shotDownCriminals
	try:
		ourCriminal = criminalList[0]
	except KeyError:
		return False
	criminalList.pop(0)
	post = '>>%s' % str(ourCriminal['id'])
	post += '\n'
	post += interjection
	createPost('g', ourCriminal['op'], post, captcha)
	shotDownCriminals.append(ourCriminal)
	print 'Criminal %s in thread %s has been arrested!' % (ourCriminal['id'], ourCriminal['op'])

if __name__ == '__main__':
    #app.debug = True
    #app.run(port=8080, host='0.0.0.0', use_reloader=False) 
	serve(app, port=int(environ['PORT']))