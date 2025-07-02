# encoding: utf - 8
import sys

from PIL import Image, ImageQt
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from ui.ui_source.ModifyDialog import Ui_ModifyDialog
from song_metadata.metadata_type import SongInfo
from components.mask_widget import MaskWidget


class ModifyDialog(QDialog, Ui_ModifyDialog):
    done_signal = pyqtSignal(SongInfo, str)

    def __init__(self, parent=None):
        super(ModifyDialog, self).__init__(parent)
        self.setupUi(self)
        self._init_signal()
        self._init_setting()

        self.pic_path = ""

    def _init_signal(self):
        self.upload_pic_button.clicked.connect(self.upload_pic_event)

    def _init_setting(self):
        self.pic_label.setText("还没有图片哦")
        self.pic_label.setScaledContents(True)
        self.year_lineEdit.setValidator(QRegExpValidator(QRegExp("[0-9]{,4}")))
        self.track_number_lineEdit.setValidator(QRegExpValidator(QRegExp("[0-9]{,3}")))

    def upload_pic_event(self) -> None:
        """上传图片并显示"""
        pic_path = QFileDialog.getOpenFileName(self, u"打开图片文件", "", "image files(*.jpg,*.png)")[0]
        if not pic_path:
            return
        img = Image.open(pic_path)
        q_img = QImage.fromData(img.getdata())
        pix = QPixmap.fromImage(q_img)

        self.pic_label.setScaledContents(True)
        self.pic_label.setPixmap(pix)

        self.pic_path = pic_path

    def load_song_info(self, song_info: SongInfo):
        """
        Renders the data that the song originally contained.

        :param song_info: The dict of song metadata.
        """
        if song_info.year:
            self.year_lineEdit.setText(song_info.year)
        if song_info.album:
            self.album_lineEdit.setText(song_info.album)
        if song_info.genre:
            self.genre_lineEdit.setText(song_info.genre)
        if song_info.singer:
            self.singer_lineEdit.setText(song_info.singer)
        if song_info.songName:
            self.song_name_lineEdit.setText(song_info.songName)
        if song_info.trackNumber:
            self.track_number_lineEdit.setText(song_info.trackNumber)
        if song_info.picBuffer.getvalue():
            q_img = QImage.fromData(song_info.picBuffer.getvalue())
            q_image = QPixmap.fromImage(q_img)
            self.pic_label.clear()
            self.pic_label.setPixmap(q_image)

    def accept(self) -> None:
        song_info = {
            'songName': self.song_name_lineEdit.text(),
            'singer': self.singer_lineEdit.text(),
            'genre': self.genre_lineEdit.text(),
            'year': self.year_lineEdit.text(),
            'album': self.album_lineEdit.text(),
            'trackNumber': self.track_number_lineEdit.text(),
            'picBuffer': None,
            'duration': None
        }
        self.done_signal.emit(SongInfo(**song_info), self.pic_path)
        super(ModifyDialog, self).accept()

    def show(self) -> None:
        self._set_mask_visible(True)
        super(ModifyDialog, self).show()

    def done(self, a0: int) -> None:
        self._set_mask_visible(False)
        super(ModifyDialog, self).done(a0)

    def _set_mask_visible(self, flag: bool):
        if self.parent():
            if not hasattr(self.parent(), "mask_widget"):
                self.parent().mask_widget = MaskWidget(self.parent())
            if flag:
                self.parent().mask_widget.show()
            else:
                self.parent().mask_widget.hide()


if __name__ == "__main__":
    # 适配2k等高分辨率屏幕,低分辨率屏幕可以缺省
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    myWin = ModifyDialog()
    myWin.show()
    sys.exit(app.exec_())
