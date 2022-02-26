#  -*- coding:utf8 -*-
 
from peewee import *
from datetime import datetime

db = SqliteDatabase('temp/data_temp.db')

class BaseModel(Model):
    create_time = DateTimeField(default=datetime.now, verbose_name='创建时间')  # 记录的创建时间
    update_time = DateTimeField(default=datetime.now, verbose_name='更新时间')  # 记录的更新时间

    def save(self, *args, **kwargs):
        self.modified = datetime.now()
        return super(BaseModel, self).save(*args, **kwargs)

    class Meta:
        database = db
 
class Msgs(BaseModel):
    msgid      = PrimaryKeyField()
    # hashid  = BigIntegerField()
    fileid   = IntegerField()
    position   = CharField()
    msgen      = CharField(index=True)
    msgzh      = CharField()
    length    = IntegerField()
    status    = IntegerField()
    calibid   = IntegerField()
    # 版本代号
    version = CharField()

    class Meta:
        order_by = ('fileid',)
        db_table = 'msgs'
    
class Calib(BaseModel):
    calibid  = PrimaryKeyField()
    calibmsg  = CharField()
    calibemail  = CharField()
    # 校准的消息id
    msgid  = IntegerField()
    # 对消息的操作 更新/标记/还是做了啥
    operate = CharField()
    # updatetime = TimeField()
    class Meta:
        order_by = ('calibid',)
        db_table = 'calib '
            
class User(BaseModel):
    userid    = PrimaryKeyField()
    calibcount  = IntegerField()
    email      = CharField()
    name       = CharField()
    github     = CharField()
    # updatetime= TimeField()

    class Meta:
        order_by = ('userid',)
        db_table = 'user'

class File(BaseModel):
    fileid    = PrimaryKeyField()
    filename    = CharField()
    path        = CharField()
    header      = CharField()
    # updatetime= TimeField()

    class Meta:
        order_by = ('fileid',)
        db_table = 'file'
