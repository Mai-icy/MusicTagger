import hashlib
import json
import os
import subprocess
import time
import io

import mutagen
from mutagen.flac import FLAC
from tinytag import TinyTag


def get_album_buffer(path: str) -> io.BytesIO:
    """
    Get the album image of id3 tag and save it to temporary buffer.
    If it is FLAC, read the last of flAC's multiple images.

    :param path: The path of the file.
    :return: resulting image buffer.
    """
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



if __name__ == '__main__':
    pass
