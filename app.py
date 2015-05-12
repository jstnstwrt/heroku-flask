import os
import time
from instagram.client import InstagramAPI
from flask import Flask, request, render_template, session, redirect, abort, flash, jsonify
import urllib, json
import re
import random

app = Flask(__name__)   # create our flask app
app.secret_key = os.environ.get('SECRET_KEY')






# configure Instagram API
instaConfig = {
	'client_id':os.environ.get('CLIENT_ID'),
	'client_secret':os.environ.get('CLIENT_SECRET'),
	'redirect_uri' : os.environ.get('REDIRECT_URI')
}
api = InstagramAPI(**instaConfig)





@app.route('/run_contest')
def run_contest():
# if instagram info is in session variables, then display user photos
	if 'instagram_access_token' in session and 'instagram_user' in session:
		api = InstagramAPI(access_token=session['instagram_access_token'])


		identifier = re.compile("We've teamed up with our friends")
		users_to_follow = 'knowlita, acme_nyc'
		user_list = users_to_follow.split(',')
		user_list = [x.strip(' ') for x in user_list]  
		
		uids = []
		for key_user in user_list:
			user_search = api.user_search(q=key_user)
			uids.append(user_search[0].id)

		media_ids = []
		for uid in uids:
			recent_media, next = api.user_recent_media( user_id=uid , count=30)
			for media in recent_media:
				if media.caption != None:
					if identifier.search(media.caption.text):
						media_ids.append(media.id)
					else:
						recent_media, next = api.user_recent_media( with_next_url = next)
						for media in recent_media:
							if media.caption != None:
								if identifier.search(media.caption.text):
									media_ids.append(media.id)

		

		media_ids = [media_ids[0],media_ids[2]]

		def find_insta_handles(text):
			p = re.compile('(?<=^|(?<=[^a-zA-Z0-9-_\.]))@([_A-Za-z]+[_A-Za-z0-9]+)')
			return p.findall(text)

		def tagged_users(comment):
			handles = find_insta_handles(comment)
			handles = [str(i) for i in handles]
			handles = [y for y in handles if y not in user_list]
			return handles


		valid_participants = []
		tagged = []
		ntp = []
		tp = []


		for img_id in media_ids:
			contest_comments = api.media_comments(media_id = img_id)
			for comment in contest_comments:
				if comment.user.username not in user_list:
					for user in tagged_users(comment.text):
						tagged.append(user)
						if len(tagged_users(comment.text)) >= 3 and comment.user.username not in user_list and comment.user.username not in valid_participants:
							valid_participants.append(comment.user.username)
							if comment.user.username in tagged:
								tp.append(comment.user.username)
							else:
								ntp.append(comment.user.username)

		
		## note that this measure is technically wrong, as the users could have overlapping followers
		tot_num_followers = 0			
		for key in user_list:
			key_search = api.user_search(q=key)
			key_basics = api.user(key_search[0].id)
			tot_num_followers += key_basics.counts['followed_by']



		num_tagged_participants = len(tp)
		num_untagged_participants = len(ntp)
		num_tagged_users = len(tagged)
		num_valid_participants = len(valid_participants)

		virality_coef = float(num_tagged_participants)/num_tagged_users
		contest_engagement = float(num_untagged_participants)/tot_num_followers




		templateData = {
			'media_ids' : media_ids,
			#'comments' : contest_comments,
			'valid_participants' : valid_participants,
			'tp' : tp,
			'ntp' : ntp,
			'tagged' : tagged,
			'num_untagged_participants' : str(num_untagged_participants),
			'num_tagged_participants' : str(num_tagged_participants),
			'num_valid_participants' : str(num_valid_participants),
			'num_tagged_users' : str(num_tagged_users),
			'num_followers' : str(tot_num_followers),
			'virality_coef' : str(round(virality_coef,4)),
			'contest_engagement' : str(round(contest_engagement,4)),

		}

		return render_template('run_contest.html', **templateData)
	else:
		return redirect('/connect')













