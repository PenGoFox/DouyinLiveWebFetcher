import urllib.parse
import urllib.error
from urllib.request import Request
import urllib.request
import re
import requests
import gzip
import json

import logging

logger = logging.getLogger("msgLogger")

no_proxy_handler = urllib.request.ProxyHandler({})
opener = urllib.request.build_opener(no_proxy_handler)

OptionalStr = str | None
OptionalDict = dict | None

#@trace_error_decorator
def get_douyin_stream_data(url: str, proxy_addr: OptionalStr = None, cookies: OptionalStr = None) -> dict:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Referer': 'https://live.douyin.com/',
        'Cookie': 'ttwid=1%7CB1qls3GdnZhUov9o2NxOMxxYS2ff6OSvEWbv0ytbES4%7C1680522049%7C280d802d6d478e3e78d0c807f7c487e7ffec0ae4e5fdd6a0fe74c3c6af149511; my_rd=1; passport_csrf_token=3ab34460fa656183fccfb904b16ff742; passport_csrf_token_default=3ab34460fa656183fccfb904b16ff742; d_ticket=9f562383ac0547d0b561904513229d76c9c21; n_mh=hvnJEQ4Q5eiH74-84kTFUyv4VK8xtSrpRZG1AhCeFNI; store-region=cn-fj; store-region-src=uid; LOGIN_STATUS=1; __security_server_data_status=1; FORCE_LOGIN=%7B%22videoConsumedRemainSeconds%22%3A180%7D; pwa2=%223%7C0%7C3%7C0%22; download_guide=%223%2F20230729%2F0%22; volume_info=%7B%22isUserMute%22%3Afalse%2C%22isMute%22%3Afalse%2C%22volume%22%3A0.6%7D; strategyABtestKey=%221690824679.923%22; stream_recommend_feed_params=%22%7B%5C%22cookie_enabled%5C%22%3Atrue%2C%5C%22screen_width%5C%22%3A1536%2C%5C%22screen_height%5C%22%3A864%2C%5C%22browser_online%5C%22%3Atrue%2C%5C%22cpu_core_num%5C%22%3A8%2C%5C%22device_memory%5C%22%3A8%2C%5C%22downlink%5C%22%3A10%2C%5C%22effective_type%5C%22%3A%5C%224g%5C%22%2C%5C%22round_trip_time%5C%22%3A150%7D%22; VIDEO_FILTER_MEMO_SELECT=%7B%22expireTime%22%3A1691443863751%2C%22type%22%3Anull%7D; home_can_add_dy_2_desktop=%221%22; __live_version__=%221.1.1.2169%22; device_web_cpu_core=8; device_web_memory_size=8; xgplayer_user_id=346045893336; csrf_session_id=2e00356b5cd8544d17a0e66484946f28; odin_tt=724eb4dd23bc6ffaed9a1571ac4c757ef597768a70c75fef695b95845b7ffcd8b1524278c2ac31c2587996d058e03414595f0a4e856c53bd0d5e5f56dc6d82e24004dc77773e6b83ced6f80f1bb70627; __ac_nonce=064caded4009deafd8b89; __ac_signature=_02B4Z6wo00f01HLUuwwAAIDBh6tRkVLvBQBy9L-AAHiHf7; ttcid=2e9619ebbb8449eaa3d5a42d8ce88ec835; webcast_leading_last_show_time=1691016922379; webcast_leading_total_show_times=1; webcast_local_quality=sd; live_can_add_dy_2_desktop=%221%22; msToken=1JDHnVPw_9yTvzIrwb7cQj8dCMNOoesXbA_IooV8cezcOdpe4pzusZE7NB7tZn9TBXPr0ylxmv-KMs5rqbNUBHP4P7VBFUu0ZAht_BEylqrLpzgt3y5ne_38hXDOX8o=; msToken=jV_yeN1IQKUd9PlNtpL7k5vthGKcHo0dEh_QPUQhr8G3cuYv-Jbb4NnIxGDmhVOkZOCSihNpA2kvYtHiTW25XNNX_yrsv5FN8O6zm3qmCIXcEe0LywLn7oBO2gITEeg=; tt_scid=mYfqpfbDjqXrIGJuQ7q-DlQJfUSG51qG.KUdzztuGP83OjuVLXnQHjsz-BRHRJu4e986'
    }
    if cookies:
        headers['Cookie'] = cookies

    def get_req(url: str,
        proxy_addr: OptionalStr = None,
        headers: OptionalDict = None,
        data: dict | bytes | None = None,
        timeout: int = 20,
        content_conding: str = 'utf-8'
    ) -> str:
        if headers is None:
            headers = {}
        
        req = urllib.request.Request(url, data=data, headers = headers)

        try:
            response = opener.open(req, timeout=timeout)
            content_encoding = response.info().get('Content-Encoding')
            try:
                if content_encoding == 'gzip':
                    with gzip.open(response, 'rt', encoding=content_conding) as gzipped:
                        resp_str = gzipped.read()
                else:
                    resp_str = response.read().decode(content_conding)
            finally:
                response.close()

        except urllib.error.HTTPError as e:
            if e.code == 400:
                resp_str = e.read().decode(content_conding)
            else:
                raise
        except urllib.error.URLError as e:
            logger.error(f"URL Error: {e}")
            raise
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise

        return resp_str

    try:
        #origin_url_list = None
        html_str = get_req(url=url, proxy_addr=proxy_addr, headers=headers)
        match_json_str = re.search(r'(\{\\"state\\":.*?)]\\n"]\)', html_str)
        if not match_json_str:
            match_json_str = re.search(r'(\{\\"common\\":.*?)]\\n"]\)</script><div hidden', html_str)
        json_str = match_json_str.group(1)
        cleaned_string = json_str.replace('\\', '').replace(r'u0026', r'&')
        room_store = re.search('"roomStore":(.*?),"linkmicStore"', cleaned_string, re.DOTALL).group(1)
        #anchor_name = re.search('"nickname":"(.*?)","avatar_thumb', room_store, re.DOTALL).group(1)
        room_store = room_store.split(',"has_commerce_goods"')[0] + '}}}'
        json_data = json.loads(room_store)['roomInfo']['room']
        #json_data['anchor_name'] = anchor_name

        return json_data

        #if 'status' in json_data and json_data['status'] == 4:
        #    return json_data

        #stream_orientation = json_data['stream_url']['stream_orientation']
        #match_json_str2 = re.findall(r'"(\{\\"common\\":.*?)"]\)</script><script nonce=', html_str)
        #if match_json_str2:
        #    json_str = match_json_str2[0] if stream_orientation == 1 else match_json_str2[1]
        #    json_data2 = json.loads(
        #        json_str.replace('\\', '').replace('"{', '{').replace('}"', '}').replace('u0026', '&'))
        #    if 'origin' in json_data2['data']:
        #        origin_url_list = json_data2['data']['origin']['main']

        #else:
        #    html_str = html_str.replace('\\', '').replace('u0026', '&')
        #    match_json_str3 = re.search('"origin":\\{"main":(.*?),"dash"', html_str, re.DOTALL)
        #    if match_json_str3:
        #        origin_url_list = json.loads(match_json_str3.group(1) + '}')

        #if origin_url_list:
        #    origin_m3u8 = {'ORIGIN': origin_url_list["hls"]}
        #    origin_flv = {'ORIGIN': origin_url_list["flv"]}
        #    hls_pull_url_map = json_data['stream_url']['hls_pull_url_map']
        #    flv_pull_url = json_data['stream_url']['flv_pull_url']
        #    json_data['stream_url']['hls_pull_url_map'] = {**origin_m3u8, **hls_pull_url_map}
        #    json_data['stream_url']['flv_pull_url'] = {**origin_flv, **flv_pull_url}
        #return json_data

    except Exception as e:
        logger.error(f"First data retrieval failed: {url} Preparing to switch parsing methods due to {e}")
        #return get_douyin_app_stream_data(url=url, proxy_addr=proxy_addr, cookies=cookies)
        return {}
