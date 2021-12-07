import requests
import time
import os

LRC_PATH = os.path.abspath(os.path.dirname(__file__)) + '..\\..\\resource\\Lyric\\'

class CloudMusicApi(object):
    def __init__(self):
        self.search_url = 'http://music.163.com/api/search/pc'  # post
        self.download_lrc_url = 'http://music.163.com/api/song/media?id=%d'  # get 需要歌曲id
        self.id_list = []

    def search_data(self, keyword: str, limit: int, search_type: int):
        self.id_list = []
        data = {
            's': keyword,
            'offset': 0,
            'limit': limit,
            'type': search_type,
        }  # 类型(歌曲：1、专辑：10、歌手：100、歌单：1000、用户：1002、mv：1004)
        res_json = requests.post(self.search_url, data=data).json()
        print(res_json)
        if not res_json['result']['songs']:
            return
        for song_data in res_json['result']['songs']:
            artist_name = ''
            song_id = song_data['id']
            song_name = song_data['name']
            for artist_data in song_data['artists']:
                artist_name += artist_data['name'] + ' '
            album_data = song_data['album']
            album_name = album_data['name']
            album_pic_url = album_data['picUrl']
            self.id_list.append(song_id)
            print(song_name, artist_name, album_name)

    def download_lrc(self, id_index, song_id=None):
        if not song_id:
            song_id = self.id_list[id_index]
        res_json = requests.get(self.download_lrc_url % song_id).json()
        print(res_json)


class CloudMusicWebApi(object):
    def __init__(self):
        self.search_url = 'https://music.163.com/api/search/get/web?&s=%s&type=1&offset=%d&total=true&limit=20'
        self.song_info_url = 'http://music.163.com/api/song/detail/?id=%d&ids=[%d]'
        self.download_lrc_url = 'http://music.163.com/api/song/media?id=%d'  # get 需要歌曲id

    def search_song_info(self, song_id: int) -> dict:
        """
        Get filtered song information based on song ID in API.

        :param song_id: song ID in API.
        :return: Filtered song information in dict.
        """
        res_json = requests.post(
            self.song_info_url %
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
        res_json = requests.post(self.search_url % (word, page * 20)).json()
        res_list = []
        if res_json["result"] == {} or res_json['code'] == 400 or res_json["result"]['songCount'] == 0:  # 该关键词没有结果数据
            return []
        for data in res_json["result"]["songs"]:
            duration = data["duration"] // 1000
            artists_list = []
            for artist_info in data["artists"]:
                artists_list.append(artist_info["name"])
            song_data = {
                "songId": data['id'],
                "songName": data['name'],
                "singer": ','.join(artists_list),
                "duration": '%d:%d%d' % (duration // 60, duration % 60 // 10, duration % 10),
            }
            res_list.append(song_data)
        return res_list

    def download_lrc(self, song_id: int, song_info: dict = None) -> bool:
        """
        Download the lyrics file of the corresponding song, save the name by the artist,
        the song name and MD5 value separated by ' - ', the suffix is LRC

        :param song_id:
        :param song_info: The song data obtained using function get_song_metadata
        :return:
        """
        res_json = requests.get(self.download_lrc_url % song_id).json()
        lrc_data = res_json['lyric']
        if song_info:
            file_name = ' - '.join([song_info['singer'], song_info['songName'], song_info['md5']]) + '.lrc'
            with open(LRC_PATH + file_name, 'w', encoding='utf-8') as f:
                f.write(lrc_data)
                f.close()
                return True
        else:
            # todo 预备方案待定
            return False



if __name__ == '__main__':
    # todo 各种错误的排查
    a = CloudMusicWebApi()
    # print(a.search_data('mili'))
    # print(a.search_data('mili', 1))
    print(a.search_song_info(1887467089))
    # a.download_lrc(1887467089)
