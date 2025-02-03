#!/usr/bin/python
# coding:utf-8

# @FileName:    liveMan.py
# @Time:        2024/1/2 21:51
# @Author:      bubu
# @Project:     douyinLiveWebFetcher

import time
import os
import codecs
import gzip
import hashlib
import random
import re
import string
import subprocess
import urllib.parse
from contextlib import contextmanager
from py_mini_racer import MiniRacer
from unittest.mock import patch
from logger import msgLogger, setGiftLoggerFilename, setChatLoggerFilename, chatLogger, giftLogger, fansClubLogger, setFansClubLoggerFilename
from DanmuXmlWriter import DanmuXmlWriter

import execjs
import requests
import websocket

from protobuf.douyin import *

def generateDateStr():
    return time.strftime("%Y_%m_%d", time.localtime(time.time()))

def generateTimeStr():
    return time.strftime("%H_%M_%S", time.localtime(time.time()))

@contextmanager
def patched_popen_encoding(encoding='utf-8'):
    original_popen_init = subprocess.Popen.__init__
    
    def new_popen_init(self, *args, **kwargs):
        kwargs['encoding'] = encoding
        original_popen_init(self, *args, **kwargs)
    
    with patch.object(subprocess.Popen, '__init__', new_popen_init):
        yield


def generateSignature(wss, script_file='sign.js'):
    """
    出现gbk编码问题则修改 python模块subprocess.py的源码中Popen类的__init__函数参数encoding值为 "utf-8"
    """
    params = ("live_id,aid,version_code,webcast_sdk_version,"
              "room_id,sub_room_id,sub_channel_id,did_rule,"
              "user_unique_id,device_platform,device_type,ac,"
              "identity").split(',')
    wss_params = urllib.parse.urlparse(wss).query.split('&')
    wss_maps = {i.split('=')[0]: i.split("=")[-1] for i in wss_params}
    tpl_params = [f"{i}={wss_maps.get(i, '')}" for i in params]
    param = ','.join(tpl_params)
    md5 = hashlib.md5()
    md5.update(param.encode())
    md5_param = md5.hexdigest()
    
    with codecs.open(script_file, 'r', encoding='utf8') as f:
        script = f.read()
        
    ctx = MiniRacer()
    ctx.eval(script)
    
    try:
        signature = ctx.call("get_sign", md5_param)
        return signature
    except Exception as e:
        msgLogger.error(e)
    
    # 以下代码对应js脚本为sign_v0.js
    # context = execjs.compile(script)
    # with patched_popen_encoding(encoding='utf-8'):
    #     ret = context.call('getSign', {'X-MS-STUB': md5_param})
    # return ret.get('X-Bogus')


def generateMsToken(length=107):
    """
    产生请求头部cookie中的msToken字段，其实为随机的107位字符
    :param length:字符位数
    :return:msToken
    """
    random_str = ''
    base_str = string.ascii_letters + string.digits + '=_'
    _len = len(base_str) - 1
    for _ in range(length):
        random_str += base_str[random.randint(0, _len)]
    return random_str


