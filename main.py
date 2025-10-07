#!/usr/bin/python
# coding:utf-8

# @FileName:    main.py
# @Time:        2024/1/2 22:27
# @Author:      bubu
# @Project:     douyinLiveWebFetcher

from liveMan import DouyinLiveWebFetcher
import time
from spider import get_douyin_stream_data
import random
from configRead import *
from web import Web
import Global

from logger import msgLogger

configFilename = "config.json"

if __name__ == '__main__':
    interval = 300

    if not loadConfig(configFilename):
        msgLogger.error("读取配置文件 {} 失败".format(configFilename))
        exit(-1)
    config = getConfig()
    live_id = config["liveid"]
    anchor_name = config["anchorname"]
    msgLogger.info("直播间id: {}".format(live_id))
    msgLogger.info("主播名: {}".format(anchor_name ))
    live_url = "https://live.douyin.com/"

    # 尝试启动 web 服务
    if "web" in config:
        web = config["web"]
        if "enable" in web and web["enable"]:
            host = web["host"]
            port = web["port"]
            Web(host, port).runInThread()

    checkBreak = 0
    live = None

    while True:
        try:
            msgLogger.info("检查直播是否打开")
            json_data = get_douyin_stream_data(live_url + live_id)
            status = json_data.get("status", 4)  # 直播状态 2 是正在直播、4 是未开播
            if status != 2:
                _interval = random.randint(-15, 15) + interval
                if _interval < 30:
                    _interval = 30

                if checkBreak > 0:
                    checkBreak -= 1
                    _interval = 30

                Global.isLiveStreaming = False
                msgLogger.info(f"直播未打开，等待{_interval}秒")
                time.sleep(_interval)
                continue
            msgLogger.info(f"直播已打开，连接弹幕")

            Global.isLiveStreaming = True

            live = DouyinLiveWebFetcher(live_id)
            Global.isRecording = True
            live.start()
            live.stop()
            Global.isRecording = False
            live = None

            msgLogger.info("直播弹幕已断开")
            time.sleep(2)
            checkBreak = 5
        except KeyboardInterrupt as err:
            msgLogger.info("手动退出")
            Global.isRecording = False
            if live is not None:
                live.stop()
            break
        except Exception as err:
            msgLogger.error(f"catch an error while run DouyinLiveWebFetcher: {err}")
            Global.isRecording = False
            if live is not None:
                live.stop()
