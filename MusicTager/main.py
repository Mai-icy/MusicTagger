#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from ui.metadata_widget import MetadataWidget

if __name__ == "__main__":
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    myWin = MetadataWidget()
    myWin.show()
    sys.exit(app.exec_())
