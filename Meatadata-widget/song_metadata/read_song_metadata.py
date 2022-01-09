#!/usr/bin/python
# -*- coding:utf-8 -*-
import hashlib
import io
import json
import os
import subprocess
import time

import mutagen
from mutagen.flac import FLAC
from tinytag import TinyTag


def get_md5(file: str) -> str:
    """
    Get the md5code of file.

    :param file: The path of file.
    :return: The md5code of file
    """
    m = hashlib.md5()
    with open(file, 'rb') as f:
        for line in f:
            m.update(line)
    md5code = m.hexdigest()
    return md5code


def get_album_buffer(path: str) -> io.BytesIO:
    """
    Get the album image of id3 tag and save it to temporary buffer.
    If it is FLAC, read the last of flAC's multiple images.

    :param path: The path of the file.
    :return: resulting image buffer.
    """
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
        else:  # Flac can contain multiple images, the last of which is read here
            buffer.write(audio.pictures[-1].data)
    return buffer


def get_album_pic(path: str) -> bool:
    """
    Get and save the picture of album with md5code file name.

    :param path: The path of the file.
    :return: If picture of album exists, return True. Conversely, return False.
    """
    pic_save_path = r'..\\..\resource\album_pic\%s.jpg'
    inf = mutagen.File(path)
    artwork = b''
    if not inf.tags:
        return False
    for i in inf.tags:
        if i[:5] == 'APIC:':
            artwork = inf.tags[i].data
    if not artwork:
        return False
    md5 = get_md5(path)
    with open(pic_save_path % md5, 'wb') as f:
        f.write(artwork)
    return True


def get_song_metadata(path: str) -> dict:
    """
    Get the metadata of the song.

    :param path: The path of the song.
    :return: The metadata of the song which is a dict.
    """
    tag = TinyTag.get(path)
    suffix = os.path.splitext(path)[-1]
    file_name = os.path.splitext(os.path.basename(path))[0]
    create_time = time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(os.path.getctime(path)))
    modified_time = time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(os.path.getmtime(path)))
    # duration = int(get_len_time(path))
    duration = tag.duration
    text_duration = '%d:%d%d' % (duration // 60, duration % 60 // 10, duration % 10)
    song_info_dict = {
        "songPath": path,
        "singer": tag.artist,
        "songName": tag.title,
        "album": tag.album,
        "genre": tag.genre,
        "year": tag.year,
        "trackNumber": tag.track,
        "duration": text_duration,
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
    return song_info_dict


def get_len_time(file: str) -> float:
    """
    Gets the duration of the target music file (using ffprobe.exe)
    写了老半天发现没有用属于是

    :param file: Path to the file to obtain
    :return: The decimal unit is seconds
    """
    ffprobe_path = r'../tool/ffmpeg/bin/ffprobe.exe'
    command = [
        ffprobe_path,
        "-loglevel",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        "-i",
        file]
    result = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    out = result.stdout.read()
    temp = str(out.decode('utf-8'))
    data = json.loads(temp)["format"]['duration']
    return eval(data)


if __name__ == '__main__':
    print(get_song_metadata(r'Z:\KuGou\2021.6.21\まふまふ - 空腹.mp3'))

    # get_album_pic(r'Z:\KuGou\2021.5.1\神山羊 - Laundry.mp3')
    # get_album_pic(r'Z:\KuGou\2021.5.1\ずっと真夜中でいいのに。 - 眩しいDNAだけ.mp3')
    # get_album_pic(r'Z:\KuGou\2021.5.1\Perfume - 再生.mp3')
    # get_song_metadata(r'Z:\KuGou\2021.8.5\サカナクション - 夜の踊り子 (深夜的舞女).mp3')
    # get_song_metadata(r'Z:\.....机房共享文件\flac歌曲\YOASOBI\03.ハルジオン.flac')
    # get_song_metadata(r'Z:\.....机房共享文件\flac歌曲\ずっと真夜中でいいのに。\01_01_ばかじゃないのに_ずっと真夜中でいいのに。.wav')
    # get_len_time(r'Z:\.....机房共享文件\flac歌曲\ずっと真夜中でいいのに。\01_01_ばかじゃないのに_ずっと真夜中でいいのに。.wav')
    # print(base_name_parse(r'Z:\KuGou\2021.8.5\サカナクション - 夜の踊り子 (深夜的舞女).mp3'))

