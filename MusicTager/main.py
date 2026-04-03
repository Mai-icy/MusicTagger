#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys

from PyQt6.QtWidgets import QApplication

from ui.metadata_widget import MetadataWidget

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWin = MetadataWidget()
    myWin.show()
    sys.exit(app.exec())
