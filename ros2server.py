# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify,make_response
import json
import time
import threading
import queue

from myscript import mycmd,db2po2
from myscript.orm import *

mycmd.CmdTask("mkdir temp && mkdir log && mkdir backup ").run()

import spdlog
logger = spdlog.FileLogger('calib_server', f"./log/calib_server_{time.strftime('%Y-%m-%d-%H:%M:%S')}.log", False,False)

app = Flask(__name__)
app.debug = False
emptyObj = {}
base_url = '/calib'

def create_table():
    Msgs.create_table()
    Calib.create_table()
    User.create_table()
    File.create_table()

create_table()

def make_reponse_header(data):
    """
    给返回头增加跨域
    """
    res = make_response(jsonify(data))
    res.headers['Access-Control-Allow-Origin'] = '*'
    res.headers['Access-Control-Allow-Method'] = '*'
    res.headers['Access-Control-Allow-Headers'] = '*'
    return res

command_queue = queue.Queue()
def gen_po():
    while True:
        if command_queue.qsize()>0:
            changes = []
            while command_queue.qsize()>0: 
                changes.append(command_queue.get())
            mycmd.CmdTask(f"cp data.db temp/data_temp.db").run()
            db2po2.genpo(changes,"/root/ros2/ros2cndep/ros2server/temp/po","/root/ros2/ros2cndep/ros2po/")
            time.sleep(10)
        else:
            time.sleep(1)
 

def auto_copy():
    # pass
    last_copy_time = time.time()
    while True:
        if time.time()-last_copy_time>3600*24:
            last_copy_time = time.time()
            mycmd.CmdTask(f"cp nav2.db backup/nav2{time.strftime('%Y-%m-%d-%H:%M:%S')}.db").run()
        else:
            time.sleep(10)

threading.Thread(target=gen_po).start()
threading.Thread(target=auto_copy).start()
    

# 获取指定msgid信息
@app.route(base_url+"/get_msg",methods=["post"])
def get_orimsg():
    ip = request.headers.getlist("X-Forwarded-For")[0]
    logger.info(f"[{ip}] {request.url} {request.data}")
    msgid = json.loads(request.data)["msgid"]
    msg = Msgs.select().where(Msgs.msgid == msgid)
    jsonData = {'msg':'查询失败', 'code': 404, 'data': []}
    if len(msg) > 0:
        jsonData = []
        for row in msg:
            result = {}
            result["msgid"] = row.msgid
            result["msgen"] = row.msgen
            result["msgzh"] = row.msgzh
            result["status"] = row.status
            result["update_time"] = row.update_time
            change_log = []
            logs = Calib.select(Calib,User.name,User.github).join(User, JOIN.LEFT_OUTER, on = (User.email == Calib.calibemail)).where(Calib.msgid==msgid).order_by(Calib.update_time.desc())
            for log in logs:
                temp = {}
                temp['update_time'] = log.update_time
                temp['contributor'] = log.user.name
                temp['github'] = log.user.github
                temp['update_time'] = str(log.update_time).replace("GMT","GMT+8")
                temp['operate'] = log.operate
                temp['calibmsg'] = log.calibmsg
                if log.operate.find("mark:no_translate")>-1:
                    temp['calibmsg'] = "将其标记为：无需翻译"
                if log.operate.find("mark:title")>-1:
                    temp['calibmsg'] = "将其标记为：标题"
                if log.operate.find("mark:no_calib")>-1:
                    temp['calibmsg'] = "将其标记为：无需校准"
                change_log.append(temp)
            result["change_log"] = change_log
            jsonData.append(result)
    return make_reponse_header({'msg':'处理成功', 'code': 200, 'data':jsonData})


