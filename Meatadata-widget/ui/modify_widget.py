# encoding: utf - 8
import io
import sys

from PIL import Image, ImageQt
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from ui.ui_source.ModifyWidget import Ui_ModifyWidget


class ModifyWidget(QWidget, Ui_ModifyWidget):
    done_signal = pyqtSignal(dict, io.BytesIO)

    def __init__(self, parent=None):
        super(ModifyWidget, self).__init__(parent)
        self.setupUi(self)
        self._init_signal()
        self.duration_lineEdit.setEnabled(False)
        self.pic_label.setScaledContents(True)
        self.buffer = io.BytesIO()

    def _init_signal(self):
        self.done_button.clicked.connect(self.done_event)
        self.upload_pic_button.clicked.connect(self.upload_pic_event)

    def upload_pic_event(self) -> None:
        """
        Upload images and display them.

        :return: None
        """
        pic_path = QFileDialog.getOpenFileName(self, u"打开图片文件", "", "image files(*.jpg)")[0]
        if not pic_path:
            return
        pix = Image.open(pic_path).toqpixmap()

        self.pic_label.setScaledContents(True)
        self.pic_label.setPixmap(pix)

        with open(pic_path, 'rb') as f:
            self.buffer.close()
            self.buffer = io.BytesIO(f.read())

    def done_event(self) -> None:
        """
        Get data from lineEdits of widget. And send a signal containing data to the main window responsible for writing

        :return: None
        """
        song_info = {
            'songName': self.song_name_lineEdit.text(),
            'singer': self.singer_lineEdit.text(),
            'genre': self.genre_lineEdit.text(),
            'year': self.year_lineEdit.text(),
            'album': self.album_lineEdit.text(),
            'trackNumber': self.track_number_lineEdit.text(),
            'picUrl': None
        }
        self.done_signal.emit(song_info, self.buffer)
        self.close()

    def load_song_info(self, song_info: dict, pic_buffer: io.BytesIO):
        """
        Renders the data that the song originally contained.

        :param song_info: The dict of song metadata.
        :param pic_buffer: Buffers containing original images.
        :return:
        """
        self.duration_lineEdit.setText(song_info['duration'])
        if song_info['year']:
            self.year_lineEdit.setText(song_info['year'])
        if song_info['album']:
            self.album_lineEdit.setText(song_info['album'])
        if song_info['genre']:
            self.genre_lineEdit.setText(song_info['genre'])
        if song_info['singer']:
            self.singer_lineEdit.setText(song_info['singer'])
        if song_info['songName']:
            self.song_name_lineEdit.setText(song_info['songName'])
        if song_info['trackNumber']:
            self.track_number_lineEdit.setText(song_info['trackNumber'])
        if pic_buffer.getvalue():
            pic_data = Image.open(pic_buffer)
            q_image = ImageQt.toqpixmap(pic_data)
            self.pic_label.clear()
            self.pic_label.setPixmap(q_image)
            pic_buffer.close()


if __name__ == "__main__":
    # 适配2k等高分辨率屏幕,低分辨率屏幕可以缺省
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    myWin = ModifyWidget()
    myWin.show()
    sys.exit(app.exec_())
