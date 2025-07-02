#!/usr/bin/python
# -*- coding:utf-8 -*-
import os

import requests
from mutagen import id3, mp4, flac
from song_metadata.metadata_type import SongInfo


def write_song_metadata(song_path: str, song_info: SongInfo, pic_path: str = None) -> tuple:
    """
    判断目标文件的格式，若格式错误则调整，并返回调整前后的格式

    :return: 若文件格式错标，则返回原格式和错标格式
    """
    suffix = os.path.splitext(song_path)[-1]
    try:
        if suffix == ".flac":
            write_flac_metadata(song_path, song_info, pic_path)
        elif suffix == ".mp3":
            write_mp3_metadata(song_path, song_info, pic_path)
        elif suffix == ".mp4" or suffix == ".m4a":
            write_mp4_metadata(song_path, song_info, pic_path)
        return ()
    except (id3.ID3NoHeaderError, mp4.MP4StreamInfoError, flac.FLACNoHeaderError):
        for file_format, func, error in [(".mp4", write_mp4_metadata, mp4.MP4StreamInfoError),
                                         (".mp3", write_mp3_metadata, id3.ID3NoHeaderError),
                                         (".flac", write_flac_metadata, flac.FLACNoHeaderError)]:
            try:
                _ = func(song_path)
            except error:
                continue
            # 可能抛出mutagen的未知错误
            else:
                return file_format, suffix
        else:
            raise TypeError("文件格式不正确")


def write_flac_metadata(song_path: str, song_info: SongInfo, pic_path: str = None):
    """为flac文件写入元数据标签 pic_path为封面图片，格式要求为png或者jpg"""
    audio = flac.FLAC(song_path)
    if song_info.songName:
        audio["TITLE"] = song_info.songName
    if song_info.singer:
        audio["ARTIST"] = song_info.singer
        audio["ALBUMARIST"] = song_info.singer
    if song_info.album:
        audio["ALBUM"] = song_info.album
    if song_info.trackNumber:
        audio["TRACKNUMBER"] = str(song_info.trackNumber[0])
    if song_info.year:
        audio["DATE"] = song_info.year
    if song_info.genre:
        audio["GENRE"] = song_info.genre
    if song_info.lyric:
        audio["LYRICS"] = song_info.lyric
    pic = flac.Picture()
    pic.type = id3.PictureType.COVER_FRONT
    pic.width = 500
    pic.height = 500
    pic.depth = 16  # color depth
    if pic_path:
        pic.mime = u"image/png" if pic_path.endswith("png") else u"image/jpeg"
        pic.data = open(pic_path, 'rb').read()
        if len(audio.pictures):
            audio.clear_pictures()
        audio.add_picture(pic)
    elif song_info.picBuffer:
        if song_info.picBuffer.getvalue():
            pic.mime = u"image/jpeg"
            pic.data = song_info.picBuffer.getvalue()
            audio.add_picture(pic)
    audio.save()


def write_mp3_metadata(song_path: str, song_info: SongInfo, pic_path: str = None):
    """为mp3文件写入ID3标签 pic_path为封面图片，格式要求为png或者jpg"""
    audio = id3.ID3(song_path)
    if song_info.songName:
        audio["TIT2"] = id3.TIT2(text=song_info.songName)
    if song_info.singer:
        audio["TPE1"] = id3.TPE1(text=song_info.singer)
    if song_info.album:
        audio["TALB"] = id3.TALB(text=song_info.album)
    if song_info.trackNumber:
        audio["TRCK"] = id3.TRCK(text=str(song_info.trackNumber[0]))
    if song_info.year:
        audio["TYER"] = id3.TYER(text=song_info.year)
    if song_info.genre:
        audio["TCON"] = id3.TCON(text=song_info.genre)
    if song_info.lyric:
        audio.add(id3.USLT(encoding=3, lang='eng', desc='desc', text=song_info.lyric))
    if pic_path:
        mime = 'image/png' if pic_path.endswith("png") else 'image/jpeg'
        with open(pic_path, 'rb') as f:
            audio["APIC:"] = id3.APIC(encoding=3, mime=mime, type=3, data=f.read())
    elif song_info.picBuffer:
        if song_info.picBuffer.getvalue():
            audio["APIC:"] = id3.APIC(encoding=3, mime='image/jpeg', type=3, data=song_info.picBuffer.getvalue())
    audio.update_to_v23()
    audio.save(v2_version=3)
    return True


def write_mp4_metadata(song_path: str, song_info: SongInfo, pic_path: str = None):
    """为mp4，m4a等mp4容器写入元数据标签 pic_path为封面图片，格式要求为png或者jpg """
    audio = mp4.MP4(song_path)
    if song_info.songName:
        audio["\xa9nam"] = song_info.songName
    if song_info.singer:
        audio["\xa9ART"] = song_info.singer
        audio["aART"] = song_info.singer
    if song_info.year:
        audio["\xa9day"] = song_info.year
    if song_info.genre:
        audio["\xa9gen"] = song_info.genre
    if song_info.album:
        audio["\xa9alb"] = song_info.album
    if song_info.trackNumber:
        audio["trkn"] = [(1, 10)]
    if pic_path:
        img_format = mp4.MP4Cover.FORMAT_PNG if pic_path.endswith("png") else mp4.MP4Cover.FORMAT_JPEG
        with open(pic_path, 'rb') as f:
            audio["covr"] = [mp4.MP4Cover(f.read(), imageformat=img_format)]
    elif song_info.picBuffer:
        if song_info.picBuffer.getvalue():
            audio["covr"] = [mp4.MP4Cover(song_info.picBuffer.getvalue(), imageformat=mp4.MP4Cover.FORMAT_JPEG)]
    audio.save()


if __name__ == "__main__":
    # FLAC(r'Z:\KuGou\2021.6.21\まふまふ - 空腹.mp3')
    id3.ID3(r"Z:\.....机房共享文件\flac歌曲\ずっと真夜中でいいのに。\眩しいDNAだけ.flac")
