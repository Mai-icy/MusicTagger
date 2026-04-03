#!/usr/bin/python
# -*- coding:utf-8 -*-

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import QLabel


class InfoLabel(QLabel):
    def __init__(self, parent=None):
        super(InfoLabel, self).__init__(parent=parent)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.metrics = QFontMetrics(self.font())

    def put_text(self, text: str):
        text = text if text else "N/A"
        new_text = self.metrics.elidedText(text, Qt.TextElideMode.ElideRight, self.width())
        self.setText(new_text)
