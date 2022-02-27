# coding: utf-8
from flask import request, Flask
import queue
import threading
import time
import myscript.mycmd as mycmd
import json

import spdlog
logger = spdlog.FileLogger('webhook', f"./log/ros2/webhook_{time.strftime('%Y-%m-%d-%H:%M:%S')}.log", False,False)

app = Flask(__name__)
# build 事件队列
build_signal = queue.Queue()
# 是否 build 中
runing = False


@app.route('/webhook/ros2cn/push', methods=['POST', 'GET'])
def ros2cnpush():
    ip = request.headers.getlist("X-Forwarded-For")[0]
    logger.info(f"[{ip}] {request.url}")
    if request.method == 'GET':
        return 'OK'
    # 如果队列是空的，则添加一个事件，否则不添加，为了防止重复请求添加过多的事件导致一直 Build
    # 这样可使队列中始终只有一个事件，当 build 开始执行后，又会变空，此时才能添加
    # 就能实现执行中多次请求，最终都只会执行一次 build
    data = json.loads(request.data)
    if 'ref' in data:
        ref = json.loads(request.data)['ref']
        branch = ref[ref.rfind('/')+1:]
        print(f"来自:ros2cn/{branch}的更新")
        build_signal.put(("ros2cn",branch))
    return 'OK'

@app.route('/webhook/ros2doc/push', methods=['POST', 'GET'])
def ros2docpush():
    ip = request.headers.getlist("X-Forwarded-For")[0]
    logger.info(f"[{ip}] {request.url}")
    if request.method == 'GET':
        return 'ros2doc webhook OK'
    data = json.loads(request.data)
    if 'ref' in data:
        ref = json.loads(request.data)['ref']
        branch = ref[ref.rfind('/')+1:]
        print(f"来自:ros2doc/{branch}的更新")
        # if build_signal.empty():
        build_signal.put(("ros2doc",branch))
    return 'OK'


@app.route('/webhook/nav2calibpage/push', methods=['POST', 'GET'])
def nav2calibpagepush():
    ip = request.headers.getlist("X-Forwarded-For")[0]
    logger.info(f"[{ip}] {request.url}")
    if request.method == 'GET':
        return 'ros2doc webhook OK'
    data = json.loads(request.data)
    if 'ref' in data:
        ref = json.loads(request.data)['ref']
        branch = ref[ref.rfind('/')+1:]
        print(f"来自:nav2calibpage/{branch}的更新")
        # if build_signal.empty():
        build_signal.put(("nav2calibpage",branch))
    return 'OK'


@app.route('/webhook/index', methods=['get'])
def index():
    ip = request.headers.getlist("X-Forwarded-For")[0]
    logger.info(f"[{ip}] {request.url}")
    if runing:
        return '<h1>运行中</h1>'
    return '<h1>空闲中</h1>'


def buildThread():
    # 循环监听 build 事件
    global runing
    while True:
        # 如果事件队列不为空，则表示需要执行Build
        if not build_signal.empty():
            repo,branch = build_signal.get()
            runing = True
            if repo == 'ros2cn':
                if branch=='dev':
                    mycmd.CmdTask("git reset --hard && git checkout dev",cwd="../ros2cn").run()
                    mycmd.CmdTask("git pull",cwd="../ros2cn").run()
                    mycmd.CmdTask("npm run install-dep",cwd="../ros2cn").run()
                    mycmd.CmdTask("npm run build",cwd="../ros2cn").run()
                    # 部署dev分支
                    mycmd.CmdTask("rm -rf /tmp/ros2cn/dist && mkdir -p /tmp/ros2cn/dist").run()
                    mycmd.CmdTask("cp -r docs/.vuepress/dist/*  /tmp/ros2cn/dist/",cwd="../ros2cn").run()
                    mycmd.CmdTask("cp -r docs/.vuepress/dist/*  /root/ros2/dev/ros2cn",cwd="../ros2cn").run()
                    # 部署gh-page分支
                    mycmd.CmdTask("git reset --hard && git checkout gh-page && git reset --hard",cwd="../ros2cn").run()
                    mycmd.CmdTask("cp -r /tmp/ros2cn/dist/*  ./",cwd="../ros2cn").run()
                    mycmd.CmdTask(f'git add . && git commit -m "{time.strftime("%Y-%m-%d-%H:%M:%S")}" ',cwd="../ros2cn").run()
                    mycmd.CmdTask('git push origin gh-page',cwd="../ros2cn").run()
                elif branch=='master':
                    # 部署master分支
                    mycmd.CmdTask("git reset --hard && git checkout master",cwd="../ros2cn").run()
                    code = mycmd.CmdTask("git pull",cwd="../ros2cn").run()
                    mycmd.CmdTask("npm run install-dep",cwd="../ros2cn").run()
                    mycmd.CmdTask("npm run build",cwd="../ros2cn").run()
                    mycmd.CmdTask("cp -r docs/.vuepress/dist/*  /root/ros2/master/ros2cn",cwd="../ros2cn").run()
            elif repo=='ros2doc':
                if branch=='foxy':
                    mycmd.CmdTask("git reset --hard && git checkout develop",cwd="../ros2doc/ros2doc").run()
                    mycmd.CmdTask("git pull",cwd="../ros2doc/ros2doc").run()
                    mycmd.CmdTask("cp -r *  /root/ros2/dev/doc",cwd="../ros2doc/ros2doc").run()
                elif branch=='main':
                    # 部署master分支
                    mycmd.CmdTask("git reset --hard && git checkout master",cwd="../ros2cn/ros2doc").run()
                    mycmd.CmdTask("git pull",cwd="../ros2doc/ros2doc").run()
                    mycmd.CmdTask("cp -r *  /root/ros2/master/doc",cwd="../ros2doc/ros2doc").run()
            elif repo=='nav2calibpage':
                if branch=='develop':
                    mycmd.CmdTask("git reset --hard && git checkout develop",cwd="../nav2calibpage").run()
                    mycmd.CmdTask("git pull",cwd="../nav2calibpage").run()
                    mycmd.CmdTask("cp -r dist/*  /root/ros2/dev/calibpage",cwd="../nav2calibpage").run()
                elif branch=='master':
                    # 部署master分支
                    mycmd.CmdTask("git reset --hard && git checkout master",cwd="../nav2calibpage").run()
                    mycmd.CmdTask("git pull",cwd="../nav2calibpage").run()
                    mycmd.CmdTask("cp -r dist/*  /root/ros2/master/calibpage",cwd="../nav2calibpage").run()
            runing = False
        time.sleep(0.5)
        

# 启动一个线程来循环事件队列
t1 = threading.Thread(target=buildThread)
t1.start()
if __name__ == "__main__":
    from waitress import serve
    # serve(app, host="0.0.0.0", port=2000)
    app.run(host="0.0.0.0", port='2020')