'''
20250611
Written by HelloWorld05
All rights reserved.
'''
 
import sys
import os
import re
import requests
from urllib.parse import unquote
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QProgressBar, QLabel, QListWidget,
    QListWidgetItem, QFileDialog, QMessageBox, QComboBox, QDialog, QCheckBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor
 
class DownloadThread(QThread):
    # 用于更新下载进度的信号
    update_progress = pyqtSignal(int, int, int)  # task_id, downloaded, total
    # 下载完成信号
    finished = pyqtSignal(int)  # task_id
    # 错误信号
    error = pyqtSignal(int, str)  # task_id, error_message
 
    def __init__(self, task_id, url, save_path, num_threads=4):
        super().__init__()
        self.task_id = task_id
        self.url = url
        self.save_path = save_path
        self.num_threads = num_threads
        self.is_paused = False
        self.is_canceled = False
        self.downloaded_size = 0
        self.total_size = 0
 
    def run(self):
        try:
            # 获取文件信息
            with requests.get(self.url, stream=True, headers={'Range': 'bytes=0-'}) as r:
                r.raise_for_status()
                 
                # 获取文件名
                content_disposition = r.headers.get('content-disposition')
                if content_disposition:
                    filename = re.findall('filename="?([^"]+)"?', content_disposition)[0]
                    filename = unquote(filename)
                else:
                    filename = os.path.basename(self.url.split('?')[0])
                 
                # 获取文件大小
                self.total_size = int(r.headers.get('content-length', 0))
                 
                # 更新保存路径
                save_path = os.path.join(self.save_path, filename)
                 
                # 检查文件是否存在
                if os.path.exists(save_path):
                    base, ext = os.path.splitext(save_path)
                    counter = 1
                    while os.path.exists(f"{base}_{counter}{ext}"):
                        counter += 1
                    save_path = f"{base}_{counter}{ext}"
                 
                # 开始下载
                self.download_file(save_path)
                 
            self.finished.emit(self.task_id)
        except Exception as e:
            self.error.emit(self.task_id, str(e))
 
    def download_file(self, save_path):
        downloaded = 0
        chunk_size = 1024 * 1024  # 1MB chunks
         
        with requests.get(self.url, stream=True) as r:
            r.raise_for_status()
            with open(save_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    if self.is_canceled:
                        if os.path.exists(save_path):
                            os.remove(save_path)
                        return
                    while self.is_paused:
                        self.msleep(100)
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        self.downloaded_size = downloaded
                        self.update_progress.emit(self.task_id, downloaded, self.total_size)
     
    def pause(self):
        self.is_paused = True
     
    def resume(self):
        self.is_paused = False
     
    def cancel(self):
        self.is_canceled = True
 
class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于")
        self.setFixedSize(600, 500)  # 增大对话框尺寸
        self.setStyleSheet("""
            QDialog {
                background-color: #2D2D30;
                color: #DCDCDC;
                font-family: Segoe UI;
            }
            QLabel {
                color: #DCDCDC;
                font-size: 14px;
            }
            QPushButton {
                background-color: #0078D7;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-size: 14px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #106EBE;
            }
            QPushButton:pressed {
                background-color: #005A9E;
            }
        """)
         
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
         
        title = QLabel("PyDownloader v1.1")
        title_font = QFont("Segoe UI", 24, QFont.Bold)  # 增大标题字体
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
         
        version = QLabel("版本 1.1")
        version.setFont(QFont("Segoe UI", 14))  # 增大版本字体
        version.setAlignment(Qt.AlignCenter)
         
        description = QLabel("PyDownloader 是一款简洁高效的下载工具，专为满足您的下载需求而设计。")
        description.setFont(QFont("Segoe UI", 14))  # 增大描述字体
        description.setAlignment(Qt.AlignCenter)
         
        features = QLabel("功能特点：\n\n"
                        "- 多线程下载，加快下载速度\n"
                        "- 支持任务暂停/继续功能\n"
                        "- 实时显示下载进度\n"
                        "- 自动命名下载文件\n"
                        "- 自定义线程数，适应不同网络环境\n"
                        "- 明暗主题转换，保护眼睛")
        features.setFont(QFont("Segoe UI", 12))  # 增大特性字体
        features.setAlignment(Qt.AlignLeft)
         
        developer = QLabel("开发者：HelloWorld05")  # 修改开发者信息
        developer.setFont(QFont("Segoe UI", 12))  # 增大开发者字体
        developer.setAlignment(Qt.AlignCenter)
         
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        close_btn.setFixedHeight(40)  # 增大按钮高度
         
        layout.addWidget(title)
        layout.addWidget(version)
        layout.addWidget(description)
        layout.addSpacing(20)
        layout.addWidget(features)
        layout.addStretch()
        layout.addWidget(developer)
        layout.addSpacing(20)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)
         
        self.setLayout(layout)
 
