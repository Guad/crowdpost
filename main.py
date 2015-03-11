import flask
import requests
import re

from string import ascii_lowercase
from random import choice
from threading import Timer

app = flask.Flask(__name__) 

# Globals
criminalList = []
shotDownCriminals = []

interjection = r"""
I'd just like to interject for moment. What you're refering to as Linux, is in fact, GNU/Linux, or as I've recently taken to calling it, GNU plus Linux. Linux is not an operating system unto itself, but rather another free component of a fully functioning GNU system made useful by the GNU corelibs, shell utilities and vital system components comprising a full OS as defined by POSIX.

Many computer users run a modified version of the GNU system every day, without realizing it. Through a peculiar turn of events, the version of GNU which is widely used today is often called Linux, and many of its users are not aware that it is basically the GNU system, developed by the GNU Project.

There really is a Linux, and these people are using it, but it is just a part of the system they use. Linux is the kernel: the program in the system that allocates the machine's resources to the other programs that you run. The kernel is an essential part of an operating system, but useless by itself; it can only function in the context of a complete operating system. Linux is normally used in combination with the GNU operating system: the whole system is basically GNU with Linux added, or GNU/Linux. All the so-called Linux distributions are really distributions of GNU/Linux!
"""
#

@app.route('/', methods=['GET', 'POST'])
def index():
    if flask.request.method == 'POST':
    		arrestCriminal(flask.request.form['g-recaptcha-response'])
		return flask.redirect(flask.url_for('index')) 
    else:
    	if not criminalList:
        	return flask.render_template('index.html', unavailable=True)
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

def updateCriminalPosts():
	global criminalList
	global shotDownCriminals
	tempPosts = scanBoardForPosts('g')
	for post in tempPosts:
		if not post in criminalList and not post in shotDownCriminals:
			criminalList.append(post)
	print 'Criminals updated.'
	Timer(1800, updateCriminalPosts, ()).start()
Timer(3, updateCriminalPosts, ()).start()

def arrestCriminal(captcha):
	global criminalList
	global shotDownCriminals
	try:
		ourCriminal = criminalList[0]
	except KeyError:
		return False
	criminalList.pop(0)
	post = '>>%s' % str(post['id'])
	post += '\n'
	post += interjection
	createPost('g', ourCriminal['op'], post, captcha)
	shotDownCriminals.append(ourCriminal)
	print 'Criminal %s in thread %s has been arrested!' % (post['id'], post['op'])

if __name__ == '__main__':
    #app.debug = True
    app.run(port=8080, host='0.0.0.0') 