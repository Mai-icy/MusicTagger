#!/usr/bin/python
# -*- coding:utf-8 -*-
import io
import os
import time
import hashlib
import collections

import mutagen
from pymediainfo import MediaInfo
from song_metadata.metadata_type import SongInfo, SongElseInfo
from mutagen.flac import FLAC
from tinytag import TinyTag


def get_md5(file: str) -> str:
    """获取文件的md5值"""
    m = hashlib.md5()
    with open(file, 'rb') as f:
        for line in f:
            m.update(line)
    md5code = m.hexdigest()
    return md5code


def get_album_buffer(path: str) -> io.BytesIO:
    """获取文件的封面数据，并保存到io缓冲"""
    if not os.path.exists(path):
        raise FileNotFoundError(f"No such file or directory: '{path}', can't get pic buffer.")
    buffer = io.BytesIO()
    suffix = os.path.splitext(path)[1]
    if suffix == '.mp3':
        inf = mutagen.File(path)
        artwork = b''
        if not inf.tags:
            return buffer
        for i in inf.tags:
            if i[:5] == 'APIC:':
                artwork = inf.tags[i].data
        if not artwork:
            return buffer
        buffer.write(artwork)
    elif suffix == '.flac':
        audio = FLAC(path)
        if len(audio.pictures) == 0:
            return buffer
        else:  # flac可以有多个图片，这里只读取一个
            buffer.write(audio.pictures[-1].data)
    return buffer


def read_song_metadata(path: str) -> (SongInfo, SongElseInfo):
    """获取文件的元数据"""
    tag = TinyTag.get(path)
    suffix = os.path.splitext(path)[-1]
    file_name = os.path.splitext(os.path.basename(path))[0]
    create_time = time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(os.path.getctime(path)))
    modified_time = time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(os.path.getmtime(path)))
    duration = tag.duration
    if path.endswith("m4a") or path.endswith("mp4"):
        media = MediaInfo.parse("..//DECO27 - パラサイト feat. 初音ミク.mp4")
        duration = round(media.tracks[0].duration / 1000)

    pic_buffer = get_album_buffer(path)

    text_duration = '%d:%d%d' % (duration // 60, duration % 60 // 10, duration % 10)
    song_info_dict = {
        "singer": tag.artist,
        "songName": tag.title,
        "album": tag.album,
        "genre": tag.genre,
        "year": tag.year,
        "trackNumber": tag.track,
        "picBuffer": pic_buffer,
        "duration": text_duration
    }
    else_info = {
        "songPath": path,
        "suffix": suffix,
        "coverName": None,
        "createTime": create_time,
        "modifiedTime": modified_time,
        "md5": get_md5(path)
    }
    if len(file_name.split(' - ')) == 2:
        if not song_info_dict['songName']:
            song_info_dict['songName'] = file_name.split(' - ')[1]
        if not song_info_dict['singer']:
            song_info_dict['singer'] = file_name.split(' - ')[0]
    return SongInfo(**song_info_dict), SongElseInfo(**else_info)


if __name__ == '__main__':
    print(read_song_metadata(r'Z:\KuGou\2021.6.21\まふまふ - 空腹.mp3'))
    # get_album_pic(r'Z:\KuGou\2021.5.1\神山羊 - Laundry.mp3')
    # get_album_pic(r'Z:\KuGou\2021.5.1\ずっと真夜中でいいのに。 - 眩しいDNAだけ.mp3')
    # get_album_pic(r'Z:\KuGou\2021.5.1\Perfume - 再生.mp3')
    # print(base_name_parse(r'Z:\KuGou\2021.8.5\サカナクション - 夜の踊り子 (深夜的舞女).mp3'))
