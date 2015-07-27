import os
import urllib

# module for user google account
from google.appengine.api import users
# wrapping data in objects equipped for datastore
from google.appengine.ext import ndb

import webapp2
import jinja2


template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
								autoescape=True)


# create datastore object classes to model data:
#   user/author info; details about the post data (content)
class Author(ndb.Model):
	"""Sub model for representing an author."""
	# we do not need to index these properties as
	# we will not query an 'Author' entity. instead
	# an object of this class is encapsulated in 'Greeting' class
	# as an attribute, so querying the 'post' entity will provide access.
	identity = ndb.StringProperty(indexed=False)
	name = ndb.StringProperty(indexed=False)
	email = ndb.StringProperty(indexed=False)

class Post(ndb.Model):
	author = ndb.StructuredProperty(Author)
	content = ndb.StringProperty(indexed=False)
	# we will only need to query by date of entity creation
	date = ndb.DateTimeProperty(auto_now_add=True)


# Constructs a Datastore key for a guestbook entity
# ancestor key to group all entities (posts) for querying
# args are kind;identifier pairs
ANCESTOR_KEY = ndb.Key('Wallbook', 'Public')

class Handler(webapp2.RequestHandler):
	"""comment"""
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		# a template object calling IT'S method render. This render method
		# accepts a dictionary of values to substitute
		return t.render(params) 

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))


class MainPage(Handler):
	def get(self):	
		# [START QUERY]
		# to query the datastore. classname(of entity).query(args)
		post_queries = Post.query(ancestor=ANCESTOR_KEY).order(-Post.date)
		#
		posts = post_queries.fetch(3)
		# [END QUERY]

		# check if user is signed in with google so we can personalise
		user = users.get_current_user()
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
			user_name = user.nickname()
		else:
			url = users.create_login_url(self.request.uri)
			url_linktext = 'Login'
			user_name = 'Anonymous'

		# user may have been sent packing (redirected) with a message
		error_msg = self.request.get("error_msg")
		if not error_msg:
			error_msg = ""
		
		template_values = {
						"posts": posts,
						"url": url,
						"url_linktext": url_linktext,
						"user_name": user_name,
						"error_msg": error_msg
						}

		self.render("wallbook.html", **template_values)


class Greeting(Handler):
	def post(self):
		# grab content user has posted ready for testing and then saving
		msg = self.request.get("message")

		# if input is valid..
			# [ input is verified by checking for empty str and max len.
			# jinja handles syntax conflict]
		max_length = 82
		if msg and 0 < len(msg) <= max_length:

			# create post entity to save in datastore
			post = Post(parent=ANCESTOR_KEY)

			# check whether user is logged into google to save details to post entity
			if users.get_current_user():
				post.author = Author(
					identity=users.get_current_user().user_id(),
					name=users.get_current_user().nickname(),
					email=users.get_current_user().email())
			else:
				post.author = Author(
					name='anonymous',
					email='anonymous@anonymous.com')
			

			# store content from user in entity
			post.content = msg
			# store entity in datastore
			post.put() # it's that easy!

			# send user to our main page which will re-render and show their message
			self.redirect('/')

		# if input is invalid..
		else:
			error_msg = """Sorry, your message must be between 1 and 82 characters long.
						"""
			self.redirect('/?' + urllib.urlencode( {'error_msg':error_msg} ))


app = webapp2.WSGIApplication([('/', MainPage),
								('/sign', Greeting)
								], debug=True)