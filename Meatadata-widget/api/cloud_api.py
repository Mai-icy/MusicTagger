#!/usr/bin/python
# -*- coding:utf-8 -*-
import requests
import time
from lyric_decode.lyric_decode import LrcFile


class CloudMusicWebApi(object):
    def __init__(self):
        self.__search_url = 'https://music.163.com/api/search/get/web?&s=%s&type=1&offset=%d&total=true&limit=20'
        self.__song_info_url = 'http://music.163.com/api/song/detail/?id=%s&ids=[%s]'
        self.__download_lrc_url = 'http://music.163.com/api/song/lyric?id=%s&lv=-1&kv=-1&tv=-1&rv=-1'  # get 需要歌曲id

    def get_song_info(self, song_id: str) -> dict:
        """
        Get filtered song information based on song ID in CloudMusic API.

        :param song_id: song ID in API.
        :return: Filtered song information in dict.
        """
        res_json = requests.post(
            self.__song_info_url %
            (song_id, song_id)).json()
        song_json = res_json['songs'][0]
        artists_list = []
        for artist_info in song_json["artists"]:
            artists_list.append(artist_info["name"])
        # todo genre 曲目风格在json中并未找到
        duration = song_json["duration"] // 1000
        song_info = {
            "singer": ','.join(artists_list),
            "songName": song_json["name"],
            "album": song_json["album"]["name"],
            "year": str(time.localtime(song_json["album"]["publishTime"] // 1000).tm_year),
            "trackNumber": str(song_json["no"]),
            "duration": '%d:%d%d' % (duration // 60, duration % 60 // 10, duration % 10),
            "genre": None,
            "picUrl": song_json["album"]["picUrl"]}
        return song_info

    def search_data(self, word: str, page: int = 0) -> list:
        """
        Get rough information about search term results songs.

        :param page: page of search api
        :param word: keyword
        :return: A list containing brief information about the search results.
        """
        word = word.replace('#', '')
        res_json = requests.post(self.__search_url % (word, page * 20)).json()
        res_list = []
        if res_json["result"] == {} or res_json['code'] == 400 or res_json["result"]['songCount'] == 0:  # 该关键词没有结果数据
            return []
        for data in res_json["result"]["songs"]:
            duration = data["duration"] // 1000
            artists_list = []
            for artist_info in data["artists"]:
                artists_list.append(artist_info["name"])
            song_data = {
                "songId": str(data['id']),
                "songName": data['name'],
                "singer": ','.join(artists_list),
                "duration": '%d:%d%d' % (duration // 60, duration % 60 // 10, duration % 10),
            }
            res_list.append(song_data)
        return res_list

    def get_lrc(self, song_id: str) -> LrcFile:
        """
        Download the lyrics file of the corresponding song.

        :param song_id:
        :return:
        """
        res_json = requests.get(self.__download_lrc_url % song_id).json()
        res_json = dict(res_json)
        lrc_file = LrcFile()
        lrc_file.load_content(res_json['lrc']['lyric'], 'non')
        if 'tlyric' in res_json.keys():
            lrc_file.load_content(res_json['tlyric']['lyric'], 'chinese')
        if 'romalrc' in res_json.keys():
            lrc_file.load_content(res_json['romalrc']['lyric'], 'romaji')
        return lrc_file


if __name__ == '__main__':
    # todo 各种错误的排查
    a = CloudMusicWebApi()
    # # print(a.search_data('mili'))
    # print(a.search_data('CheerS-Claris', 0))
    b = a.get_lrc("1301572361")
    # print(b.get_content('romaji'))
    # a.download_lrc(1887467089)