@app.route('/test')
def acme_test():
# if instagram info is in session variables, then display user photos
	if 'instagram_access_token' in session and 'instagram_user' in session:
		api = InstagramAPI(access_token=session['instagram_access_token'])

		# recent_media, next = api.user_recent_media(user_id=922345846,count=30)
		# check = recent_media[0].location.point.latitude

		users_to_follow = 'knowlita, acme_nyc'
		user_list = users_to_follow.split(',')
		user_list = [x.strip(' ') for x in user_list]  
		
		uids = []
		for key_user in user_list:
			user_search = api.user_search(q=key_user)
			uids.append(user_search[0].id)

		contest_followers = []
		for uid in uids:
			followers, next = api.user_followed_by(user_id= uid)
			for follower in followers:
				contest_followers.append(follower.username)
			while next:
				followers, next = api.user_follows(with_next_url=next)
				for follower in followers:
					contest_followers.append(follower.username)


		contest_followers = list(set(contest_followers))

		## old hack way
		# acme_id = '922345846'
		# acme_followers, next = api.user_followed_by(user_id= acme_id)
		# acme_users = []
		# for user in acme_followers:
		# 	acme_users.append(user.username)

		# i = 0
		# while len(acme_users) < acme_basics.counts['followed_by']-50:
		# 	i += 1
		# 	response = urllib.urlopen(next)
		# 	data = json.loads(response.read())
		# 	for user in data['data']:
		# 		acme_users.append(user['username'])
		# 	next = data['pagination']['next_url']
		
		


		def is_follower(username):
			return (username in contest_followers)


		def find_insta_handles(text):
			p = re.compile('(?<=^|(?<=[^a-zA-Z0-9-_\.]))@([_A-Za-z]+[_A-Za-z0-9]+)')
			return p.findall(text)

		def tagged_users(comment):
			handles = find_insta_handles(comment)
			handles = [str(i) for i in handles]
			handles = [y for y in handles if y not in user_list]
			return handles



		knowlita_contest_img_id = '937178239574293509_922345846'
		acme_contest_img_id = '937173533246931090_28306327'

		contest_imgs = [knowlita_contest_img_id, acme_contest_img_id]
		valid_participants = []

		for img_id in contest_imgs:
			contest_comments = api.media_comments(media_id = img_id )
			for comment in contest_comments:
				if comment.user.username not in valid_participants and comment.user.username not in user_list:
					if len(tagged_users(comment.text)) >= 3 and is_follower(comment.user.username):
						valid_participants.append(comment.user.username)



		templateData = {

			'comments' : contest_comments,
			'participants' : valid_participants,
		}

		return render_template('test.html', **templateData)
	else:
		return redirect('/connect')




@app.route('/find_identifier')
def find_identifier():
# if instagram info is in session variables, then display user photos
	if 'instagram_access_token' in session and 'instagram_user' in session:
		api = InstagramAPI(access_token=session['instagram_access_token'])

		identifier = re.compile("We've teamed up with our friends")
		users_to_follow = 'knowlita, acme_nyc'
		user_list = users_to_follow.split(',')
		user_list = [x.strip(' ') for x in user_list]  
		
		uids = []
		for key_user in user_list:
			user_search = api.user_search(q=key_user)
			uids.append(user_search[0].id)

		media_ids = []
		for uid in uids:
			recent_media, next = api.user_recent_media( user_id=uid , count=30)
			for media in recent_media:
				if media.caption != None:
					if identifier.search(media.caption.text):
						media_ids.append((media.id, media.images['standard_resolution'].url))
					else:
						recent_media, next = api.user_recent_media( with_next_url = next)
						for media in recent_media:
							if media.caption != None:
								if identifier.search(media.caption.text):
									media_ids.append((media.id, media.images['standard_resolution'].url))

		
		templateData = {
			'media_ids' : media_ids,
			'uids' : uids
		}

		return render_template('find_identifier.html', **templateData)
	else:
		return redirect('/connect')







