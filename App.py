import sys
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QStackedWidget,
    QTableWidget,
    QCheckBox,
    QHBoxLayout,
    QStyledItemDelegate,
)
from PyQt5.QtGui import QPixmap, QPainter, QBrush
from PyQt5.QtCore import Qt, QSize
from yuyt import Badminton

class CustomCheckBox(QCheckBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            "QCheckBox::indicator {"
            "width: 20px;"
            "height: 20px;"
            "border: 2px solid #0078d4;"
            "border-radius: 5px;"
            "background-color: white;"
            "}"
            "QCheckBox::indicator:checked {"
            "background-color: #0078d4;"
            "border: 2px solid #0056a0;"
            "}"
        )


class TokenLoginApp(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        # 设置窗口标题和大小
        self.setWindowTitle("羽毛球预约系统")
        self.setGeometry(100, 100, 1000, 700)  # 更大窗口尺寸

        # 创建堆叠式布局
        self.stacked_widget = QStackedWidget()
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.stacked_widget)

        # 创建登录界面
        self.login_page = QWidget()
        self.stacked_widget.addWidget(self.login_page)
        self.create_login_page()

        # 创建主界面
        self.main_page = QWidget()
        self.stacked_widget.addWidget(self.main_page)
        self.create_main_page()

    def create_login_page(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)

        # 添加 Logo
        logo_label = QLabel()
        logo_pixmap = QPixmap(
            "https://img.meituan.net/csc/8db0b5dadc4b2259e20063c8cd8eaf836980.png"
        )  # 替换为你的 Logo 文件路径
        logo_label.setPixmap(
            logo_pixmap.scaled(400, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )  # 调整 Logo 大小
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)

        # 创建并添加 Token 输入框和提交按钮
        self.token_input = QLineEdit(self)
        self.token_input.setPlaceholderText("请输入 Token")
        self.token_input.setFixedSize(300, 40)
        layout.addWidget(self.token_input)

        login_button = QPushButton("登录", self)
        login_button.setFixedSize(150, 50)
        login_button.clicked.connect(self.submit_token)
        layout.addWidget(login_button)

        self.login_page.setLayout(layout)

    def create_main_page(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)

        # 添加 Logo
        logo_label = QLabel()
        logo_pixmap = QPixmap(
            "https://img.meituan.net/csc/8db0b5dadc4b2259e20063c8cd8eaf836980.png"
        )  # 替换为你的 Logo 文件路径
        logo_label.setPixmap(
            logo_pixmap.scaled(400, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )  # 调整 Logo 大小
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)

        # 创建表格
        self.table_widget = QTableWidget(13, 9)  # 13 行 9 列
        self.table_widget.setHorizontalHeaderLabels(
            [f"{i+1}号羽毛球" for i in range(9)]
        )  # 设置列标题
        self.table_widget.setVerticalHeaderLabels(
            [f"{i+9}:00--{i+10}:00" for i in range(13)]
        )  # 设置行标题

        # 设置表格样式和尺寸
        self.table_widget.setColumnWidth(0, 90)
        self.table_widget.setColumnWidth(1, 90)
        self.table_widget.setColumnWidth(2, 90)
        self.table_widget.setColumnWidth(3, 90)
        self.table_widget.setColumnWidth(4, 90)
        self.table_widget.setColumnWidth(5, 90)
        self.table_widget.setColumnWidth(6, 90)
        self.table_widget.setColumnWidth(7, 90)
        self.table_widget.setColumnWidth(8, 90)

        self.table_widget.setRowHeight(0, 50)
        self.table_widget.setRowHeight(1, 50)
        self.table_widget.setRowHeight(2, 50)
        self.table_widget.setRowHeight(3, 50)
        self.table_widget.setRowHeight(4, 50)
        self.table_widget.setRowHeight(5, 50)
        self.table_widget.setRowHeight(6, 50)
        self.table_widget.setRowHeight(7, 50)
        self.table_widget.setRowHeight(8, 50)
        self.table_widget.setRowHeight(9, 50)
        self.table_widget.setRowHeight(10, 50)
        self.table_widget.setRowHeight(11, 50)
        self.table_widget.setRowHeight(12, 50)

        # 填充表格，每个单元格添加自定义复选框
        for row in range(13):
            for col in range(9):
                check_box = CustomCheckBox()
                self.table_widget.setCellWidget(row, col, check_box)

        layout.addWidget(self.table_widget)

        # 添加确认按钮
        confirm_button = QPushButton("确认选择", self)
        confirm_button.setFixedSize(150, 50)
        confirm_button.clicked.connect(self.confirm_selection)
        layout.addWidget(confirm_button)

        self.main_page.setLayout(layout)

    def submit_token(self):
        token = self.token_input.text()

        # 检查 token 是否为空
        if not token:
            QMessageBox.warning(self, "警告", "Token 不能为空！")
        else:
            # 验证 token 是否有效（这里只是示例，实际情况可以加入更多逻辑）
            if token == "ss":  # 这里替换为实际的 Token 验证逻辑
                self.stacked_widget.setCurrentWidget(self.main_page)
            else:
                QMessageBox.warning(self, "警告", "无效的 Token，请重新输入！")
                self.token_input.clear()

    def confirm_selection(self):
        selected_cells = []
        for row in range(13):
            for col in range(9):
                checkbox = self.table_widget.cellWidget(row, col)
                if checkbox.isChecked():
                    selected_cells.append((row, col))

        if not selected_cells:
            QMessageBox.information(self, "选择信息", "没有选择任何场地或时间段。")
        else:
            selected_str = ", ".join(
                [f"行 {row+1}, 列 {col+1}" for row, col in selected_cells]
            )
            QMessageBox.information(
                self, "选择信息", f"已选择的场地和时间段：\n{selected_str}"
            )
            print(selected_cells)
            Badminton().booking(selected_cells)


# 主程序入口
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = TokenLoginApp()
    ex.show()
    sys.exit(app.exec_())
