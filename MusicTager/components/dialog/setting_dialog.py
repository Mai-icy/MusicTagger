#!/usr/bin/python
# -*- coding:utf-8 -*-

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from ui.ui_source.SettingDialog import Ui_SettingDialog
from components.mask_widget import MaskWidget

from collections import namedtuple
from enum import Enum


Setting = namedtuple("Setting", ["api_mode", "is_lyric", "is_rename", "auto_if"])


class ApiMode(Enum):
    CLOUD = 0
    KUGOU = 1


class SettingDialog(QDialog, Ui_SettingDialog):
    done_signal = pyqtSignal(Setting)

    def __init__(self, parent=None):
        super(SettingDialog, self).__init__(parent)
        self.setupUi(self)
        self._init_signal()
        self.auto_if = False

    def _init_signal(self):
        self.auto_button.clicked.connect(self.auto_event)

    def auto_event(self):
        self.auto_if = True
        self.accept()

    def accept(self) -> None:
        mode = ApiMode(self.api_comboBox.currentIndex())
        setting_dict = {
            "api_mode": mode,
            "is_lyric": self.is_download_lrc_checkBox.isChecked(),
            "is_rename": self.is_rename_file_checkBox.isChecked(),
            "auto_if": self.auto_if
        }
        setting = Setting(**setting_dict)
        self.done_signal.emit(setting)
        super(SettingDialog, self).accept()

    def show(self) -> None:
        self.auto_if = False
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

