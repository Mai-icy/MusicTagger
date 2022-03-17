#!/usr/bin/python
# -*- coding:utf-8 -*-

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from ui.ui_source.AutoMetadataDialog import Ui_AutoMetadataDialog
from components.mask_widget import MaskWidget


class AutoMetadataDialog(QDialog, Ui_AutoMetadataDialog):
    add_signal = pyqtSignal(str)
    prepare_close_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super(AutoMetadataDialog, self).__init__(parent)
        self.setupUi(self)
        self.add_signal.connect(self.value_add)
        self.prepare_close_signal.connect(self.prepare_reject)

    def set_max(self, maximum):
        self.progressBar.setMaximum(maximum)

    def value_add(self):
        now_value = self.progressBar.value()
        if now_value + 1 == self.progressBar.maximum():
            self.prepare_reject()
        self.progressBar.setValue(now_value + 1)

    def show(self) -> None:
        self.progressBar.reset()
        self.label.setText("正在为你自动补充元数据")
        self._set_mask_visible(True)
        super(AutoMetadataDialog, self).show()

    def done(self, a0: int) -> None:
        self._set_mask_visible(False)
        super(AutoMetadataDialog, self).done(a0)
    
    def reject(self) -> None:
        self.parent().stop_auto = True
        self.label.setText("正在中断操作...")

    def prepare_reject(self):
        super(AutoMetadataDialog, self).reject()
    
    def _set_mask_visible(self, flag: bool):
        if self.parent():
            if not hasattr(self.parent(), "mask_widget"):
                self.parent().mask_widget = MaskWidget(self.parent())
            if flag:
                self.parent().mask_widget.show()
            else:
                self.parent().mask_widget.hide()