# 校准指定 msgid 信息
@app.route(base_url+'/calib_msg', methods=["post"])
def calib_msg():
    ip = request.headers.getlist("X-Forwarded-For")[0]
    logger.info(f"[{ip}] {request.url} {request.data}")
    # 加载请求数据
    params = json.loads(request.data)
    msgid = params["msgid"]
    calibmsg = params["calibmsg"]
    name = params["name"]
    github = params["github"]
    email = params["email"]
    # 判断状态标记
    status = -1
    if 'status' in params: status = params['status']
    # 判断消息是否存在
    msg = Msgs.get(Msgs.msgid == msgid)
    result = {"msg": "msgid 不存在，请联系 fishros 官方维护者", "code": 404, "data": []}
    if msg is None: return make_reponse_header(result)

    msg_length = msg.length
    msg_status = msg.status
    msgen = msg.msgen

    if msg_status==status:
        if status==200:
            result = {"msg": "该段落已被标记为标题", "code": -1, "data": []}
        elif status==201:
            result = {"msg": "该段落已被标记为无需翻译", "code": -1, "data": []}
        elif status==202:
            result = {"msg": "该段落已被标记为无需校准", "code": -1, "data": []}
        else:
            result = {"msg": "该段落已被标记", "code": -1, "data": []}
        return make_reponse_header(result)
            
    if status==202 and msg_status!=0:  result = {"msg": "该段落已经被校准。只有没有被校准过的段落才能标记无需校准。", "code": -1, "data": []}

    # 用户是否存在
    calibcount  = 0
    # is_exis_user = Msgs.get(User.email == email) 
    is_exis_user = User.select().where(User.email == email)

    # User.select().where()
    if len(is_exis_user) == 0:
        User.create(email=email, name=name, github= github,calibcount= calibcount)
        # is_exis_user = Msgs.get(User.email == email) 
        
        is_exis_user = User.select().where(User.email == email)
    userid = is_exis_user[0].userid
    calibcount = is_exis_user[0].calibcount

    # 添加操作标记
    operate = ""
    if status==200: 
        operate = "mark:title"
        msg_status = 200
    elif status==201: 
        operate= "mark:no_translate"
        msg_status = 201
    elif status==202: 
        operate= "mark:no_calib"
        msg_status = 202
    else: 
        operate = f"update:{msgid}|{msg_length}"  
        if msg_status>=200: msg_status=1
        else: msg_status += 1

    # 插入并更新
    calib = Calib.insert(calibmsg= calibmsg, calibemail = email, msgid = msgid, operate=operate ).execute()
    if status!=-1:   Msgs.update({Msgs.calibid: calib, Msgs.status: msg_status}).where(Msgs.msgen == msgen).execute()
    else: Msgs.update({Msgs.msgzh: calibmsg, Msgs.calibid: calib, Msgs.status: msg_status}).where(Msgs.msgen == msgen).execute()
    # 更新用户名字和github账户和翻译数量
    User.update({User.name:name, User.github:github,User.calibcount: User.calibcount + msg_length}).where(User.userid == userid).execute()

    data = {
        "name": name,
        "calibcount": calibcount
    }
    #调用产生po文件
    command_queue.put_nowait((msgid,name,email,github,operate))
    return make_reponse_header({"msg": "添加翻译内容成功！", "code": 200, "data": data})



# 翻译排行
@app.route(base_url+'/calib_rank',methods=['post','get'])
def calib_rank():
    result = db.execute_sql("SELECT user.name,user.github,calibemail ,user.calibcount,count(calibemail) as count_result FROM 'calib ',user WHERE msgid>0 and user.email=='calib '.calibemail and calibemail is not NULL GROUP BY calibemail ORDER BY count_result DESC ")
    dic_rank = []
    for row in result:
        if len(row[0])>0 and len(row[1])>0:
            if row[2]!="fishros@foxmail.com":
                temp = {}
                temp['name']=row[0]
                temp['github']=row[1]
                temp['p_count']=row[4]
                temp['word_count']=row[3]
                dic_rank.append(temp)
    return make_reponse_header({
        "msg": "查询成功",
        "code": 200,
        "data": dic_rank
    })

def getData(res):
    jsonData = []
    data = {}
    data["msgid"] = res.msgid
    data["msgen"] = res.msgen
    data["msgzh"] = res.msgzh
    data["status"] = res.status
    data["update_time"] = res.update_time
    jsonData.append(data)
    return jsonData

# 下一条翻译
@app.route(base_url+'/next_msg',methods=['get'])
def next_msg():
    ip = request.headers.getlist("X-Forwarded-For")[0]

    return_dict = {'code': 200, 'msg': '处理成功', 'data': None}
    msgid = int(request.args.to_dict()['msgid'])
    logger.info(f"[{ip}] {request.url} {msgid}")

    result = Msgs.select().where((Msgs.msgid > msgid) & (Msgs.status == 0))

    if len(result) == 0:
        result1 = Msgs.select().where((Msgs.msgid > 0) & (Msgs.msgid < msgid) & (Msgs.status ==0))
        if len(result1) == 0:
            result2 = Msgs.select().order_by(Msgs.status.desc())[0]
            return_dict["data"] = getData(result2)
            return make_reponse_header(return_dict)
        else:
            return_dict["data"] = getData(result1[0])
            return make_reponse_header(return_dict)
    else: 
        return_dict["data"] = getData(result[0])
        return make_reponse_header(return_dict)

 
if __name__ == '__main__':
    from waitress import serve
    serve(app, host="0.0.0.0", port=2021)
    # app.run(host='0.0.0.0',port=2021)
