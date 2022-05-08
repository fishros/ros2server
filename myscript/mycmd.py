# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
import os
import re
import sys
import time
import subprocess
import locale


class PrintUtils():
    @staticmethod
    def print_delay(data,delay=0.03,end="\n"):
        for d in data:
            d = d.encode("utf-8").decode("utf-8")
            print("\033[37m{}".format(d),end="",flush=True)
            time.sleep(delay)
        print(end=end)

    @staticmethod
    def print_error(data,end="\n"):
        print("\033[31m{}".format(data),end=end)

    @staticmethod
    def print_info(data,end="\n"):
        print("\033[37m{}".format(data))

    @staticmethod
    def print_success(data,end="\n"):
        print("\033[32m{}".format(data))

    @staticmethod
    def print_fish(timeout=1,scale=30):
        return 
        start = time.perf_counter()
        for i in range(scale + 1):
            a = "🐟" * i
            b = ".." * (scale - i)
            c = (i / scale) * 100
            dur = time.perf_counter() - start
            print("\r{:^3.0f}%[{}->{}]{:.2f}s".format(c,a,b,dur),end = "")
            time.sleep(timeout/scale)
        print("\n")


class Task():
    """
    - type: 任务类型
    - params: 任务参数
    - result: 任务执行结果
    - progress: 任务执行进度
    - timeout: 任务超时时间 
    - subtask: 子任务
    """
    TASK_TYPE_CMD = 0
    TASK_TYPE_CHOOSE = 1
    TASK_TYPE_PATTERN= 2
    def __init__(self,type) -> None:
        self.type = Task.TASK_TYPE_CMD 
    def run(self):
        pass


class Progress():
    def __init__(self,timeout=10,scale=20) -> None:
        self.timeout = timeout
        self.start = time.perf_counter()
        self.dur  = time.perf_counter() -self.start 
        self.scale = scale
        self.i = 0

    def update(self,log=""):
        length = 60
        if len(log)>length: log = log[:length]
        log = log+"                "
        if (self.i%4) == 0: 
            print('\r[/]{}'.format(log),end="")
        elif(self.i%4) == 1: 
            print('\r[\\]{}'.format(log),end="")
        elif (self.i%4) == 2: 
            print('\r[|]{}'.format(log),end="")
        elif (self.i%4) == 3: 
            print('\r[-]{}'.format(log),end="")
        sys.stdout.flush()
        self.i += 1
        # update time
        # self.dur  = time.perf_counter() -self.start 
        # self.i = int(self.dur/(self.timeout/self.scale))
        # a = "🐟" * self.i
        # b = ".." * (self.scale - self.i)
        # c = (self.i / self.scale) * 100
        # 
        # log += " "*()
        # print("\r{:^3.0f}%[{}->{}]{:.2f}s {}".format(c,a,b,self.dur,log),end = "")
    
    def finsh(self,log=""):
        length = 60
        if len(log)>length: log = log[:length]
        log = log+"                           " 
        print('\r[-]{}'.format(log),end="")
        # i = self.scale
        # a = "🐟" * i
        # b = ".." * (self.scale - i)
        # c = (i / self.scale) * 100
        # print("\r{:^3.0f}%[{}->{}]{:.2f}s {}".format(c,a,b,self.dur,log),end = "")



class CmdTask(Task):
    def __init__(self,command,cwd=None,timeout=0,groups=False,os_command=False) -> None:
        super().__init__(Task.TASK_TYPE_CMD)
        self.command = command
        self.timeout = timeout
        self.os_command = os_command
        self.cwd = cwd

    @staticmethod
    def __run_command(command,cwd=None,timeout=10):
        out,err = [],[]
        sub = subprocess.Popen(command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            shell=True)

        # sub.communicate
        bar  = Progress(timeout=timeout)
        bar.update()

        while sub.poll()==None:
            line = sub.stdout.readline()
            line = line.decode("utf-8").strip("\n")
            bar.update(line)
            time.sleep(0.001)
            out.append(line)
        
        if sub.poll()==None:
            sub.kill()
            print("\033[31mTimeOut!:{}".format(timeout))
            return None,'','运行超时:请切换网络后重试'

        code = sub.returncode
        msg = 'code:{}'.format(code)
        if code == 0: msg="success"
        bar.finsh('Result:{}'.format(msg))

        for line in  sub.stderr.readlines():
            err.append(line.decode('utf-8'))
        print("\n")
        return (code,out,err)
    
    @staticmethod
    def _os_command(command,cwd,timeout=10):
        if cwd is not None:
            os.system(f"cd {cwd} && command")
        else:
            os.system(command)


    def run(self):
        PrintUtils.print_info("\033[32mRun CMD Task:[{}]".format(self.command))
        if self.os_command:
            return self._os_command(self.command,self.cwd,self.timeout)
        return self.__run_command(self.command,self.cwd,self.timeout)



