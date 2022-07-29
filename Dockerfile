FROM python:3.8.12

RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple \
    && pip install flask spdlog peewee

RUN pip install waitress

RUN pip install requests
RUN pip install Pillow
RUN pip install emoji
# docker build -t fishros2/python-flask .
# docker run -it --name nav2server --rm -v `pwd`:`pwd` -w `pwd` -p 2001:2001 python:3.8.12 python nav2_calib_server.py