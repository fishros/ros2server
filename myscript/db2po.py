from myscript.ormgenpo import *
import time
import json


def get_files_list():
    files = {}
    file = File.select()
    for f in file:
        files[f.fileid] = {"path":f.path,"header":f.header}
    return files


def get_msgs_by_fileid(fileid):
    msgs_array = []
    msgs = Msgs.select().where(Msgs.fileid==fileid)
    for msg in msgs:
        calibs = Calib.select().where(Calib.calibid==msg.calibid)[0]

        user = User.select().where(User.email == calibs.calibemail)[0]
        if msg.status==0:
            user_qoute = f" `[待校准@{msg.msgid}] <http://localhost:3000/#/home?msgid={msg.msgid}>`_ "
        elif msg.status==200:
            user_qoute = f""
        else:
            user_qoute = f" `[{user.name}@{msg.msgid}] <http://localhost:3000/#/home?msgid={msg.msgid}>`_ "
        msg.msgzh += user_qoute
        # 无需翻译的状态201
        if msg.status==201: msg.msgzh = msg.msgen

        msgs_array.append([msg.position,msg.msgen,msg.msgzh,msg.calibid])
    return msgs_array


def gen_po(changes):
    files = get_files_list()
    for fileid in files.keys():
        msgs = get_msgs_by_fileid(fileid)
        msg_data = files[fileid]["header"]
        for msg in msgs:
            msg_data += f'\n{msg[0]}msgid "{msg[1]}"\nmsgstr "{msg[2]}"\n\n'
        with open("temp/po/"+files[fileid]["path"],"w",encoding='utf-8') as f:
            f.write(msg_data)

    with open("temp/po/README.md","w") as f:
        temp= {}
        temp['changes'] = []
        for i in range(len(changes)):
            msgid,name,email,github,operate = changes[i]
            temp['changes'].append({"msgid":msgid,"name":name,"email":email,"github":github,"operate":operate}) 
        temp['time'] = f"{time.strftime('%Y-%m-%d-%H:%M:%S')}"
        f.write(json.dumps(temp))
