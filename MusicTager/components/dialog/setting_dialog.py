#!/usr/bin/python
# -*- coding:utf-8 -*-

import json
import os
from collections import namedtuple
from enum import Enum

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QDialog

from components.mask_widget import MaskWidget
from ui.ui_source.SettingDialog import Ui_SettingDialog



Setting = namedtuple("Setting", ["api_mode", "is_lrc", "is_rename"])
CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'config.json')


class ApiMode(Enum):
    CLOUD = 0
    KUGOU = 1
    SPOTIFY = 2


class SettingDialog(QDialog, Ui_SettingDialog):
    done_signal = pyqtSignal(Setting)

    def __init__(self, parent=None):
        super(SettingDialog, self).__init__(parent)
        self.setupUi(self)
        self._load_config()
        self._init_signal()

    def _init_signal(self):
        self.api_comboBox.currentIndexChanged.connect(self.comboBox_event)

    def _load_config(self):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
            self.api_comboBox.setCurrentIndex(config.get("api_mode", 0))
            self.is_download_lrc_checkBox.setChecked(config.get("is_lrc", False))
            self.is_rename_file_checkBox.setChecked(config.get("is_rename", True))
        except (FileNotFoundError, json.JSONDecodeError):
            # 如果文件不存在或解析失败，则使用默认设置
            self.api_comboBox.setCurrentIndex(0)
            self.is_download_lrc_checkBox.setChecked(False)
            self.is_rename_file_checkBox.setChecked(True)

    def _save_config(self):
        config = {
            "api_mode": self.api_comboBox.currentIndex(),
            "is_lrc": self.is_download_lrc_checkBox.isChecked(),
            "is_rename": self.is_rename_file_checkBox.isChecked()
        }
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

    def comboBox_event(self):
        """spotify暂时不支持下载歌词"""
        if self.api_comboBox.currentIndex() == 2:  # 选中到spotify api，禁用打开自动下载歌词
            self.is_download_lrc_checkBox.setChecked(False)
            self.is_download_lrc_checkBox.setEnabled(False)
        elif not self.is_download_lrc_checkBox.isEnabled():
            self.is_download_lrc_checkBox.setEnabled(True)

    def accept(self) -> None:
        self._save_config()
        setting = Setting(
            api_mode=ApiMode(self.api_comboBox.currentIndex()),
            is_lrc=self.is_download_lrc_checkBox.isChecked(),
            is_rename=self.is_rename_file_checkBox.isChecked(),
        )
        self.done_signal.emit(setting)
        super(SettingDialog, self).accept()

    def show(self) -> None:
        self._set_mask_visible(True)
        super(SettingDialog, self).show()

    def done(self, a0: int) -> None:
        self._set_mask_visible(False)
        super(SettingDialog, self).done(a0)

    def _set_mask_visible(self, flag: bool):
        if self.parent():
            if not hasattr(self.parent(), "mask_widget"):
                self.parent().mask_widget = MaskWidget(self.parent())
            if flag:
                self.parent().mask_widget.show()
            else:
                self.parent().mask_widget.hide()
