from PyQt5.QtWidgets import (QDialog, QLineEdit, QCheckBox, QPushButton, QLabel,
                             QVBoxLayout, QHBoxLayout, QGridLayout, QFileDialog, QSizePolicy)
from PyQt5.QtCore import pyqtSignal, Qt

class BatchModifyDialog(QDialog):
    """
    一个用于批量修改音乐文件元数据的对话框。
    """
    def __init__(self, parent=None):
        """
        初始化对话框，创建并布局所有UI组件。
        """
        super().__init__(parent)
        self.setWindowTitle("批量修改")
        self.setMinimumWidth(400)

        self._cover_path = ""

        # Main layout
        main_layout = QVBoxLayout(self)

        # Grid layout for input fields
        grid_layout = QGridLayout()
        grid_layout.setColumnStretch(0, 0)
        grid_layout.setColumnStretch(1, 1)

        # --- UI Elements ---
        # Artist
        self.artist_checkbox = QCheckBox("艺术家:")
        self.artist_edit = QLineEdit()
        grid_layout.addWidget(self.artist_checkbox, 0, 0)
        grid_layout.addWidget(self.artist_edit, 0, 1)

        # Album
        self.album_checkbox = QCheckBox("专辑:")
        self.album_edit = QLineEdit()
        grid_layout.addWidget(self.album_checkbox, 1, 0)
        grid_layout.addWidget(self.album_edit, 1, 1)

        # Album Artist
        self.album_artist_checkbox = QCheckBox("专辑艺术家:")
        self.album_artist_edit = QLineEdit()
        grid_layout.addWidget(self.album_artist_checkbox, 2, 0)
        grid_layout.addWidget(self.album_artist_edit, 2, 1)

        # Year
        self.year_checkbox = QCheckBox("年份:")
        self.year_edit = QLineEdit()
        grid_layout.addWidget(self.year_checkbox, 3, 0)
        grid_layout.addWidget(self.year_edit, 3, 1)

        # Genre
        self.genre_checkbox = QCheckBox("流派:")
        self.genre_edit = QLineEdit()
        grid_layout.addWidget(self.genre_checkbox, 4, 0)
        grid_layout.addWidget(self.genre_edit, 4, 1)

        # Cover
        self.cover_checkbox = QCheckBox("封面:")
        self.cover_select_button = QPushButton("选择图片...")
        self.cover_path_label = QLabel("未选择图片")
        self.cover_path_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.cover_path_label.setWordWrap(True)
        
        cover_layout = QHBoxLayout()
        cover_layout.addWidget(self.cover_select_button)
        cover_layout.addWidget(self.cover_path_label)
        
        grid_layout.addWidget(self.cover_checkbox, 5, 0)
        grid_layout.addLayout(cover_layout, 5, 1)

        main_layout.addLayout(grid_layout)

        # --- Buttons ---
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("确定")
        self.cancel_button = QPushButton("取消")
        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        main_layout.addLayout(button_layout)

        # --- Connections ---
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.cover_select_button.clicked.connect(self.select_cover_image)

        # Link checkboxes to their line edits
        self.artist_checkbox.stateChanged.connect(self.artist_edit.setEnabled)
        self.album_checkbox.stateChanged.connect(self.album_edit.setEnabled)
        self.album_artist_checkbox.stateChanged.connect(self.album_artist_edit.setEnabled)
        self.year_checkbox.stateChanged.connect(self.year_edit.setEnabled)
        self.genre_checkbox.stateChanged.connect(self.genre_edit.setEnabled)
        
        cover_widgets = [self.cover_select_button, self.cover_path_label]
        for widget in cover_widgets:
            self.cover_checkbox.stateChanged.connect(widget.setEnabled)

        # --- Initial State ---
        self.artist_edit.setEnabled(False)
        self.album_edit.setEnabled(False)
        self.album_artist_edit.setEnabled(False)
        self.year_edit.setEnabled(False)
        self.genre_edit.setEnabled(False)
        self.cover_select_button.setEnabled(False)
        self.cover_path_label.setEnabled(False)


    def select_cover_image(self):
        """
        打开文件对话框以选择封面图片，并更新标签显示路径。
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择封面图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            self._cover_path = file_path
            self.cover_path_label.setText(file_path)

    def get_modification_data(self):
        """
        收集所有勾选并已填写的字段数据。

        :return: 一个包含要修改的元数据字段的字典。
        """
        data = {}

        if self.artist_checkbox.isChecked() and self.artist_edit.text():
            data['artist'] = self.artist_edit.text()
        
        if self.album_checkbox.isChecked() and self.album_edit.text():
            data['album'] = self.album_edit.text()

        if self.album_artist_checkbox.isChecked() and self.album_artist_edit.text():
            data['albumartist'] = self.album_artist_edit.text()

        if self.year_checkbox.isChecked() and self.year_edit.text():
            data['date'] = self.year_edit.text()
            
        if self.genre_checkbox.isChecked() and self.genre_edit.text():
            data['genre'] = self.genre_edit.text()

        if self.cover_checkbox.isChecked() and self._cover_path:
            data['cover'] = self._cover_path
            
        return data
