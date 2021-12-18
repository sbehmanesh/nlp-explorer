from django.db import connection, models

class Festival(models.Model):
    title = models.CharField(max_length=256,blank=True,db_index=True)
    address = models.CharField(max_length=512,blank=True,db_index=True)
    date = models.CharField(max_length=128,blank=True,db_index=True)
    lat = models.CharField(max_length=16,blank=True)
    long = models.CharField(max_length=16,blank=True)
    link = models.CharField(max_length=128,blank=True)
    type = models.CharField(max_length=32,blank=True)


class Features(models.Model):
    word = models.CharField(max_length=256,blank=True,db_index=True)
    type = models.CharField(max_length=32,blank=True,db_index=True)

