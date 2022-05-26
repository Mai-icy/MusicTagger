#!/usr/bin/python
# -*- coding:utf-8 -*-
import re
import os
import sys
import time
import threading

from PIL import Image
from PyQt5.Qt import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import api
import song_metadata as sm
from components import dialog
from components.work_thread import thread_drive
from components.dialog.setting_dialog import ApiMode
from ui.ui_source.MetadataWidget import Ui_MetadataWidget

LRC_PATH = "download\\"


class MetadataWidget(QWidget, Ui_MetadataWidget):
    warning_dialog_show_signal = pyqtSignal(str)
    auto_dialog_show_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super(MetadataWidget, self).__init__(parent)
        self.setupUi(self)

        self.modify_dialog = dialog.ModifyDialog(self)
        self.setting_dialog = dialog.SettingDialog(self)
        self.warning_dialog = dialog.WarningDialog(self)
        self.auto_dialog = dialog.AutoMetadataDialog(self)
        self.cloud_api = api.CloudMusicWebApi()
        self.kugou_api = api.KugouApi()

        self._init_signal()
        self._init_table_widgets()
        self._init_setting()

        self.search_data = []  # List[SongSearchInfo]
        self.song_info = None  # SongInfo
        self.stop_auto = False  # bool

    def _init_setting(self):
        """初始化设置"""
        self.api_mode = ApiMode(0)
        self.is_rename = False
        self.is_download_lrc = False
        self.result_pic_label.setScaledContents(True)

    def _init_signal(self):
        """初始化信号"""
        self.add_file_button.clicked.connect(self.add_file_event)
        self.delete_file_button.clicked.connect(self.delete_file_event)
        self.confirm_buton.clicked.connect(self.write_event)
        self.search_button.clicked.connect(self.search_event)
        self.pass_button.clicked.connect(self.pass_event)
        self.modify_button.clicked.connect(self.modify_event)
        self.setting_button.clicked.connect(self.setting_dialog.show)

        self.file_listWidget.itemClicked.connect(self.path_click_event)
        self.search_tableWidget.itemClicked.connect(self.result_click_event)

        self.modify_dialog.done_signal.connect(self.modify_done_event)
        self.setting_dialog.done_signal.connect(self._setting_done_event)
        self.auto_dialog_show_signal.connect(self.auto_dialog.show)
        self.warning_dialog_show_signal.connect(self.show_warning_event)

    def _init_table_widgets(self):
        """设置表格属性"""
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

        self.setAcceptDrops(True)
        self.search_tableWidget.setAcceptDrops(True)  # 允许文件拖入

        column_text_list = ['曲名', '歌手', '时长', 'id']
        for column in range(0, 4):
            item = QTableWidgetItem()
            item.setText(column_text_list[column])
            self.search_tableWidget.setHorizontalHeaderItem(column, item)
        self.search_tableWidget.hideColumn(3)

    def add_file_event(self) -> None:
        """打开并添加文件"""
        file_name_list = QFileDialog.getOpenFileNames(self, u"打开文件", "", "Music files(*.mp3 *.flac)")[0]
        self.file_listWidget.addItems(file_name_list)

    def delete_file_event(self) -> None:
        """去掉文件"""
        if self.file_listWidget and self.file_listWidget.selectedIndexes():
            row = self.file_listWidget.selectedIndexes()[0].row()
            self.file_listWidget.removeItemWidget(self.file_listWidget.takeItem(row))

    def path_click_event(self, item) -> None:
        """解析选中的文件，并搜索关键词"""
        try:
            song_info, else_info = sm.read_song_metadata(item.text())
            self.set_left_text(self.path_label, else_info.songPath)
            self.set_left_text(self.filename_label, os.path.basename(item.text()))
            self.set_left_text(self.original_song_name_label, song_info.songName)
            self.set_left_text(self.original_singer_label, song_info.singer)
            self.set_left_text(self.original_duration_label, song_info.duration)
            self.set_left_text(self.original_md5_label, else_info.md5)
            if song_info.singer and song_info.songName:
                # keyword = os.path.splitext(item.text())[0]
                keyword = '-'.join([song_info.singer, song_info.songName])
            else:
                keyword = os.path.splitext(item.text())[0]
            self.search_lineEdit.setText(keyword)
            self.file_listWidget.setEnabled(False)  # 搜索完成后解放
            self.search_tableWidget.setEnabled(False)
            self.search_event()
        except Exception as e:
            self.warning_dialog_show_signal.emit(repr(e))
            item.setBackground(QColor(Qt.red))
            return

    def show_warning_event(self, msg):
        """显示警告窗口"""
        self.warning_dialog.set_text(msg)
        if not self.warning_dialog.isVisible():
            # for _dialog in (self.setting_dialog, self.modify_dialog, self.auto_dialog):
            #     if _dialog.isVisible():
            #         self.warning_dialog.setParent(_dialog)
            #         break
            # else:
            #     self.warning_dialog.setParent(self)
            self.warning_dialog.show()

    def write_metadata(self, item_row, song_info, song_id_or_md5, *, pic_path: str = None):
        """结合ui数据写入元数据"""
        item = self.file_listWidget.item(item_row)
        file_path = item.text()
        try:
            format_change = sm.write_song_metadata(file_path, song_info, pic_path=pic_path)

            if format_change:
                old_format, new_format = format_change
                self.warning_dialog_show_signal.emit(f"检测到文件格式有误，\n已从{old_format}修改为{new_format}.")
                item.setBackground(QColor(Qt.red))
            else:
                item.setBackground(QColor(Qt.lightGray))
            if self.is_download_lrc:
                time.sleep(0.1)
                self.download_lrc(song_id_or_md5, ' - '.join([song_info.singer, song_info.songName]))
            if self.is_rename:
                dir_name = os.path.dirname(file_path)
                suffix = os.path.splitext(file_path)[-1]
                new_name = ' - '.join([song_info.singer, song_info.songName])
                new_name = re.sub(r"|[?\\/*<>|:\"]+", "", new_name)
                new_path = os.path.join(dir_name, new_name + suffix)
                os.rename(file_path, new_path)
                item.setText(new_path)
        except Exception as e:
            self.warning_dialog_show_signal.emit(repr(e))
            item.setBackground(QColor(Qt.red))
            return

    def write_event(self, *, pic_path: str = None) -> None:
        """写入元数据，item的背景颜色会根据写入结果改变颜色，并指向下一个选项"""
        if self.song_info:
            row = self.file_listWidget.currentRow()
            song_id_or_md5 = self.search_tableWidget.item(self.search_tableWidget.currentItem().row(), 3).text()
            self.write_metadata(row, self.song_info, song_id_or_md5, pic_path=pic_path)
            self.song_info = None
            self.file_listWidget.setCurrentRow(self.file_listWidget.currentRow() + 1)
            if self.file_listWidget.selectedItems():
                self.path_click_event(self.file_listWidget.selectedItems()[0])

    def pass_event(self) -> None:
        """跳过当前选择并选择下一个"""
        if not self.file_listWidget.currentItem():
            return
        self.song_info = None
        self.file_listWidget.setCurrentRow(self.file_listWidget.currentRow() + 1)
        if self.file_listWidget.selectedItems():
            self.path_click_event(self.file_listWidget.selectedItems()[0])

    def modify_event(self) -> None:
        """手动修改数据"""
        if not self.file_listWidget.currentItem():
            return
        song_info, _ = sm.read_song_metadata(self.file_listWidget.currentItem().text())
        self.modify_dialog.load_song_info(song_info)
        self.modify_dialog.show()

    def modify_done_event(self, song_info, pic_path) -> None:
        """接收自定义写入的数据并写入文件"""
        self.song_info = song_info
        self.write_event(pic_path=pic_path)

    def _setting_done_event(self, setting: dialog.setting_dialog.Setting) -> None:
        """从设置对话框中获取数据载入"""
        self.api_mode = setting.api_mode
        self.is_download_lrc = setting.is_lyric
        self.is_rename = setting.is_rename
        if setting.auto_if:
            self.auto_complete_event()

    def auto_complete_event(self) -> None:
        """开启自动匹配元数据写入"""
        if not self.file_listWidget:
            self.warning_dialog.set_text("你还没有载入文件！")
            self.warning_dialog.show()
            return
        elif not self.file_listWidget.selectedIndexes():
            self.file_listWidget.setCurrentRow(0)

        t = threading.Thread(target=self._thread_auto_complete)
        t.start()

    def _thread_auto_complete(self):
        """自动补全元数据"""
        self.stop_auto = False
        start_index = self.file_listWidget.currentRow()
        total_num = self.file_listWidget.count()
        rows = range(start_index, total_num)
        path_list = [self.file_listWidget.item(i).text() for i in rows]
        if self.api_mode == ApiMode.CLOUD:
            search_func = self.cloud_api.search_data
            search_info_func = self.cloud_api.get_song_info
        elif self.api_mode == ApiMode.KUGOU:
            search_func = self.kugou_api.search_hash
            search_info_func = self.kugou_api.get_song_info
        else:
            raise ValueError("api_mode参数错误，未知的模式")

        self.auto_dialog.set_max(total_num - 1)
        self.auto_dialog_show_signal.emit("")
        try:
            for row, file_path in zip(rows, path_list):
                if self.stop_auto:
                    self.auto_dialog.prepare_close_signal.emit("")
                    break
                song_info, else_info = sm.read_song_metadata(file_path)
                if song_info.singer and song_info.songName:
                    keyword = '-'.join([song_info.singer, song_info.songName])
                else:
                    keyword = os.path.splitext(file_path)[0]
                try:
                    search_data = search_func(keyword)
                except api.NoneResultError:
                    search_data = []
                if search_data:
                    res_info = search_info_func(search_data[0].idOrMd5)
                    score = sm.compare_song_info(song_info, res_info)
                    if score >= 80:
                        self.write_metadata(row, res_info, search_data[0].idOrMd5)
                    self.auto_dialog.add_signal.emit("")
                else:
                    self.auto_dialog.add_signal.emit("")
        except Exception as e:
            self.warning_dialog_show_signal.emit(repr(e))
            self.auto_dialog.prepare_close_signal.emit("")
        finally:
            self.search_tableWidget.setEnabled(True)
            self.file_listWidget.setEnabled(True)

    def _load_search_data(self) -> None:
        """载入数据到表格"""
        self.search_tableWidget.clearContents()
        self.search_tableWidget.setRowCount(len(self.search_data))
        for outer_index, outer_data in enumerate(self.search_data):
            for inner_index, inner_data in enumerate(outer_data):
                item = QTableWidgetItem()
                item.setText(inner_data)
                self.search_tableWidget.setItem(outer_index, inner_index, item)
        if self.search_data:  # 自动选中当前第一个
            self.search_tableWidget.selectRow(0)
            self.result_click_event(self.search_tableWidget.item(0, 1))
        else:
            self.result_pic_label.setText("无搜索结果")
            self.song_info = None
            self.search_tableWidget.setEnabled(True)
            self.file_listWidget.setEnabled(True)

    def _load_song_info(self) -> None:
        """加载搜索结果的数据到ui"""
        self.set_left_text(self.result_genre_label, 'N/A')
        self.set_left_text(self.result_year_label, self.song_info.year)
        self.set_left_text(self.result_album_label, self.song_info.album)
        self.set_left_text(self.result_singer_label, self.song_info.singer)
        self.set_left_text(self.result_duration_label, self.song_info.duration)
        self.set_left_text(self.result_song_name_label, self.song_info.songName)
        if self.song_info.trackNumber:
            self.set_left_text(self.result_track_number_label, str(self.song_info.trackNumber[0]))
        else:
            self.set_left_text(self.result_track_number_label, "N/A")
        if self.song_info.picBuffer.getvalue():
            pix = Image.open(self.song_info.picBuffer).toqpixmap()
            self.result_pic_label.setPixmap(pix)
        else:
            self.result_pic_label.setText("无图片")

    @thread_drive(None)
    def download_lrc(self, md5_or_id: str, save_name: str) -> None:
        """下载对应的歌词文件"""
        if self.api_mode == ApiMode.CLOUD:
            lrc_file = self.cloud_api.get_lrc(md5_or_id)
        elif self.api_mode == ApiMode.KUGOU:
            lrc_info = self.kugou_api.get_lrc_info(md5_or_id)[0]
            lrc_file = self.kugou_api.get_lrc(lrc_info)
        else:
            raise ValueError("api_mode参数错误，未知的模式")
        if not os.path.exists(LRC_PATH):
            os.makedirs(LRC_PATH)
        save_name = re.sub(r"|[?\\/*<>|:\"]+", "", save_name)
        path = LRC_PATH + save_name + '.txt'
        lrc_file.save_to_mrc(path)

    @thread_drive(_load_search_data)
    def search_event(self, *args) -> None:
        """搜索框中的数据"""
        keyword = self.search_lineEdit.text()
        if keyword:
            try:
                if self.api_mode == ApiMode.CLOUD:
                    self.search_data = self.cloud_api.search_data(keyword)
                elif self.api_mode == ApiMode.KUGOU:
                    self.search_data = self.kugou_api.search_hash(keyword)
                else:
                    raise ValueError("api_mode参数错误，未知的模式")
            except api.NoneResultError:
                self.search_data = []
            except Exception as e:
                self.warning_dialog_show_signal.emit(repr(e))
                self.search_data = []
                return

    @thread_drive(_load_song_info)
    def result_click_event(self, item) -> None:
        """选中搜索结果中的项目，显示详细信息"""
        self.search_tableWidget.setEnabled(False)
        self.result_pic_label.clear()
        self.result_pic_label.setText("获取数据中")
        if self.api_mode == ApiMode.CLOUD:
            song_id = self.search_tableWidget.item(item.row(), 3).text()
            self.song_info = self.cloud_api.get_song_info(song_id)
        elif self.api_mode == ApiMode.KUGOU:
            md5 = self.search_tableWidget.item(item.row(), 3).text()
            self.song_info = self.kugou_api.get_song_info(md5)
        else:
            raise ValueError("api_mode参数错误，未知的模式")
        self.search_tableWidget.setEnabled(True)
        self.file_listWidget.setEnabled(True)

    @staticmethod
    def set_left_text(label: QLabel, text: str) -> None:
        """显示文件数据可复制并且多余字符用点代替"""
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)  # 设置label可复制
        metrics = QFontMetrics(label.font())
        text = text if text else "N/A"
        new_text = metrics.elidedText(text, Qt.ElideRight, label.width())
        label.setText(new_text)

    def dragEnterEvent(self, a0: QDragEnterEvent) -> None:
        accept_format = (".flac", ".mp3", ".m4a", ".mp4")

        def check_suffix(q_url) -> bool:
            for suffix in accept_format:
                if q_url.fileName().endswith(suffix):
                    return True
            return False

        if len(a0.mimeData().urls()) == 0:
            a0.ignore()
        elif all(check_suffix(file) for file in a0.mimeData().urls()):
            a0.acceptProposedAction()
        else:
            a0.ignore()

    def dropEvent(self, a0: QDropEvent) -> None:
        for q_url in a0.mimeData().urls():
            self.file_listWidget.addItem(q_url.toLocalFile())


if __name__ == "__main__":
    # 适配2k等高分辨率屏幕,低分辨率屏幕可以缺省
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    myWin = MetadataWidget()
    myWin.show()
    sys.exit(app.exec_())



