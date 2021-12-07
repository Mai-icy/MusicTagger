# encoding: utf-8
import sys
import os
import io
import requests

from PIL import Image

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from ui.ui_source.MetadataWidget import Ui_MetadataWidget
from ui.modify_widget import ModifyWidget
import song_metadata as sm
from api.cloud_api import CloudMusicWebApi


class MetadataWidget(QWidget, Ui_MetadataWidget):
    def __init__(self, parent=None):
        super(MetadataWidget, self).__init__(parent)
        self.setupUi(self)
        self.modify_widget = ModifyWidget()
        self._init_signal()
        self._init_table_widgets()
        self.cloud_api = CloudMusicWebApi()

        self.song_info = {}

    def _init_signal(self):
        self.add_file_button.clicked.connect(self.add_file_event)
        self.delete_file_button.clicked.connect(self.delete_file_event)
        self.confirm_buton.clicked.connect(self.write_event)
        self.search_button.clicked.connect(self.search_event)
        self.pass_button.clicked.connect(self.pass_event)
        self.modify_button.clicked.connect(self.modify_event)

        self.file_listWidget.itemClicked.connect(self.path_click_event)
        self.search_tableWidget.itemClicked.connect(self.result_click_event)

        self.modify_widget.done_signal.connect(self.modify_done_event)

    def _init_table_widgets(self):
        self.search_tableWidget.horizontalHeader().setVisible(True)
        self.search_tableWidget.horizontalHeader().setHighlightSections(True)
        self.search_tableWidget.horizontalHeader().setSortIndicatorShown(False)
        self.search_tableWidget.horizontalHeader().setStretchLastSection(False)

        self.search_tableWidget.verticalHeader().setVisible(False)
        self.search_tableWidget.setShowGrid(False)

        self.search_tableWidget.horizontalHeader().setDefaultAlignment(Qt.AlignLeft)

        self.search_tableWidget.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.search_tableWidget.verticalHeader().setDefaultSectionSize(47)
        self.search_tableWidget.horizontalHeader().setMinimumHeight(30)  # 表头高度

        self.search_tableWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.search_tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.search_tableWidget.clear()
        self.search_tableWidget.setColumnCount(4)

        self.search_tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.search_tableWidget.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.search_tableWidget.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        # self.setColumnWidth(0, 380)  # 设置指定列宽
        self.search_tableWidget.setColumnWidth(2, 55)
        self.search_tableWidget.setColumnWidth(3, 55)

        column_text_list = ['曲名', '歌手', '时长', 'id']
        for column in range(0, 4):
            item = QTableWidgetItem()
            item.setText(column_text_list[column])
            self.search_tableWidget.setHorizontalHeaderItem(column, item)
        self.search_tableWidget.hideColumn(3)

    def add_file_event(self) -> None:
        file_name_list = QFileDialog.getOpenFileNames(self, u"打开文件", "", "Music files(*.mp3 *.flac)")[0]
        self.file_listWidget.addItems(file_name_list)

    def delete_file_event(self) -> None:
        if self.file_listWidget and self.file_listWidget.selectedIndexes():
            row = self.file_listWidget.selectedIndexes()[0].row()
            self.file_listWidget.removeItemWidget(self.file_listWidget.takeItem(row))

    def path_click_event(self, item) -> None:
        """
        Analyze the selected file data and display and search.

        :param item: The clicked item.
        :return: None
        """
        song_data = sm.get_song_metadata(item.text())
        self.set_left_text(self.path_label, item.text())
        self.set_left_text(self.filename_label, os.path.basename(item.text()))
        self.set_left_text(self.original_song_name_label, song_data['songName'])
        self.set_left_text(self.original_singer_label, song_data['singer'])
        self.set_left_text(self.original_duration_label, song_data['duration'])
        self.set_left_text(self.original_md5_label, song_data['md5'])
        """
        self.path_label.setText(item.text())
        self.filename_label.setText(os.path.basename(item.text()))
        self.original_song_name_label.setText(song_data['songName'])
        self.original_singer_label.setText(song_data['singer'])
        self.original_duration_label.setText(song_data['duration'])
        self.original_md5_label.setText(song_data['md5'])
        """
        if song_data['singer'] and song_data['songName']:
            keyword = '-'.join([song_data['singer'], song_data['songName']])
        else:
            keyword = os.path.basename(item.text())
        self.search_lineEdit.setText(keyword)
        self.search_event()

    def result_click_event(self, item) -> None:
        """
        When you click on the content in the TableWidget,
        display the metadata of the search results for the corresponding ID.

        :param item: The clicked item
        :return: None
        """
        song_id = int(self.search_tableWidget.item(item.row(), 3).text())
        self.song_info = self.cloud_api.search_song_info(song_id)
        pic_res = requests.get(self.song_info['picUrl'])
        pix = Image.open(io.BytesIO(pic_res.content)).toqpixmap()

        self.result_pic_label.setScaledContents(True)
        self.result_pic_label.setPixmap(pix)
        self.set_left_text(self.result_genre_label, 'N/A')
        self.set_left_text(self.result_year_label, self.song_info['year'])
        self.set_left_text(self.result_album_label, self.song_info['album'])
        self.set_left_text(self.result_singer_label, self.song_info['singer'])
        self.set_left_text(self.result_duration_label, self.song_info['duration'])
        self.set_left_text(self.result_song_name_label, self.song_info['songName'])
        self.set_left_text(self.result_track_number_label, self.song_info['trackNumber'])

    def write_event(self, pic_buffer: io.BytesIO = None) -> None:
        """
        Be sure to write metadata and point to the next song path in the list.
        Item's background turns gray on success and red on failure.

        :param args:
        :param pic_buffer: Custom image
        :return: None
        """
        if self.song_info:
            file_path = self.file_listWidget.currentItem().text()
            if os.path.splitext(file_path)[1] == '.mp3':
                if pic_buffer.getvalue():
                    is_success = sm.write_mp3_metadata(file_path, self.song_info, pic_buffer)
                else:
                    is_success = sm.write_mp3_metadata(file_path, self.song_info)
            elif os.path.splitext(file_path)[1] == '.flac':
                if pic_buffer.getvalue():
                    is_success = sm.write_flac_metadata(file_path, self.song_info, pic_buffer)
                else:
                    is_success = sm.write_flac_metadata(file_path, self.song_info)
            else:
                is_success = False
            item = self.file_listWidget.currentItem()
            if is_success:
                item.setBackground(QColor(Qt.lightGray))
            else:
                item.setBackground(QColor(Qt.red))

            self.song_info.clear()
            self.file_listWidget.setCurrentRow(self.file_listWidget.currentRow() + 1)
            if self.file_listWidget.selectedItems():
                self.path_click_event(self.file_listWidget.selectedItems()[0])

    def search_event(self) -> None:
        """
        Search for corresponding data displayed in the TableWidget.

        :return: None
        """
        keyword = self.search_lineEdit.text()
        if keyword:
            search_res_data = self.cloud_api.search_data(keyword)
            self.__load_search_data(search_res_data)

    def pass_event(self) -> None:
        """
        Skip the path chosen on the left and select the next one.

        :return: None
        """
        self.song_info.clear()
        self.file_listWidget.setCurrentRow(self.file_listWidget.currentRow() + 1)
        if self.file_listWidget.selectedItems():
            self.path_click_event(self.file_listWidget.selectedItems()[0])

    def modify_event(self) -> None:
        if not self.file_listWidget.currentItem():
            return
        song_info = sm.get_song_metadata(self.file_listWidget.currentItem().text())
        pic_buffer = sm.get_album_buffer(self.file_listWidget.currentItem().text())
        self.modify_widget.load_song_info(song_info, pic_buffer)
        self.modify_widget.show()

    def modify_done_event(self, song_info: dict, pic_buffer: io.BytesIO) -> None:
        """
        Receives data from modify widget and writes into file.

        :param song_info: Song metadata entered by the user.
        :param pic_buffer: ictures uploaded by users.
        :return: None
        """
        self.song_info = song_info
        self.write_event(pic_buffer=pic_buffer)

    def __load_search_data(self, search_data: list) -> None:
        """
        load the search result to the table

        :param search_data: made by CloudWebApi.search_data.
        :return: None
        """
        self.search_tableWidget.clearContents()
        self.search_tableWidget.setRowCount(len(search_data))
        for index, data in enumerate(search_data):
            item = QTableWidgetItem()
            item.setText(data['songName'])
            self.search_tableWidget.setItem(index, 0, item)

            item = QTableWidgetItem()
            item.setText(data['singer'])
            self.search_tableWidget.setItem(index, 1, item)

            item = QTableWidgetItem()
            item.setText(data['duration'])
            self.search_tableWidget.setItem(index, 2, item)

            item = QTableWidgetItem()
            item.setText(str(data['songId']))
            self.search_tableWidget.setItem(index, 3, item)

        if search_data:  # 自动选中当前第一个
            self.search_tableWidget.selectRow(0)
            self.result_click_event(self.search_tableWidget.selectedItems()[0])

    @staticmethod
    def set_left_text(label: QLabel, text: str) -> None:
        """
        Displays the text content on the label and replaces
         the extra text with an ellipsis.

        :param label: The label that needs to display the text.
        :param text: The text you want to show.
        :return: None
        """
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)  # 设置label可复制
        metrics = QFontMetrics(label.font())
        new_text = metrics.elidedText(text, Qt.ElideRight, label.width())
        label.setText(new_text)




if __name__ == "__main__":
    # 适配2k等高分辨率屏幕,低分辨率屏幕可以缺省
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    myWin = MetadataWidget()
    myWin.show()
    sys.exit(app.exec_())





