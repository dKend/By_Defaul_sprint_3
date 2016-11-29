import webapp2
import os
import jinja2
import unittest 
import HTMLTestRunner
import time

import main

#from main import TEST_OUT
from question_system import *
from db_entities import *
from basehandler import BaseHandler
from strings import *
from google.appengine.ext import ndb
from google.appengine.ext.webapp import Request
from google.appengine.ext.webapp import Response
from StringIO import StringIO
from google.appengine.ext.ndb import Key

from webapp2_extras import sessions
from webapp2_extras.securecookie import SecureCookieSerializer


JINJA_ENVIRONMENT = jinja2.Environment(
		loader=jinja2.FileSystemLoader(os.path.dirname(__file__))
)

if len(User.query(User.username == 'admin').fetch()) == 0:
	u = User(
		username = 'admin',
		password = 'admin',
		firstname = 'test',
		lastname = 'test',
		email = 'test',
		accounttype ='admin'
	)
	u_key = u.unique_put()
else:
	u = User.query(User.username == 'admin').fetch()[0]
	u_key = u.key
	
if len(User.query(User.username == 'student').fetch()) == 0:
	s = User(
		username = 'student',
		password = 'student',
		firstname = 'student',
		lastname = 'student',
		email = 'student',
		accounttype ='student'
	)
	s_key = s.unique_put()
else:
	s = User.query(User.username == 'student').fetch()[0]
	s_key = s.key
	
if len(User.query(User.username == 'instructor').fetch()) == 0:
	i = User(
		username = 'instructor',
		password = 'instructor',
		firstname = 'instructor',
		lastname = 'instructor',
		email = 'instructor',
		accounttype ='instructor'
	)
	i_key = i.unique_put()
else:
	i = User.query(User.username == 'instructor').fetch()[0]
	i_key = i.key
	
c = Class(classname = 'TESTCLASS')
d = Class(classname = 'testclass2')
c.unique_put()
d.unique_put()
s = s_key.get()
u = u_key.get()
i = i_key.get()
s.reset_classlist()
u.reset_classlist()
i.reset_classlist()
u.add_class(c)
u.add_class(d)
s.add_class(c)
s.add_class(d)
i.add_class(c)
i.add_class(d)
i.put()
u.put()
s.put()
	
