"""
控制面板组件
包含所有控制选项的选项卡面板
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
                           QPushButton, QTableWidget, QTableWidgetItem, QSlider, 
                           QComboBox, QDoubleSpinBox, QHeaderView, QTabWidget)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont
import math

class CoordinateSystemPanel(QWidget):
    """坐标系设置面板"""
    
    # 信号定义
    system_selected = pyqtSignal(str) # 坐标系选择信号
    parameter_changed = pyqtSignal() # 参数修改信号
    add_system = pyqtSignal() # 添加坐标系信号
    delete_system = pyqtSignal() # 删除坐标系信号
    rename_system = pyqtSignal(str)  # ✅ 修改：重命名坐标系信号（只传递旧名称）
    
    def __init__(self, parent=None):
        """
        初始化坐标系设置面板
        
        参数:
        parent (QWidget, optional): 父组件
        """
        super().__init__(parent)
        
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 坐标系选择
        coord_group = QGroupBox("坐标系选择")
        coord_group_layout = QHBoxLayout(coord_group)
        
        self.source_system_combo = QComboBox()
        self.target_system_combo = QComboBox()

        
        coord_group_layout.addWidget(QLabel("源坐标系:"))
        coord_group_layout.addWidget(self.source_system_combo)
        coord_group_layout.addWidget(QLabel("目标坐标系:"))
        coord_group_layout.addWidget(self.target_system_combo)

        
        # 禁用控件
        self.source_system_combo.setEnabled(False)
        self.target_system_combo.setEnabled(False)
        
        layout.addWidget(coord_group)
        
        # 坐标系参数设置
        system_params_group = QGroupBox("坐标系参数设置")
        system_params_layout = QVBoxLayout(system_params_group)
        
        # 坐标系选择
        self.system_select_combo = QComboBox()
        self.system_select_combo.setEditable(False)  # ✅ 设置为不可编辑
        self.system_select_combo.currentTextChanged.connect(self.system_selected.emit)
        
        system_params_layout.addWidget(QLabel("选择要编辑的坐标系:"))
        system_params_layout.addWidget(self.system_select_combo)

        # ✅ 新增：重命名按钮
        rename_btn_layout = QHBoxLayout()
        self.rename_system_btn = QPushButton("重命名选中坐标系")
        self.rename_system_btn.clicked.connect(self.on_rename_system_clicked)
        rename_btn_layout.addWidget(self.rename_system_btn)
        rename_btn_layout.addStretch()
        system_params_layout.addLayout(rename_btn_layout)

        # 原点位置
        origin_layout = QHBoxLayout()
        origin_layout.addWidget(QLabel("原点X:"))
        self.origin_x_spin = QDoubleSpinBox()
        self.origin_x_spin.setRange(-100, 100)
        self.origin_x_spin.setDecimals(3)
        self.origin_x_spin.valueChanged.connect(self.parameter_changed.emit)
        
        origin_layout.addWidget(self.origin_x_spin)
        origin_layout.addWidget(QLabel("原点Y:"))
        self.origin_y_spin = QDoubleSpinBox()
        self.origin_y_spin.setRange(-100, 100)
        self.origin_y_spin.setDecimals(3)
        self.origin_y_spin.valueChanged.connect(self.parameter_changed.emit)
        
        origin_layout.addWidget(self.origin_y_spin)
        system_params_layout.addLayout(origin_layout)
        
        # 轴角度
        angle_layout = QHBoxLayout()
        angle_layout.addWidget(QLabel("X轴角度:"))
        self.x_angle_spin = QDoubleSpinBox()
        self.x_angle_spin.setRange(0, 360)
        self.x_angle_spin.setDecimals(3)
        self.x_angle_spin.valueChanged.connect(self.parameter_changed.emit)
        
        angle_layout.addWidget(self.x_angle_spin)
        angle_layout.addWidget(QLabel("Y轴角度:"))
        self.y_angle_spin = QDoubleSpinBox()
        self.y_angle_spin.setRange(0, 360)
        self.y_angle_spin.setDecimals(3)
        self.y_angle_spin.valueChanged.connect(self.parameter_changed.emit)
        
        angle_layout.addWidget(self.y_angle_spin)
        system_params_layout.addLayout(angle_layout)
        
        # 比例因子
        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel("X轴比例:"))
        self.x_scale_spin = QDoubleSpinBox()
        self.x_scale_spin.setRange(0.1, 10)
        self.x_scale_spin.setDecimals(3)
        self.x_scale_spin.valueChanged.connect(self.parameter_changed.emit)
        
        scale_layout.addWidget(self.x_scale_spin)
        scale_layout.addWidget(QLabel("Y轴比例:"))
        self.y_scale_spin = QDoubleSpinBox()
        self.y_scale_spin.setRange(0.1, 10)
        self.y_scale_spin.setDecimals(3)
        self.y_scale_spin.valueChanged.connect(self.parameter_changed.emit)
        
        scale_layout.addWidget(self.y_scale_spin)
        system_params_layout.addLayout(scale_layout)
        
        # 添加/删除坐标系按钮
        button_layout = QHBoxLayout()
        self.add_system_btn = QPushButton("添加坐标系")
        self.add_system_btn.clicked.connect(self.add_system.emit)
        
        self.delete_system_btn = QPushButton("删除坐标系")
        self.delete_system_btn.clicked.connect(self.delete_system.emit)
        
        button_layout.addWidget(self.add_system_btn)
        button_layout.addWidget(self.delete_system_btn)
        system_params_layout.addLayout(button_layout)
        
        layout.addWidget(system_params_group)

    def mousePressEvent(self, event):
        """
        重写鼠标按下事件，点击空白区域时清除焦点
        """
        # 清除所有子控件的焦点
        self.clearFocus()
        for child in self.findChildren(QWidget):
            child.clearFocus()
        event.accept()    
    
    
    def update_system_list(self, system_names, current_system=None):
        """
        更新坐标系列表
        
        参数:
        system_names (list): 坐标系名称列表
        current_system (str, optional): 当前选中的坐标系
        """
        # 保存当前选中的坐标系
        if current_system is None and self.system_select_combo.count() > 0:
            current_system = self.system_select_combo.currentText()
        
        # 清空下拉框
        self.source_system_combo.clear()
        self.target_system_combo.clear()
        self.system_select_combo.clear()
        
        # 添加坐标系名称
        for name in system_names:
            self.source_system_combo.addItem(name)
            self.target_system_combo.addItem(name)
            # 世界坐标系不可编辑
            if name != "世界坐标系":
                self.system_select_combo.addItem(name)
        
        # 选择当前坐标系
        if current_system and self.system_select_combo.findText(current_system) >= 0:
            self.system_select_combo.setCurrentText(current_system)
    
    def update_parameter_display(self, params):
        """
        更新参数显示
        
        参数:
        params (dict): 坐标系参数
        """
        self.origin_x_spin.setValue(params.get('origin_x', 0))
        self.origin_y_spin.setValue(params.get('origin_y', 0))
        self.x_angle_spin.setValue(params.get('x_angle', 0))
        self.y_angle_spin.setValue(params.get('y_angle', 90))
        self.x_scale_spin.setValue(params.get('x_scale', 1))
        self.y_scale_spin.setValue(params.get('y_scale', 1))
    
    def get_parameters(self):
        """
        获取当前参数
        
        返回:
        dict: 当前参数
        """
        return {
            'origin_x': self.origin_x_spin.value(),
            'origin_y': self.origin_y_spin.value(),
            'x_angle': self.x_angle_spin.value(),
            'y_angle': self.y_angle_spin.value(),
            'x_scale': self.x_scale_spin.value(),
            'y_scale': self.y_scale_spin.value()
        }
    
    def get_source_system(self):
        """
        获取源坐标系名称
        
        返回:
        str: 源坐标系名称
        """
        return self.source_system_combo.currentText()
    
    def get_target_system(self):
        """
        获取目标坐标系名称
        
        返回:
        str: 目标坐标系名称
        """
        return self.target_system_combo.currentText()
    
    def get_selected_system(self):
        """
        获取选中的坐标系名称
        
        返回:
        str: 选中的坐标系名称
        """
        return self.system_select_combo.currentText()
    
    def on_rename_system_clicked(self):
        """点击重命名坐标系按钮"""
        old_name = self.system_select_combo.currentText()
        if old_name and old_name != "世界坐标系":
            # 发送重命名信号，参数为旧名称
            self.rename_system.emit(old_name)


class RobotArmPanel(QWidget):
    """机械臂设置面板"""
    
    # 信号定义
    parameter_changed = pyqtSignal()
    move_robot = pyqtSignal(float, float)
    rotate_robot = pyqtSignal(float)
    
    def __init__(self, parent=None):
        """
        初始化机械臂设置面板
        
        参数:
        parent (QWidget, optional): 父组件
        """
        super().__init__(parent)
        
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 机械臂参数设置
        robot_params_group = QGroupBox("机械臂参数设置")
        robot_params_layout = QVBoxLayout(robot_params_group)
        
        # 旋转轴位置
        base_layout = QHBoxLayout()
        base_layout.addWidget(QLabel("旋转轴X:"))
        self.base_x_spin = QDoubleSpinBox()
        self.base_x_spin.setRange(-1000, 1000)
        self.base_x_spin.setDecimals(3)
        self.base_x_spin.valueChanged.connect(self.parameter_changed.emit)
        
        base_layout.addWidget(self.base_x_spin)
        base_layout.addWidget(QLabel("旋转轴Y:"))
        self.base_y_spin = QDoubleSpinBox()
        self.base_y_spin.setRange(-1000, 1000)
        self.base_y_spin.setDecimals(3)
        self.base_y_spin.valueChanged.connect(self.parameter_changed.emit)
        
        base_layout.addWidget(self.base_y_spin)
        robot_params_layout.addLayout(base_layout)
        
        # 旋转角度
        angle_layout = QHBoxLayout()
        angle_layout.addWidget(QLabel("旋转角度:"))
        self.angle_spin = QDoubleSpinBox()
        self.angle_spin.setRange(0, 360)
        self.angle_spin.setDecimals(3)
        self.angle_spin.valueChanged.connect(self.parameter_changed.emit)
        
        angle_layout.addWidget(self.angle_spin)
        
        # 角度范围选择 - 移到旋转角度控件前面
        angle_range_layout = QHBoxLayout()
        angle_range_layout.addWidget(QLabel("角度范围:"))
        self.angle_range_combo = QComboBox()
        self.angle_range_combo.addItems(['0~360度', '-360~360度', '-180~180度'])
        self.angle_range_combo.setCurrentIndex(0)  # 默认0~360度
        self.angle_range_combo.currentTextChanged.connect(self.on_angle_range_changed)
        
        angle_range_layout.addWidget(self.angle_range_combo)
        robot_params_layout.addLayout(angle_range_layout)
        
        # 旋转角度滑块 - 根据角度范围动态设置范围
        self.angle_slider = QSlider(Qt.Horizontal)
        self.update_angle_slider_range()  # 初始设置滑块范围
        self.angle_slider.valueChanged.connect(self.on_angle_slider_changed)
        
        angle_layout.addWidget(self.angle_slider)
        robot_params_layout.addLayout(angle_layout)
        
        # 旋转半径
        radius_layout = QHBoxLayout()
        radius_layout.addWidget(QLabel("旋转半径:"))
        self.radius_spin = QDoubleSpinBox()
        self.radius_spin.setRange(0.1, 200) 
        self.radius_spin.setDecimals(3)
        self.radius_spin.valueChanged.connect(self.parameter_changed.emit)
        
        radius_layout.addWidget(self.radius_spin)
        robot_params_layout.addLayout(radius_layout)
        
        # 机械臂平移按钮
        move_layout = QHBoxLayout()
        self.move_up_btn = QPushButton("↑")
        self.move_down_btn = QPushButton("↓")
        self.move_left_btn = QPushButton("←")
        self.move_right_btn = QPushButton("→")
        
        self.move_up_btn.clicked.connect(lambda: self.move_robot.emit(0, 1)) #0.5是向上移动的距离
        self.move_down_btn.clicked.connect(lambda: self.move_robot.emit(0, -1))
        self.move_left_btn.clicked.connect(lambda: self.move_robot.emit(-1, 0))
        self.move_right_btn.clicked.connect(lambda: self.move_robot.emit(1, 0))
        
        move_layout.addWidget(self.move_left_btn)
        move_layout.addWidget(self.move_up_btn)
        move_layout.addWidget(self.move_down_btn)
        move_layout.addWidget(self.move_right_btn)
        robot_params_layout.addLayout(move_layout)
        
        # 机械臂旋转按钮
        rotate_layout = QHBoxLayout()
        self.rotate_left_btn = QPushButton("顺时针旋转")
        self.rotate_right_btn = QPushButton("逆时针旋转")
        
        self.rotate_left_btn.clicked.connect(lambda: self.rotate_robot.emit(-15))#-15是逆时针旋转
        self.rotate_right_btn.clicked.connect(lambda: self.rotate_robot.emit(15))
        
        rotate_layout.addWidget(self.rotate_left_btn)
        rotate_layout.addWidget(self.rotate_right_btn)
        robot_params_layout.addLayout(rotate_layout)
        
        # 显示抓手坐标
        self.gripper_pos_label = QLabel("抓手坐标: (0.00, 0.00,0.00°)")
        robot_params_layout.addWidget(self.gripper_pos_label)
        
        layout.addWidget(robot_params_group)


        # 添加信号连接
        self.base_x_spin.valueChanged.connect(self._update_gripper_position)
        self.base_y_spin.valueChanged.connect(self._update_gripper_position)
        self.angle_spin.valueChanged.connect(self._update_gripper_position)
        self.radius_spin.valueChanged.connect(self._update_gripper_position)
    

    def mousePressEvent(self, event):
        """
        重写鼠标按下事件，点击空白区域时清除焦点
        """
        # 清除所有子控件的焦点
        self.clearFocus()
        for child in self.findChildren(QWidget):
            child.clearFocus()
        event.accept()


    def _update_gripper_position(self):
        base_x = self.base_x_spin.value()
        base_y = self.base_y_spin.value()
        angle_deg = self.angle_spin.value()
        radius = self.radius_spin.value()

        angle_rad = math.radians(angle_deg)
        gripper_x = base_x + radius * math.cos(angle_rad)
        gripper_y = base_y + radius * math.sin(angle_rad)

        self.update_gripper_position_display(gripper_x, gripper_y, angle_deg)
    
    
    def update_parameter_display(self, params):
        """
        更新参数显示
        
        参数:
        params (dict): 机械臂参数
        """
        self.base_x_spin.setValue(params.get('base_x', 0))
        self.base_y_spin.setValue(params.get('base_y', 0))
        self.angle_spin.setValue(params.get('angle', 0))
        self.angle_slider.setValue(int(params.get('angle', 0)))
        self.radius_spin.setValue(params.get('radius', 1))#1是抓手的半径
        
        # ✅ 使用传入的抓手坐标参数（这些值已经在 RobotArm 类中用正确的 radius 计算过）
        gripper_x = params.get('gripper_x', 0)
        gripper_y = params.get('gripper_y', 0)
        angle = params.get('angle', 0)
        self.update_gripper_position_display(gripper_x, gripper_y, angle)
    
    def get_parameters(self):
        """
        获取当前参数
        
        返回:
        dict: 当前参数
        """
        return {
            'base_x': self.base_x_spin.value(),
            'base_y': self.base_y_spin.value(),
            'angle': self.angle_spin.value(),
            'radius': self.radius_spin.value()
        }
    
    def update_gripper_position_display(self, x, y, angle=None):
        """
        更新抓手坐标显示
        
        参数:
        x (float): 抓手X坐标
        y (float): 抓手Y坐标
        angle (float, optional): 抓手角度
        """
        if angle is not None:
            self.gripper_pos_label.setText(f"抓手坐标: ({x:.3f}, {y:.3f}, {angle:.3f}°)")
        else:
            self.gripper_pos_label.setText(f"抓手坐标: ({x:.3f}, {y:.3f})")
    
    def update_angle_slider_range(self):
        """
        根据当前选择的角度范围更新角度滑块的范围
        """
        angle_range_text = self.angle_range_combo.currentText()
        current_angle = self.angle_spin.value()
        
        if angle_range_text == '0~360度':
            self.angle_slider.setRange(0, 360)
            # 将当前角度映射到0-360范围
            mapped_angle = current_angle % 360
        elif angle_range_text == '-360~360度':
            self.angle_slider.setRange(-360, 360)
            # 将当前角度映射到-360-360范围
            while current_angle > 360:
                current_angle -= 720
            while current_angle < -360:
                current_angle += 720
            mapped_angle = current_angle
        elif angle_range_text == '-180~180度':
            self.angle_slider.setRange(-180, 180)
            # 将当前角度映射到-180-180范围
            mapped_angle = ((current_angle + 180) % 360) - 180
        else:
            self.angle_slider.setRange(0, 360)
            mapped_angle = current_angle % 360
        
        # 更新滑块和输入框的值
        self.angle_slider.setValue(int(mapped_angle))
        self.angle_spin.setValue(mapped_angle)
    
    def on_angle_range_changed(self, text):
        """
        角度范围选择改变时的处理函数
        
        参数:
        text (str): 选择的角度范围文本
        """
        # 更新角度滑块范围
        self.update_angle_slider_range()
        
        # 发送角度范围改变信号
        angle_range_map = {
            '0~360度': '0-360',
            '-360~360度': '-360-360',
            '-180~180度': '-180-180'
        }
        if text in angle_range_map:
            # 发送角度范围改变信号，需要在主程序中处理
            self.parameter_changed.emit()
    
    def on_angle_slider_changed(self, value):
        """
        角度滑块变化处理
        
        参数:
        value (int): 滑块值
        """
        self.angle_spin.setValue(value)


class PointConversionPanel(QWidget):
    """坐标点转换面板"""
    
    # 信号定义
    transform_point = pyqtSignal()
    add_point = pyqtSignal(float, float, float)  # 修改：添加 x, y, angle 参数
    edit_point = pyqtSignal(str)  # 参数为点名称
    remove_point = pyqtSignal()
    clear_points = pyqtSignal()
    batch_transform = pyqtSignal() # 添加批量转换信号
    import_points = pyqtSignal() # 添加导入点信号
    export_points = pyqtSignal()
    update_point = pyqtSignal(str, float, float, float, str)  # 点名称, x, y, 角度, 坐标系
    point_name_changed = pyqtSignal(int, str, str)  # ✅ 修改：行号，旧名称，新名称
    input_changed = pyqtSignal()  # ✅ 新增：输入变化信号（用于单点转换）

    def __init__(self, parent=None):
        """
        初始化坐标点转换面板
        
        参数:
        parent (QWidget, optional): 父组件
        """
        super().__init__(parent)
        
        # ✅ 关键修复：添加标志位阻止信号循环
        self._block_cell_change_signal = False

        # ✅ 关键修复：添加字典存储每行对应的点名称（用于获取旧名称）
        self._row_to_point_name = {}

        # 1. 确保类中包含此方法定义
    
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 单点转换
        single_point_group = QGroupBox("单点转换")
        single_point_layout = QVBoxLayout(single_point_group)
        
        # 源坐标系选择
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("源坐标系:"))
        self.source_system_combo = QComboBox()
        # ✅ 关键修复：连接信号
        self.source_system_combo.currentTextChanged.connect(self.input_changed.emit)
        source_layout.addWidget(self.source_system_combo)
        single_point_layout.addLayout(source_layout)
        
        # 输入点坐标（包含角度）
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("X:"))
        self.input_x_spin = QDoubleSpinBox()
        self.input_x_spin.setRange(-1000, 1000)
        self.input_x_spin.setDecimals(3)
        # ✅ 关键修复：连接信号
        self.input_x_spin.valueChanged.connect(self.input_changed.emit)
        input_layout.addWidget(self.input_x_spin)
        
        input_layout.addWidget(QLabel("Y:"))
        self.input_y_spin = QDoubleSpinBox()
        self.input_y_spin.setRange(-1000, 1000)
        self.input_y_spin.setDecimals(3) # 设置小数位数
        # ✅ 关键修复：连接信号
        self.input_y_spin.valueChanged.connect(self.input_changed.emit)
        input_layout.addWidget(self.input_y_spin)
        
        input_layout.addWidget(QLabel("A:"))
        self.input_a_spin = QDoubleSpinBox()
        self.input_a_spin.setRange(-360, 360)
        self.input_a_spin.setDecimals(3)
        self.input_a_spin.setSuffix("°")
        # ✅ 关键修复：连接信号
        self.input_a_spin.valueChanged.connect(self.input_changed.emit)
        input_layout.addWidget(self.input_a_spin)
        
        single_point_layout.addLayout(input_layout)
        
        # 目标坐标系选择
        target_layout = QHBoxLayout()
        target_layout.addWidget(QLabel("目标坐标系:"))
        self.target_system_combo = QComboBox()
        # ✅ 关键修复：连接信号
        self.target_system_combo.currentTextChanged.connect(self.input_changed.emit)
        target_layout.addWidget(self.target_system_combo)
        single_point_layout.addLayout(target_layout)
        
        # 转换按钮
        self.transform_btn = QPushButton("转换")
        self.transform_btn.clicked.connect(self.transform_point.emit)
        single_point_layout.addWidget(self.transform_btn)
        
        # 显示转换结果
        self.result_label = QLabel("转换结果: (0.000, 0.000, 0.000°)")
        single_point_layout.addWidget(self.result_label)
        
        layout.addWidget(single_point_group)
        
        # 批量转换
        batch_point_group = QGroupBox("批量转换")
        batch_point_layout = QVBoxLayout(batch_point_group)
        
        # 创建新的点表格，分为源坐标系和目标坐标系
        self.point_table = QTableWidget()
        self.point_table.setColumnCount(8)  # 序号 + 点名称 + 源坐标系(X,Y,A) + 目标坐标系(X,Y,A)
        self.point_table.setHorizontalHeaderLabels(["序号", "点名称", "X机", "Y机", "A机", "X", "Y", "A"])
        
        # 设置表头样式
        header = self.point_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # 点名称列自动拉伸
        
        # 设置列宽
        self.point_table.setColumnWidth(0, 60)  # 序号
        self.point_table.setColumnWidth(2, 80)  # 源X
        self.point_table.setColumnWidth(3, 80)  # 源Y
        self.point_table.setColumnWidth(4, 80)  # 源A
        self.point_table.setColumnWidth(5, 80)  # 目标X
        self.point_table.setColumnWidth(6, 80)  # 目标Y
        self.point_table.setColumnWidth(7, 80)  # 目标A
        
        # 设置表头标签
        header_labels = [
            "序号", "点名称", 
            "X机", "Y机", "A机", 
            "X", "Y", "A"
        ]
        
        # 设置表头标签
        for i, label in enumerate(header_labels):
            item = QTableWidgetItem(label)
            item.setTextAlignment(Qt.AlignCenter)
            if i in [0, 1]:
                # 序号和点名称列
                item.setBackground(QColor(240, 240, 240))
            elif i in [2, 3, 4]:
                # 源坐标系列
                item.setBackground(QColor(220, 230, 241))
            else:
                # 目标坐标系列
                item.setBackground(QColor(235, 245, 235))
            self.point_table.setHorizontalHeaderItem(i, item)
        
        # 连接信号
        self.point_table.cellChanged.connect(self.on_point_cell_changed)  # 监听单元格变化
        self.point_table.itemDoubleClicked.connect(self.on_point_cell_double_clicked) # 监听单元格双击
        
        batch_point_layout.addWidget(self.point_table)
        
        # 点操作按钮
        point_ops_layout = QHBoxLayout()
        self.add_point_btn = QPushButton("添加点")
        self.add_point_btn.clicked.connect(self.show_add_point_dialog)
        
        self.edit_point_btn = QPushButton("编辑点")
        self.edit_point_btn.clicked.connect(self.on_edit_point)
        
        self.remove_point_btn = QPushButton("删除点")
        self.remove_point_btn.clicked.connect(self.remove_point.emit)
        
        self.clear_points_btn = QPushButton("清空所有点")
        self.clear_points_btn.clicked.connect(self.clear_points.emit)
        
        point_ops_layout.addWidget(self.add_point_btn)
        # point_ops_layout.addWidget(self.edit_point_btn)
        point_ops_layout.addWidget(self.remove_point_btn)
        point_ops_layout.addWidget(self.clear_points_btn)
        batch_point_layout.addLayout(point_ops_layout)
        
        # 批量转换按钮
        self.batch_transform_btn = QPushButton("批量转换选中点")
        self.batch_transform_btn.clicked.connect(self.batch_transform.emit)
        batch_point_layout.addWidget(self.batch_transform_btn)
        
        # 导入导出按钮
        import_export_layout = QHBoxLayout()
        self.import_btn = QPushButton("导入点")
        self.import_btn.clicked.connect(self.import_points.emit)
        
        self.export_btn = QPushButton("导出点")
        self.export_btn.clicked.connect(self.export_points.emit)
        
        import_export_layout.addWidget(self.import_btn)
        import_export_layout.addWidget(self.export_btn)
        batch_point_layout.addLayout(import_export_layout)
        
        layout.addWidget(batch_point_group)


    def mousePressEvent(self, event):
        """
        重写鼠标按下事件，点击空白区域时清除焦点
        """
        # 清除所有子控件的焦点
        self.clearFocus()
        for child in self.findChildren(QWidget):
            child.clearFocus()
        event.accept()    
    
    def update_target_coordinates(self, data):
        # 实现坐标更新逻辑
        pass

    def on_point_cell_changed(self, event):
        # 2. 调用时确保方法已存在
        try:
            self.update_target_coordinates(event.data)
        except AttributeError:
            # 可选：添加异常处理以便调试
            print("Error: update_target_coordinates method missing")


    def get_input_point(self):
        """
        获取输入点坐标和角度
        
        返回:
        tuple: (x, y, angle)
        """
        return (self.input_x_spin.value(), self.input_y_spin.value(), self.input_a_spin.value())
    
    def set_input_point(self, x, y, angle=0.0):
        """
        设置输入点坐标和角度
        
        参数:
        x (float): X坐标
        y (float): Y坐标
        angle (float): 角度
        """
        self.input_x_spin.setValue(x)
        self.input_y_spin.setValue(y)
        self.input_a_spin.setValue(angle)
    
    def set_result_text(self, text):
        """
        设置结果文本
        
        参数:
        text (str): 结果文本
        """
        self.result_label.setText(text)
    
    def on_point_cell_double_clicked(self, item):
        """
        双击表格单元格编辑点信息
        
        参数:
        item (QTableWidgetItem): 被双击的单元格
        """
        row = item.row()
        col = item.column()
        # self.on_edit_point()

        # ✅ 只允许双击第 1、2、3、4 列时进入编辑模式
        if col in [1, 2, 3, 4]:
            edit_item = self.point_table.item(row, col)
            if edit_item:
                self.point_table.editItem(edit_item)
        # ✅ 双击其他列时，不响应或打开完整的编辑对话框
        else:
            # 可选：如果需要在双击其他列时打开完整编辑对话框
            point_name = self.point_table.item(row, 1).text()
            self.edit_point.emit(point_name)
    
    def on_edit_point(self):
        """
        编辑选中的点信息
        """
        selected_rows = self.point_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        point_name = self.point_table.item(row, 1).text()
        
        # 发送编辑点信号
        self.edit_point.emit(point_name)


    def update_system_list(self, system_names):
        """
        更新单点转换的源和目标坐标系下拉框
        
        参数:
        system_names (list): 坐标系名称列表
        """
        if hasattr(self, 'source_system_combo') and hasattr(self, 'target_system_combo'):
            # 保存当前选择
            current_source = self.source_system_combo.currentText()
            current_target = self.target_system_combo.currentText()
            
            # 更新下拉框内容
            self.source_system_combo.clear()
            self.target_system_combo.clear()
            self.source_system_combo.addItems(system_names)
            self.target_system_combo.addItems(system_names)
            
            # 恢复之前的选择，如果存在的话
            if current_source in system_names:
                self.source_system_combo.setCurrentText(current_source)
            if current_target in system_names:
                self.target_system_combo.setCurrentText(current_target)
            # 如果没有选择或选择不存在，默认选择第一个和第二个
            elif len(system_names) > 1:
                self.target_system_combo.setCurrentIndex(1)

            
    
    def update_point_table(self, points):
        """
        更新点表格（兼容旧接口，调用新的update_points_display方法）
        
        参数:
        points (dict): 点字典
        """
        self.update_points_display(points)
    
    def update_points_display(self, points):
        """
        更新批量转换表格的点显示
        
        参数:
        points (dict): 点字典
        """
        try:
            print(f"📊 update_points_display 被调用，points keys: {list(points.keys())}")
            
            # ✅ 关键修复：更新表格前阻塞信号
            self._block_cell_change_signal = True
            
            # ✅ 关键修复：清空并重建行到名称的映射
            self._row_to_point_name.clear()
            
            # 清空表格
            self.point_table.setRowCount(0)
            
            # 获取当前选择的目标坐标系
            target_system = self.target_system_combo.currentText()

            # 预先获取坐标转换器
            transformer = None
            parent = self.parent()
            while parent is not None:
                if hasattr(parent, 'transformer'):
                    transformer = parent.transformer
                    break
                parent = parent.parent()
            
            # 添加所有点到表格（保持传入的顺序）
            for idx, (point_name, point_data) in enumerate(points.items()):
                row = self.point_table.rowCount()
                self.point_table.insertRow(row)
                
                # ✅ 关键修复：建立行号到点名称的映射
                self._row_to_point_name[row] = point_name
                print(f"   建立映射：行 {row} -> 点名称：{point_name}")
                
                # 设置序号（从 1 开始）
                self.point_table.setItem(row, 0, QTableWidgetItem(str(idx + 1)))
                
                # 设置点名称
                self.point_table.setItem(row, 1, QTableWidgetItem(point_name))
                
                # ✅ 第 2、3、4 列显示世界坐标系下的坐标
                world_x = point_data['x']
                world_y = point_data['y']
                world_angle = point_data.get('angle', 0.0)
                
                self.point_table.setItem(row, 2, QTableWidgetItem(f"{world_x:.2f}"))
                self.point_table.setItem(row, 3, QTableWidgetItem(f"{world_y:.2f}"))
                self.point_table.setItem(row, 4, QTableWidgetItem(f"{world_angle:.1f}"))
                
                # ✅ 计算并显示转换后的目标坐标
                if target_system and transformer:
                    try:
                        target_sys = transformer.get_coordinate_system(target_system)
                        if target_sys:
                            tx, ty = target_sys.point_from_world(world_x, world_y)
                            t_angle = (world_angle - target_sys.x_angle) % 360
                            if t_angle > 180:
                                t_angle -= 360
                            
                            self.point_table.setItem(row, 5, QTableWidgetItem(f"{tx:.2f}"))
                            self.point_table.setItem(row, 6, QTableWidgetItem(f"{ty:.2f}"))
                            self.point_table.setItem(row, 7, QTableWidgetItem(f"{t_angle:.2f}"))
                        else:
                            self.point_table.setItem(row, 5, QTableWidgetItem("?"))
                            self.point_table.setItem(row, 6, QTableWidgetItem("?"))
                            self.point_table.setItem(row, 7, QTableWidgetItem("?"))
                    except Exception as e:
                        print(f"Error transforming point {point_name}: {e}")
                        self.point_table.setItem(row, 5, QTableWidgetItem("错误"))
                        self.point_table.setItem(row, 6, QTableWidgetItem("错误"))
                        self.point_table.setItem(row, 7, QTableWidgetItem("错误"))
                else:
                    self.point_table.setItem(row, 5, QTableWidgetItem("-"))
                    self.point_table.setItem(row, 6, QTableWidgetItem("-"))
                    self.point_table.setItem(row, 7, QTableWidgetItem("-"))
     
                # 设置单元格样式和编辑属性
                for col in range(8):
                    item = self.point_table.item(row, col)
                    if item:
                        item.setTextAlignment(Qt.AlignCenter)
                        
                        if col in [0, 1]:
                            item.setBackground(QColor(240, 240, 240))
                        elif col in [2, 3, 4]:
                            item.setBackground(QColor(220, 230, 241))
                        else:
                            item.setBackground(QColor(235, 245, 235))
                        
                        if col in [1, 2, 3, 4]:
                            item.setFlags(item.flags() | Qt.ItemIsEditable)
                        else:
                            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            
            print(f"✅ 表格已刷新")
            
        except Exception as e:
            print(f"Error in update_points_display: {e}")
        finally:
            # ✅ 关键修复：确保在所有操作完成后才恢复信号
            self._block_cell_change_signal = False
            print(f"   信号阻塞已解除")
    
    def update_transformed_point(self, row, target_x, target_y, target_angle):
        """
        更新转换后的目标坐标
        
        参数:
        row (int): 行号
        target_x (float): 目标X坐标
        target_y (float): 目标Y坐标
        target_angle (float): 目标角度
        """
        if 0 <= row < self.point_table.rowCount():
            # 更新目标坐标系列
            self.point_table.setItem(row, 5, QTableWidgetItem(f"{target_x:.2f}"))
            self.point_table.setItem(row, 6, QTableWidgetItem(f"{target_y:.2f}"))
            self.point_table.setItem(row, 7, QTableWidgetItem(f"{target_angle:.2f}"))
            
            # 设置文本对齐和背景色
            for col in [5, 6, 7]:
                item = self.point_table.item(row, col)
                if item:
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setBackground(QColor(245, 245, 245))
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # 确保不可编辑
    
    def show_add_point_dialog(self):
        """
        显示添加点对话框，让用户输入世界坐标系下的坐标
        """
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, \
            QDoubleSpinBox, QPushButton, QMessageBox
        from PyQt5.QtCore import Qt
        
        # ✅ 创建对话框
        dialog = QDialog()
        dialog.setWindowTitle("添加点")
        dialog.setModal(True)
        
        layout = QVBoxLayout(dialog)
        
        # 说明文本
        info_label = QLabel("请输入点在世界坐标系下的坐标：")
        info_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(info_label)
        
        # X 坐标
        x_layout = QHBoxLayout()
        x_layout.addWidget(QLabel("X 坐标:"))
        x_spin = QDoubleSpinBox()
        x_spin.setRange(-1000, 1000)
        x_spin.setDecimals(3)
        x_spin.setValue(0.0)
        x_layout.addWidget(x_spin)
        layout.addLayout(x_layout)
        
        # Y 坐标
        y_layout = QHBoxLayout()
        y_layout.addWidget(QLabel("Y 坐标:"))
        y_spin = QDoubleSpinBox()
        y_spin.setRange(-1000, 1000)
        y_spin.setDecimals(3)
        y_spin.setValue(0.0)
        y_layout.addWidget(y_spin)
        layout.addLayout(y_layout)
        
        # 角度
        angle_layout = QHBoxLayout()
        angle_layout.addWidget(QLabel("角度 (°):"))
        angle_spin = QDoubleSpinBox()
        angle_spin.setRange(-360, 360)
        angle_spin.setDecimals(1)
        angle_spin.setValue(0.0)
        angle_layout.addWidget(angle_spin)
        layout.addLayout(angle_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        # ✅ 只连接简单的接受/拒绝，不发射信号
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        
        # ✅ 显示对话框并等待关闭
        result = dialog.exec_()
        
        # ✅ 关键修复：在对话框完全关闭后，再手动调用主程序的处理方法
        if result == QDialog.Accepted:
            try:
                # 获取输入值
                x = x_spin.value()
                y = y_spin.value()
                angle = angle_spin.value()
                
                # ✅ 直接调用主窗口的处理方法，而不是发射信号
                parent = self.parent()
                while parent is not None:
                    if hasattr(parent, 'on_add_point_from_dialog'):
                        parent.on_add_point_from_dialog(float(x), float(y), float(angle))
                        break
                    parent = parent.parent()
                    
            except Exception as e:
                print(f"Error in show_add_point_dialog: {e}")
                import traceback
                traceback.print_exc()
    
    def _handle_ok_click(self, dialog, x_spin, y_spin, angle_spin):
        """
        处理确定按钮点击，确保对话框先关闭
        
        参数:
        dialog (QDialog): 对话框实例
        x_spin (QDoubleSpinBox): X 坐标输入框
        y_spin (QDoubleSpinBox): Y 坐标输入框
        angle_spin (QDoubleSpinBox): 角度输入框
        """
        # ✅ 第一步：立即关闭对话框
        dialog.accept()
        
        # ✅ 第二步：获取输入值
        x = x_spin.value()
        y = y_spin.value()
        angle = angle_spin.value()
        
        # ✅ 第三步：使用 QTimer.singleShot 延迟发射信号（100ms 后）
        # 这样确保对话框已经完全关闭后再处理耗时操作
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(
            100,  # 100 毫秒延迟
            lambda: self.add_point.emit(float(x), float(y), float(angle))
        )
    
    def _on_add_point_ok(self, dialog, x_spin, y_spin, angle_spin, accepted_value):
        """
        处理确定按钮点击，确保对话框关闭
        
        参数:
        dialog (QDialog): 对话框实例
        x_spin (QDoubleSpinBox): X 坐标输入框
        y_spin (QDoubleSpinBox): Y 坐标输入框
        angle_spin (QDoubleSpinBox): 角度输入框
        accepted_value (int): Accepted 枚举值
        """
        # ✅ 显式关闭对话框
        dialog.done(accepted_value)
        dialog.close()
        dialog.deleteLater()
    
    def _on_add_point_cancel(self, dialog, rejected_value):
        """
        处理取消按钮点击，确保对话框关闭
        
        参数:
        dialog (QDialog): 对话框实例
        rejected_value (int): Rejected 枚举值
        """
        dialog.done(rejected_value)
        dialog.close()
        dialog.deleteLater()

    def on_point_cell_changed(self, row, column):
        """
        处理点表格单元格变化事件
        
        参数:
        row (int): 行号
        column (int): 列号
        """
        # ✅ 关键修复：如果信号被阻塞，直接返回
        if self._block_cell_change_signal:
            return
        
        # ✅ 只处理可编辑的列（第 1、2、3、4 列）
        if column not in [1, 2, 3, 4]:
            return
        
        # ✅ 处理点名称列（第 1 列）的变化
        if column == 1:
            new_name = self.point_table.item(row, 1).text().strip()
            
            # ✅ 关键修复：直接从映射中获取旧名称
            old_name = self._row_to_point_name.get(row, '')
            
            print(f"🔍 重命名：row={row}, old_name={old_name}, new_name={new_name}")
            
            # 发送信号（传递旧名称和新名称）
            self.point_name_changed.emit(row, old_name, new_name)
        
        # ✅ 处理坐标列（第 2、3、4 列）的变化
        elif column in [2, 3, 4]:
            # ✅ 关键修复：直接从映射中获取正确的点名称
            point_name = self._row_to_point_name.get(row, '')
            
            # 如果映射中没有，尝试从表格第 1 列读取
            if not point_name:
                name_item = self.point_table.item(row, 1)
                if name_item:
                    point_name = name_item.text().strip()
            
            if not point_name:
                print(f"⚠️ 第{row}行点名称为空")
                return
            
            print(f"🔍 坐标更新：row={row}, point_name={point_name}")
            
            try:
                # 获取当前点的源坐标值
                x_item = self.point_table.item(row, 2)
                y_item = self.point_table.item(row, 3)
                a_item = self.point_table.item(row, 4)
                
                if x_item and y_item and a_item:
                    try:
                        x = float(x_item.text())
                        y = float(y_item.text())
                        a = float(a_item.text())
                        
                        # 获取源坐标系
                        source_system = self.source_system_combo.currentText()
                        
                        # ✅ 关键修复：不再立即发射信号，而是先检查数据是否真的改变
                        parent = self.parent()
                        while parent is not None:
                            if hasattr(parent, 'points'):
                                if point_name in parent.points:
                                    old_point_data = parent.points[point_name]
                                    old_x = old_point_data['x']
                                    old_y = old_point_data['y']
                                    old_a = old_point_data.get('angle', 0.0)
                                    
                                    print(f"   表格值：x={x:.4f}, y={y:.4f}, a={a:.4f}")
                                    print(f"   数据值：x={old_x:.4f}, y={old_y:.4f}, a={old_a:.4f}")
                                    
                                    # ✅ 只在数据真正改变时才发射信号
                                    if abs(x - old_x) > 0.001 or abs(y - old_y) > 0.001 or abs(a - old_a) > 0.1:
                                        print(f"   ✅ 数据已改变，发射更新信号")
                                        self.update_point.emit(point_name, x, y, a, source_system)
                                        
                                        # ✅ 计算并更新目标坐标
                                        target_system = self.target_system_combo.currentText()
                                        if source_system and target_system and source_system != target_system:
                                            transformer_parent = parent
                                            while transformer_parent is not None:
                                                if hasattr(transformer_parent, 'transformer'):
                                                    tx, ty, t_angle = transformer_parent.transformer.transform_point(
                                                        x, y, a, source_system, target_system)
                                                    
                                                    # ✅ 立即更新目标坐标
                                                    self.update_transformed_point(row, tx, ty, t_angle)
                                                    break
                                                transformer_parent = transformer_parent.parent()
                                    else:
                                        print(f"   ℹ️ 数据未改变，跳过更新")
                                break
                            parent = parent.parent()
                            
                    except ValueError as ve:
                        print(f"Invalid number format: {ve}")
                        
            except Exception as e:
                print(f"Error in on_point_cell_changed: {e}")
    
    def get_selected_point_rows(self):
        """
        获取选中的点行
        
        返回:
        list: 选中的行索引列表
        """
        return [index.row() for index in self.point_table.selectionModel().selectedRows()]
    
    def get_point_name_at_row(self, row):
        """
        获取指定行的点名称
        
        参数:
        row (int): 行索引
        
        返回:
        str: 点名称
        """
        # return self.point_table.item(row, 0).text()
        # return self.point_panel.get_point_name_at_row(row)  # 调用 point_panel 的方法
        item = self.point_table.item(row, 1)
        if item:
            return item.text()
        return ""

class ControlPanel(QWidget):
    """控制面板组件"""
    
    # 信号定义
    system_selected = pyqtSignal(str)
    coordinate_parameter_changed = pyqtSignal()
    robot_parameter_changed = pyqtSignal()
    add_coordinate_system = pyqtSignal()
    delete_coordinate_system = pyqtSignal()
    move_robot = pyqtSignal(float, float)
    rotate_robot = pyqtSignal(float)
    transform_point = pyqtSignal()
    add_point = pyqtSignal(float, float, float)  # 修改：x, y, angle（世界坐标系）
    edit_point = pyqtSignal(str)  # 参数为点名称
    remove_point = pyqtSignal()
    clear_points = pyqtSignal()
    batch_transform = pyqtSignal()
    import_points = pyqtSignal()
    export_points = pyqtSignal()
    update_point = pyqtSignal(str, float, float, float, str)  # 新增：点名称，x, y, 角度，坐标系
    
    
    def __init__(self, parent=None):
        """
        初始化控制面板
        
        参数:
        parent (QWidget, optional): 父组件
        """
        super().__init__(parent)
        
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        
        # 创建坐标系设置面板
        self.coordinate_panel = CoordinateSystemPanel()
        self.coordinate_panel.system_selected.connect(self.system_selected.emit)
        self.coordinate_panel.parameter_changed.connect(self.coordinate_parameter_changed.emit)
        self.coordinate_panel.add_system.connect(self.add_coordinate_system.emit)
        self.coordinate_panel.delete_system.connect(self.delete_coordinate_system.emit)
        
        # 创建机械臂设置面板
        self.robot_panel = RobotArmPanel()
        self.robot_panel.parameter_changed.connect(self.robot_parameter_changed.emit)
        self.robot_panel.move_robot.connect(self.move_robot.emit)
        self.robot_panel.rotate_robot.connect(self.rotate_robot.emit)
        
        # 创建坐标点转换面板
        self.point_panel = PointConversionPanel()
        self.point_panel.transform_point.connect(self.transform_point.emit)
        self.point_panel.add_point.connect(self.add_point.emit)
        self.point_panel.edit_point.connect(self.edit_point.emit)
        self.point_panel.remove_point.connect(self.remove_point.emit)
        self.point_panel.clear_points.connect(self.clear_points.emit)
        self.point_panel.batch_transform.connect(self.batch_transform.emit)
        self.point_panel.import_points.connect(self.import_points.emit)
        self.point_panel.export_points.connect(self.export_points.emit)
        self.point_panel.update_point.connect(self.update_point.emit)
        # 添加选项卡
        self.tab_widget.addTab(self.coordinate_panel, "坐标系设置")
        self.tab_widget.addTab(self.robot_panel, "机械臂设置")
        self.tab_widget.addTab(self.point_panel, "坐标点转换")
        
        # 添加选项卡到布局
        layout.addWidget(self.tab_widget)
    
    def update_system_list(self, system_names, current_system=None):
        """
        更新坐标系列表
        
        参数:
        system_names (list): 坐标系名称列表
        current_system (str, optional): 当前选中的坐标系
        """
        self.coordinate_panel.update_system_list(system_names, current_system)
    
    def update_coordinate_parameters(self, params):
        """
        更新坐标系参数显示
        
        参数:
        params (dict): 坐标系参数
        """
        self.coordinate_panel.update_parameter_display(params)
    
    def update_robot_parameters(self, params):
        """
        更新机械臂参数显示
        
        参数:
        params (dict): 机械臂参数
        """
        self.robot_panel.update_parameter_display(params)
    
    def get_coordinate_parameters(self):
        """
        获取当前坐标系参数
        
        返回:
        dict: 当前坐标系参数
        """
        return self.coordinate_panel.get_parameters()
    
    def get_robot_parameters(self):
        """
        获取当前机械臂参数
        
        返回:
        dict: 当前机械臂参数
        """
        return self.robot_panel.get_parameters()
    
    def get_source_system(self):
        """
        获取源坐标系名称
        
        返回:
        str: 源坐标系名称
        """
        return self.coordinate_panel.get_source_system()
    
    def get_target_system(self):
        """
        获取目标坐标系名称
        
        返回:
        str: 目标坐标系名称
        """
        # return self.coordinate_panel.get_target_system()
        return self.point_panel.target_system_combo.currentText()
    
    def get_selected_system(self):
        """
        获取选中的坐标系名称
        
        返回:
        str: 选中的坐标系名称
        """
        return self.coordinate_panel.get_selected_system()
    
    def get_input_point(self):
        """
        获取输入点坐标
        
        返回:
        tuple: (x, y)
        """
        return self.point_panel.get_input_point()
    
    def set_input_point(self, x, y):
        """
        设置输入点坐标
        
        参数:
        x (float): X坐标
        y (float): Y坐标
        """
        self.point_panel.set_input_point(x, y)
    
    def set_result_text(self, text):
        """
        设置结果文本
        
        参数:
        text (str): 结果文本
        """
        self.point_panel.set_result_text(text)
    
    def update_point_table(self, points):
        """
        更新点表格
        
        参数:
        points (dict): 点字典
        """
        self.point_panel.update_point_table(points)
    
    def get_selected_point_rows(self):
        """
        获取选中的点行
        
        返回:
        list: 选中的行索引列表
        """
        return self.point_panel.get_selected_point_rows()
    
    def get_point_name_at_row(self, row):
        """
        获取指定行的点名称
        
        参数:
        row (int): 行索引
        
        返回:
        str: 点名称
        """
        return self.point_panel.get_point_name_at_row(row)
        # return self.point_table.item(row, 1).text()  # 从第 1 列获取点名称（序号是第 0 列）
    
    def update_view_info(self, zoom_level, view_range):
        """
        更新视图信息显示
        
        参数:
        zoom_level (float): 缩放级别
        view_range (tuple): 视图范围 (x_min, x_max, y_min, y_max)
        """
        # 这个方法用于更新视图信息，但当前版本的控制面板没有专门的视图信息显示区域
        # 这里只是保留接口，实际功能可以根据需要扩展
        pass