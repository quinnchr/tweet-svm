from django.db import models

class Servers(models.Model):
    server_id = models.BigIntegerField(primary_key=True)
    address = models.IPAddressField()
    class Meta:
        db_table = u'servers'

class Keywords(models.Model):
    keyword_id = models.BigIntegerField(primary_key=True)
    server_id = models.BigIntegerField()
    keyword = models.CharField(max_length=128)
    class Meta:
        db_table = u'keywords'

class Users(models.Model):
    user_id = models.BigIntegerField(primary_key=True)
    class Meta:
        db_table = u'users'

class UserKeywords(models.Model):
    id = models.BigIntegerField(primary_key=True)
    user = models.ForeignKey(Users)
    keyword = models.ForeignKey(Keywords)
    class Meta:
        db_table = u'user_keywords'