class QuestionTests(unittest.TestCase):
	student = User.query(User.username == 'student').fetch()[0]
	admin = User.query(User.username == 'instructor').fetch()[0]
	student_key = student.key
	admin_key = admin.key
	classy = Class.query(Class.classname == 'TESTCLASS').fetch()[0]
	class_key = classy.key
	q00 = Question(senderUID = student_key, classUID = class_key, message = 'What is the air speed velocity of a swallow?')
	q00_key = q00.put()
	q01 = Question(senderUID = student_key, classUID = class_key, message = 'What is your favorite color?')
	q01_key = q01.put()
	q02 = Question(senderUID = student_key, classUID = class_key, message = 'What is your quest?')
	q02_key = q02.put()
	def setup(self):
		return 0
	def tear(self):
		self.q00.respondentUID=None
		self.q00.response=None
		self.q00.put()
		
		self.q01.respondentUID=None
		self.q01.response=None
		self.q01.put()
		
		self.q02.respondentUID=None
		self.q02.response=None
		self.q02.put()
		
		categories = Category.query(ancestor=self.class_key).fetch()
		for c in categories:
			c.key.delete()
	def test_instructor_can_respond(self):
		self.setup()
		qkey = self.q00_key
		respond = ResponseHandler()
		session = {
			'account': self.admin.username,
			'accounttypr': ADMIN,
			'class': self.classy.classname,
			'question_key': qkey.urlsafe(),
		}
		secure_cookie_serializer = SecureCookieSerializer(SECRET_KEY)
		serialized = secure_cookie_serializer.serialize('session', session)
		headers = {'Cookie':'session=%s' % serialized}
		
		respond.request = Request.blank('/respond?response=test')
		respond.request.method='POST'
		#respond.request.body = 'response=test'
		respond.request.headers=headers
		#print '\n'+respond.request.get('message')+'\n'
		
		self.assertTrue(respond.request.get('response') == 'test')
		
		response = respond.request.get_response(main.app)
		#message = response.get('message')
		question = qkey.get()
		self.assertFalse(question == None)
		self.assertFalse(question.respondentUID == None)
		self.assertFalse(question.response == None)
		self.assertFalse(question.response == '')
		self.assertTrue(question.respondentUID == self.admin.key)
		self.assertTrue(question.response == 'test')
		#del respond
		self.tear()
	def test_instructor_can_create_new_category(self):
		self.setup()
		qkey = self.q00_key
		respond = ResponseHandler()
		session = {
			'account': self.admin.username,
			'accounttypr': ADMIN,
			'class': self.classy.classname,
			'question_key': qkey.urlsafe(),
		}
		secure_cookie_serializer = SecureCookieSerializer(SECRET_KEY)
		serialized = secure_cookie_serializer.serialize('session', session)
		headers = {'Cookie':'session=%s' % serialized}
		respond.request = Request.blank('/respond?response=test&cname=test_category')
		respond.request.method='POST'
		respond.request.headers=headers
		
		#ensure that the vars were passed to test properly
		self.assertTrue(respond.request.get('response') == 'test')
		self.assertTrue(respond.request.get('cname') == 'test_category')
		
		self.assertTrue(len(Category.query(Category.name=='test_category').fetch())==0) #category doesnt exist yet
		
		response = respond.request.get_response(main.app)
		
		time.sleep(2)
		category = Category.query(Category.name == 'test_category').fetch()
		
		self.assertTrue(len(category)==1) #was created and is unique, also has the correct name
		category = category[0]
		self.assertTrue(category.key.parent() == self.classy.key)
		category.key.delete()
		
		#del respond
		self.tear()
	def test_instructor_can_set_category_to_answer(self):
		self.setup()
		
		qkey = self.q00_key
		
		respond = ResponseHandler()
		session = {
			'account': self.admin.username,
			'accounttypr': ADMIN,
			'class': self.classy.classname,
			'question_key': qkey.urlsafe(),
		}
		secure_cookie_serializer = SecureCookieSerializer(SECRET_KEY)
		serialized = secure_cookie_serializer.serialize('session', session)
		headers = {'Cookie':'session=%s' % serialized}
		respond.request = Request.blank('/respond?response=test&cname=test_category')
		respond.request.method='POST'
		respond.request.headers=headers
		
		#ensure that the vars were passed to test properly
		self.assertTrue(respond.request.get('response') == 'test')
		self.assertTrue(respond.request.get('cname') == 'test_category')
		
		response = respond.request.get_response(main.app)
		
		time.sleep(2)
		question = qkey.get()
		cate = Category.query(Category.name == 'test_category').fetch()
		self.assertTrue(len(cate)==1) #was created/found and is unique, also has the correct name
		cate = cate[0]
		self.assertTrue(question.category == cate.key)
		question.key.delete()
		cate.key.delete()
		#del respond
		self.tear()
	def test_instructor_can_respond_with_faq(self):
		self.setup()
		
		qkey = self.q00_key
		
		respond = ResponseHandler()
		session = {
			'account': self.admin.username,
			'accounttypr': ADMIN,
			'class': self.classy.classname,
			'question_key': qkey.urlsafe(),
		}
		secure_cookie_serializer = SecureCookieSerializer(SECRET_KEY)
		serialized = secure_cookie_serializer.serialize('session', session)
		headers = {'Cookie':'session=%s' % serialized}
		respond.request = Request.blank('/respond?response=test&infaq=infaq')
		respond.request.method='POST'
		respond.request.headers=headers
		
		self.assertTrue(respond.request.get('response') == 'test')
		self.assertTrue(respond.request.get('infaq') == 'infaq')
		
		response = respond.request.get_response(main.app)
		
		time.sleep(2)
		
		question = qkey.get()
		self.assertTrue(question.response == R_INFAQ)
		
		self.tear()
	def test_questions_in_FAQ_have_category(self):
		self.setup()
		#create a category and put it to the DB
		cate = Category(name="test category 00", parent=self.classy.key)
		cate.put()
		
		time.sleep(2)
		
		#update the category of q00
		self.q00.category = cate.key
		self.q00.put()
		
		time.sleep(2)
		
		#get all of the questions in the FAQ of classy
		#	ie. all of the questions with a classUID of classy's key
		#	and who have any category
		#	faq is a list
		faq = self.classy.FAQ
		
		self.assertTrue(faq!=None)
		self.assertTrue(len(faq)==1)
		self.assertTrue(faq[0].key == self.q00_key)
		
		cate.key.delete()
		self.tear()
	def test_questions_not_in_FAQ_have_no_category(self):
		self.setup()
		#create a category and put it to the DB
		cate = Category(name="test category 01", parent=self.classy.key)
		cate.put()
		
		time.sleep(2)
		
		#update the category of q00
		self.q00.category = cate.key
		self.q00.put()
		
		time.sleep(2)
		
		#questions not in the FAQ will NOT have their category field set
		all_questions = Question.query().fetch()
		not_faq = Question.query(Question.category==None).fetch()
		faq = self.classy.FAQ
		
		for q in faq:
			self.assertTrue(q.category!=None)
			self.assertFalse(q in not_faq)
			self.assertTrue(q in all_questions)
		
		for q in not_faq:
			self.assertTrue(q.category==None)
			self.assertFalse(q in faq)
			self.assertTrue(q in all_questions)
		
		cate.key.delete()
		self.tear()
	def test_unanswered_questions_have_no_category(self):
		self.setup()
		questions = [None]*100
		for i in range(100):
			questions[i] = Question(senderUID = self.student.key, classUID = self.classy.key, message = 'This is an unanswered question?').put()
			
		time.sleep(2)
		for q in questions:
			self.assertTrue(q.get().category==None)
			q.delete()
		
		self.tear()
	def test_question_submit_student(self):
		self.setup()
		
		key00 = self.q00_key
		key01 = self.q01_key
		key02 = self.q02_key
		
		self.assertTrue(key00 != None)
		self.assertTrue(key01 != None)
		self.assertTrue(key02 != None)
		self.assertTrue(key02 != key00)
		self.assertTrue(key00 == self.q00.key)
		self.assertTrue(key01 == self.q01.key)
		self.assertTrue(key02 == self.q02.key)
		
		q00 = key00.get()
		q01 = key01.get()
		q02 = key02.get()
		
		self.assertTrue(q00.message == self.q00.message)
		self.assertTrue(q00.senderUID == self.q00.senderUID)
		self.assertTrue(q00.classUID == self.q00.classUID)
		self.assertTrue(q00.response == None)
		
		self.assertTrue(q01.message == self.q01.message)
		self.assertTrue(q01.senderUID == self.q01.senderUID)
		self.assertTrue(q01.classUID == self.q01.classUID)
		self.assertTrue(q01.response == None)
		
		self.assertTrue(q02.message == self.q02.message)
		self.assertTrue(q02.senderUID == self.q02.senderUID)
		self.assertTrue(q02.classUID == self.q02.classUID)
		self.assertTrue(q02.response == None)
		
		self.tear()
	"""
	def test_validate_user(self):
		self.assertTrue(False)
	"""
	def destroy_self(self):
		self.q00_key.delete()
		self.q01_key.delete()
		self.q02_key.delete()
	def test_student_can_enter_a_code_to_join_class(self):
		self.assertTrue(False)
	def test_incorrect_code_gives_error(self):
		self.assertTrue(False)
	def test_students_can_edit_account_info(self):
		self.assertTrue(False)
	def test_instructor_can_create_student_accounts(self):
		self.assertTrue(False)
	def test_instructor_can_edit_FAW(self):
		self.assertTrue(False)
	def test_student_can_view_FAQ(self):
		self.assertTrue(False)
	def test_else_can_view_FAQ(self):
		self.assertTrue(False)
	def test_student_can_view_their_prev_questiosn(self):
		self.assertTrue(False)
	def test_instructor_can_view_their_prev_questions(self):
		self.assertTrue(False)
	def test_admin_can_create_instructor(self):
		self.assertTrue(False)
	def test_admin_can_create_student(self):
		self.assertTrue(False)
	def test_instructor_can_batch_create_student_accounts(self):
		self.assertTrue(False)
	def test_datastore_key(self):
		cate = Category(name='test')
		self.assertTrue(cate.key == None)
		cate_key = cate.put()
		self.assertTrue(cate.key == cate_key)
		self.assertTrue(cate.key != None)
		cate_key.delete()
	
class FakeFile():
	data = ''
	def write(self, str):
		self.data = self.data+str
	
suite = unittest.TestLoader().loadTestsFromTestCase(QuestionTests)
#outfile = ''#open(os.path.join(os.path.dirname(__file__), 'test_output.html'), 'w')
#unittest.TextTestRunner(verbosity=2).run(suite)
runner = HTMLTestRunner.HTMLTestRunner(
	stream=FakeFile(),
	title='Test Results',
	description='Test output for question_system.'
)

