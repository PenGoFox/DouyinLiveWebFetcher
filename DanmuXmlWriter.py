import header
import version
import time
from xml.sax.saxutils import escape

class DanmuXmlWriter:
    def __init__(self, filename, roomid, name, title, areaNameParent, areaNameChild, startTime):
        self._filename = filename
        self._beginStr = "<i>\n"
        self._endStr = "</i>\n"

        self._initWithHeader(roomid, name, title, areaNameParent, areaNameChild, startTime)

        # 定义要转义的符号和对应的 XML 实体
        self._escapeEntities = {
            "&": "&amp;",   # 转义 & 符号
            "<": "&lt;",    # 转义 < 符号
            ">": "&gt;",    # 转义 > 符号
            "\"": "&quot;", # 转义 " 符号
            "'": "&apos;"   # 转义 ' 符号
        }

    def _escape(self, content):
        return escape(content, entities=self._escapeEntities)

    def _initWithHeader(self, roomid, name, title, areaNameParent, areaNameChild, startTime):
        self._startTime = time.time()
        with open(self._filename, "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="utf-8"?>\n')
            f.write('<?xml-stylesheet type="text/xsl" href="#s"?>\n')
            f.write(self._beginStr)
            f.write(header.genHeader(version.version, roomid, name, title, areaNameParent, areaNameChild, startTime) + "\n")
            f.write(self._endStr)

    def appendTag(self, tag_name, attributes, text=None):
        attrStr = ""
        for key in attributes:
            attrStr += f'{key}="{self._escape(attributes[key])}" '

        with open(self._filename, "rb+") as f:
            f.seek(-len(self._endStr) - 1, 2)
            toWrite = ""
            if text is None:
                toWrite = f"<{tag_name} {attrStr} />\n\n{self._endStr}"
            else:
                toWrite = f"<{tag_name} {attrStr}>{self._escape(text)}</{tag_name}>\n\n{self._endStr}"
            f.write(toWrite.encode("utf-8"))

    def appendDanmu(self, user, uid, sec_id, text):
        #<!-- p 的内容格式：弹幕出现时间（秒）,弹幕类型,字号,颜色,发送时间戳,固定为0,发送者UID,固定为0 -->
        ts = time.time()
        attrs = {"p": f"{ts - self._startTime:.3f},1,25,00,{ts * 1e3:.0f},0,{uid},0,{sec_id}", "user": f"{user}"}
        tag = "d"
        self.appendTag(tag, attrs, text)

    def appendGift(self, user, uid, sec_id, giftName, giftcount):
        ts = time.time()
        attrs = {
            "ts": f"{ts - self._startTime:.3f}",
            "user": user,
            "uid": uid,
            "sec_id": sec_id,
            "giftname": giftName,
            "giftcount": giftcount
        }
        tag = "gift"
        self.appendTag(tag, attrs)
