
preTextA = '''
    <chatid>0</chatid>
    <mission>0</mission>
    <maxlimit>1000</maxlimit>
    <state>0</state>
    <real_name>0</real_name>
    <source>0</source>
    '''

preTextB = '''
    <WebFetcherXmlStyle>
        <z:stylesheet version="1.0" id="s" xml:id="s" xmlns:z="http://www.w3.org/1999/XSL/Transform">
            <z:output method="html"/>
            <z:template match="/">
                <html>
                    <meta  name="viewport" content="width=device-width"/>
                    <title>WebFetcher弹幕文件 - <z:value-of select="/i/WebFetcherRecordInfo/@name"/> </title>
                    <style>body{margin:0}h1,h2,p,table{margin-left:5px}table{border-spacing:0}td,th{border:1px solid grey;padding:1px}th{position:sticky;top:0;background:#4098de}tr:hover{background:#d9f4ff}div{overflow:auto;max-height:80vh;max-width:100vw;width:fit-content}</style>
                    <h1> WebFetcher 弹幕XML文件 </h1>
                    <p>本文件不支持在 IE 浏览器里预览，请使用 Chrome Firefox Edge 等浏览器。</p>
                    <p>文件写法参照 mikufans 录播姬（有改动）</p>
                    <table>
                        <tr>
                            <td>WebFetcher 版本</td>
                            <td>
                                <z:value-of select="/i/WebFetcher/@version"/>
                            </td>
                        </tr>
                        <tr>
                            <td>房间号</td>
                            <td>
                                <z:value-of select="/i/WebFetcherRecordInfo/@roomid"/>
                            </td>
                        </tr>
                        <tr>
                            <td>主播名</td>
                            <td>
                                <z:value-of select="/i/WebFetcherRecordInfo/@name"/>
                            </td>
                        </tr>
                        <tr>
                            <td>录制开始时间</td>
                            <td>
                                <z:value-of select="/i/WebFetcherRecordInfo/@start_time"/>
                            </td>
                        </tr>
                        <tr>
                            <td>
                                <a  href="#d">弹幕</a>
                            </td>
                            <td>共<z:value-of select="count(/i/d)"/>条记录</td>
                        </tr>
                        <tr>
                            <td>
                                <a  href="#gift">礼物</a>
                            </td>
                            <td>共<z:value-of select="count(/i/gift)"/>条记录</td>
                        </tr>
                    </table>
                    <h2  id="d">弹幕</h2>
                    <div  id="dm">
                        <table>
                            <tr>
                                <th>用户名</th>
                                <th>出现时间</th>
                                <th>用户ID</th>
                                <th>弹幕</th>
                                <th style="display:none">参数</th>
                            </tr>
                            <z:for-each select="/i/d">
                                <tr>
                                    <td>
                                        <z:value-of select="@user"/>
                                    </td>
                                    <td>
                                    </td>
                                    <td>
                                    </td>
                                    <td>
                                        <z:value-of select="."/>
                                    </td>
                                    <td style="display:none">
                                        <z:value-of select="@p"/>
                                    </td>
                                </tr>
                            </z:for-each>
                        </table>
                    </div>
                    <script>
                        Array.from(document.querySelectorAll('#dm tr')).slice(1).map(t => t.querySelectorAll('td')).forEach(t => {
                            let p = t[4].textContent.split(','),
                                a = p[0];
                            t[1].textContent = `${(Math.floor(a/60/60)+'').padStart(2,0)}:${(Math.floor(a/60%60)+'').padStart(2,0)}:${(a%60).toFixed(3).padStart(6,0)}`;
                            t[2].innerHTML = `&lt;a target=_blank rel="nofollow noreferrer" href="https://www.douyin.com/user/${p[8]}"&gt;${p[6]}&lt;/a&gt;`
                        })
                    </script>
                    <h2  id="g">礼物</h2>
                    <div id="gift">
                        <table>
                            <tr>
                                <th>用户名</th>
                                <th>用户ID</th>
                                <th>礼物名</th>
                                <th>礼物数量</th>
                                <th>出现时间</th>
                                <th style="display:none">参数</th>
                            </tr>
                            <z:for-each select="/i/gift">
                                <tr>
                                    <td>
                                        <z:value-of select="@user"/>
                                    </td>
                                    <td>
                                        <a target="_blank" rel="nofollow noreferrer">
                                            <z:attribute name="href">
                                                <z:text>https://www.douyin.com/user/</z:text>
                                                <z:value-of select="@sec_id" />
                                            </z:attribute>
                                            <z:value-of select="@uid"/>
                                        </a>
                                    </td>
                                    <td>
                                        <z:value-of select="@giftname"/>
                                    </td>
                                    <td>
                                        <z:value-of select="@giftcount"/>
                                    </td>
                                    <td>
                                    </td>
                                    <td style="display:none">
                                        <z:value-of select="@ts"/>
                                    </td>
                                </tr>
                            </z:for-each>
                        </table>
                    </div>
                    <script>
                        Array.from(document.querySelectorAll('#gift tr')).slice(1).map(t => t.querySelectorAll('td')).forEach(t => {
                            let p = t[5].textContent,
                                a = p;
                            t[4].textContent = `${(Math.floor(a/60/60)+'').padStart(2,0)}:${(Math.floor(a/60%60)+'').padStart(2,0)}:${(a%60).toFixed(3).padStart(6,0)}`;
                        })
                    </script>
                </html>
            </z:template>
        </z:stylesheet>
    </WebFetcherXmlStyle>
'''

def genHeader(version, roomid, name, title, areaNameParent, areaNameChild, startTime):
    ret = preTextA
    ret += f'<WebFetcher version="{version}" />'
    ret += f'<WebFetcherRecordInfo roomid="{roomid}" shortid="0" name="{name}" title="{title}" areanameparent="{areaNameParent}" areanamechild="{areaNameChild}" start_time="{startTime}" />'
    ret += preTextB
    return ret
