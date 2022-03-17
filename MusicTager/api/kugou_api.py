#!/usr/bin/python
# -*- coding:utf-8 -*-
import re
import io

import base64
from typing import List, Dict
import requests
from lyric_decode.lyric_decode import KrcFile
from song_metadata.metadata_type import SongInfo, SongSearchInfo
from api.api_error import NoneResultError

header = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:7.0a1) Gecko/20110623 Firefox/7.0a1 Fennec/7.0a1'}


class KugouApi:
    def __init__(self):
        # 获取hash值需要搜索关键词。获取access_key和id需要hash值。下载文件需要access_key和id
        self._get_hash_search_url = 'http://mobilecdn.kugou.com/api/v3/search/song?format=json&keyword={}&page={}&pagesize=20&showtype=1 '
        self._get_key_search_url = 'http://krcs.kugou.com/search?ver=1&man=yes&client=mobi&keyword=&duration=&hash={}'
        self._get_lrc_url = 'http://lyrics.kugou.com/download?ver=1&client=pc&id={}&accesskey={}&fmt={}&charset=utf8'
        self._album_info_url = 'http://mobilecdn.kugou.com/api/v3/album/info?albumid={}&plat=0&pagesize=100&area_code=1'
        self._song_info_url = 'http://m.kugou.com/app/i/getSongInfo.php?cmd=playInfo&hash={}'

        self.total_num = 0

    def search_hash(self, keyword: str, page: object = 1) -> List[SongSearchInfo]:
        """
        Query the basic information and MD5 value of a song.

        :rtype: object
        :param keyword: The words you want to search for
        :param page: the number of page
        :return: Contains a list of basic song information
        """
        keyword = re.sub(r"|[!@#$%^&*/]+", "", keyword)
        url = self._get_hash_search_url.format(keyword, page)
        res_json = requests.get(url, headers=header).json()
        song_info_list = []
        self.total_num = res_json['data']['total']
        for data in res_json['data']['info']:
            duration = data["duration"]
            # album = data["duration"]
            # suffix = "." + data["extname"],
            song_info = {
                "singer": data["singername"],
                "songName": data["songname"],
                "duration": f'{duration // 60}:{duration % 60 // 10}{duration % 10}',
                "idOrMd5": data["hash"]
            }
            song_info_list.append(SongSearchInfo(**song_info))
        return song_info_list

    def get_song_info(self, md5: str) -> SongInfo:
        """
        Get filtered song information based on song ID in CloudMusic API.

        :param md5: md5 of song.
        :return: Filtered song information in dict.
        """
        song_json = requests.get(self._song_info_url.format(md5), headers=header).json()
        duration = song_json["timeLength"]
        album_img = str(song_json["album_img"])

        album_id = song_json["albumid"]  # album_id = 0
        if album_id == 0:
            album = None
            year = None
        else:
            album_json = requests.get(self._album_info_url.format(album_id), headers=header).json()
            album = album_json["data"].get("albumname", None)
            year = album_json["data"].get("publishtime", None)

        pic_url = album_img.replace("/{size}/", "/")
        if pic_url:
            pic_data = requests.get(pic_url).content
            pic_buffer = io.BytesIO(pic_data)
        else:
            pic_buffer = io.BytesIO()

        song_info = {
            "singer": song_json["author_name"],
            "songName": song_json["songName"],
            "album": album,
            "year": year,  # 例 '2021-08-11 00:00:00'
            "trackNumber": None,  # 实在难搞w
            "duration": f'{duration // 60}:{duration % 60 // 10}{duration % 10}',
            "genre": None,
            "picBuffer": pic_buffer}
        return SongInfo(**song_info)

    def get_lrc_info(self, md5: str) -> List[Dict[str, str]]:
        """
        Obtain the lyrics information and key to be downloaded using the MD5 value.

        :param md5: MD5 value of song.
        :return: Contains a list of basic lyrics data.
        """
        url = self._get_key_search_url.format(md5)
        res_json = requests.get(url, headers=header).json()
        if res_json['errcode'] != 200:
            raise requests.RequestException
        res_list = []
        for data in res_json['candidates']:
            duration = data["duration"] // 1000
            lyric_info = {
                "songName": data["song"],
                "id": data["id"],
                "key": data["accesskey"],
                "score": data["score"],
                "source": data["product_from"],
                "duration": f'{duration // 60}:{duration % 60 // 10}{duration % 10}'
            }
            res_list.append(lyric_info)
        if res_list:
            return res_list
        else:
            raise NoneResultError

    def get_lrc(self, lyric_info: dict) -> KrcFile:
        """
        Get lyric content.

        :param lyric_info: The info of lyric.
        :return: Content of the lyrics.
        """
        url = self._get_lrc_url.format(lyric_info["id"], lyric_info["key"], 'krc')
        res_json = requests.get(url).json()
        content = res_json['content']
        result = base64.b64decode(content.encode())

        krc_file = KrcFile()
        krc_file.load_content(result)
        return krc_file


if __name__ == '__main__':
    a = KugouApi()
    print(a.get_song_info('f6463b5a6fd6b237ff81f53aea3cdc4e'))
    # b = a.get_lrc({'songName': 'ねぇねぇねぇ。', 'id': '56752254', 'key': 'B234B3AD9B04997104CE5C24CAD1531B', 'score': 60, 'source': 'ugc', 'duration': '3:30'})
    # print(b.save_to_mrc('1.mrc'))
