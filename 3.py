import sys
import re
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QMessageBox, QComboBox, QGridLayout, QGroupBox, QStyleFactory
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

class IPChanger(QWidget):
    def __init__(self):
        super().__init__()
        self.status_value = None
        self.current_ip_value = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle("macOS IP 修改工具")
        self.setGeometry(200, 200, 500, 350)

        # 主题美化
        QApplication.setStyle(QStyleFactory.create("Macintosh"))

        main_layout = QVBoxLayout()

        # 🎨【网卡信息】分组
        net_group = QGroupBox("网卡信息")
        net_layout = QGridLayout()
        net_group.setLayout(net_layout)

        self.interface_label = QLabel("选择网卡:")
        self.interface_dropdown = QComboBox()
        self.interface_dropdown.currentIndexChanged.connect(self.update_ui)
        self.get_network_interfaces()

        self.status_label = QLabel("网卡状态:")
        self.status_value = QLabel("N/A")
        self.current_ip_label = QLabel("当前 IP:")
        self.current_ip_value = QLabel("N/A")

        net_layout.addWidget(self.interface_label, 0, 0)
        net_layout.addWidget(self.interface_dropdown, 0, 1)
        net_layout.addWidget(self.status_label, 1, 0)
        net_layout.addWidget(self.status_value, 1, 1)
        net_layout.addWidget(self.current_ip_label, 2, 0)
        net_layout.addWidget(self.current_ip_value, 2, 1)

        # 🎨【IP 配置】分组
        ip_group = QGroupBox("IP 配置")
        ip_layout = QGridLayout()
        ip_group.setLayout(ip_layout)

        self.ip_label = QLabel("新 IP:")
        self.ip_input = QLineEdit()
        self.subnet_label = QLabel("子网掩码:")
        self.subnet_input = QLineEdit()
        self.gateway_label = QLabel("网关:")
        self.gateway_input = QLineEdit()

        ip_layout.addWidget(self.ip_label, 0, 0)
        ip_layout.addWidget(self.ip_input, 0, 1)
        ip_layout.addWidget(self.subnet_label, 1, 0)
        ip_layout.addWidget(self.subnet_input, 1, 1)
        ip_layout.addWidget(self.gateway_label, 2, 0)
        ip_layout.addWidget(self.gateway_input, 2, 1)

        # 🎨【操作按钮】
        self.apply_btn = QPushButton("修改 IP")
        self.apply_btn.clicked.connect(self.change_ip)
        self.apply_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")

        self.dhcp_btn = QPushButton("恢复 DHCP")
        self.dhcp_btn.clicked.connect(self.set_dhcp)
        self.dhcp_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")

        # 🎨【主界面布局】
        main_layout.addWidget(net_group)
        main_layout.addWidget(ip_group)
        main_layout.addWidget(self.apply_btn)
        main_layout.addWidget(self.dhcp_btn)

        self.setLayout(main_layout)
        self.update_ui()

    def get_network_interfaces(self):
        """获取 macOS 可用的网络接口列表"""
        try:
            result = subprocess.run("networksetup -listallnetworkservices", shell=True, capture_output=True, text=True)
            interfaces = result.stdout.strip().split("\n")[1:]  # 去掉第一行（标题）
            self.interface_dropdown.addItems(interfaces)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法获取网卡列表: {str(e)}")

    def get_network_info(self, interface):
        """获取网卡状态和当前 IP"""
        try:
            result = subprocess.run(f"networksetup -getinfo \"{interface}\"", shell=True, capture_output=True, text=True)
            output = result.stdout.strip()

            status_match = re.search(r"IP address: (.+)", output)
            ip_address = status_match.group(1) if status_match else "未连接"

            if "DHCP Configuration" in output:
                return "动态 IP (DHCP)", ip_address
            else:
                return "静态 IP", ip_address
        except Exception:
            return "未知", "N/A"

    def update_ui(self):
        """更新 UI（显示当前网卡状态和 IP）"""
        interface = self.interface_dropdown.currentText()
        if not interface:
            return

        status, ip = self.get_network_info(interface)
        if self.status_value and self.current_ip_value:
            self.status_value.setText(status)
            self.current_ip_value.setText(ip)

    def validate_ip(self, ip):
        """校验 IP 格式"""
        pattern = r"^(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)$"
        return re.match(pattern, ip) is not None

    def change_ip(self):
        """修改 IP 地址"""
        interface = self.interface_dropdown.currentText()
        ip = self.ip_input.text().strip()
        subnet = self.subnet_input.text().strip()
        gateway = self.gateway_input.text().strip()

        if not (self.validate_ip(ip) and self.validate_ip(subnet) and self.validate_ip(gateway)):
            QMessageBox.warning(self, "错误", "IP、子网掩码或网关格式不正确！")
            return

        cmd = f"osascript -e 'do shell script \"networksetup -setmanual \\\"{interface}\\\" {ip} {subnet} {gateway}\" with administrator privileges'"
        self.run_command(cmd)

    def set_dhcp(self):
        """切换到 DHCP 自动获取 IP"""
        interface = self.interface_dropdown.currentText()
        cmd = f"osascript -e 'do shell script \"networksetup -setdhcp \\\"{interface}\\\"\" with administrator privileges'"
        self.run_command(cmd)

    def run_command(self, cmd):
        """运行 shell 命令"""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                QMessageBox.information(self, "成功", "操作成功")
                self.update_ui()
            else:
                QMessageBox.critical(self, "错误", f"执行失败:\n{result.stderr}")
        except Exception as e:
            QMessageBox.critical(self, "异常", f"发生错误:\n{str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = IPChanger()
    window.show()
    sys.exit(app.exec())