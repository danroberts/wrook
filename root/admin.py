#!python
# coding=UTF-8


from google.appengine.ext import db
from google.appengine.api import memcache

from feathers import webapp, customize

class CommandResult(db.Model):
	ErrorCode = db.IntegerProperty(default="0") # 0 = no errors
	Message = db.TextProperty(default="")

class Command(db.Model):
	Title = db.StringProperty(default="")
	Description = db.TextProperty(default="")
	Code = db.TextProperty(default="")

class AdminCommands(webapp.RequestHandler):
	def get(self):
		onRequest(self)
#		if self.CurrentMember:
		self.render('views/admin-commands.html')
#		else: self.requestLogin()
	
	def post(self, key):
		onRequest(self)
#		if self.CurrentMember:
		if (key == "doDefaultAllBookStatus"):
			operationResults = self.doDefaultAllBookStatus()
		if (key == "doDefaultAllChapterNumberTo0"):
			operationResults = self.doDefaultAllChapterNumberTo0()
		if (key == "doLoadLicenseTypes"):
			operationResults = self.doLoadLicenseTypes()
		if (key == "doSetEncryptionKey"):
			operationResults = self.doSetEncryptionKey()
		else:
			operationResults = CommandResult(ErrorCode=1, Message=_("No commands have been processed. Missing parameters!"))
		self.Model.update({"operationResults": operationResults})
		self.render('views/admin-commands.html')
#		else: self.requestLogin()
	
	def doDefaultAllBookStatus(self):
		for book in Book.all():
			if book.Stage == "planning": book.Stage = "writing"
			for chapter in book.Chapters:
				if chapter.Stage == "planning": chapter.Stage = "writing"
				chapter.put()
			book.put()
		result = CommandResult(ErrorCode=0, Message=_("Empty status properties of all books and chapters have been defaulted!"))
		return result
	
	def doSetEncryptionKey(self):
		appConfig = getWrookAppConfig()
		appConfig.EncryptionKey = self.request.get("encryptionKey")
		appConfig.put()
		result = CommandResult(ErrorCode=0, Message=_("The new encryption key has been set!"))
		return result
	
	def doLoadLicenseTypes(self):
		import licensing
		licensing.LoadLicenseTypes()
		result = CommandResult(ErrorCode=0, Message=_("All license types have been loaded into the database!"))
		return result
	
	def doDefaultAllChapterNumberTo0(self):
		for chapter in Chapter.all():
			chapter.Number=0
			chapter.put()
		result = CommandResult(ErrorCode=0, Message=_("All chapter numbers have been reseted to 0!"))
		return result

class Test(webapp.RequestHandler):
	def get(self):
		import _runtest
		self.response.out.write(_runtest.getTestResults())

class set_default_theme(webapp.RequestHandler): 
	#TODO: Refactor -  Move back to the Customize module
	def get(self):
		import app
		onRequest(self)
		if self.CurrentMember:
			theme = customize.Theme.get(self.request.get("selectedTheme"))
			if theme and self.CurrentMember.isAdmin:
				db.delete(app.Moment.all().filter("isDefault =", True)) # Removes the current default moments
				moment = app.Moment(
					Title = "Default moment",
					Theme = theme,
					isDefault = True
					)
				moment.put()
				memcache.delete("wrookDefaultTheme") # Invalidates the cached default theme
				self.redirect("/Themes")
			else: self.error(500)
		else: self.requestLogin()


def URLMappings():
	return [
		( '/SetDefaultTheme', set_default_theme),
		( '/Admin/Commands', AdminCommands), # Refactor: move to an admin module?
		(r'/Admin/Commands/(.*)', AdminCommands), # Refactor: move to an admin module?
		( '/Test', Test)] # Refactor: move to an admin module?