@app.route('/success_metrics')
def success_metrics():
# if instagram info is in session variables, then display user photos
	if 'instagram_access_token' in session and 'instagram_user' in session:
		api = InstagramAPI(access_token=session['instagram_access_token'])

		users_to_follow = 'knowlita, acme_nyc'
		user_list = users_to_follow.split(',')
		user_list = [x.strip(' ') for x in user_list]  
		
		


		def find_insta_handles(text):
			p = re.compile('(?<=^|(?<=[^a-zA-Z0-9-_\.]))@([_A-Za-z]+[_A-Za-z0-9]+)')
			return p.findall(text)

		def tagged_users(comment):
			handles = find_insta_handles(comment)
			handles = [str(i) for i in handles]
			handles = [y for y in handles if y not in user_list]
			return handles



		knowlita_contest_img_id = '937178239574293509_922345846'
		acme_contest_img_id = '937173533246931090_28306327'
		contest_imgs = [knowlita_contest_img_id, acme_contest_img_id]

		

		valid_participants = []
		tagged = []
		ntp = []
		tp = []

		for img_id in contest_imgs:
			contest_comments = api.media_comments(media_id = img_id)
			for comment in contest_comments:
				for user in tagged_users(comment.text):
					tagged.append(user)
				if len(tagged_users(comment.text)) >= 3:
					valid_participants.append(comment.user.username)
					if comment.user.username in tagged:
						tp.append(comment.user.username)
					else:
						ntp.append(comment.user.username)

		user_search = api.user_search(q='knowlita')
		knowlita = api.user(user_search[0].id)


		num_tagged_participants = len(tp)
		num_untagged_participants = len(ntp)
		num_tagged_users = len(tagged)
		num_valid_participants = len(valid_participants)
		num_followers = knowlita.counts['followed_by']

		virality_coef = float(num_tagged_participants)/num_tagged_users
		contest_engagement = float(num_untagged_participants)/num_followers




		templateData = {
			'valid_participants' : valid_participants,
			'tp' : tp,
			'ntp' : ntp,
			'num_untagged_participants' : str(num_untagged_participants),
			'num_tagged_participants' : str(num_tagged_participants),
			'num_valid_participants' : str(num_valid_participants),
			'num_tagged_users' : str(num_tagged_users),
			'num_followers' : str(num_followers),
			'virality_coef' : str(round(virality_coef,4)),
			'contest_engagement' : str(round(contest_engagement,4)),

		}

		return render_template('success_metrics.html', **templateData)
	else:
		return redirect('/connect')



































@app.route('/')
def user_photos():

	# if instagram info is in session variables, then display user photos
	if 'instagram_access_token' in session and 'instagram_user' in session:
		return 'hey'
	else:
		return redirect('/connect')


# Redirect users to Instagram for login
@app.route('/connect')
def main():

	url = api.get_authorize_url(scope=["likes","comments"])
	return redirect(url)

# Instagram will redirect users back to this route after successfully logging in
@app.route('/instagram_callback')
def instagram_callback():

	code = request.args.get('code')

	if code:

		access_token, user = api.exchange_code_for_access_token(code)
		if not access_token:
			return 'Could not get access token'

		app.logger.debug('got an access token')
		app.logger.debug(access_token)

		# Sessions are used to keep this data 
		session['instagram_access_token'] = access_token
		session['instagram_user'] = user

		return redirect('/') # redirect back to main page
		
	else:
		return "Uhoh no code provided"


	
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


# This is a jinja custom filter
@app.template_filter('strftime')
def _jinja2_filter_datetime(date, fmt=None):
    pyDate = time.strptime(date,'%a %b %d %H:%M:%S +0000 %Y') # convert instagram date string into python date/time
    return time.strftime('%Y-%m-%d %h:%M:%S', pyDate) # return the formatted date.
    
# --------- Server On ----------
# start the webserver
if __name__ == "__main__":
	app.debug = True
	
	port = int(os.environ.get('PORT', 5000)) # locally PORT 5000, Heroku will assign its own port
	app.run(host='0.0.0.0', port=port)
