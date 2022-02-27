import time
import json
from playhouse.shortcuts import model_to_dict, dict_to_model
from myscript.ormgenpo import *
from myscript import mycmd


def update_repo(popath,branch="foxy",path="../ros2po/"):
    """
    更新github仓库
    """
    mycmd.CmdTask(f"git reset --hard && git checkout {branch}",cwd=path).run()
    mycmd.CmdTask(f"cp {popath}/* {path}").run()
    mycmd.CmdTask(f'git config --local user.name "小鱼"',cwd=path).run()
    mycmd.CmdTask(f'git config --local user.email "sangxin2014@sina.com"',cwd=path).run()
    mycmd.CmdTask(f'git add . && git commit -m "{time.strftime("%Y-%m-%d-%H:%M:%S")}"',cwd=path).run()
    mycmd.CmdTask(f"git push origin {branch}",cwd=path).run()


def transzh_by_status(msgid,msgen,msgzh,status,name):
    host  = "http://localhost:3000/#/home?msgid="
    if status==201: return msgen
    if status==0:
        user_qoute = f" `[待校准@{msgid}] <{host}{msgid}>`_ "
    elif status==200:
        user_qoute = f""
    else:
        user_qoute = f" `[{name}@{msgid}] {host}{msgid}>`_ "
    return msgzh+user_qoute


def genpo(changes,temp_po_path,po_repo_path):
    msgs = {}
    versions = {}
    
    for change in changes:
        msgid,name,email,github,operate = change
        msg = Msgs.select().where(Msgs.msgid==msgid).get()
        msgversion = msg.version.split(",")
        print(msgversion,msg.version)
        for name in msgversion:
            version = model_to_dict(Version.select().where(Version.name==name).order_by(Version.update_time.desc()).get())
            versions[version['name']] = version
            if version['name'] not in msgs.keys():
                msgs[version['name']] = {}
                msgs[version['name']]['change'] = []

                files = {}
                msgids = version['msgs'].split(",")[:-1]
                for tmsgid in msgids:
                    tmsg = Msgs.select(Msgs,File.path,File.header,User.name) \
                    .join(Calib, JOIN.INNER, on = (Calib.calibid == Msgs.calibid)) \
                    .join(User, JOIN.INNER, on = (User.email == Calib.calibemail))  \
                    .join(File, JOIN.INNER, on = (File.fileid == Msgs.fileid))  \
                    .where(Msgs.msgid==tmsgid).get()

                    filename = tmsg.calib.user.file.path
                    if filename not in files.keys():
                        header = ""
                        header = tmsg.calib.user.file.header
                        files[filename] = {"path":filename,'header':header,"msgs":[]}

                    files[filename]['msgs'].append({"position":tmsg.position ,"msgen":tmsg.msgen ,"msgzh":transzh_by_status(tmsg.msgid,tmsg.msgen,tmsg.msgzh,tmsg.status,tmsg.calib.user.name)  })
                msgs[version['name']]['file']  = files



    # 生成不同版本
    for version in msgs.keys():
        # 生成不同文件
        path = f"{temp_po_path}{version}"
        mycmd.CmdTask(f"mkdir -p {path}").run()
        for file in msgs[version]['file'].keys():
            data = msgs[version]['file'][file]["header"]
            for msg in  msgs[version]['file'][file]['msgs']:
                data += f'\n{msg["position"]}msgid "{msg["msgen"]}"\nmsgstr "{msg["msgzh"]}"\n\n'
            with open(path+file,"w") as f: f.write(data)

            with open(f"{path}/README.md","w") as f:
                temp= {}
                temp['changes'] = []
                for i in range(len(changes)):
                    msgid,name,email,github,operate = changes[i]
                    temp['changes'].append({"msgid":msgid,"name":name,"email":email,"github":github,"operate":operate}) 
                temp['time'] = f"{time.strftime('%Y-%m-%d-%H:%M:%S')}"
                f.write(json.dumps(temp))
        update_repo(path,version,po_repo_path)

