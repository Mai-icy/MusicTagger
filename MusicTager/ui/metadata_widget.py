#!/usr/bin/python
# -*- coding:utf-8 -*-
import re
import os
import sys
import time
import json
import threading

from PIL import Image
from PyQt5.Qt import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import api
from song_metadata.compare_metadata import compare_song_info
from song_metadata.metadata_type import SongInfo
from components import dialog
from components.work_thread import thread_drive
from components.dialog.setting_dialog import ApiMode
from song_metadata.read_metadata import read_song_metadata
from song_metadata.write_metadata import write_song_metadata
from ui.ui_source.MetadataWidget import Ui_MetadataWidget

LRC_PATH = "download\\"


class MetadataWidget(QWidget, Ui_MetadataWidget):
    warning_dialog_show_signal = pyqtSignal(str)
    auto_dialog_show_signal = pyqtSignal(str)
    progress_update_signal = pyqtSignal(int)

    def __init__(self, parent=None):
        super(MetadataWidget, self).__init__(parent)
        self.setupUi(self)
        self._load_stylesheet()

        self.threads = []  # 用于跟踪所有工作线程

        self._init_ui_components()
        self._init_layouts()
        self._init_dialogs()
        self._init_apis()
        
        self.progress_dialog = QProgressDialog("正在批量处理...", "取消", 0, 100, self)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setAutoClose(True)
        self.progress_dialog.reset()

        self._init_signal()
        self._init_table_widgets()
        self._init_setting()

        self.search_data = []  # List[SongSearchInfo]
        self.song_info = None  # SongInfo
        self.stop_auto = False  # bool

    def _load_stylesheet(self):
        """加载QSS样式表"""
        style_path = os.path.join(os.path.dirname(__file__), 'style.qss')
        try:
            with open(style_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print(f"警告: 样式文件 'style.qss' 未找到。")

    def _init_ui_components(self):
        """初始化UI小部件"""
        # 初始化所有在布局中需要的标签
        self.path_label = QLabel("N/A")
        self.filename_label = QLabel("N/A")
        self.original_song_name_label = QLabel("N/A")
        self.original_singer_label = QLabel("N/A")
        self.original_album_label = QLabel("N/A")
        self.original_year_label = QLabel("N/A")
        self.original_genre_label = QLabel("N/A")
        self.original_duration_label = QLabel("N/A")
        self.original_lyric_label = QLabel("N/A")
        self.original_md5_label = QLabel("N/A")

        self.original_pic_label = QLabel()
        self.original_pic_label.setMinimumSize(140, 140)
        self.original_pic_label.setMaximumSize(140, 140)
        self.original_pic_label.setObjectName("original_pic_label")
        self.original_pic_label.setScaledContents(True)

        self.result_song_name_label = QLabel("N/A")
        self.result_singer_label = QLabel("N/A")
        self.result_album_label = QLabel("N/A")

    def _init_layouts(self):
        """初始化布局"""
        # 原始元数据布局
        original_form_layout = QFormLayout(self.groupBox)
        original_form_layout.setObjectName("original_form_layout")
        original_form_layout.addRow("路径:", self.path_label)
        original_form_layout.addRow("文件名:", self.filename_label)
        original_form_layout.addRow("曲名:", self.original_song_name_label)
        original_form_layout.addRow("歌手:", self.original_singer_label)
        original_form_layout.addRow("专辑:", self.original_album_label)
        original_form_layout.addRow("年份:", self.original_year_label)
        original_form_layout.addRow("流派:", self.original_genre_label)
        original_form_layout.addRow("时长:", self.original_duration_label)
        original_form_layout.addRow("歌词:", self.original_lyric_label)
        original_form_layout.addRow("MD5:", self.original_md5_label)
        original_form_layout.addRow("封面:", self.original_pic_label)

        # 搜索结果布局已在 setupUi 中大部分完成
        # 这里仅作确认和微调
        if not self.groupBox_2.layout():
             # 如果groupBox_2没有布局，则创建一个新的
            result_layout = QHBoxLayout(self.groupBox_2)
            result_layout.addWidget(self.result_pic_label)
            details_layout = QFormLayout()
            details_layout.addRow("曲名:", self.result_song_name_label)
            details_layout.addRow("歌手:", self.result_singer_label)
            details_layout.addRow("专辑:", self.result_album_label)
            # 添加其他需要的标签
            result_layout.addLayout(details_layout)

    def _init_dialogs(self):
        """初始化对话框"""
        self.modify_dialog = dialog.ModifyDialog(self)
        self.setting_dialog = dialog.SettingDialog(self)
        self.warning_dialog = dialog.WarningDialog(self)
        self.auto_dialog = dialog.AutoMetadataDialog(self)

    def _init_apis(self):
        """初始化API客户端"""
        self.cloud_api = api.CloudMusicWebApi()
        self.kugou_api = api.KugouApi()
        self.spotify_api = api.SpotifyApi()

    def _init_setting(self):
        """初始化设置"""
        self.api_mode = ApiMode(0)
        self.is_rename = False
        self.is_lrc = False
        self.result_pic_label.setScaledContents(True)
        self._load_config()

    def _load_config(self):
        """加载用户设置"""
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config.json')
        try:
            if not os.path.exists(config_path):
                raise FileNotFoundError
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            self.api_mode = ApiMode(config.get("api_mode", 0))
            self.is_rename = config.get("is_rename", False)
            self.is_lrc = config.get("is_lrc", False)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"配置文件加载或解析失败: {e}，将创建默认配置文件。")
            self._create_default_config(config_path)

    def _create_default_config(self, path: str):
        """创建默认配置文件"""
        default_config = {
            "api_mode": 0,
            "is_rename": False,
            "is_lrc": False
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=4)
            # 应用默认设置
            self.api_mode = ApiMode(default_config["api_mode"])
            self.is_rename = default_config["is_rename"]
            self.is_lrc = default_config["is_lrc"]
        except IOError as e:
            print(f"无法创建默认配置文件: {e}")

    def _init_signal(self):
        """初始化信号"""
        self.add_file_button.clicked.connect(self.add_file_event)
        self.delete_file_button.clicked.connect(self.delete_file_event)
        self.confirm_buton.clicked.connect(self.write_event)
        self.search_button.clicked.connect(self.search_event)
        self.pass_button.clicked.connect(self.pass_event)
        self.modify_button.clicked.connect(self.modify_event)
        self.setting_button.clicked.connect(self.setting_dialog.show)

        self.batch_modify_button.clicked.connect(self.batch_modify_metadata)
        self.file_listWidget.itemChanged.connect(self.on_item_changed)
        self.select_all_checkbox.stateChanged.connect(self.toggle_select_all)
        self.file_listWidget.currentItemChanged.connect(self.path_click_event)
        self.search_tableWidget.currentItemChanged.connect(self.result_click_event)

        self.modify_dialog.done_signal.connect(self.modify_done_event)
        self.setting_dialog.done_signal.connect(self._setting_done_event)
        self.auto_dialog_show_signal.connect(self.auto_dialog.show)
        self.warning_dialog_show_signal.connect(self.show_warning_event)
        self.progress_update_signal.connect(self.update_progress_dialog)

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
        for file_path in file_name_list:
            item = QListWidgetItem(file_path)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.file_listWidget.addItem(item)

    def delete_file_event(self) -> None:
        """去掉文件"""
        if self.file_listWidget and self.file_listWidget.selectedIndexes():
            row = self.file_listWidget.selectedIndexes()[0].row()
            self.file_listWidget.removeItemWidget(self.file_listWidget.takeItem(row))

    def path_click_event(self, current_item: QListWidgetItem, previous_item: QListWidgetItem) -> None:
        """解析选中的文件，并搜索关键词"""
        if not current_item:
            return
        try:
            song_info, else_info = read_song_metadata(current_item.text())
            self.show_metadata(song_info, current_item.text(), song_info.picBuffer)
            self.set_left_text(self.original_md5_label, else_info.md5)
            keyword = self.generate_search_keyword(current_item.text(), song_info)
            self.search_lineEdit.setText(keyword)
            self.file_listWidget.setEnabled(False)  # 搜索完成后解放
            self.search_tableWidget.setEnabled(False)
            self.search_event()
        except Exception as e:
            self.warning_dialog_show_signal.emit(repr(e))
            current_item.setBackground(QColor(255, 100, 100, 100)) # 使用更柔和的红色
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

    def _write_metadata_to_file(self, item_row, song_info, song_id_or_md5, *, pic_path: str = None):
        """结合ui数据写入元数据"""
        item = self.file_listWidget.item(item_row)
        file_path = item.text()
        try:
            format_change = write_song_metadata(file_path, song_info, pic_path=pic_path)

            if format_change:
                old_format, new_format = format_change
                self.warning_dialog_show_signal.emit(f"检测到文件格式有误，\n已从{old_format}修改为{new_format}.")
                item.setBackground(QColor(255, 100, 100, 100)) # 使用更柔和的红色
            else:
                item.setBackground(QColor(211, 211, 211, 150)) # 使用柔和的灰色
            if self.is_lrc:
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
            item.setBackground(QColor(255, 100, 100, 100))
            return

    def write_event(self, *, pic_path: str = None) -> None:
        """写入元数据，item的背景颜色会根据写入结果改变颜色，并指向下一个选项"""
        if self.song_info:
            row = self.file_listWidget.currentRow()
            if row == -1:
                QMessageBox.warning(self, "提示", "请先在左侧列表中选择一个文件。")
                return
            song_id_or_md5 = self.search_tableWidget.item(self.search_tableWidget.currentItem().row(), 3).text()
            self._write_metadata_to_file(row, self.song_info, song_id_or_md5, pic_path=pic_path)
            self.song_info = None
            self.file_listWidget.setCurrentRow(self.file_listWidget.currentRow() + 1)
            # The path_click_event is automatically triggered by the currentItemChanged signal from setCurrentRow

    def pass_event(self) -> None:
        """跳过当前选择并选择下一个"""
        if not self.file_listWidget.currentItem():
            return
        self.song_info = None
        self.file_listWidget.setCurrentRow(self.file_listWidget.currentRow() + 1)
        # The path_click_event is automatically triggered by the currentItemChanged signal from setCurrentRow

    def modify_event(self) -> None:
        """手动修改数据"""
        if not self.file_listWidget.currentItem():
            return
        song_info, _ = read_song_metadata(self.file_listWidget.currentItem().text())
        self.modify_dialog.load_song_info(song_info)
        self.modify_dialog.show()

    def modify_done_event(self, song_info, pic_path) -> None:
        """接收自定义写入的数据并写入文件"""
        self.song_info = song_info
        self.write_event(pic_path=pic_path)

    def _setting_done_event(self, setting: dialog.setting_dialog.Setting) -> None:
        """从设置对话框中获取数据载入"""
        self.api_mode = setting.api_mode
        self.is_lrc = setting.is_lrc
        self.is_rename = setting.is_rename
        if setting.auto_if:
            self.auto_complete_event()

    @thread_drive(None)
    def auto_complete_event(self) -> None:
        """开启自动匹配元数据写入"""
        if not self.file_listWidget:
            self.warning_dialog.set_text("你还没有载入文件！")
            self.warning_dialog.show()
            return
        elif not self.file_listWidget.selectedIndexes():
            self.file_listWidget.setCurrentRow(0)

        self._thread_auto_complete()

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
        elif self.api_mode == ApiMode.SPOTIFY:
            search_func = self.spotify_api.search_data
            search_info_func = self.spotify_api.get_song_info
        else:
            raise ValueError("api_mode参数错误，未知的模式")

        self.auto_dialog.set_max(total_num - 1)
        self.auto_dialog_show_signal.emit("")
        try:
            for row, file_path in zip(rows, path_list):
                if self.stop_auto:
                    self.auto_dialog.prepare_close_signal.emit("")
                    break
                song_info, else_info = read_song_metadata(file_path)
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
                    score = compare_song_info(song_info, res_info)
                    if score >= 80:
                        self._write_metadata_to_file(row, res_info, search_data[0].idOrMd5)
                    elif len(search_data) > 1:
                        res_info = search_info_func(search_data[1].idOrMd5)
                        score = compare_song_info(song_info, res_info)
                        if score >= 80:
                            self._write_metadata_to_file(row, res_info, search_data[1].idOrMd5)
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
            # The result_click_event is automatically triggered by the currentItemChanged signal from selectRow
        else:
            self.result_pic_label.setText("无搜索结果")
            self.song_info = None
        self.search_tableWidget.setEnabled(True)
        self.file_listWidget.setEnabled(True)

    def _load_song_info(self) -> None:
        """加载搜索结果的数据到ui"""
        if not self.song_info:
            return
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
            try:
                # 确保picBuffer是有效的
                if self.song_info.picBuffer and self.song_info.picBuffer.getvalue():
                    # 使用Pillow打开图片并转换为QPixmap
                    q_img = QImage.fromData(self.song_info.picBuffer.getvalue())
                    if q_img.isNull():
                        raise ValueError("无法加载图片数据")
                    pix = QPixmap.fromImage(q_img)
                    self.result_pic_label.setPixmap(pix)
                else:
                    self.result_pic_label.setText("无图片")
            except Exception as e:
                self.result_pic_label.setText("图片加载失败")
                print(f"图片加载失败: {e}")
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
        elif self.api_mode == ApiMode.SPOTIFY:
            return
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
                elif self.api_mode == ApiMode.SPOTIFY:
                    self.search_data = self.spotify_api.search_data(keyword)
                else:
                    raise ValueError("api_mode参数错误，未知的模式")
            except api.NoneResultError:
                self.search_data = []
            except Exception as e:
                self.warning_dialog_show_signal.emit(repr(e))
                self.search_data = []
                return

    @thread_drive(_load_song_info)
    def result_click_event(self, current_item: QTableWidgetItem, previous_item: QTableWidgetItem) -> None:
        """选中搜索结果中的项目，显示详细信息"""
        if not current_item:
            return
        self.search_tableWidget.setEnabled(False)
        self.result_pic_label.clear()
        self.result_pic_label.setText("获取数据中")
        try:
            row = current_item.row()
            if self.api_mode == ApiMode.CLOUD:
                song_id = self.search_tableWidget.item(row, 3).text()
                self.song_info = self.cloud_api.get_song_info(song_id)
            elif self.api_mode == ApiMode.KUGOU:
                md5 = self.search_tableWidget.item(row, 3).text()
                self.song_info = self.kugou_api.get_song_info(md5)
            elif self.api_mode == ApiMode.SPOTIFY:
                song_id = self.search_tableWidget.item(row, 3).text()
                self.song_info = self.spotify_api.get_song_info(song_id)
            else:
                raise ValueError("api_mode参数错误，未知的模式")
        except api.NoneResultError:
            self.search_data = []
        except Exception as e:
            self.warning_dialog_show_signal.emit(repr(e))
            self.search_data = []
            return
        self.search_tableWidget.setEnabled(True)
        self.file_listWidget.setEnabled(True)

    def set_left_text(self, label: QLabel, text: str) -> None:
        """根据文本内容设置标签样式和文本，并处理长文本的显示。"""
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        # 检查文本是否有效
        if text and text.strip():
            # 清除样式，恢复默认
            label.setStyleSheet("")  # QSS会处理默认颜色
            display_text = text
        else:
            label.setStyleSheet("color: #d9534f;") # 使用更柔和的红色
            display_text = "N/A"

        # 处理长文本的省略显示
        metrics = QFontMetrics(label.font())
        elided_text = metrics.elidedText(display_text, Qt.ElideRight, label.width())
        label.setText(elided_text)

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
            item = QListWidgetItem(q_url.toLocalFile())
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.file_listWidget.addItem(item)

    def show_metadata(self, song_info: SongInfo, file_path: str = None, pic_buffer=None):
        """在UI上显示元数据信息，并根据数据是否缺失来改变UI反馈"""
        if file_path:
            self.set_left_text(self.path_label, file_path)
            self.set_left_text(self.filename_label, os.path.basename(file_path))

        # 更新所有元数据标签
        self.set_left_text(self.original_song_name_label, song_info.songName)
        self.set_left_text(self.original_singer_label, song_info.singer)
        self.set_left_text(self.original_album_label, song_info.album)
        self.set_left_text(self.original_year_label, song_info.year)
        self.set_left_text(self.original_genre_label, song_info.genre)
        self.set_left_text(self.original_duration_label, song_info.duration)

        # 检查歌词
        if song_info.lyric and song_info.lyric.strip():
            self.original_lyric_label.setText("有")
            self.original_lyric_label.setStyleSheet("")
        else:
            self.original_lyric_label.setText("无")
            self.original_lyric_label.setStyleSheet("color: #d9534f;")

        # 单独处理MD5，因为它来自else_info
        # 注意：在调用此函数时，需要确保else_info是可用的，或者在这里处理它
        # self.set_left_text(self.original_md5_label, "N/A") # 暂时保持

        # 处理封面
        if pic_buffer and pic_buffer.getvalue():
            q_img = QImage.fromData(pic_buffer.getvalue())
            if not q_img.isNull():
                pix = QPixmap.fromImage(q_img)
                self.original_pic_label.setPixmap(pix)
                self.original_pic_label.setStyleSheet("")  # 样式由QSS控制
            else:
                self.original_pic_label.setText("图片无效")
                # QSS会处理错误状态的样式，这里可以留空或设置特定对象名
        else:
            self.original_pic_label.setText("N/A")
            # QSS会处理默认/空状态的样式

    def generate_search_keyword(self, file_path: str, song_info: SongInfo) -> str:
        """根据歌曲信息或文件名生成搜索关键词"""
        if song_info.singer and song_info.songName:
            return '-'.join([song_info.singer, song_info.songName])
        else:
            # 如果没有元数据，则从文件名中提取关键词
            return os.path.splitext(os.path.basename(file_path))[0]
    def batch_modify_metadata(self):
        """批量自动匹配元数据并写入"""
        checked_items = []
        for i in range(self.file_listWidget.count()):
            item = self.file_listWidget.item(i)
            if item.checkState() == Qt.Checked:
                checked_items.append(item)

        if not checked_items:
            QMessageBox.warning(self, "提示", "请先勾选需要处理的文件。")
            return
        
        self.progress_dialog.setMaximum(len(checked_items))
        self.progress_dialog.setValue(0)
        self.progress_dialog.show()

        # 启动后台线程执行批量处理
        self._thread_batch_modify(checked_items)

    def _batch_modify_done(self):
        """批量修改完成后的回调函数"""
        self.progress_dialog.reset()
        QMessageBox.information(self, "完成", "批量自动匹配已完成！")
        # 刷新UI
        if self.file_listWidget.currentItem():
            # Force a refresh of the current item by directly calling the event handler
            self.path_click_event(self.file_listWidget.currentItem(), None)
        else:
            # If no item is current, select the first one, which will trigger the refresh
            if self.file_listWidget.count() > 0:
                self.file_listWidget.setCurrentRow(0)


    @thread_drive(_batch_modify_done)
    def _thread_batch_modify(self, checked_items):
        """在后台线程中执行批量元数据匹配和写入"""
        try:
            if self.api_mode == ApiMode.CLOUD:
                search_func = self.cloud_api.search_data
                info_func = self.cloud_api.get_song_info
            elif self.api_mode == ApiMode.KUGOU:
                search_func = self.kugou_api.search_hash
                info_func = self.kugou_api.get_song_info
            elif self.api_mode == ApiMode.SPOTIFY:
                search_func = self.spotify_api.search_data
                info_func = self.spotify_api.get_song_info
            else:
                raise ValueError("api_mode参数错误，未知的模式")

            for i, item in enumerate(checked_items):
                if self.progress_dialog.wasCanceled():
                    break
                file_path = item.text()
                try:
                    # 1. 生成关键词
                    original_song_info, _ = read_song_metadata(file_path)
                    keyword = self.generate_search_keyword(file_path, original_song_info)

                    # 2. 执行搜索
                    search_results = search_func(keyword)

                    if not search_results:
                        print(f"文件 '{os.path.basename(file_path)}' 未找到匹配结果。")
                        continue

                    # 3. 获取最佳匹配的详细信息
                    best_match = search_results[0]
                    new_song_info = info_func(best_match.idOrMd5)

                    # 4. 写入文件
                    row = self.file_listWidget.row(item)
                    self._write_metadata_to_file(row, new_song_info, best_match.idOrMd5)
                
                except Exception as e:
                    # 使用信号在主线程显示错误，避免线程安全问题
                    self.warning_dialog_show_signal.emit(f"处理文件失败：{os.path.basename(file_path)}\n错误：{e}")
                finally:
                    self.progress_update_signal.emit(i + 1)
        except Exception as e:
            self.warning_dialog_show_signal.emit(f"批量处理时发生严重错误：\n{e}")

    def on_item_changed(self, item):
        """根据勾选的文件数量，设置批量修改按钮的可用状态"""
        checked_count = 0
        for i in range(self.file_listWidget.count()):
            if self.file_listWidget.item(i).checkState() == Qt.Checked:
                checked_count += 1
        self.batch_modify_button.setEnabled(checked_count > 1)

    def update_progress_dialog(self, value):
        self.progress_dialog.setValue(value)

    def toggle_select_all(self, state):
        """(取消)全选 all items in the file list."""
        check_state = Qt.Checked if state == Qt.Checked else Qt.Unchecked
        self.file_listWidget.itemChanged.disconnect(self.on_item_changed)
        for i in range(self.file_listWidget.count()):
            self.file_listWidget.item(i).setCheckState(check_state)
        self.file_listWidget.itemChanged.connect(self.on_item_changed)
        if self.file_listWidget.count() > 0:
            self.on_item_changed(self.file_listWidget.item(0))

    def closeEvent(self, event):
        """重写关闭事件，确保所有线程都已结束"""
        running_threads = [t for t in self.threads if t.isRunning()]
        if running_threads:
            QMessageBox.warning(self, "请稍后", "正在进行后台任务，请等待完成后再关闭窗口。")
            event.ignore()
        else:
            event.accept()


if __name__ == "__main__":
    # 适配2k等高分辨率屏幕,低分辨率屏幕可以缺省
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    myWin = MetadataWidget()
    myWin.show()
    sys.exit(app.exec_())
