import os
import sys
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QLabel, QPushButton, QRadioButton, QButtonGroup,
    QStatusBar, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon

class ScriptLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 应用配置
        self.setWindowTitle("交我抢")
        self.setFixedSize(450, 350)
        
        # 定义目标脚本 (显示名称: 文件名)
        self.scripts = {
            "气膜": "bm-time.py",
            "健身房": "gym-time.py"
        }
        
        # 初始化UI
        self.init_ui()
        
        # 检查脚本是否存在
        self.check_scripts()

    def init_ui(self):
        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.setWindowIcon(QIcon("Badmin.ico")) # 如果有图标文件，可以取消注释

        
        # 标题
        title = QLabel("请选择要执行的脚本")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 15px;")
        layout.addWidget(title)
        
        # 脚本选择区域
        self.radio_group = QButtonGroup()
        for name, file in self.scripts.items():
            radio = QRadioButton(f"{name} ({file})")
            radio.setStyleSheet("font-size: 14px; padding: 8px;")
            self.radio_group.addButton(radio)
            layout.addWidget(radio)
        
        # 默认选中第一个
        if self.radio_group.buttons():
            self.radio_group.buttons()[0].setChecked(True)
        
        # 执行按钮
        self.run_btn = QPushButton("执行脚本")
        self.run_btn.setStyleSheet(
            """
            QPushButton {
                font-size: 14px; 
                padding: 10px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            """
        )
        self.run_btn.clicked.connect(self.execute_script)
        layout.addWidget(self.run_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

    def check_scripts(self):
        """检查脚本文件是否存在"""
        missing = []
        for file in self.scripts.values():
            if not os.path.exists(file):
                missing.append(file)
        
        if missing:
            QMessageBox.critical(
                self,
                "文件缺失",
                f"以下脚本文件不存在:\n{', '.join(missing)}\n\n请确保所有文件与启动器在同一目录。"
            )
            self.run_btn.setEnabled(False)

    def execute_script(self):
        """执行选中的脚本"""
        selected_button = self.radio_group.checkedButton()
        if not selected_button:
            QMessageBox.warning(self, "警告", "请先选择一个脚本")
            return
        
        # 从按钮文本提取文件名
        display_name = selected_button.text().split("(")[0].strip()
        file_name = self.scripts[display_name]
        
        self.status_bar.showMessage(f"正在执行: {display_name}...")
        QApplication.processEvents()  # 立即更新UI
        
        try:
            # 使用系统Python解释器运行
            python = sys.executable
            subprocess.Popen([python, file_name], creationflags=subprocess.CREATE_NEW_CONSOLE)
            self.status_bar.showMessage(f"已启动: {display_name}")
        except Exception as e:
            self.status_bar.showMessage("执行失败")
            QMessageBox.critical(
                self,
                "错误",
                f"无法执行脚本 {file_name}:\n{str(e)}"
            )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置应用样式 (可选)
    app.setStyle("Fusion")
    
    # 设置窗口图标 (准备icon.ico文件)
    if os.path.exists("icon.ico"):
        app.setWindowIcon(QIcon("icon.ico"))
    
    launcher = ScriptLauncher()
    launcher.show()
    sys.exit(app.exec())