class ChooseTask(Task):
    def __init__(self,dic,tips,array=False) -> None:
        self.tips= tips
        self.dic = dic
        self.array = array
        super().__init__(Task.TASK_TYPE_CHOOSE)

    @staticmethod
    def __choose(data,tips,array):
        if array:
            count = 1
            dic = {}
            for e in data:
                dic[count] = e
                count += 1
        else:
            dic = data
        dic[0]="quit"
        # 0 quit
        choose = -1 
        for key in dic:
            PrintUtils.print_delay('[{}]:{}'.format(key,dic[key]))
        while True:
            choose = input("请输入[]内的数字以选择:")
            if choose.isdecimal() :
                if (int(choose) in dic.keys() ) or (int(choose)==0):
                    choose = int(choose)
                    break
        PrintUtils.print_fish()
        return choose,dic[choose]

    def run(self):
        PrintUtils.print_delay("RUN Choose Task:[请输入括号内的数字]")
        PrintUtils.print_delay(self.tips)
        return ChooseTask.__choose(self.dic,self.tips,self.array)



class FileUtils():
    @staticmethod
    def delete(path):
        if os.path.exists(path):
            result = CmdTask("sudo rm -rf {}".format(path),3).run()
            return result[0]==0
        return False

    @staticmethod
    def new(path,name=None,data=''):
        if not os.path.exists(path):
            CmdTask("sudo mkdir -p {}".format(path),3).run()
        if name!=None:
            with open(path+name,"w") as f:
                f.write(data)
        return True
    
    @staticmethod
    def append(path,adddata=''):
        data = ""
        with open(path) as f:
            data = f.read()

        data  += "\n"+adddata
        with open(path,"w") as f:
            f.write(data)
        return True

    @staticmethod
    def find_replace(file,pattern,new):
        """
        查找和删除文件
        """
        is_file = True
        for root, dirs, files in os.walk(file):
            for f in files:
                is_file = False
                file_path = os.path.join(root, f)
                with open(file_path) as f:
                    data = f.read()
                    re_result = re.findall(pattern,data)
                    if re_result:
                        for key in re_result:
                            data = data.replace(key,new)
                        with open(file_path,"w",encoding="utf-8") as f:
                            f.write(data)
            # 遍历所有的文件夹
            for d in dirs:
                os.path.join(root, d)
        if is_file:
            with open(file) as f:
                data = f.read()
            re_result = re.findall(pattern,data)
            if re_result:
                for key in re_result:
                    data = data.replace(key,new)
                with open(file,"w",encoding="utf-8") as f:
                    f.write(data)

    @staticmethod
    def find_replace_sub(file,start,end,new):
        """
        查找和删除文件
        """
        is_file = True
        for root, dirs, files in os.walk(file):
            for f in files:
                is_file = False
                file_path = os.path.join(root, f)
                with open(file_path) as f:
                    data = f.read()
                    start_index = data.find(start)
                    end_index = data.find(end)
                    if start_index>0 and end_index>0:
                        data = data[:start_index]+data[end_index+len(end):]
                        with open(file_path,"w") as f:
                            f.write(data)
            # 遍历所有的文件夹
            for d in dirs:
                os.path.join(root, d)
        if is_file:
            with open(file) as f:
                data = f.read()
                start_index = data.find(start)
                end_index = data.find(end)
                if start_index>0 and end_index>0:
                    data = data[:start_index]+data[end_index+len(end):]
                    with open(file,"w") as f:
                        f.write(data)
                    
    @staticmethod
    def check_result(result,patterns):
        for line in result:
            for pattern in patterns:
                if len(re.findall(pattern, line))>0:
                    return True


class AptUtils():
    @staticmethod
    def checkapt():
        apt_command = CmdTask('sudo apt update',100)
        result = apt_command.run()
        if result[0]!=0:
            PrintUtils.print_error("你的系统当前apt存在问题，请先使用一键换源处理...若无法处理，请将下列错误信息告知小鱼...{},{}".format(result[1],result[2]))
            return False
        return True

    @staticmethod
    def getArch():
        result = CmdTask("dpkg --print-architecture",2).run()
        if result[0]==0: return result[1][0].strip("\n")
        PrintUtils.print_error("小鱼提示:自动获取系统架构失败...请手动选择")
        return None
    
    @staticmethod
    def search_package(name,pattern,replace1="",replace2=""):
        result = CmdTask("sudo apt-cache search {} ".format(name),20).run()
        if result[0]!=0: 
            PrintUtils.print_error("搜索不到任何{}相关的包".format(name))
            return None
        dic = {}
        for line in result[1]:
            temp = re.findall(pattern,line)      
            if len(temp)>0: dic[temp[0].replace(replace1,"").replace(replace2,"")] = temp[0]
        return dic
    
    @staticmethod 
    def install_pkg(name):
        dic = AptUtils().search_package(name,name)
        result = None
        for key in dic.keys():
            result = CmdTask("sudo apt install {} -y".format(dic[key]), 0).run()
        return result