class DouyinLiveWebFetcher:
    
    def __init__(self, live_id):
        from configRead import getConfig

        """
        直播间弹幕抓取对象
        :param live_id: 直播间的直播id，打开直播间web首页的链接如：https://live.douyin.com/261378947940，
                        其中的261378947940即是live_id
        """
        dateStr = generateDateStr()
        timeStr = generateTimeStr()
        dirStr = f"Logs/{live_id}/"
        if not os.path.exists(dirStr) or not os.path.isdir(dirStr): # 创建名称类似 Log/直播id/ 的目录
            os.makedirs(dirStr)
        dirStr += f"{dateStr} {timeStr}"
        setChatLoggerFilename(dirStr)
        setGiftLoggerFilename(dirStr)
        setFansClubLoggerFilename(dirStr)

        config = getConfig()
        anchor_name = config["anchorname"]
        xmlDirStr = f"Danmu/{live_id}-{anchor_name}/"
        if not os.path.exists(xmlDirStr) or not os.path.isdir(xmlDirStr):
            os.makedirs(xmlDirStr)
        dateTimeStr = f"{dateStr} {timeStr}"
        xmlFilename = xmlDirStr + dateTimeStr + ".xml"
        title = "default"
        areaNameParent = "default"
        areaNameChild = "default"
        self.xmlWriter = DanmuXmlWriter(xmlFilename, live_id, anchor_name, title, areaNameParent, areaNameChild, dateTimeStr)

        self.giftTraceDict = dict() # 礼物跟踪列表，用来去重
        self.giftTraceDictCleanDeltaT = config["gift_clean_delta_t"] if "gift_clean_delta_t" in config else 10 # 清除礼物数据的时间间隔，默认为 10 秒
        self.giftTraceDictLastCleanTimestamp = time.time() # 上次清除旧礼物数据的时间戳

        self.__ttwid = None
        self.__room_id = None
        self.live_id = live_id
        self.live_url = "https://live.douyin.com/"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) " \
                          "Chrome/120.0.0.0 Safari/537.36"
    
    def start(self):
        self._connectWebSocket()
    
    def stop(self):
        self.ws.close()
    
    @property
    def ttwid(self):
        """
        产生请求头部cookie中的ttwid字段，访问抖音网页版直播间首页可以获取到响应cookie中的ttwid
        :return: ttwid
        """
        if self.__ttwid:
            return self.__ttwid
        headers = {
            "User-Agent": self.user_agent,
        }
        try:
            response = requests.get(self.live_url, headers=headers)
            response.raise_for_status()
        except Exception as err:
            msgLogger.error("【X】Request the live url error: {}".format(err))
        else:
            self.__ttwid = response.cookies.get('ttwid')
            return self.__ttwid
    
    @property
    def room_id(self):
        """
        根据直播间的地址获取到真正的直播间roomId，有时会有错误，可以重试请求解决
        :return:room_id
        """
        if self.__room_id:
            return self.__room_id
        url = self.live_url + self.live_id
        headers = {
            "User-Agent": self.user_agent,
            "cookie": f"ttwid={self.ttwid}&msToken={generateMsToken()}; __ac_nonce=0123407cc00a9e438deb4",
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except Exception as err:
            msgLogger.error("【X】Request the live room url error: {}".format(err))
        else:
            match = re.search(r'roomId\\":\\"(\d+)\\"', response.text)
            if match is None or len(match.groups()) < 1:
                msgLogger.error("【X】No match found for roomId")
            
            self.__room_id = match.group(1)
            
            return self.__room_id
    
    def _connectWebSocket(self):
        """
        连接抖音直播间websocket服务器，请求直播间数据
        """
        wss = ("wss://webcast5-ws-web-hl.douyin.com/webcast/im/push/v2/?app_name=douyin_web"
               "&version_code=180800&webcast_sdk_version=1.0.14-beta.0"
               "&update_version_code=1.0.14-beta.0&compress=gzip&device_platform=web&cookie_enabled=true"
               "&screen_width=1536&screen_height=864&browser_language=zh-CN&browser_platform=Win32"
               "&browser_name=Mozilla"
               "&browser_version=5.0%20(Windows%20NT%2010.0;%20Win64;%20x64)%20AppleWebKit/537.36%20(KHTML,"
               "%20like%20Gecko)%20Chrome/126.0.0.0%20Safari/537.36"
               "&browser_online=true&tz_name=Asia/Shanghai"
               "&cursor=d-1_u-1_fh-7392091211001140287_t-1721106114633_r-1"
               f"&internal_ext=internal_src:dim|wss_push_room_id:{self.room_id}|wss_push_did:7319483754668557238"
               f"|first_req_ms:1721106114541|fetch_time:1721106114633|seq:1|wss_info:0-1721106114633-0-0|"
               f"wrds_v:7392094459690748497"
               f"&host=https://live.douyin.com&aid=6383&live_id=1&did_rule=3&endpoint=live_pc&support_wrds=1"
               f"&user_unique_id=7319483754668557238&im_path=/webcast/im/fetch/&identity=audience"
               f"&need_persist_msg_count=15&insert_task_id=&live_reason=&room_id={self.room_id}&heartbeatDuration=0")
        
        signature = generateSignature(wss)
        wss += f"&signature={signature}"
        
        headers = {
            "cookie": f"ttwid={self.ttwid}",
            'user-agent': self.user_agent,
        }
        self.ws = websocket.WebSocketApp(wss,
                                         header=headers,
                                         on_open=self._wsOnOpen,
                                         on_message=self._wsOnMessage,
                                         on_error=self._wsOnError,
                                         on_close=self._wsOnClose)
        try:
            self.ws.run_forever()
        except Exception:
            self.stop()
            raise

    def _wsOnOpen(self, ws):
        """
        连接建立成功
        """
        msgLogger.info("WebSocket connected.")
    
    def _wsOnMessage(self, ws, message):
        """
        接收到数据
        :param ws: websocket实例
        :param message: 数据
        """
        
        # 根据proto结构体解析对象
        package = PushFrame().parse(message)
        response = Response().parse(gzip.decompress(package.payload))
        
        # 返回直播间服务器链接存活确认消息，便于持续获取数据
        if response.need_ack:
            ack = PushFrame(log_id=package.log_id,
                            payload_type='ack',
                            payload=response.internal_ext.encode('utf-8')
                            ).SerializeToString()
            ws.send(ack, websocket.ABNF.OPCODE_BINARY)
        
        # 根据消息类别解析消息体
        for msg in response.messages_list:
            method = msg.method
            try:
                {
                    'WebcastChatMessage': self._parseChatMsg,  # 聊天消息
                    'WebcastGiftMessage': self._parseGiftMsg,  # 礼物消息
                    #'WebcastLikeMessage': self._parseLikeMsg,  # 点赞消息
                    #'WebcastMemberMessage': self._parseMemberMsg,  # 进入直播间消息
                    'WebcastSocialMessage': self._parseSocialMsg,  # 关注消息
                    #'WebcastRoomUserSeqMessage': self._parseRoomUserSeqMsg,  # 直播间统计
                    'WebcastFansclubMessage': self._parseFansclubMsg,  # 粉丝团消息
                    'WebcastControlMessage': self._parseControlMsg,  # 直播间状态消息
                    #'WebcastEmojiChatMessage': self._parseEmojiChatMsg,  # 聊天表情包消息
                    #'WebcastRoomStatsMessage': self._parseRoomStatsMsg,  # 直播间统计信息
                    #'WebcastRoomMessage': self._parseRoomMsg,  # 直播间信息
                    #'WebcastRoomRankMessage': self._parseRankMsg,  # 直播间排行榜信息
                }.get(method)(msg.payload)
            except Exception:
                pass
    
    def _wsOnError(self, ws, error):
        msgLogger.error("WebSocket error: {}".format(error))
    
    def _wsOnClose(self, ws, *args):
        msgLogger.info("WebSocket connection closed.")
    
    def _parseChatMsg(self, payload):
        """聊天消息"""
        message = ChatMessage().parse(payload)
        user_name = message.user.nick_name
        user_id = message.user.id
        dyid = message.user.display_id # 抖音号
        sec_uid = message.user.sec_uid # 可用于直接拼接用户空间的 url
        content = message.content
        chatLogger.info(f"[{user_id}] [{dyid}] {user_name}: {content}")
        self.xmlWriter.appendDanmu(user_name, dyid, sec_uid, content)
    
    def _parseGiftMsg(self, payload):
        """礼物消息"""
        message = GiftMessage().parse(payload)

        user_name = message.user.nick_name
        user_id = message.user.id
        dyid = message.user.display_id # 抖音号
        sec_uid = message.user.sec_uid # 可用于直接拼接用户空间的 url

        gift_name = message.gift.name
        gift_cnt = message.combo_count

        repeat_count = message.repeat_count # 送礼重复次数，理论上这玩意儿大于 0
        repeat_end = message.repeat_end # 重复送礼是否已经结束

        timestamp = time.time()
        traceKey = (dyid, gift_name) # 要跟踪的 key
        traceVal = (timestamp, repeat_count) # 将要记录的 value
        if 1 == repeat_end: # 重复送礼物已经结束，从字典删除即可
            msgLogger.debug(f"delete key: {traceKey}")
            del self.giftTraceDict[traceKey]
        elif 1 == repeat_count: # 第一次送礼物必须要写出，猜测重复送礼物不一定会有这条
            self.giftTraceDict[traceKey] = traceVal

            # 写信息
            giftLogger.info(f"[{user_id}] [{dyid}] \"{user_name}\" 送出了 \"{gift_name}\"x1")
            self.xmlWriter.appendGift(user_name, dyid, sec_uid, gift_name, str(1))
            msgLogger.debug(f"{traceKey}{traceVal} [{user_id}] [{dyid}] \"{user_name}\" 送出了 \"{gift_name}\"x1")
        else:
            count = 0
            if traceKey not in self.giftTraceDict: # 不一定之前有记录
                count = repeat_count
            else:
                lastValue = self.giftTraceDict[traceKey]
                count = repeat_count - lastValue[1] # 相比上一次重复送礼多送了多少礼物
            self.giftTraceDict[traceKey] = traceVal # 更新一下这个礼物记录

            # 写信息
            giftLogger.info(f"[{user_id}] [{dyid}] \"{user_name}\" 送出了 \"{gift_name}\"x{count}")
            self.xmlWriter.appendGift(user_name, dyid, sec_uid, gift_name, str(count))
            msgLogger.debug(f"{traceKey}{traceVal} [{user_id}] [{dyid}] \"{user_name}\" 送出了 \"{gift_name}\"x{count}")

        # 删掉一定时间之前的所有记录
        deltaT = timestamp - self.giftTraceDictLastCleanTimestamp
        if deltaT > self.giftTraceDictCleanDeltaT:
            newDict = dict()
            for key, val in self.giftTraceDict.items(): # 获取还要用的记录
                # 在上次记录时间之后的或者有重复送礼物但还没送完的就继续用
                if val[0] >= self.giftTraceDictLastCleanTimestamp or val[1] > 1:
                    newDict[key] = val
            self.giftTraceDict = newDict # 更新为新的记录表
            msgLogger.debug(f"clean before {self.giftTraceDictLastCleanTimestamp}")
            self.giftTraceDictLastCleanTimestamp = timestamp # 更新时间戳

    def _parseLikeMsg(self, payload):
        '''点赞消息'''
        message = LikeMessage().parse(payload)
        user_name = message.user.nick_name
        count = message.count
        #(f"[点赞msg] {user_name} 点了{count}个赞\n")
    
    def _parseMemberMsg(self, payload):
        '''进入直播间消息'''
        message = MemberMessage().parse(payload)
        user_name = message.user.nick_name
        user_id = message.user.id
        gender = ["女", "男"][message.user.gender]
        #(f"[进场msg] [{user_id}][{gender}]{user_name} 进入了直播间\n")
    
    def _parseSocialMsg(self, payload):
        '''关注消息'''
        message = SocialMessage().parse(payload)
        user_name = message.user.nick_name
        user_id = message.user.id
        #(f"[关注msg] [{user_id}]{user_name} 关注了主播\n")
    
    def _parseRoomUserSeqMsg(self, payload):
        '''直播间统计'''
        message = RoomUserSeqMessage().parse(payload)
        current = message.total
        total = message.total_pv_for_anchor
        #(f"[统计msg] 当前观看人数: {current}, 累计观看人数: {total}\n")
    
    def _parseFansclubMsg(self, payload):
        '''粉丝团消息'''
        message = FansclubMessage().parse(payload)
        content = message.content
        user_id = message.user.id
        dyid = message.user.display_id # 抖音号
        fansClubLogger.info(f"[{user_id}] [{dyid}] {content}")
        #(f"[粉丝团msg] {content}\n")
    
    def _parseEmojiChatMsg(self, payload):
        '''聊天表情包消息'''
        message = EmojiChatMessage().parse(payload)
        emoji_id = message.emoji_id
        user = message.user
        common = message.common
        default_content = message.default_content
        #(f"[聊天表情包id] {emoji_id},user：{user},common:{common},default_content:{default_content}\n")
    
    def _parseRoomMsg(self, payload):
        message = RoomMessage().parse(payload)
        common = message.common
        room_id = common.room_id
        #(f"[直播间msg] 直播间id:{room_id}\n")
    
    def _parseRoomStatsMsg(self, payload):
        message = RoomStatsMessage().parse(payload)
        display_long = message.display_long
        #(f"[直播间统计msg] {display_long}\n")
    
    def _parseRankMsg(self, payload):
        message = RoomRankMessage().parse(payload)
        ranks_list = message.ranks_list
        #(f"[直播间排行榜msg] {ranks_list}\n")
    
    def _parseControlMsg(self, payload):
        '''直播间状态消息'''
        message = ControlMessage().parse(payload)
        
        if message.status == 3:
            msgLogger.info("直播间已结束")
            self.stop()
