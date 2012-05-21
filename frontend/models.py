from django.db import models
from django.contrib.auth.models import User, UserManager

class Server(models.Model):
	address = models.IPAddressField()
	class Meta:
		db_table = u'servers'

class ApiUser(User):
	server = models.ForeignKey(Server)
	api_key = models.CharField(max_length=128)
	api_secret = models.CharField(max_length=128)
	objects = UserManager()
	class Meta:
		db_table = u'api_users'

class Stream(models.Model):
	user = models.ForeignKey(ApiUser)
	name = models.CharField(max_length=128)
	class Meta:
		db_table = u'streams'

class Source(models.Model):
	stream = models.ForeignKey(Stream)
	name = models.CharField(max_length=128)
	keyword = models.CharField(max_length=128)
	class Meta:
		db_table = u'sources'

