#!/usr/bin/python
# -*- coding:utf-8 -*-

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from ui.ui_source.MetadataWidgetSetting import Ui_MetadataWidgetSetting


class MetadataSetting(QWidget, Ui_MetadataWidgetSetting):
    done_signal = pyqtSignal(dict)
    auto_signal = pyqtSignal(dict)

    def __init__(self, parent=None):
        super(MetadataSetting, self).__init__(parent)
        self.setupUi(self)
        self._init_signal()
        self.checkBox_2.setCheckable(False)

    def _init_signal(self):
        self.sure_button.clicked.connect(self.done_event)
        self.auto_button.clicked.connect(lambda: self.done_event(is_auto=True))

    def done_event(self, is_auto=False):
        text = self.api_comboBox.currentText()
        if text == "酷狗api":
            mode = "kugou"
        elif text == "网易云api":
            mode = "cloud"
        else:
            mode = ""

        setting_dict = {
            "mode": mode,
            "is_lyric": self.is_download_lrc_checkBox.isChecked()
        }
        if is_auto:
            self.auto_signal.emit(setting_dict)
        else:
            self.done_signal.emit(setting_dict)
        self.close()