class DownloadItemWidget(QWidget):
    def __init__(self, task_id, url, save_path, num_threads=4):
        super().__init__()
        self.task_id = task_id
        self.url = url
        self.save_path = save_path
        self.num_threads = num_threads
        self.download_thread = None
         
        # 创建UI元素
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)  # 增加边距
        layout.setSpacing(10)  # 调整间距
         
        # 文件名标签
        self.filename_label = QLabel(os.path.basename(url))
        self.filename_label.setStyleSheet("font-weight: bold; color: #DCDCDC; font-size: 14px;")
        self.filename_label.setWordWrap(True)
         
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(20)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #3F3F46;
                border-radius: 5px;
                background-color: #1E1E1E;
                text-align: center;
                height: 20px;
                font-size: 12px;
            }
            QProgressBar::chunk {
                background-color: #0078D7;
                border-radius: 5px;
            }
        """)
         
        # 状态标签
        self.status_label = QLabel("等待开始...")
        self.status_label.setStyleSheet("color: #A0A0A0; font-size: 12px;")
         
        # 控制按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)  # 按钮间距
         
        self.start_btn = QPushButton("开始")
        self.pause_btn = QPushButton("暂停")
        self.cancel_btn = QPushButton("取消")
         
        # 设置按钮样式
        button_style = """
            QPushButton {
                background-color: #3F3F46;
                color: #DCDCDC;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 14px;
                min-width: 80px;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #4F4F56;
            }
            QPushButton:pressed {
                background-color: #2F2F36;
            }
        """
        self.start_btn.setStyleSheet(button_style)
        self.pause_btn.setStyleSheet(button_style)
        self.cancel_btn.setStyleSheet(button_style)
         
        # 设置按钮固定大小
        self.start_btn.setFixedSize(90, 35)
        self.pause_btn.setFixedSize(90, 35)
        self.cancel_btn.setFixedSize(90, 35)
         
        # 添加按钮到布局
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.pause_btn)
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addStretch()
         
        layout.addWidget(self.filename_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
        layout.addLayout(btn_layout)
         
        self.setLayout(layout)
         
        # 连接信号
        self.start_btn.clicked.connect(self.start_download)
        self.pause_btn.clicked.connect(self.pause_download)
        self.cancel_btn.clicked.connect(self.cancel_download)
 
    def start_download(self):
        if self.download_thread is None:
            self.download_thread = DownloadThread(
                self.task_id, self.url, self.save_path, self.num_threads
            )
            self.download_thread.update_progress.connect(self.update_progress)
            self.download_thread.finished.connect(self.download_finished)
            self.download_thread.error.connect(self.download_error)
            self.download_thread.start()
            self.status_label.setText("下载中...")
            self.status_label.setStyleSheet("color: #4EC9B0; font-size: 12px;")
        elif self.download_thread.is_paused:
            self.download_thread.resume()
            self.status_label.setText("下载中...")
            self.status_label.setStyleSheet("color: #4EC9B0; font-size: 12px;")
 
    def pause_download(self):
        if self.download_thread and not self.download_thread.is_paused:
            self.download_thread.pause()
            self.status_label.setText("已暂停")
            self.status_label.setStyleSheet("color: #D69D85; font-size: 12px;")
 
    def cancel_download(self):
        if self.download_thread:
            self.download_thread.cancel()
            self.status_label.setText("已取消")
            self.status_label.setStyleSheet("color: #F44747; font-size: 12px;")
            self.progress_bar.setValue(0)
 
    def update_progress(self, task_id, downloaded, total):
        if task_id != self.task_id:
            return
             
        # 更新进度条
        if total > 0:
            percent = int((downloaded / total) * 100)
            self.progress_bar.setValue(percent)
             
            # 更新状态标签
            downloaded_mb = downloaded / (1024 * 1024)
            total_mb = total / (1024 * 1024)
            self.status_label.setText(f"下载中: {downloaded_mb:.2f}MB / {total_mb:.2f}MB")
 
    def download_finished(self, task_id):
        if task_id == self.task_id:
            self.progress_bar.setValue(100)
            self.status_label.setText("下载完成")
            self.status_label.setStyleSheet("color: #B5CEA8; font-size: 12px;")
 
    def download_error(self, task_id, error_msg):
        if task_id == self.task_id:
            self.status_label.setText(f"错误: {error_msg}")
            self.status_label.setStyleSheet("color: #F44747; font-size: 12px;")
 
class DownloadManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyDownloader v1.1")
        self.setGeometry(100, 100, 900, 700)  # 增大窗口尺寸
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1E1E1E;
                color: #DCDCDC;
                font-family: Segoe UI;
            }
            QLineEdit {
                background-color: #252526;
                border: 1px solid #3F3F46;
                border-radius: 4px;
                padding: 10px;
                color: #DCDCDC;
                selection-background-color: #0078D7;
                font-size: 14px;
                height: 40px;
            }
            QListWidget {
                background-color: #252526;
                border: 1px solid #3F3F46;
                border-radius: 4px;
                alternate-background-color: #2D2D30;
                font-size: 14px;
            }
            QPushButton {
                background-color: #0078D7;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 14px;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #106EBE;
            }
            QPushButton:pressed {
                background-color: #005A9E;
            }
            QComboBox {
                background-color: #252526;
                color: #DCDCDC;
                border: 1px solid #3F3F46;
                border-radius: 4px;
                padding: 10px;
                font-size: 14px;
                min-height: 40px;
            }
            QComboBox QAbstractItemView {
                background-color: #252526;
                color: #DCDCDC;
                selection-background-color: #0078D7;
                font-size: 14px;
            }
            QLabel {
                font-size: 14px;
            }
        """)
         
        self.task_counter = 0
        self.init_ui()
 
    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
         
        # 标题栏
        header_layout = QHBoxLayout()
        self.about_btn = QPushButton("关于")
        self.about_btn.setFixedSize(100, 40)
        self.about_btn.clicked.connect(self.show_about)
        header_layout.addWidget(self.about_btn, alignment=Qt.AlignLeft)
         
        title = QLabel("PyDownloader v1.1")
        title.setStyleSheet("font-size: 24pt; font-weight: bold; color: #DCDCDC;")
        title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title)
        header_layout.addStretch()
         
        # 添加明暗主题切换按钮
        self.theme_toggle = QCheckBox("切换主题")
        self.theme_toggle.setFixedSize(120, 40)
        self.theme_toggle.stateChanged.connect(self.toggle_theme)
        header_layout.addWidget(self.theme_toggle, alignment=Qt.AlignRight)
         
        main_layout.addLayout(header_layout)
         
        # 下载控制区域
        control_layout = QHBoxLayout()
        control_layout.setSpacing(15)
         
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("输入下载链接...")
         
        self.browse_btn = QPushButton("保存位置")
        self.browse_btn.setFixedWidth(150)
        self.browse_btn.setFixedHeight(45)
        self.browse_btn.clicked.connect(self.browse_save_path)
         
        self.thread_combo = QComboBox()
        self.thread_combo.addItems(["1", "2", "4", "8", "16"])
        self.thread_combo.setCurrentIndex(2)
        self.thread_combo.setFixedWidth(100)
        self.thread_combo.setFixedHeight(45)
         
        self.download_btn = QPushButton("添加下载")
        self.download_btn.setFixedWidth(150)
        self.download_btn.setFixedHeight(45)
        self.download_btn.clicked.connect(self.add_download_task)
         
        control_layout.addWidget(self.url_input)
        control_layout.addWidget(self.browse_btn)
        control_layout.addWidget(QLabel("线程数:"))
        control_layout.addWidget(self.thread_combo)
        control_layout.addWidget(self.download_btn)
         
        main_layout.addLayout(control_layout)
         
        # 下载列表
        self.download_list = QListWidget()
        self.download_list.setAlternatingRowColors(True)
        self.download_list.setStyleSheet("""
            QListWidget::item {
                border-bottom: 1px solid #3F3F46;
                padding: 10px;
            }
            QListWidget::item:selected {
                background-color: #3A3A3A;
            }
        """)
         
        download_label = QLabel("下载任务:")
        download_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        main_layout.addWidget(download_label)
        main_layout.addWidget(self.download_list)
         
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
         
        # 设置默认保存路径
        self.save_path = os.path.expanduser("~/Downloads")
         
        # 状态栏
        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet("font-size: 12px;")
        self.status_bar.showMessage(f"就绪 | 保存路径: {self.save_path}")
 
    def browse_save_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择保存路径", self.save_path)
        if path:
            self.save_path = path
            self.status_bar.showMessage(f"保存路径已更新: {path}")
 
    def add_download_task(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "输入错误", "请输入有效的下载链接")
            return
             
        num_threads = int(self.thread_combo.currentText())
        self.task_counter += 1
         
        # 创建列表项
        list_item = QListWidgetItem(self.download_list)
        list_item.setSizeHint(QSize(0, 150))  # 调整列表项高度
         
        # 创建自定义部件
        item_widget = DownloadItemWidget(
            self.task_counter, url, self.save_path, num_threads
        )
         
        self.download_list.setItemWidget(list_item, item_widget)
        self.url_input.clear()
         
        # 自动开始下载
        item_widget.start_download()
         
        self.status_bar.showMessage(f"已添加任务: {os.path.basename(url)}")
 
    def show_about(self):
        about_dialog = AboutDialog(self)
        about_dialog.exec_()
 
    def toggle_theme(self, state):
        if state == Qt.Checked:
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #F0F0F0;
                    color: #000000;
                    font-family: Segoe UI;
                }
                QLineEdit {
                    background-color: #FFFFFF;
                    border: 1px solid #808080;
                    border-radius: 4px;
                    padding: 10px;
                    color: #000000;
                    selection-background-color: #0078D7;
                    font-size: 14px;
                    height: 40px;
                }
                QListWidget {
                    background-color: #FFFFFF;
                    border: 1px solid #808080;
                    border-radius: 4px;
                    alternate-background-color: #F0F0F0;
                    font-size: 14px;
                }
                QPushButton {
                    background-color: #0078D7;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 12px 24px;
                    font-weight: bold;
                    font-size: 14px;
                    min-height: 40px;
                }
                QPushButton:hover {
                    background-color: #106EBE;
                }
                QPushButton:pressed {
                    background-color: #005A9E;
                }
                QComboBox {
                    background-color: #FFFFFF;
                    color: #000000;
                    border: 1px solid #808080;
                    border-radius: 4px;
                    padding: 10px;
                    font-size: 14px;
                    min-height: 40px;
                }
                QComboBox QAbstractItemView {
                    background-color: #FFFFFF;
                    color: #000000;
                    selection-background-color: #0078D7;
                    font-size: 14px;
                }
                QLabel {
                    font-size: 14px;
                }
            """)
            self.status_bar.setStyleSheet("font-size: 12px; color: black;")
        else:
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #1E1E1E;
                    color: #DCDCDC;
                    font-family: Segoe UI;
                }
                QLineEdit {
                    background-color: #252526;
                    border: 1px solid #3F3F46;
                    border-radius: 4px;
                    padding: 10px;
                    color: #DCDCDC;
                    selection-background-color: #0078D7;
                    font-size: 14px;
                    height: 40px;
                }
                QListWidget {
                    background-color: #252526;
                    border: 1px solid #3F3F46;
                    border-radius: 4px;
                    alternate-background-color: #2D2D30;
                    font-size: 14px;
                }
                QPushButton {
                    background-color: #0078D7;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 12px 24px;
                    font-weight: bold;
                    font-size: 14px;
                    min-height: 40px;
                }
                QPushButton:hover {
                    background-color: #106EBE;
                }
                QPushButton:pressed {
                    background-color: #005A9E;
                }
                QComboBox {
                    background-color: #252526;
                    color: #DCDCDC;
                    border: 1px solid #3F3F46;
                    border-radius: 4px;
                    padding: 10px;
                    font-size: 14px;
                    min-height: 40px;
                }
                QComboBox QAbstractItemView {
                    background-color: #252526;
                    color: #DCDCDC;
                    selection-background-color: #0078D7;
                    font-size: 14px;
                }
                QLabel {
                    font-size: 14px;
                }
            """)
            self.status_bar.setStyleSheet("font-size: 12px; color: white;")
 
if __name__ == "__main__":
    app = QApplication(sys.argv)
     
    # 设置应用样式
    app.setStyle("Fusion")
     
    # 设置深色主题
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(30, 30, 30))
    dark_palette.setColor(QPalette.WindowText, QColor(220, 220, 220))
    dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.AlternateBase, QColor(45, 45, 48))
    dark_palette.setColor(QPalette.ToolTipBase, QColor(220, 220, 220))
    dark_palette.setColor(QPalette.ToolTipText, QColor(220, 220, 220))
    dark_palette.setColor(QPalette.Text, QColor(220, 220, 220))
    dark_palette.setColor(QPalette.Button, QColor(45, 45, 48))
    dark_palette.setColor(QPalette.ButtonText, QColor(220, 220, 220))
    dark_palette.setColor(QPalette.BrightText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.Highlight, QColor(0, 120, 215))
    dark_palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
    app.setPalette(dark_palette)
     
    # 设置全局字体
    font = QFont("Segoe UI", 12)
    app.setFont(font)
     
    window = DownloadManager()
    window.show()
    sys.exit(app.exec_())