"""
工业机械臂运动模拟器主程序
整合所有模块，实现完整功能
"""

import sys
import os
font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'simhei.ttf')
if os.path.exists(font_path):
    size = os.path.getsize(font_path)
    print(f"✅ 字体文件存在：{font_path}")
    print(f"   文件大小：{size:,} 字节")
else:
    print(f"❌ 字体文件不存在！")
    print(f"   期望路径：{font_path}")
    print("\n请从 C:\\Windows\\Fonts\\simhei.ttf 复制到这个位置")
import math
import time
import json
import matplotlib
matplotlib.use('Qt5Agg')  # 使用Qt5后端
# ✅ 获取应用程序运行目录（兼容打包后的环境）
if getattr(sys, 'frozen', False):
    # 如果是打包后的 exe 运行
    application_path = os.path.dirname(sys.executable)
    # 对于 --onefile 模式，需要解压到临时目录
    if hasattr(sys, '_MEIPASS'):
        application_path = sys._MEIPASS
else:
    # 如果是 Python 脚本运行
    application_path = os.path.dirname(os.path.abspath(__file__))

# ✅ 设置工作目录
os.chdir(application_path)

# ✅ 更健壮的字体处理
from matplotlib import font_manager

try:
    # 尝试加载自定义字体
    font_path = os.path.join(application_path, 'fonts', 'simhei.ttf')
    
    if os.path.exists(font_path):
        # 注册字体
        font_manager.fontManager.addfont(font_path)
        print(f"✅ 成功加载字体：{font_path}")
        
        # 设置默认字体
        matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
    else:
        print(f"⚠️ 警告：未找到字体文件 {font_path}")
        print("   将使用系统默认字体")
        # 使用系统字体
        matplotlib.rcParams['font.sans-serif'] = [
            'Microsoft YaHei', 
            'SimHei', 
            'DejaVu Sans'
        ]
    
    matplotlib.rcParams['axes.unicode_minus'] = False
    
except Exception as e:
    print(f"⚠️ 字体加载失败：{e}")
    print("   将使用 Matplotlib 默认字体")
    matplotlib.rcParams['font.sans-serif'] = ['DejaVu Sans']
    matplotlib.rcParams['axes.unicode_minus'] = False

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, QMessageBox, 
                           QTextEdit, QVBoxLayout, QLabel, QScrollArea, QPushButton, 
                           QFrame, QSplitter, QMenu, QAction, QDialog, QLineEdit, 
                           QDoubleSpinBox, QComboBox, QTableWidget, QTableWidgetItem,
                           QHeaderView, QTabWidget, QGroupBox, QSlider, QFileDialog,
                           QInputDialog, QListWidget, QGridLayout, QFormLayout, QSpinBox,
                           QSizePolicy)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor, QTextCursor

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入模型模块
from models.coordinate_system import CoordinateSystem
from models.robot_arm import RobotArm

# 导入工具模块
from utils.coordinate_transformer import CoordinateTransformer
from utils.point_manager import PointManager

# 导入UI模块
from ui.zoomable_canvas import ZoomableCanvas
from ui.control_panel import ControlPanel


class RobotArmSimulator(QMainWindow):
    """机械臂模拟器主窗口类"""
    
    def __init__(self):
        """初始化机械臂模拟器"""
        super().__init__()
        
        # 设置窗口标题和大小
        self.setWindowTitle("工业机械臂运动模拟器")
        self.setGeometry(100, 100, 1200, 700) #100是
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # ✅ 新增：设置中央部件的大小策略
        central_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # ✅ 新增：设置主布局的边距为 0
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 创建可缩放画布
        self.canvas = ZoomableCanvas()
        self.canvas.point_clicked.connect(self.on_canvas_clicked)
        self.canvas.canvas_updated.connect(self.on_canvas_updated)
        
        # 重写has_object_at_position方法，检查点击位置是否有对象
        self.canvas.has_object_at_position = self.has_object_at_position
        
        # 注意：button_press_event 已经在 on_pick 方法中处理，这里不再重复连接
        
        # 创建控制面板
        self.control_panel = ControlPanel()
        
        # 连接控制面板信号
        self.control_panel.system_selected.connect(self.on_system_selected)
        self.control_panel.coordinate_parameter_changed.connect(self.on_coordinate_parameter_changed)
        self.control_panel.robot_parameter_changed.connect(self.on_robot_parameter_changed)
        self.control_panel.add_coordinate_system.connect(self.on_add_coordinate_system)
        self.control_panel.delete_coordinate_system.connect(self.on_delete_coordinate_system)
        self.control_panel.move_robot.connect(self.on_robot_move)
        self.control_panel.rotate_robot.connect(self.on_robot_rotate)
        self.control_panel.transform_point.connect(self.on_transform_point)
        self.control_panel.add_point.connect(self.on_add_point)
        self.control_panel.edit_point.connect(self.on_edit_point)
        self.control_panel.remove_point.connect(self.on_remove_point)
        self.control_panel.clear_points.connect(self.on_clear_points)
        self.control_panel.batch_transform.connect(self.on_batch_transform)
        self.control_panel.import_points.connect(self.on_import_points)
        self.control_panel.export_points.connect(self.on_export_points)

        # ✅ 新增：连接坐标系重命名信号
        self.control_panel.coordinate_panel.rename_system.connect(self.on_rename_coordinate_system)
        
        # 创建左侧容器，包含控制面板和场景管理
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        
        # 添加控制面板到左侧容器
        left_layout.addWidget(self.control_panel, 1)
        
        # 创建场景管理区域
        scene_management = QWidget()
        scene_layout = QVBoxLayout(scene_management)
        
        # 场景管理标题
        scene_title = QLabel("场景管理")
        scene_title.setStyleSheet("font-weight: bold; font-size: 12pt;")
        scene_layout.addWidget(scene_title)
        
        # 场景操作按钮
        scene_buttons = QWidget()
        scene_buttons_layout = QHBoxLayout(scene_buttons)
        
        self.add_scene_button = QPushButton("添加场景")
        self.add_scene_button.setStyleSheet("background-color: #2196F3; color: white;")
        self.add_scene_button.clicked.connect(self.on_add_scene)
        
        self.load_scene_button = QPushButton("加载场景")
        self.load_scene_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.load_scene_button.clicked.connect(self.on_load_scene)
        
        self.refresh_scenes_button = QPushButton("刷新列表")
        self.refresh_scenes_button.setStyleSheet("background-color: #FF9800; color: white;")
        self.refresh_scenes_button.clicked.connect(self.on_refresh_scenes)
        
        scene_buttons_layout.addWidget(self.add_scene_button)
        scene_buttons_layout.addWidget(self.load_scene_button)
        scene_buttons_layout.addWidget(self.refresh_scenes_button)
        scene_layout.addWidget(scene_buttons)
        
        # 场景列表
        self.scene_list_label = QLabel("已保存的场景：")
        scene_layout.addWidget(self.scene_list_label)
        
        self.scene_list = QTextEdit()
        self.scene_list.setReadOnly(True)
        self.scene_list.setMaximumHeight(100)
        # 设置基础样式
        self.scene_list.setStyleSheet("""
            background-color: #f8f9fa; 
            font-size: 10pt;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 4px;
            color: #000000;
        """)
        # ✅ 设置上下文菜单策略
        self.scene_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.scene_list.customContextMenuRequested.connect(self.on_scene_context_menu)
               
        # ✅ 启用鼠标追踪（必须在绑定事件之前）
        self.scene_list.viewport().setMouseTracking(True)
        self.scene_list.setMouseTracking(True)
        
        # ✅ 正确绑定鼠标事件
        self.scene_list.viewport().enterEvent = lambda event: self.on_scene_list_enter()
        self.scene_list.viewport().leaveEvent = lambda event: self.on_scene_list_leave()
        self.scene_list.viewport().mouseMoveEvent = lambda event: self.on_scene_list_mouse_move(event)
        self.scene_list.viewport().mousePressEvent = lambda event: self.on_scene_list_mouse_press(event)
        
        # ✅ 初始化悬浮状态
        self.hovered_scene = None
        self.last_hovered_row = -1

         # ✅ 将 scene_list 添加到布局
        scene_layout.addWidget(self.scene_list) 
        
        # 添加场景管理到左侧容器
        left_layout.addWidget(scene_management)
        
        # 创建右侧容器，只包含画布
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)

        
        right_layout.addWidget(self.canvas, 1)  # 画布占满右侧容器

        # 设置右侧容器的大小策略，使其尽可能扩展
        right_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


        # 设置布局的边距为0，避免出现空白边框
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        # 创建QSplitter用于左右滑动
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(left_container)
        self.splitter.addWidget(right_container)
        
        # 设置初始分割比例
        self.splitter.setSizes([400, 1000])
        
        # 添加分割器到主布局
        main_layout.addWidget(self.splitter, 1)
        
        # 创建底部容器，包含保存和取消按钮
        bottom_container = QWidget()
        bottom_container.setMaximumHeight(60)
        bottom_layout = QHBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(10, 5, 10, 5)
        
        # 创建保存和取消按钮
        self.save_button = QPushButton("保存配置")
        self.save_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px 16px;")
        self.save_button.clicked.connect(self.on_save_scene)
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 8px 16px;")
        self.cancel_button.clicked.connect(self.on_cancel_changes)
        
        # 添加按钮到底部布局
        bottom_layout.addWidget(self.save_button)
        bottom_layout.addWidget(self.cancel_button)
        bottom_layout.addStretch(1)  # 右侧留白，确保按钮在左下角
        
        # 将底部容器添加到主布局
        main_layout.addWidget(bottom_container)
        main_layout.setAlignment(bottom_container, Qt.AlignBottom)
        
        # 创建日志面板（必须在其他初始化之前创建）
        self.create_log_panel()
        
        # 初始化数据模型
        self.init_models()
        
        # 从本地存储加载数据（必须在create_log_panel之后调用）
        self.load_data()
        
        # 初始化UI
        self.init_ui()
        
        # 初始化矩形选择器
        self.rect_selector = None
        
        # 初始化拖拽状态
        self.is_dragging = False
        self.drag_item = None
        self.drag_start_pos = (0, 0)
        self.drag_motion_id = None
        self.drag_release_id = None
        # 拖拽物体时节流全量重绘，避免一帧内多次 update_visualization 导致抖动
        self._drag_viz_min_interval = 1.0 / 55.0
        self._last_drag_viz_time = 0.0
        
        # 连接画布点击事件
        self.canvas.canvas.mpl_connect('pick_event', self.on_pick)
        
        # 更新可视化
        self.update_visualization()
        
        # 更新视图信息
        self.update_view_info()
        
        # 标记是否有未保存的更改
        self.has_unsaved_changes = False
        
        # 连接所有可能导致更改的信号
        self.connect_change_signals()
        
        # 初始化机械臂字典
        self.robot_arms = {}
        self.robot_arm = RobotArm(0, 0, 0, 3.0, 'gray')
        self.robot_arms["机械臂1"] = self.robot_arm

        # ✅ 初始化场景状态变量
        self.current_scene = "default"
        self.loaded_scene = None
        self.has_unsaved_changes = False
        
        # ✅ 设置初始窗口标题
        self.setWindowTitle(f"工业机械臂运动模拟器 - {self.current_scene}")
    def init_models(self):
        """初始化数据模型"""
        # 创建坐标转换器
        self.transformer = CoordinateTransformer()
        
        # 创建点管理器
        self.point_manager = PointManager()
        
        # 创建世界坐标系（在视觉领域也叫机械坐标系）
        self.world_system = CoordinateSystem("世界坐标系", 0, 0, 0, 90, 1, 1, 'black')
        self.transformer.add_coordinate_system(self.world_system)
        
        # 注意：根据需求，世界坐标系在视觉领域也叫机械坐标系，两者为一个概念
        # 因此不再创建单独的机械坐标系，避免重复
        
        # 创建默认图像坐标系
        self.image_system = CoordinateSystem("图像坐标系", 2, 2, 30, 120, 1, 1, 'blue')
        self.transformer.add_coordinate_system(self.image_system)
        
        # 创建机械臂
        self.robot_arm = RobotArm(0, 0, 45, 2, 'gray') #1是默认长度
        
        # 创建点列表
        self.points = {}
        
        # 设置机械臂在世界坐标系（机械坐标系）中的位置
        self.robot_arm.set_base_position(0, 0)
        
        # 设置默认角度范围为0~360度
        self.robot_arm.set_angle_range('0-360')
        
        # 注意：load_data() 现在在 create_log_panel() 之后调用
    
    def init_ui(self):
      # 连接坐标转换面板的信号
        if hasattr(self.control_panel, 'point_panel'):
            self.control_panel.point_panel.transform_point.connect(self.on_transform_point)
            self.control_panel.point_panel.update_point.connect(self.on_update_point_from_table)
        """初始化 UI"""
        # 更新坐标系列表
        self.update_system_list()
        
        # 确保坐标转换面板的坐标系下拉框也被更新
        system_names = self.transformer.get_system_names()
        if hasattr(self.control_panel, 'point_panel'):
            self.control_panel.point_panel.update_system_list(system_names)
        
        # 更新机械臂参数显示
        self.update_robot_parameter_display()
    
    def create_log_panel(self):
        """创建右下角的日志面板（默认隐藏）"""
        # 创建日志面板窗口
        self.log_window = QWidget(self)
        self.log_window.setWindowTitle("运行日志")
        self.log_window.setGeometry(1000, 700, 350, 150)
        self.log_window.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        
        # 创建布局
        layout = QVBoxLayout(self.log_window)
        
        # 创建标题
        title_label = QLabel("运行日志/报错信息")
        title_label.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(title_label)
        
        # 创建文本编辑框
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("background-color: #f5f5f5; font-family: Consolas; font-size: 10pt;")
        layout.addWidget(self.log_text)
        
        # 默认隐藏日志窗口，用户可以通过菜单或按钮显示
        # self.log_window.hide()
    
    def add_log(self, message, level="info"):
        """
        添加日志到日志面板
        
        参数:
        message (str): 日志消息
        level (str): 日志级别 ("info", "warning", "error")
        """
        from datetime import datetime
        
        # 获取当前时间
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        
        # 格式化日志消息
        log_message = f"[{time_str}] [{level.upper()}] {message}\n"
        
        # 添加到文本编辑框
        self.log_text.append(log_message)
        
        # 自动滚动到底部
        self.log_text.moveCursor(QTextCursor.End)
    
    def save_data(self, scene_name="default"):
        """
        保存数据到本地存储
        
        参数:
        scene_name (str): 场景名称，默认为"default"
        """
        import json
        import os
        from datetime import datetime
        try:
            # 创建数据字典
            data = {
                'scene_name': scene_name,
                'timestamp': datetime.now().isoformat(),
                'points': self.points,
                'robot_arm': {
                    'base_x': self.robot_arm.base_x,
                    'base_y': self.robot_arm.base_y,
                    'angle': self.robot_arm.angle,
                    'radius': self.robot_arm.radius,
                    'color': self.robot_arm.color,
                    'angle_range': self.robot_arm.angle_range,
                },
                'coordinate_systems': {}
            }
            
            # 保存所有坐标系
            for name, system in self.transformer.get_all_coordinate_systems().items():
                if name != "世界坐标系":  # 不保存世界坐标系，使用默认值
                    data['coordinate_systems'][name] = {
                        'origin_x': system.origin_x,
                        'origin_y': system.origin_y,
                        'x_angle': system.x_angle,
                        'y_angle': system.y_angle,
                        'x_scale': system.x_scale,
                        'y_scale': system.y_scale,
                        'color': system.color
                    }
            
            # 保存到文件
            save_dir = os.path.join(os.path.expanduser("~"), ".robot_arm_simulator", "scenes")
            os.makedirs(save_dir, exist_ok=True)
            
            save_path = os.path.join(save_dir, f"{scene_name}.json")
            
            # 确保目录存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 如果是默认场景，也保存一份到默认位置
            if scene_name == "default":
                default_path = os.path.join(os.path.expanduser("~"), ".robot_arm_simulator", "data.json")
                os.makedirs(os.path.dirname(default_path), exist_ok=True)
                with open(default_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 更新场景列表显示
            self.update_scene_list()
            self.current_scene = scene_name
            self.has_unsaved_changes = False
            

            # ✅ 更新场景列表显示
            self.update_scene_list()
            
            # ✅ 更新窗口标题
            self.setWindowTitle(f"工业机械臂运动模拟器 - {scene_name}")
  
            print(f"场景 '{scene_name}' 保存成功到 {save_path}")
            return True
            
        except Exception as e:
            error_msg = f"场景保存失败: {str(e)}"
            print(error_msg)
            return False
    
    def on_add_scene(self):
        """
        添加新场景
        """
        from PyQt5.QtWidgets import QInputDialog, QMessageBox
        
        try:
                    # 检查是否有未保存的更改
            if self.has_unsaved_changes:
                reply = QMessageBox.question(
                    self,
                    "未保存的更改",
                    "当前场景有未保存的更改，是否先保存？",
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    self.save_data()
                elif reply == QMessageBox.Cancel:
                    return
        
            # 弹出输入对话框，让用户输入场景名称
            scene_name, ok = QInputDialog.getText(
                self, 
                "添加场景", 
                "请输入新场景名称:", 
                text=""
            )
            
            if ok and scene_name.strip():
                scene_name = scene_name.strip()
                
                # 检查场景是否已存在
                save_dir = os.path.join(os.path.expanduser("~"), ".robot_arm_simulator", "scenes")
                save_path = os.path.join(save_dir, f"{scene_name}.json")
                
                if os.path.exists(save_path):
                    reply = QMessageBox.question(
                        self,
                        "场景已存在",
                        f"场景 '{scene_name}' 已存在，是否覆盖？",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    
                    if reply != QMessageBox.Yes:
                        return
                
                # 保存当前配置到新场景
                if self.save_data(scene_name):

                    
                    # 清除现有的非世界坐标系
                    for name in list(self.transformer.get_all_coordinate_systems().keys()):
                        if name != "世界坐标系":
                            self.transformer.remove_coordinate_system(name)
                            print("清除图像坐标系成功")
                    
                    # 重置机械臂位置
                    self.robot_arm.set_base_position(3, 3)
                    self.robot_arm.angle = 45
                    print("重置机械臂位置成功")

                    # 清空点列表
                    self.points.clear()
                    self.point_manager.points.clear()
                    print("清空点列表成功")
                    
                    # 更新UI
                    self.update_system_list()
                    self.update_robot_parameter_display()
                    self.control_panel.update_point_table(self.points)
                    print("更新UI成功")
                    
                    # 更新可视化
                    self.update_visualization()
                    print("更新可视化成功")
                                                        
                    
                    # 更新当前场景名称
                    self.current_scene = scene_name
                    # ✅ 更新已加载场景名称（关键修复）
                    self.loaded_scene = scene_name
                    # ✅ 重置未保存更改标记
                    self.has_unsaved_changes = False

                    # ✅ 更新窗口标题，移除未保存标记
                    current_title = self.windowTitle()
                    if current_title.endswith(" *"):
                        self.setWindowTitle(current_title[:-2])
                    # ✅ 刷新场景列表显示
                    self.update_scene_list()


                    QMessageBox.information(self, "成功", f"场景 '{scene_name}' 创建成功！")
                     # ✅ 添加日志
                    self.add_log(f"创建新场景：{scene_name}", "info")
            
                else:
                    QMessageBox.warning(self, "失败", "场景创建失败，请检查日志获取详细信息。")
            elif ok:
                QMessageBox.warning(self, "输入错误", "场景名称不能为空！")

                
        except Exception as e:
            error_msg = f"添加场景失败: {str(e)}"
            print(error_msg)
            QMessageBox.warning(self, "错误", f"添加场景时发生错误: {str(e)}")
    
    def on_refresh_scenes(self):
        """
        刷新场景列表显示
        """
        
        try:
            # ✅ 强制清除缓存，重新读取文件系统
            save_dir = os.path.join(os.path.expanduser("~"), ".robot_arm_simulator", "scenes")
            
            # ✅ 验证场景目录是否存在
            if not os.path.exists(save_dir):
                self.scene_list.setHtml("暂无保存的场景")
                self.add_log("场景目录不存在", "warning")
                return
            
            # ✅ 获取最新的场景文件列表
            scene_files = []
            for file in os.listdir(save_dir):
                if file.endswith('.json'):
                    scene_name = os.path.splitext(file)[0]
                    scene_file = os.path.join(save_dir, file)
                    
                    # ✅ 检查文件是否存在且不为空
                    if os.path.exists(scene_file) and os.path.getsize(scene_file) > 0:
                        scene_files.append(scene_name)
                    else:
                        # ✅ 删除无效文件
                        try:
                            if os.path.exists(scene_file):
                                os.remove(scene_file)
                                self.add_log(f"删除无效场景文件：{file}", "info")
                        except Exception as e:
                            print(f"无法删除无效文件 {file}: {str(e)}")
            
            # ✅ 强制刷新场景列表
            self.update_scene_list()
            
            # ✅ 添加日志
            self.add_log(f"场景列表已刷新，共 {len(scene_files)} 个场景", "info")
            
            # ✅ 显示提示信息
            QMessageBox.information(self, "刷新成功", f"已刷新场景列表，共 {len(scene_files)} 个场景")
            
        except Exception as e:
            self.add_log(f"刷新场景列表失败：{str(e)}", "error")
            QMessageBox.warning(self, "错误", f"刷新场景列表失败：{str(e)}")
      
    
    def on_load_selected_scene(self):
        """加载场景 - 显示场景选择对话框"""
        try:
            # 获取所有保存的场景
            scene_dir = os.path.join(os.path.expanduser("~"), ".robot_arm_simulator", "scenes")
            
            # 检查场景目录是否存在
            if not os.path.exists(scene_dir):
                self.add_log("场景目录不存在", level="warning")
                QMessageBox.information(self, "提示", "暂无保存的场景！")
                return
            
            # 获取所有场景文件
            scene_files = [f for f in os.listdir(scene_dir) if f.endswith('.json')]
            
            if not scene_files:
                self.add_log("没有找到场景文件", level="warning")
                QMessageBox.information(self, "提示", "暂无保存的场景！")
                return
            
            # 提取场景名称（去除.json后缀）
            scene_names = [os.path.splitext(f)[0] for f in scene_files]
            
            # 创建场景选择对话框
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout, QLabel
            
            class SceneSelectionDialog(QDialog):
                def __init__(self, scenes, parent=None):
                    super().__init__(parent)
                    self.setWindowTitle("选择要加载的场景")
                    self.setGeometry(300, 300, 400, 300)
                    
                    layout = QVBoxLayout(self)
                    
                    # 添加说明标签
                    label = QLabel("请选择要加载的场景：")
                    layout.addWidget(label)
                    
                    # 创建场景列表
                    self.scene_list = QListWidget()
                    self.scene_list.addItems(scenes)
                    self.scene_list.setSelectionMode(QListWidget.SingleSelection)
                    if scenes:
                        self.scene_list.setCurrentRow(0)
                    layout.addWidget(self.scene_list)
                    
                    # 创建按钮布局
                    button_layout = QHBoxLayout()
                    
                    # 加载按钮
                    self.load_button = QPushButton("加载")
                    self.load_button.clicked.connect(self.accept)
                    button_layout.addWidget(self.load_button)
                    
                    # 取消按钮
                    self.cancel_button = QPushButton("取消")
                    self.cancel_button.clicked.connect(self.reject)
                    button_layout.addWidget(self.cancel_button)
                    
                    layout.addLayout(button_layout)
                
                def get_selected_scene(self):
                    """获取选中的场景名称"""
                    selected_items = self.scene_list.selectedItems()
                    if selected_items:
                        return selected_items[0].text()
                    return None
            
            # 显示对话框
            dialog = SceneSelectionDialog(scene_names, self)
            if dialog.exec_():
                selected_scene = dialog.get_selected_scene()
                
                if selected_scene:
                    self.add_log(f"用户选择加载场景: {selected_scene}")
                    
                     # ✅ 调用 load_data 方法加载场景（内部会设置状态）
                    success = self.load_data(selected_scene)
                    
                    if success:
                        # ✅ 更新窗口标题
                        self.setWindowTitle(f"工业机械臂运动模拟器 - {selected_scene}")
                        # ✅ 刷新场景列表
                        self.update_scene_list()
                        self.add_log(f"场景 '{selected_scene}' 加载成功")
                        QMessageBox.information(self, "成功", f"场景 '{selected_scene}' 加载成功！")
                    else:
                        self.add_log(f"场景 '{selected_scene}' 加载失败", level="error")
                        QMessageBox.warning(self, "错误", f"加载场景 '{selected_scene}' 失败！")
                        
        except Exception as e:
            self.add_log(f"加载场景时发生错误: {str(e)}", level="error")
            QMessageBox.warning(self, "错误", f"加载场景时发生错误: {str(e)}")
    
    def on_scene_context_menu(self, position):
        """场景列表右键菜单"""
        try:
             # ✅ 关键修复：使用 cursorForPosition 获取光标，然后选择当前行
            cursor = self.scene_list.cursorForPosition(position)
            
            # ✅ 选择当前行（BlockUnderCursor）
            cursor.select(cursor.BlockUnderCursor)
            selected_text = cursor.selectedText().strip()
            
            # ✅ 调试输出
            print(f"右键菜单 - 原始文本：{selected_text}")
            
            # ✅ 如果没有选中任何文本，则不显示菜单
            if not selected_text:
                return
            
            # ✅ 解析场景名称
            scene_name = self._parse_scene_name_from_text(selected_text)
            
            # ✅ 调试输出
            print(f"右键菜单 - 解析后名称：{scene_name}")

            # ✅ 如果无法解析场景名称，不显示菜单
            if not scene_name:
                self.add_log("无法识别场景名称", "warning")
                return
            
            # ✅ 创建右键菜单（只保留删除功能）
            menu = QMenu()
            
            # ✅ 只添加删除菜单项
            delete_action = QAction("删除场景", self)
            delete_action.triggered.connect(lambda: self.on_delete_scene_by_name(scene_name))
            menu.addAction(delete_action)

            # 显示菜单
            menu.exec_(self.scene_list.mapToGlobal(position))
            
        except Exception as e:
            self.add_log(f"显示场景右键菜单时发生错误：{str(e)}", level="error")
            import traceback
            traceback.print_exc()

    def _parse_scene_name_from_text(self, text):
        """
        从场景列表文本中解析场景名称
        """
        try:
            if not text:
                return None
            
            # ✅ 去除 HTML 标签
            import re
            text = re.sub(r'<[^>]+>', '', text)
            
            # ✅ 只取第一行（关键修复：避免多行文本）
            lines = text.split('\n')
            if lines:
                text = lines[0].strip()
            else:
                text = text.strip()
            
            # ✅ 如果文本中包含多个场景分隔符，只取第一个场景
            # 检查是否有"• "或"▶ "在文本中间（表示多行被合并了）
            if ' • ' in text or ' ▶ ' in text:
                # 取第一个分隔符之前的内容
                for sep in [' • ', ' ▶ ']:
                    if sep in text:
                        text = text.split(sep)[0].strip()
                        break
            
            # ✅ 去除前后缀
            if text.startswith('▶ ') or text.startswith('• '):
                text = text[2:]
            
            # ✅ 去除状态后缀（如" (当前显示)"）
            if ' (' in text:
                text = text.split(' (')[0]
            
            # ✅ 再次清理可能的分隔符
            if ' • ' in text or ' ▶ ' in text:
                for sep in [' • ', ' ▶ ']:
                    if sep in text:
                        text = text.split(sep)[0].strip()
                        break
            
            # ✅ 验证场景名称有效性
            if text and len(text) > 0 and len(text) < 50:
                print(f"✓ 解析成功：{text}")
                return text
            else:
                print(f"✗ 解析失败：{text}")
                return None
                
        except Exception as e:
            print(f"解析场景名称失败：{str(e)}")
            import traceback
            traceback.print_exc()
            return None
        
    def on_load_scene_by_name(self, scene_name):
        """通过名称载入场景"""
        
        try:
            # ✅ 解析场景名称
            scene_name = self._parse_scene_name_from_text(scene_name)
            
            if not scene_name:
                QMessageBox.warning(self, "错误", "无法识别场景名称！")
                return
            
            # ✅ 检查是否有未保存的更改
            if self.has_unsaved_changes:
                reply = QMessageBox.question(
                    self,
                    "未保存的更改",
                    "当前场景有未保存的更改，是否先保存？",
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    self.save_data()
                elif reply == QMessageBox.Cancel:
                    return
            
            # ✅ 载入场景
            if self.load_data(scene_name):

                # ✅ 更新窗口标题
                self.setWindowTitle(f"工业机械臂运动模拟器 - {scene_name}")
                # ✅ 刷新场景列表（确保状态标识正确显示）
                self.update_scene_list()
                # ✅ 添加日志
                self.add_log(f"场景 '{scene_name}' 载入成功", "info")
                # ✅ 显示成功提示
                QMessageBox.information(self, "成功", f"场景 '{scene_name}' 载入成功！")
            else:
                self.add_log(f"场景 '{scene_name}' 载入失败", "error")
                QMessageBox.warning(self, "错误", f"载入场景失败：{scene_name}")

        except Exception as e:
            self.add_log(f"载入场景 '{scene_name}' 时发生错误：{str(e)}", "error")
            QMessageBox.warning(self, "错误", f"载入场景失败：{str(e)}")

    def on_delete_scene_by_name(self, scene_name):
        """通过名称删除场景"""
        try:
            # ✅ 解析场景名称（确保没有多余字符）
            scene_name = self._parse_scene_name_from_text(scene_name)

            # ✅ 调试输出（可选）
            print(f"删除场景 - 解析后名称：{scene_name}")
            
            if not scene_name:
                QMessageBox.warning(self, "错误", "无法识别场景名称！")
                return
            
            # ✅ 确认删除
            reply = QMessageBox.question(
                self, 
                "确认删除", 
                f"确定要删除场景 '{scene_name}' 吗？\n此操作不可恢复！",
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # ✅ 删除场景文件
                scene_dir = os.path.expanduser("~/.robot_arm_simulator/scenes")
                scene_file = os.path.join(scene_dir, f"{scene_name}.json")
                 
                print(f"删除场景文件：{scene_file}")  # ✅ 调试输出

                if os.path.exists(scene_file):
                    os.remove(scene_file)
                    self.add_log(f"场景 '{scene_name}' 删除成功", "info")
                    
                    # ✅ 如果删除的是当前选中的场景，清除当前场景
                    if hasattr(self, 'current_scene') and self.current_scene == scene_name:
                        self.current_scene = None
                    
                    # ✅ 如果删除的是当前载入的场景，清除载入状态
                    if hasattr(self, 'loaded_scene') and self.loaded_scene == scene_name:
                        self.loaded_scene = None
                    
                    # ✅ 立即刷新场景列表
                    self.update_scene_list()
                    
                    # ✅ 显示成功消息（只提示一次）
                    QMessageBox.information(self, "成功", f"场景 '{scene_name}' 已成功删除！")
                else:
                    self.add_log(f"场景文件 '{scene_file}' 不存在", level="warning")
                    QMessageBox.warning(self, "错误", "场景文件不存在")
                
        except Exception as e:
            self.add_log(f"删除场景 '{scene_name}' 时发生错误: {str(e)}", level="error")
            QMessageBox.warning(self, "错误", f"删除场景失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def on_scene_list_enter(self):
        """鼠标进入场景列表时的处理"""
        self.scene_list.setStyleSheet("""
            background-color: #e3f2fd; 
            font-size: 10pt;
            border: 1px solid #2196F3;
            border-radius: 4px;
            padding: 4px;
            color: #0d47a1;
        """)
    
    def on_scene_list_leave(self):
        """鼠标离开场景列表时的处理"""
        self.scene_list.setStyleSheet("""
            background-color: #f8f9fa; 
            font-size: 10pt;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 4px;
            color: #000000;
        """)
        
        # 重置悬浮状态
        if self.hovered_scene:
            self.hovered_scene = None
            self.update_scene_list()
    
    def on_scene_list_mouse_move(self, event):
        """鼠标在场景列表上移动时的处理"""
        try:
            # 获取鼠标位置对应的文本行
            
            cursor = self.scene_list.cursorForPosition(event.pos())
            block = cursor.block()
            line_text = block.text().strip()
            
            # ✅ 解析场景名称
            scene_name = self._parse_scene_name_from_text(line_text)
            
            # ✅ 如果悬浮的场景改变了，更新显示
            if scene_name and scene_name != self.hovered_scene:
                self.hovered_scene = scene_name
                self.update_scene_list()
            elif not scene_name and self.hovered_scene:
                # ✅ 鼠标不在场景行上，清除悬浮状态
                self.hovered_scene = None
                self.update_scene_list()
            
        except Exception as e:
            print(f"鼠标移动处理错误: {str(e)}")
    
    def on_scene_list_mouse_press(self, event):
        """鼠标在场景列表上点击时的处理"""
        try:
            # ✅ 只处理左键点击
            if event.button() != Qt.LeftButton:
                return
            
            # ✅ 关键修复：使用 cursorForPosition 获取光标，然后选择当前行
            cursor = self.scene_list.cursorForPosition(event.pos())
            
            # ✅ 选择当前行（BlockUnderCursor）
            cursor.select(cursor.BlockUnderCursor)
            line_text = cursor.selectedText().strip()
            
            # ✅ 解析场景名称
            scene_name = self._parse_scene_name_from_text(line_text)
            
            # ✅ 调试输出
            print(f"单击选中 - 原始文本：{line_text}")
            print(f"单击选中 - 解析后名称：{scene_name}")
            
            if not scene_name:
                return
            
            # ✅ 检查是否有未保存的更改
            if self.has_unsaved_changes:
                reply = QMessageBox.question(
                    self,
                    "未保存的更改",
                    "当前场景有未保存的更改，是否先保存？",
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    self.save_data()
                elif reply == QMessageBox.Cancel:
                    return
            
            # ✅ 设置当前选中的场景
            self.current_scene = scene_name
            self.add_log(f"选中场景：{scene_name}", "info")
            
            # ✅ 刷新场景列表显示选中状态
            self.update_scene_list()

            
        except Exception as e:
            print(f"鼠标点击处理错误：{str(e)}")
            import traceback
            traceback.print_exc()
    
    def update_scene_list(self):
        """
        更新场景列表显示
        """
        try:
            # 获取场景目录
            save_dir = os.path.join(os.path.expanduser("~"), ".robot_arm_simulator", "scenes")
            os.makedirs(save_dir, exist_ok=True)
            
            # 获取所有场景文件，过滤掉空文件
            scene_files = []
            for file in os.listdir(save_dir):
                if file.endswith('.json'):
                    scene_name = os.path.splitext(file)[0]
                    scene_file = os.path.join(save_dir, file)
                    
                    if os.path.exists(scene_file) and os.path.getsize(scene_file) > 0:
                        scene_files.append(scene_name)
                    else:
                        try:
                            if os.path.exists(scene_file):
                                os.remove(scene_file)
                        except:
                            pass
                
            # 按名称排序
            scene_files.sort()
            
             # ✅ 同步 current_scene 和 loaded_scene
            if hasattr(self, 'loaded_scene') and self.loaded_scene:
                self.current_scene = self.loaded_scene
            elif not hasattr(self, 'current_scene') or not self.current_scene:
                self.current_scene = "default"

             # ✅ 关键修复：使用<div>包裹每行，确保 BlockUnderCursor 能正确识别
            if scene_files:
                scene_text = ""
                for scene in scene_files:
                    is_loaded = hasattr(self, 'loaded_scene') and scene == self.loaded_scene
                    is_selected = hasattr(self, 'current_scene') and scene == self.current_scene
                    
                    # 构建场景行文本
                    if is_loaded:
                        prefix = "▶ "
                        suffix = " (当前显示)"
                        color = "#607D8B"
                        weight = "bold"
                    elif is_selected:
                        prefix = "▶ "
                        suffix = " (当前选中)"
                        color = "#1976D2"
                        weight = "bold"
                    else:
                        prefix = "• "
                        suffix = ""
                        color = "#212121"
                        weight = "normal"
                    
                    # ✅ 每行用独立的 div 包裹
                    scene_text += f"<div style='color: {color}; font-weight: {weight}; line-height: 1.8;'>{prefix}{scene}{suffix}</div>"
                
            else:
                scene_text = "<div style='color: gray;'>暂无保存的场景</div>"
            
            # 设置为HTML格式显示
            self.scene_list.setHtml(scene_text)
            
        except Exception as e:
            print(f"更新场景列表失败: {str(e)}")
            self.add_log(f"更新场景列表失败：{str(e)}", "error")
            self.scene_list.setHtml("<div style='color: red;'>获取场景列表失败</div>")
    
    def load_data(self, scene_name="default"):
        """
        从本地存储加载数据
        
        参数:
        scene_name (str): 场景名称，默认为"default"
        """
        import json
        import os
        
        try:
            # 尝试从场景目录加载
            save_dir = os.path.join(os.path.expanduser("~"), ".robot_arm_simulator", "scenes")
            save_path = os.path.join(save_dir, f"{scene_name}.json")
            
            # 如果场景文件不存在，尝试从默认位置加载
            if not os.path.exists(save_path):
                save_path = os.path.join(os.path.expanduser("~"), ".robot_arm_simulator", "data.json")
            
            if not os.path.exists(save_path):
                self.add_log(f"未找到场景文件 '{scene_name}'", "info")
                return False
            
            with open(save_path, 'r', encoding='utf-8') as f:
                data = json.load(f)


            # ✅ 添加容错处理：检查机械臂数据格式
            if 'robot_arms' in data:
                for arm_name, arm_data in data['robot_arms'].items():
                    # 创建新的机械臂对象
                    arm = RobotArm(
                        name=arm_name,
                        base_x=arm_data.get('base_x', 0),
                        base_y=arm_data.get('base_y', 0),
                        angle=arm_data.get('angle', 45),
                        radius=arm_data.get('radius', 2),  # ✅ 使用 radius
                        color=arm_data.get('color', 'gray')
                    )
                    
                    # ✅ 兼容旧版本：如果存在 length 属性，将其赋值给 radius
                    if 'length' in arm_data:
                        arm.radius = arm_data['length']
                    
                    # 添加到字典
                    self.robot_arms[arm_name] = arm
            
            # 加载点数据
            if 'points' in data:
                self.points = data['points']
                self.point_manager.points = self.points
                self.add_log(f"加载了 {len(self.points)} 个点", "info")
            
            # 加载机械臂数据
            if 'robot_arm' in data:
                arm_data = data['robot_arm']
                 # 确保 robot_arm 是字典类型
                if isinstance(arm_data, dict):
                    rng = arm_data.get('angle_range', '0-360')
                    ui_range_map = {
                        '0-360': '0~360度',
                        '-360-360': '-360~360度',
                        '-180-180': '-180~180度',
                    }
                    if rng not in ui_range_map:
                        rng = '0-360'
                    if rng in ui_range_map:
                        self.control_panel.robot_panel.angle_range_combo.blockSignals(True)
                        try:
                            self.control_panel.robot_panel.angle_range_combo.setCurrentText(ui_range_map[rng])
                        finally:
                            self.control_panel.robot_panel.angle_range_combo.blockSignals(False)
                        self.control_panel.robot_panel._set_angle_spin_and_slider_range(ui_range_map[rng])
                    self.robot_arm.set_angle_range(rng)
                    self.robot_arm.update_parameters(
                        base_x=arm_data.get('base_x', 0),
                        base_y=arm_data.get('base_y', 0),
                        angle=arm_data.get('angle', 45),
                        radius=arm_data.get('radius', arm_data.get('length', 2)),
                        color=arm_data.get('color', 'red'),
                    )
                    self.add_log("加载了机械臂数据", "info")
                else:
                # 如果不是字典，尝试转换或提示用户
                    self.add_log(f"机械臂数据格式错误: {type(arm_data)}", "error")
                    return False
                
            # 加载坐标系数据
            if 'coordinate_systems' in data:
                # 清除现有的非世界坐标系
                for name in list(self.transformer.get_all_coordinate_systems().keys()):
                    if name != "世界坐标系":
                        self.transformer.remove_coordinate_system(name)
                
                # 添加新的坐标系
                for name, system_data in data['coordinate_systems'].items():
                    system = CoordinateSystem(
                        name,
                        system_data['origin_x'],
                        system_data['origin_y'],
                        system_data['x_angle'],
                        system_data['y_angle'],
                        system_data['x_scale'],
                        system_data['y_scale'],
                        system_data['color']
                    )
                    self.transformer.add_coordinate_system(system)
                
                self.add_log(f"加载了 {len(data['coordinate_systems'])} 个坐标系", "info")
            
            
         
            # ✅ 先更新状态变量（在更新 UI 之前）
            scene_display_name = data.get('scene_name', scene_name)
            self.loaded_scene = scene_display_name
            self.current_scene = scene_display_name
            self.has_unsaved_changes = False
            
            # ✅ 再更新 UI 和可视化
            self.update_system_list()
            self.update_robot_parameter_display()
            self.control_panel.update_point_table(self.points)
            
            # ✅ 更新可视化（刷新画布）
            self.update_visualization()
            
                # ✅ 修复：正确调用 canvas 刷新方法
            try:
                # 方法 1：调用 ZoomableCanvas 的 update_view 方法
                self.canvas.update_view()
            except Exception as e:
                try:
                    # 方法 2：调用 matplotlib 原生 canvas 的 draw 方法
                    self.canvas.canvas.draw()
                except Exception as e2:
                    # 方法 3：调用 Qt 的 update 方法
                    self.canvas.update()
                    self.canvas.repaint()
            # ✅ 更新场景列表显示（确保状态标识正确）
            self.update_scene_list()
            
            

            # ✅ 更新窗口标题
            self.setWindowTitle(f"工业机械臂运动模拟器 - {scene_display_name}")
            # ✅ 添加日志
            self.add_log(f"场景 '{scene_display_name}' 加载成功", "info")
            return True
            
        except Exception as e:
            self.add_log(f"场景加载失败：{str(e)}", "error")
            import traceback
            traceback.print_exc()
            return False
    
    def update_system_list(self):
        """更新坐标系列表"""
        # 获取所有坐标系名称
        system_names = self.transformer.get_system_names()
        
        # 更新控制面板中的坐标系列表
        self.control_panel.update_system_list(system_names)
        
        # 确保坐标转换面板的坐标系下拉框也被更新
        self.control_panel.point_panel.update_system_list(system_names)

        
    
    def on_system_selected(self, system_name):
        """
        当选择坐标系时的处理函数
        
        参数:
        system_name (str): 选中的坐标系名称
        """
        # 获取选中的坐标系
        system = self.transformer.get_coordinate_system(system_name)
        
        if system:
            # 更新控制面板中的参数显示
            self.control_panel.update_coordinate_parameters(system.get_parameters())
    
    def on_rename_coordinate_system(self, old_name):
        """重命名坐标系"""
        try:
            if old_name not in self.transformer.get_all_coordinate_systems():
                return
            
            # ✅ 创建编辑对话框
            dialog = QDialog(self)
            dialog.setWindowTitle(f"重命名坐标系 - {old_name}")
            dialog.setMinimumWidth(400)
            dialog.setModal(True)
            
            layout = QVBoxLayout(dialog)
            
            # 说明文本
            info_label = QLabel(f"请输入新的坐标系名称：")
            layout.addWidget(info_label)
            
            # 坐标系名称输入框
            name_layout = QHBoxLayout()
            name_layout.addWidget(QLabel("坐标系名称:"))
            name_edit = QLineEdit(old_name)
            name_layout.addWidget(name_edit)
            layout.addLayout(name_layout)
            
            # 按钮
            button_layout = QHBoxLayout()
            ok_btn = QPushButton("确定")
            cancel_btn = QPushButton("取消")
            
            button_layout.addWidget(ok_btn)
            button_layout.addWidget(cancel_btn)
            layout.addLayout(button_layout)
            
            # 连接信号
            ok_btn.clicked.connect(dialog.accept)
            cancel_btn.clicked.connect(dialog.reject)
            
            # 显示对话框
            if dialog.exec_() == QDialog.Accepted:
                new_name = name_edit.text().strip()
                
                if not new_name:
                    QMessageBox.warning(self, "警告", "坐标系名称不能为空")
                    return
                
                # 如果名称没有改变，直接返回
                if new_name == old_name:
                    return
                
                # 检查新名称是否已存在
                if new_name in self.transformer.get_all_coordinate_systems():
                    QMessageBox.warning(self, "警告", f"坐标系名称 '{new_name}' 已存在")
                    return
                
                # ✅ 获取坐标系对象
                system = self.transformer.get_coordinate_system(old_name)
                
                # ✅ 保存坐标系参数和颜色
                params = system.get_parameters()
                color = system.color
                
                # ✅ 删除旧坐标系
                self.transformer.remove_coordinate_system(old_name)
                
                # ✅ 创建新坐标系（保持原有参数）
                new_system = CoordinateSystem(
                    new_name,
                    params['origin_x'],
                    params['origin_y'],
                    params['x_angle'],
                    params['y_angle'],
                    params['x_scale'],
                    params['y_scale'],
                    color
                )
                self.transformer.add_coordinate_system(new_system)
                
                # ✅ 更新 UI（会重新填充下拉框）
                self.update_system_list()
                
                # ✅ 选中新坐标系
                self.control_panel.coordinate_panel.system_select_combo.setCurrentText(new_name)
                
                # ✅ 更新控制面板中的参数显示
                self.control_panel.update_coordinate_parameters(new_system.get_parameters())
                
                # ✅ 强制刷新画布显示
                self.canvas.update_view()
                
                # ✅ 标记有未保存的更改
                self.on_change_detected()
                
                self.add_log(f"坐标系 '{old_name}' 已重命名为 '{new_name}'", "info")
                
        except Exception as e:
            error_msg = f"重命名坐标系失败：{str(e)}"
            print(error_msg)
            self.add_log(error_msg, "error")

    def on_coordinate_parameter_changed(self):
        """当坐标系参数改变时的处理函数"""
        # 获取选中的坐标系名称
        system_name = self.control_panel.get_selected_system()
        
        # 获取选中的坐标系
        system = self.transformer.get_coordinate_system(system_name)
        
        if system:
            # 获取控制面板中的参数
            params = self.control_panel.get_coordinate_parameters()
            
            # 验证坐标系的XY轴是否垂直（只验证非世界坐标系）
            if system_name != "世界坐标系":
                x_angle = params.get('x_angle', system.x_angle)
                y_angle = params.get('y_angle', system.y_angle)
                
                # 计算角度差
                angle_diff = abs(y_angle - x_angle)
                # 检查是否接近90度或270度（允许1度的误差）
                if not (89 <= angle_diff <= 91 or 269 <= angle_diff <= 271):
                    # 注释掉警告弹窗，避免干扰用户
                    # QMessageBox.warning(self, "警告", f"坐标系 '{system_name}' 的XY轴应该相互垂直！角度差应为90度或270度。\n当前角度差: {angle_diff:.1f}度\n\n警告：非垂直坐标系可能导致坐标转换不准确，但不会阻止您继续操作。")
                    # 不使用return，允许参数继续更新
                    print(f"警告：坐标系 '{system_name}' 的XY轴应该相互垂直！角度差应为90度或270度。当前角度差: {angle_diff:.1f}度")
            
            # 更新坐标系参数
            system.update_parameters(**params)
            
            # 更新可视化
            self.update_visualization()

            # ✅ 标记有未保存的更改（不自动保存）
            self.on_change_detected()
    
    def on_add_coordinate_system(self):
        """添加新坐标系的处理函数"""
        # 获取新坐标系名称
        count = 1
        while f"图像坐标系{count}" in self.transformer.get_system_names():
            count += 1
        
        name = f"图像坐标系{count}"
        
        # 创建新坐标系
        new_system = CoordinateSystem(name, count, count, 0, 90, 1, 1, 'blue')
        self.transformer.add_coordinate_system(new_system)
        
        # 更新坐标系列表
        self.update_system_list()
        
        # 选择新坐标系
        self.control_panel.coordinate_panel.system_select_combo.setCurrentText(name)
        
        # 更新可视化
        self.update_visualization()
    
    def on_delete_coordinate_system(self):
        """删除坐标系的处理函数"""
        # 获取选中的坐标系名称
        system_name = self.control_panel.get_selected_system()
        
        # 不允许删除世界坐标系和机械坐标系
        if system_name in ["世界坐标系", "机械坐标系"]:
            QMessageBox.warning(self, "警告", f"不能删除 {system_name}！")
            return
        
        # 确认删除
        reply = QMessageBox.question(self, "确认", f"确定要删除坐标系 '{system_name}' 吗？",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # 从转换器中移除
            self.transformer.remove_coordinate_system(system_name)
            
            # 更新坐标系列表
            self.update_system_list()
            
            # 更新可视化
            self.update_visualization()
    
    def on_robot_parameter_changed(self):
        """当机械臂参数改变时的处理函数"""
        # 先应用角度范围模式，再写入角度，保证 set_angle 规范化与界面一致
        angle_range_text = self.control_panel.robot_panel.angle_range_combo.currentText()
        angle_range_map = {
            '0~360度': '0-360',
            '-360~360度': '-360-360',
            '-180~180度': '-180-180'
        }
        if angle_range_text in angle_range_map:
            self.robot_arm.set_angle_range(angle_range_map[angle_range_text])
        
        params = self.control_panel.get_robot_parameters()
        self.robot_arm.update_parameters(**params)
        
        # 注意：根据需求，世界坐标系在视觉领域也叫机械坐标系，两者为一个概念
        # 因此不再更新单独的机械坐标系原点
        
        # 更新控制面板中的抓手坐标显示（包含角度）
        self.update_robot_parameter_display()
        
        # 更新可视化
        self.update_visualization()

        # ✅ 标记有未保存的更改（不自动保存）
        self.on_change_detected()
    
    def on_robot_move(self, dx, dy):
        """
        机械臂平移的处理函数
        
        参数:
        dx (float): X方向移动距离
        dy (float): Y方向移动距离
        """
        # 移动机械臂
        self.robot_arm.move_base(dx, dy)
        
        # 注意：根据需求，世界坐标系在视觉领域也叫机械坐标系，两者为一个概念
        # 因此不再更新单独的机械坐标系原点
        
        # 更新控制面板中的参数显示
        self.update_robot_parameter_display()
        
        # 更新可视化
        self.update_visualization()

        # ✅ 标记有未保存的更改（不自动保存）
        self.on_change_detected()
    
    def on_robot_rotate(self, d_angle):
        """
        机械臂旋转的处理函数
        
        参数:
        d_angle (float): 旋转角度增量（度）
        """
        # 旋转机械臂
        self.robot_arm.rotate(d_angle)
        
        # 更新控制面板中的参数显示
        self.update_robot_parameter_display()
        
        # 更新可视化
        self.update_visualization()

        # ✅ 标记有未保存的更改（不自动保存）
        self.on_change_detected()
    
    def update_robot_parameter_display(self):
        """更新机械臂参数显示"""
        # 获取机械臂参数
        params = self.robot_arm.get_parameters()
        
        # 更新控制面板中的参数显示
        self.control_panel.update_robot_parameters(params)
        
        # # 计算抓手位置并更新显示（包含角度）
        # gripper_x = self.robot_arm.base_x + self.robot_arm.length * math.cos(math.radians(self.robot_arm.angle))
        # gripper_y = self.robot_arm.base_y + self.robot_arm.length * math.sin(math.radians(self.robot_arm.angle))
        
        # # 更新抓手位置显示，包含角度信息
        # self.control_panel.robot_panel.update_gripper_position_display(gripper_x, gripper_y, self.robot_arm.angle)
    
    def _display_angle_for_transform_target(self, angle_deg, target_name):
        """
        坐标转换结果中的角度展示规则：
        - 目标为「图像坐标系」时：方向角固定按 0~360° 显示；
        - 目标为世界坐标系等与机械臂一致时：按机械臂设置中的角度范围模式显示。
        """
        if target_name == "图像坐标系":
            a = angle_deg % 360
            if a < 0:
                a += 360
            return a
        return RobotArm.normalize_angle_to_range(angle_deg, self.robot_arm.angle_range)
    
    def update_view_info(self):
        """更新视图信息"""
        # 获取当前缩放级别
        zoom_level = self.canvas.get_zoom_level()
        
        # 获取当前视图范围
        view_range = self.canvas.get_axes_limits()
        
        # 更新控制面板中的视图信息
        self.control_panel.update_view_info(zoom_level, view_range)
    
    def on_toggle_grid(self):
        """切换网格显示状态"""
        self.canvas.toggle_grid()
    
    def on_toggle_axes(self):
        """切换坐标轴显示状态"""
        self.canvas.toggle_axes()
    
    def on_reset_view(self):
        """重置视图"""
        self.canvas.set_default_view()
        self.update_view_info()
    
    def on_zoom_in(self):
        """放大视图"""
        # 获取当前视图范围
        x_min, x_max, y_min, y_max = self.canvas.get_axes_limits()
        
        # 计算新的视图范围（放大50%）
        x_center = (x_min + x_max) / 2
        y_center = (y_min + y_max) / 2
        x_range = (x_max - x_min) * 0.5
        y_range = (y_max - y_min) * 0.5
        
        new_x_min = x_center - x_range / 2
        new_x_max = x_center + x_range / 2
        new_y_min = y_center - y_range / 2
        new_y_max = y_center + y_range / 2
        
        # 设置新的视图范围
        self.canvas.set_axes_limits(new_x_min, new_x_max, new_y_min, new_y_max)
        
        # 更新视图信息
        self.update_view_info()
    
    def on_zoom_out(self):
        """缩小视图"""
        # 获取当前视图范围
        x_min, x_max, y_min, y_max = self.canvas.get_axes_limits()
        
        # 计算新的视图范围（缩小50%）
        x_center = (x_min + x_max) / 2
        y_center = (y_min + y_max) / 2
        x_range = (x_max - x_min) * 1.5
        y_range = (y_max - y_min) * 1.5
        
        new_x_min = x_center - x_range / 2
        new_x_max = x_center + x_range / 2
        new_y_min = y_center - y_range / 2
        new_y_max = y_center + y_range / 2
        
        # 设置新的视图范围
        self.canvas.set_axes_limits(new_x_min, new_x_max, new_y_min, new_y_max)
        
        # 更新视图信息
        self.update_view_info()
    
    def on_grid_style_changed(self, style):
        """
        网格样式改变时的处理
        
        参数:
        style (str): 网格样式 ('major', 'minor', 'both')
        """
        self.canvas.set_grid_style(style)
    
    def on_zoom_to_rectangle(self):
        """矩形缩放处理"""
        if self.rect_selector is None:
            # 创建矩形选择器
            self.rect_selector = self.canvas.add_rectangle_selector(self.on_rectangle_selected)
            
            # 更新按钮状态
            self.control_panel.set_rect_zoom_mode(True)
        else:
            # 移除矩形选择器
            self.rect_selector.set_visible(False)
            self.rect_selector.disconnect_events()
            self.rect_selector = None
            
            # 更新按钮状态
            self.control_panel.set_rect_zoom_mode(False)
    
    def on_rectangle_selected(self, eclick, erelease):
        """
        矩形选择完成后的处理
        
        参数:
        eclick (MouseEvent): 鼠标点击事件
        erelease (MouseEvent): 鼠标释放事件
        """
        # 获取选择的矩形区域
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata
        
        # 缩放到选择的区域
        self.canvas.zoom_to_rectangle(x1, y1, x2, y2)
        
        # 移除矩形选择器
        self.rect_selector.set_visible(False)
        self.rect_selector.disconnect_events()
        self.rect_selector = None
        
        # 更新按钮状态
        self.control_panel.set_rect_zoom_mode(False)
        
        # 更新视图信息
        self.update_view_info()
    
    def on_canvas_clicked(self, x, y):
        """
        当点击画布时的处理函数
        
        参数:
        x (float): 点击的X坐标
        y (float): 点击的Y坐标
        """
        # 获取源坐标系和目标坐标系
        source_system = self.control_panel.get_source_system()
        
        # 将世界坐标系中的点转换到源坐标系
        system = self.transformer.get_coordinate_system(source_system)
        if system:
            sx, sy = system.point_from_world(x, y)
            
            # 更新控制面板中的输入点坐标
            self.control_panel.set_input_point(sx, sy)
        
        # 调用添加点的方法
        self.on_add_point_clicked(x, y)
    
    def on_canvas_button_press(self, event):
            """
            处理画布按钮按下事件，用于提前检测拖拽
            
            参数:
            event (MouseEvent): 鼠标事件
            """
            # ✅ 只在左键按下时处理
            if event.button != 1:
                return
            
            # ✅ 确保点击在坐标轴内
            if event.inaxes != self.canvas.ax:
                return
            
            # ✅ 注意：这里不设置 is_dragging，只有 on_pick 确认后才设置
            # 这样可以防止误触发    
        


    def on_canvas_point_click(self, event):
        """
        处理画布上的点击事件，用于添加点
        
        参数:
        event (MouseEvent): 鼠标事件
        """
        # # 只处理左键点击，并且不是点击在可拖拽对象上
        # if event.button == 1 and event.inaxes == self.canvas.ax:
        #     # 检查是否点击了可拖拽的对象（坐标系原点、机械臂底座、抓手）
        #     # 通过检查gid来判断
        #     contains, info = self.canvas.ax.contains(event)
        #     if contains and 'artist' in info:
        #         artist = info['artist']
        #         if hasattr(artist, 'get_gid') and artist.get_gid():
        #             gid = artist.get_gid()
        #             # 如果点击的是坐标系原点、机械臂底座或抓手，则不添加点
        #             if gid.startswith('origin_') or gid in ['robot_base', 'robot_gripper']:
        #                 return
            
         # ✅ 关键修复：添加严格条件限制
        # 只处理左键点击
        if event.button != 1:
            return
        
        # ✅ 确保点击在坐标轴内
        if event.inaxes != self.canvas.ax:
            return
        
        # ✅ 关键修复：如果正在拖拽对象，不添加点
        if self.is_dragging:
            return
        
        # ✅ 确保鼠标位置有效
        if event.xdata is None or event.ydata is None:
            return

            # 如果不是点击在可拖拽对象上，则添加点
        self.on_add_point_clicked(event.xdata, event.ydata)

    def snap_coordinate(self, value, snap_threshold=0.1):
        """
        坐标规整函数，将坐标值吸附到 0.5 的倍数
        
        参数:
        value (float): 原始坐标值
        snap_threshold (float): 整数吸附阈值，默认 0.1
        
        返回:
        float: 规整后的坐标值
        """
        # 步骤 1: 先四舍五入到最近的 0.5 倍数
        snapped = round(value * 2) / 2
        
        # 步骤 2: 检查是否接近整数，如果是则吸附到整数
        nearest_int = round(snapped)
        if abs(snapped - nearest_int) <= snap_threshold:
            return float(nearest_int)
        
        return snapped
    
    def on_add_point_clicked(self, x, y):
        """
        在画布上点击添加点的处理函数
        
        参数:
        x (float): 点击的X坐标（世界坐标系）
        y (float): 点击的Y坐标（世界坐标系）
        """
        # ✅ 新增：坐标规整，吸附到 0.5 倍数
        x = self.snap_coordinate(x)
        y = self.snap_coordinate(y)


        try:
            # 验证所有坐标系的 XY 轴是否垂直
            invalid_systems = []
            for name, system in self.transformer.get_all_coordinate_systems().items():
                if name != "世界坐标系":
                    x_axis_angle = math.radians(system.x_angle)
                    y_axis_angle = math.radians(system.y_angle)
                    
                    dot_product = math.cos(x_axis_angle) * math.cos(y_axis_angle) + math.sin(x_axis_angle) * math.sin(y_axis_angle)
                    
                    if abs(dot_product) > 1:
                        angle_diff = abs(system.y_angle - system.x_angle)
                        invalid_systems.append(f"  - {name}: 当前角度差 {angle_diff:.1f}度")
            
            if invalid_systems:
                warning_msg = "检测到以下坐标系的 XY 轴不垂直：\n" + "\n".join(invalid_systems) + "\n\n警告：非垂直坐标系可能导致坐标转换不准确，但不会阻止您继续操作。"
                self.add_log(warning_msg, "warning")
            
            # 步骤 1: 创建点名称并添加到数据模型
            count = 1
            while f"点{count}" in self.points:
                count += 1
            name = f"点{count}"
            
            # 默认角度为 0 度（指向 x 轴正方向）
            self.points[name] = {'x': x, 'y': y, 'system': "世界坐标系", 'angle': 0.0}
            self.point_manager.add_point(name, x, y, "世界坐标系")
            
            print(f"✅ 步骤 1 - 已添加点到数据模型：{name}, 坐标：({x:.2f}, {y:.2f})")
            
            # 步骤 2: 更新整个表格显示（这会建立正确的映射关系）
            self.control_panel.update_point_table(self.points)
            
            print(f"✅ 步骤 2 - 表格已刷新")
            
            # 步骤 3: 获取目标坐标系，计算并更新转换后的坐标
            target_name = self.control_panel.get_target_system()
            
            if target_name:
                try:
                    target_sys = self.transformer.get_coordinate_system(target_name)
                    if target_sys:
                        # 进行坐标转换：世界坐标系 → 目标坐标系
                        tx, ty = target_sys.point_from_world(x, y)
                        t_angle = (0.0 - target_sys.x_angle) % 360
                        if t_angle > 180:
                            t_angle -= 360
                        t_angle = self._display_angle_for_transform_target(t_angle, target_name)
                        
                        print(f"✅ 步骤 3 - 坐标转换：世界坐标 ({x:.2f}, {y:.2f}) -> {target_name}坐标 ({tx:.2f}, {ty:.2f}), 角度：{t_angle:.2f}°")
                        
                        # 更新表格中的目标坐标列
                        table = self.control_panel.point_panel.point_table
                        row = table.rowCount() - 1  # 获取最后一行（刚添加的点）
                        
                        if row >= 0:
                            from PyQt5.QtWidgets import QTableWidgetItem
                            from PyQt5.QtCore import Qt
                            
                            table.setItem(row, 5, QTableWidgetItem(f"{tx:.2f}"))
                            table.setItem(row, 6, QTableWidgetItem(f"{ty:.2f}"))
                            table.setItem(row, 7, QTableWidgetItem(f"{t_angle:.2f}"))
                            
                            # 设置目标坐标列的样式（不可编辑）
                            for col in [5, 6, 7]:
                                item = table.item(row, col)
                                if item:
                                    item.setTextAlignment(Qt.AlignCenter)
                                    item.setBackground(QColor(245, 245, 245))
                                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    else:
                        print(f"⚠️ 目标坐标系 '{target_name}' 不存在")
                except Exception as e:
                    print(f"❌ 坐标转换失败：{e}")
            else:
                print(f"ℹ️ 未选择目标坐标系，跳过转换")
            
            # 步骤 4: 更新可视化，让点显示在画布上
            self.update_visualization()
            
            print(f"✅ 步骤 4 - 画布已刷新")
            
            # 步骤 5: 标记有未保存的更改
            self.on_change_detected()
            
            self.add_log(f"在画布上添加点 '{name}' ({x:.2f}, {y:.2f})", "info")
            
        except Exception as e:
            error_msg = f"添加点失败：{str(e)}"
            print(error_msg)
            self.add_log(error_msg, "error")
            import traceback
            traceback.print_exc()

    def connect_change_signals(self):
        """
        连接所有可能导致更改的信号，用于跟踪未保存的更改
        """
        
        # ✅ 关键修复：连接画布的按钮按下事件，用于提前检测拖拽开始
        self.canvas.canvas.mpl_connect('button_press_event', self.on_canvas_button_press)

        # 连接坐标系参数更改信号
        self.control_panel.coordinate_parameter_changed.connect(self.on_change_detected)
        
        # 连接机械臂参数更改信号
        self.control_panel.robot_parameter_changed.connect(self.on_change_detected)
        
        # 连接添加/删除坐标系信号
        self.control_panel.add_coordinate_system.connect(self.on_change_detected)
        self.control_panel.delete_coordinate_system.connect(self.on_change_detected)
        
        # 连接机械臂移动/旋转信号
        self.control_panel.move_robot.connect(lambda dx, dy: self.on_change_detected())
        self.control_panel.rotate_robot.connect(lambda angle: self.on_change_detected())
        
        # ✅ 修改：连接点操作信号 - 将原来的 add_point 连接改为连接新的处理函数
        # Deleted:self.control_panel.add_point.connect(self.on_change_detected)
        self.control_panel.add_point.connect(self.on_add_point_from_dialog)  # 新增：连接到对话框处理函数
        self.control_panel.remove_point.connect(self.on_change_detected)
        self.control_panel.clear_points.connect(self.on_change_detected)
        self.control_panel.batch_transform.connect(self.on_change_detected)
        self.control_panel.import_points.connect(self.on_change_detected)
        self.control_panel.update_point.connect(self.on_update_point_from_table)
        
        # ✅ 新增：连接点名称变化信号
        self.control_panel.point_panel.point_name_changed.connect(self.on_point_name_changed)
        
        # ✅ 新增：连接单点转换输入变化信号
        self.control_panel.point_panel.input_changed.connect(self.on_change_detected)
        
        # 连接画布点击事件（添加点）
        self.canvas.point_clicked.connect(lambda x, y: self.on_change_detected())
        
        # 连接拖拽释放事件
        self.canvas.canvas.mpl_connect('button_release_event', self.on_drag_release_with_change)
    
    def on_change_detected(self):
        """
        当检测到更改时调用，标记有未保存的更改
        """
        self.has_unsaved_changes = True
        # 更新窗口标题，提示有未保存的更改
        current_title = self.windowTitle()
        if not current_title.endswith("*"):
            self.setWindowTitle(current_title + " *")
    
    def on_drag_release_with_change(self, event):
        """
        处理拖拽释放事件，并标记有未保存的更改
        """
        # 调用原始的拖拽释放处理函数
        self.on_drag_release(event)
        # 如果是拖拽结束，则标记有未保存的更改
        if hasattr(self, 'is_dragging') and not self.is_dragging:
            self.on_change_detected()
    
    def on_cancel_changes(self):
        """
        处理取消更改事件，恢复到上次保存的状态
        """
        from PyQt5.QtWidgets import QMessageBox
        
        # 如果没有未保存的更改，直接返回
        if not self.has_unsaved_changes:
            return
        
        # 询问用户是否确定取消更改
        reply = QMessageBox.question(
            self,
            "确认取消",
            "确定要取消所有未保存的更改吗？\n所有未保存的修改将会丢失。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # 获取当前场景名称（如果有）
                current_scene = getattr(self, 'current_scene', 'default')
                
                # 重新加载场景
                if self.load_data(current_scene):
                    # 重置未保存更改标记
                    self.has_unsaved_changes = False
                    
                    # 更新窗口标题，移除未保存更改的标记
                    current_title = self.windowTitle()
                    if current_title.endswith(" *"):
                        self.setWindowTitle(current_title[:-2])
                    
                    self.add_log("已取消所有未保存的更改", "info")
                else:
                    QMessageBox.warning(self, "错误", "无法重新加载场景，请查看日志获取详细信息。")
            except Exception as e:
                self.add_log(f"取消更改失败: {str(e)}", "error")
                QMessageBox.warning(self, "错误", f"取消更改时发生错误: {str(e)}")
    
    def on_save_scene(self):
        """
        处理保存场景事件
        """
        from PyQt5.QtWidgets import QInputDialog, QMessageBox
        
        try:
                        # 如果没有未保存的更改，提示用户
            if not self.has_unsaved_changes:
                QMessageBox.information(self, "提示", "当前场景没有未保存的更改！")
                return
            # # 获取当前场景名称（如果有）
            current_scene = getattr(self, 'current_scene', 'default')
            #  # ✅ 获取当前场景名称（优先使用 current_scene）
            # current_scene = getattr(self, 'current_scene', None)
            
            # 弹出输入对话框，让用户输入场景名称
            scene_name, ok = QInputDialog.getText(
                self, 
                "保存场景", 
                "请输入场景名称:", 
                # text=current_scene
                text=current_scene if current_scene else "default"
            )
            
            if ok and scene_name.strip():
                scene_name = scene_name.strip()

                    # 如果名称改变，询问是否创建新场景
                if scene_name != current_scene:
                    reply = QMessageBox.question(
                        self,
                        "场景名称改变",
                        f"是否将当前配置保存为新场景 '{scene_name}'？\n点击'是'创建新场景，点击'否'覆盖原场景 '{current_scene}'",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    
                    if reply == QMessageBox.Yes:
                        # 创建新场景
                        self.current_scene = scene_name
                    
                # 保存场景
                if self.save_data(scene_name):
                    # 更新当前场景名称
                    self.current_scene = scene_name
                    # ✅ 更新已加载场景名称
                    self.loaded_scene = scene_name
                    # 重置未保存更改标记
                    self.has_unsaved_changes = False
                    
                    # 更新窗口标题，移除未保存更改的标记
                    self.setWindowTitle(f"工业机械臂运动模拟器 - {scene_name}")
                    
                    current_title = self.windowTitle()
                    if current_title.endswith(" *"):
                        self.setWindowTitle(current_title[:-2])

                    # ✅ 刷新场景列表
                    self.update_scene_list()

                    QMessageBox.information(self, "保存成功", f"场景 '{scene_name}' 保存成功！")
                else:
                    QMessageBox.warning(self, "保存失败", "场景保存失败，请查看日志获取详细信息。")
            elif ok:
                QMessageBox.warning(self, "输入错误", "场景名称不能为空！")
                
        except Exception as e:
            self.add_log(f"保存场景失败: {str(e)}", "error")
            QMessageBox.warning(self, "错误", f"保存场景时发生错误: {str(e)}")
    
    def on_load_scene(self):
        """
        处理加载场景事件
        """
        import os
        from PyQt5.QtWidgets import QFileDialog, QMessageBox, QInputDialog
        
        try:
            # 检查是否有未保存的更改
            if self.has_unsaved_changes:
                reply = QMessageBox.question(
                    self,
                    "未保存的更改",
                    "您有未保存的更改，是否要保存当前场景？",
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    # 获取当前场景名称（如果有）
                    current_scene = getattr(self, 'current_scene', 'default')
                    
                    # 弹出输入对话框，让用户输入场景名称
                    scene_name, ok = QInputDialog.getText(
                        self, 
                        "保存场景", 
                        "请输入场景名称:", 
                        text=current_scene
                    )
                    
                    if ok and scene_name.strip():
                        # 保存当前场景
                        self.save_data(scene_name.strip())
                    else:
                        # 用户取消了保存，也取消加载新场景
                        return
                elif reply == QMessageBox.Cancel:
                    # 用户取消了操作
                    return
            
            # 打开文件对话框，让用户选择场景文件
            scene_dir = os.path.join(os.path.expanduser("~"), ".robot_arm_simulator", "scenes")
            os.makedirs(scene_dir, exist_ok=True)
            
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "加载场景",
                scene_dir,
                "JSON Files (*.json);;All Files (*)"
            )
            
            if file_path:
                # 从文件路径中提取场景名称
                scene_name = os.path.splitext(os.path.basename(file_path))[0]
                
                # 询问用户是否确定加载
                reply = QMessageBox.question(
                    self,
                    "确认加载",
                    f"确定要加载场景 '{scene_name}' 吗？\n当前未保存的修改将会丢失。",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # 加载场景
                    if self.load_data(scene_name):
                        # # 更新当前场景名称
                        # self.current_scene = scene_name
                        #     # ✅ 更新已加载场景名称（关键修复）
                        # self.loaded_scene = scene_name
                        # # 重置未保存更改标记
                        # self.has_unsaved_changes = False
                        # ✅ 更新窗口标题
                        self.setWindowTitle(f"工业机械臂运动模拟器 - {scene_name}")
                        # ✅ 刷新场景列表（关键修复）
                        self.update_scene_list()
                        # ✅ 添加日志
                        self.add_log(f"场景 '{scene_name}' 加载成功", "info")
                       
                        QMessageBox.information(self, "加载成功", f"场景 '{scene_name}' 加载成功！")
                    else:
                        QMessageBox.warning(self, "加载失败", "场景加载失败，请查看日志获取详细信息。")
                        
        except Exception as e:
            self.add_log(f"加载场景失败: {str(e)}", "error")
            QMessageBox.warning(self, "错误", f"加载场景时发生错误: {str(e)}")
    
    
    def on_pick(self, event):
        """
        处理画布上对象被点击的事件
        
        参数:
        event (PickEvent): 点击事件
        """
        # ✅ 关键修复：只在左键按下且没有处于拖拽状态时处理
        if event.mouseevent.button != 1 or self.is_dragging:
            return
        
        # 获取被点击的对象
        artist = event.artist
        gid = artist.get_gid()
        


        if gid:
            # 处理坐标系原点被点击
            if gid.startswith("origin_"):
                system_name = gid.replace("origin_", "")
                # 世界坐标系位置固定，不可拖拽
                if system_name != "世界坐标系":
                    # ✅ 验证：确保鼠标确实在坐标系原点附近
                    mouse_x = event.mouseevent.xdata
                    mouse_y = event.mouseevent.ydata
                    
                    if mouse_x is not None and mouse_y is not None:
                        system = self.transformer.get_coordinate_system(system_name)
                        if system:
                            distance = math.sqrt((mouse_x - system.origin_x)**2 + (mouse_y - system.origin_y)**2)
                            # ✅ 严格限制：距离必须小于 0.3 才能拖拽
                            if distance <= 0.3:
                                self.start_drag_coordinate_system(system_name, event.mouseevent)
                                return
                
                self.add_log("世界坐标系位置固定，不可拖拽", "info")
            

            # 处理机械臂底座被点击
            elif gid == "robot_base":
                # ✅ 验证：确保鼠标确实在机械臂底座附近
                mouse_x = event.mouseevent.xdata
                mouse_y = event.mouseevent.ydata
                
                if mouse_x is not None and mouse_y is not None:
                    distance = math.sqrt((mouse_x - self.robot_arm.base_x)**2 + (mouse_y - self.robot_arm.base_y)**2)
                    # ✅ 严格限制：距离必须小于 0.3 才能拖拽
                    if distance <= 0.3:
                        self.start_drag_robot_base(event.mouseevent)
                        return
            
            # 处理机械臂抓手被点击
            elif gid == "robot_gripper":
                # ✅ 验证：确保鼠标确实在机械臂抓手附近
                mouse_x = event.mouseevent.xdata
                mouse_y = event.mouseevent.ydata
                
                if mouse_x is not None and mouse_y is not None:
                    # gripper_x = self.robot_arm.base_x + self.robot_arm.length * math.cos(math.radians(self.robot_arm.angle))
                    # gripper_y = self.robot_arm.base_y + self.robot_arm.length * math.sin(math.radians(self.robot_arm.angle))
                    gripper_x = self.robot_arm.base_x + self.robot_arm.radius * math.cos(math.radians(self.robot_arm.angle))
                    gripper_y = self.robot_arm.base_y + self.robot_arm.radius * math.sin(math.radians(self.robot_arm.angle))
       
                    
                    distance = math.sqrt((mouse_x - gripper_x)**2 + (mouse_y - gripper_y)**2)
                    # ✅ 严格限制：距离必须小于 0.3 才能拖拽
                    if distance <= 0.3:
                        self.start_drag_robot_gripper(event.mouseevent)
                        return
            
    
    def start_drag_coordinate_system(self, system_name, mouse_event):
        """
        开始拖拽坐标系
        
        参数:
        system_name (str): 坐标系名称
        mouse_event (MouseEvent): 鼠标事件
        """
        self.is_dragging = True
        self.drag_item = ("coordinate", system_name)
        self.drag_start_pos = (mouse_event.xdata, mouse_event.ydata)
        self._last_drag_viz_time = 0.0  # 新拖拽首帧立即重绘
        
        # 连接鼠标移动和释放事件，并保存连接ID
        self.drag_motion_id = self.canvas.canvas.mpl_connect('motion_notify_event', self.on_drag_move)
        self.drag_release_id = self.canvas.canvas.mpl_connect('button_release_event', self.on_drag_release)
    
    def start_drag_robot_base(self, mouse_event):
        """
        开始拖拽机械臂底座
        
        参数:
        mouse_event (MouseEvent): 鼠标事件
        """
        self.is_dragging = True
        self.drag_item = ("robot_base", None)
        self.drag_start_pos = (mouse_event.xdata, mouse_event.ydata)
        self._last_drag_viz_time = 0.0
        
        # 连接鼠标移动和释放事件，并保存连接ID
        self.drag_motion_id = self.canvas.canvas.mpl_connect('motion_notify_event', self.on_drag_move)
        self.drag_release_id = self.canvas.canvas.mpl_connect('button_release_event', self.on_drag_release)
    
    def start_drag_robot_gripper(self, mouse_event):
        """
        开始拖拽机械臂抓手
        
        参数:
        mouse_event (MouseEvent): 鼠标事件
        """
        self.is_dragging = True
        self.drag_item = ("robot_gripper", None)
        self.drag_start_pos = (mouse_event.xdata, mouse_event.ydata)
        self._last_drag_viz_time = 0.0
        
        # 连接鼠标移动和释放事件，并保存连接ID
        self.drag_motion_id = self.canvas.canvas.mpl_connect('motion_notify_event', self.on_drag_move)
        self.drag_release_id = self.canvas.canvas.mpl_connect('button_release_event', self.on_drag_release)
    
    def on_drag_move(self, event):
        """
        处理拖拽移动事件
        
        参数:
        event (MouseEvent): 鼠标事件
        """
        if self.is_dragging and event.xdata is not None and event.ydata is not None:
            # 计算移动距离
            dx = event.xdata - self.drag_start_pos[0]
            dy = event.ydata - self.drag_start_pos[1]
            
            # 根据拖拽的对象类型进行处理
            if self.drag_item[0] == "coordinate":
                system_name = self.drag_item[1]
                system = self.transformer.get_coordinate_system(system_name)
                
                if system:
                    # 更新坐标系原点
                    system.update_parameters(
                        origin_x=system.origin_x + dx,
                        origin_y=system.origin_y + dy
                    )
                    
                    # 如果是机械坐标系，同时更新机械臂底座位置
                    if system_name == "机械坐标系":
                        self.robot_arm.update_parameters(
                            base_x=self.robot_arm.base_x + dx,
                            base_y=self.robot_arm.base_y + dy
                        )
                    
                    # 更新控制面板中的参数显示
                    if self.control_panel.get_selected_system() == system_name:
                        self.control_panel.update_coordinate_parameters(system.get_parameters())
            
            elif self.drag_item[0] == "robot_base":
                # 更新机械臂底座位置
                self.robot_arm.update_parameters(
                    base_x=self.robot_arm.base_x + dx,
                    base_y=self.robot_arm.base_y + dy
                )
                
                # 注意：根据需求，世界坐标系在视觉领域也叫机械坐标系，两者为一个概念
                # 因此不再更新单独的机械坐标系原点
                
                # 更新控制面板中的机械臂参数显示
                self.update_robot_parameter_display()
            
            elif self.drag_item[0] == "robot_gripper":
                # 计算新的角度
                import math
                new_angle = math.degrees(math.atan2(
                    event.ydata - self.robot_arm.base_y,
                    event.xdata - self.robot_arm.base_x
                ))
                
                # 更新机械臂角度
                self.robot_arm.update_parameters(angle=new_angle)
                
                # 更新控制面板中的机械臂参数显示
                self.update_robot_parameter_display()
            
            # 更新拖拽起始位置
            self.drag_start_pos = (event.xdata, event.ydata)
            
            # 更新可视化（限频，避免每根 motion 事件都全量 clear+重绘）
            now = time.monotonic()
            if now - self._last_drag_viz_time >= self._drag_viz_min_interval:
                self._last_drag_viz_time = now
                self.update_visualization()
    
    def on_drag_release(self, event):
        """
        处理拖拽释放事件
        
        参数:
        event (MouseEvent): 鼠标事件
        """
        if self.is_dragging:
            # ✅ 先重置状态，防止 update_visualization 再次触发拖拽
            self.is_dragging = False
            item_to_release = self.drag_item
            self.drag_item = None
            
            # 断开特定的鼠标移动和释放事件连接
            if self.drag_motion_id is not None:
                try:
                    self.canvas.canvas.mpl_disconnect(self.drag_motion_id)
                    self.drag_motion_id = None
                except:
                    pass
            
            if self.drag_release_id is not None:
                try:
                    self.canvas.canvas.mpl_disconnect(self.drag_release_id)
                    self.drag_release_id = None
                except:
                    pass
            
            # ✅ 延迟更新可视化，避免在事件处理中立即重绘
            # 使用 QTimer.singleShot 在主线程空闲时更新
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(0, self.update_visualization)
    
    def on_canvas_updated(self):
        """当画布更新时的处理函数"""
        # 更新视图信息
        self.update_view_info()
    
    def has_object_at_position(self, x, y, tolerance=0.3):
        """
        检查指定位置是否有对象（坐标系原点、点或机械臂）
        
        参数:
        x (float): X坐标
        y (float): Y坐标
        tolerance (float): 容差范围
        
        返回:
        bool: 如果有对象返回True，否则返回False
        """
        import math
        
        # 检查所有坐标系的原点
        coordinate_systems = self.transformer.get_all_coordinate_systems()
        for name, system in coordinate_systems.items():
            distance = math.sqrt((x - system.origin_x)**2 + (y - system.origin_y)**2)
            if distance <= tolerance:
                return True
        
        # 检查所有点
        for point_name, point_data in self.points.items():
            distance = math.sqrt((x - point_data['x'])**2 + (y - point_data['y'])**2)
            if distance <= tolerance:
                return True
        
        # 检查机械臂的位置（旋转轴和抓手位置）
        # 旋转轴位置
        arm_base_distance = math.sqrt((x - self.robot_arm.base_x)**2 + (y - self.robot_arm.base_y)**2)
        if arm_base_distance <= tolerance:
            return True
        
        # 抓手位置
        # gripper_x = self.robot_arm.base_x + self.robot_arm.length * math.cos(math.radians(self.robot_arm.angle))
        # gripper_y = self.robot_arm.base_y + self.robot_arm.length * math.sin(math.radians(self.robot_arm.angle))
        gripper_x = self.robot_arm.base_x + self.robot_arm.radius * math.cos(math.radians(self.robot_arm.angle))
        gripper_y = self.robot_arm.base_y + self.robot_arm.radius * math.sin(math.radians(self.robot_arm.angle))
        
        gripper_distance = math.sqrt((x - gripper_x)**2 + (y - gripper_y)**2)
        if gripper_distance <= tolerance:
            return True
        
        return False
    
    def on_transform_point(self, x=None, y=None, angle=None, source_name=None, target_name=None, row=None):
        """
        坐标转换处理函数，支持单点转换和批量转换
        
        参数:
        x (float, optional): X坐标，如果为None则从控制面板获取
        y (float, optional): Y坐标，如果为None则从控制面板获取
        angle (float): 角度,如果为None 则从控制面板获取
        source_name (str, optional): 源坐标系名称，如果为None则从控制面板获取
        target_name (str, optional): 目标坐标系名称，如果为None则从控制面板获取
        row (int, optional): 表格行号，如果提供则更新对应行的目标坐标
        """
        try:
            # 如果没有提供参数，则从控制面板获取
            if source_name is None:
                source_name = self.control_panel.point_panel.source_system_combo.currentText()
            if target_name is None:
                target_name = self.control_panel.point_panel.target_system_combo.currentText()
            if x is None or y is None:
                x, y, angle = self.control_panel.point_panel.get_input_point()
            
            # 进行坐标转换
            tx, ty , t_angle= self.transformer.transform_point(x, y, angle, source_name, target_name)
            t_angle = self._display_angle_for_transform_target(t_angle, target_name)
            
            # 如果提供了行号，则更新表格中的目标坐标
            if row is not None:
                self.control_panel.update_transformed_point(row, tx, ty, t_angle)
            else:
                # 否则更新单点转换的结果显示
                self.control_panel.set_result_text(f"转换结果: ({tx:.2f}, {ty:.2f}, {t_angle:.2f}°)")
            
            

            # 更新可视化
            self.update_visualization()

            


        except Exception as e:
            QMessageBox.warning(self, "错误", f"转换失败: {str(e)}")
    
    def on_add_point(self):
        """添加点的处理函数"""
        try:
            # ✅ 修复问题 3：显示对话框，让用户输入世界坐标系下的坐标
            self.control_panel.point_panel.show_add_point_dialog()
            
        except Exception as e:
            self.add_log(f"添加点失败：{str(e)}", "error")

    def on_add_point_from_dialog(self, x, y, angle):
        """
        从对话框添加点的处理函数
        
        参数:
        x (float): X 坐标（世界坐标系）
        y (float): Y 坐标（世界坐标系）
        angle (float): 角度（世界坐标系）
        """
        try:
            # 步骤 1: 创建点名称并添加到数据模型
            count = 1
            while f"点{count}" in self.points:
                count += 1
            name = f"点{count}"

            self.points[name] = {'x': x, 'y': y, 'system': "世界坐标系", 'angle': angle}
            self.point_manager.add_point(name, x, y, "世界坐标系", angle)
            
            print(f"✅ 步骤 1 - 已添加点到数据模型：{name}, 坐标：({x:.2f}, {y:.2f}), 角度：{angle:.1f}°")
            
            # 步骤 2: 更新整个表格显示（这会建立正确的映射关系）
            self.control_panel.update_point_table(self.points)
            
            print(f"✅ 步骤 2 - 表格已刷新")
            
            # 步骤 3: 获取目标坐标系，计算并更新转换后的坐标
            target_name = self.control_panel.get_target_system()
            
            if target_name:
                try:
                    target_sys = self.transformer.get_coordinate_system(target_name)
                    if target_sys:
                        # 进行坐标转换：世界坐标系 → 目标坐标系
                        tx, ty = target_sys.point_from_world(x, y)
                        t_angle = (angle - target_sys.x_angle) % 360
                        if t_angle > 180:
                            t_angle -= 360
                        t_angle = self._display_angle_for_transform_target(t_angle, target_name)
                        
                        print(f"✅ 步骤 3 - 坐标转换：世界坐标 ({x:.2f}, {y:.2f}) -> {target_name}坐标 ({tx:.2f}, {ty:.2f}), 角度：{t_angle:.2f}°")
                        
                        # 更新表格中的目标坐标列
                        table = self.control_panel.point_panel.point_table
                        row = table.rowCount() - 1  # 获取最后一行（刚添加的点）
                        
                        if row >= 0:
                            from PyQt5.QtWidgets import QTableWidgetItem
                            from PyQt5.QtCore import Qt
                            
                            table.setItem(row, 5, QTableWidgetItem(f"{tx:.2f}"))
                            table.setItem(row, 6, QTableWidgetItem(f"{ty:.2f}"))
                            table.setItem(row, 7, QTableWidgetItem(f"{t_angle:.2f}"))
                            
                            # 设置目标坐标列的样式（不可编辑）
                            for col in [5, 6, 7]:
                                item = table.item(row, col)
                                if item:
                                    item.setTextAlignment(Qt.AlignCenter)
                                    item.setBackground(QColor(245, 245, 245))
                                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    else:
                        print(f"⚠️ 目标坐标系 '{target_name}' 不存在")
                except Exception as e:
                    print(f"❌ 坐标转换失败：{e}")
            else:
                print(f"ℹ️ 未选择目标坐标系，跳过转换")
            
            # 步骤 4: 更新可视化，让点显示在画布上
            self.update_visualization()
            
            print(f"✅ 步骤 4 - 画布已刷新")
            
            # 步骤 5: 标记有未保存的更改
            self.on_change_detected()
            
            self.add_log(f"添加点 '{name}' 成功", "info")
        except Exception as e:
            error_msg = f"添加点失败：{str(e)}"
            print(error_msg)
            self.add_log(error_msg, "error")
            import traceback
            traceback.print_exc()

    def on_edit_point(self, point_name):
        """编辑点信息"""
        try:
            if point_name not in self.points:
                return
            
            point = self.points[point_name]
            
            # 创建编辑点的对话框
            dialog = QDialog(self)
            dialog.setWindowTitle(f"编辑点 - {point_name}")
            dialog.setMinimumWidth(400)
            
            layout = QVBoxLayout(dialog)
            
            # 点名称
            name_layout = QHBoxLayout()
            name_layout.addWidget(QLabel("点名称:"))
            name_edit = QLineEdit(point_name)
            name_layout.addWidget(name_edit)
            layout.addLayout(name_layout)
            
            # X坐标
            x_layout = QHBoxLayout()
            x_layout.addWidget(QLabel("X坐标:"))
            x_spin = QDoubleSpinBox()
            x_spin.setRange(-1000, 1000)
            x_spin.setDecimals(3)
            x_spin.setValue(point['x'])
            x_layout.addWidget(x_spin)
            layout.addLayout(x_layout)
            
            # Y坐标
            y_layout = QHBoxLayout()
            y_layout.addWidget(QLabel("Y坐标:"))
            y_spin = QDoubleSpinBox()
            y_spin.setRange(-1000, 1000)
            y_spin.setDecimals(3)
            y_spin.setValue(point['y'])
            y_layout.addWidget(y_spin)
            layout.addLayout(y_layout)
            
            # 角度
            angle_layout = QHBoxLayout()
            angle_layout.addWidget(QLabel("角度(°):"))
            angle_spin = QDoubleSpinBox()
            angle_spin.setRange(-360, 360)
            angle_spin.setDecimals(3)
            angle_spin.setValue(point.get('angle', 0.0))
            angle_layout.addWidget(angle_spin)
            layout.addLayout(angle_layout)
            
            # 坐标系选择
            system_layout = QHBoxLayout()
            system_layout.addWidget(QLabel("坐标系:"))
            system_combo = QComboBox()
            system_combo.addItems(self.transformer.get_system_names())
            system_combo.setCurrentText(point['system'])
            system_layout.addWidget(system_combo)
            layout.addLayout(system_layout)
            
            # 按钮
            button_layout = QHBoxLayout()
            ok_btn = QPushButton("确定")
            cancel_btn = QPushButton("取消")
            
            button_layout.addWidget(ok_btn)
            button_layout.addWidget(cancel_btn)
            layout.addLayout(button_layout)
            
            # 连接信号
            ok_btn.clicked.connect(dialog.accept)
            cancel_btn.clicked.connect(dialog.reject)
            
            # 显示对话框
            if dialog.exec_() == QDialog.Accepted:
                new_name = name_edit.text().strip()
                if not new_name:
                    QMessageBox.warning(self, "警告", "点名称不能为空")
                    return
                
                # 如果名称改变，需要删除旧点并添加新点
                if new_name != point_name:
                    if new_name in self.points:
                        QMessageBox.warning(self, "警告", f"点名称 '{new_name}' 已存在")
                        return
                    
                    # 删除旧点
                    del self.points[point_name]
                    self.point_manager.remove_point(point_name)
                    
                    # 添加新点
                    self.points[new_name] = {
                        'x': x_spin.value(),
                        'y': y_spin.value(),
                        'system': system_combo.currentText(),
                        'angle': angle_spin.value()
                    }
                    self.point_manager.add_point(new_name, x_spin.value(), y_spin.value(), system_combo.currentText())
                    
                else:
                    # 更新现有点
                    self.points[point_name] = {
                        'x': x_spin.value(),
                        'y': y_spin.value(),
                        'system': system_combo.currentText(),
                        'angle': angle_spin.value()
                    }
                    self.point_manager.update_point(point_name, x_spin.value(), y_spin.value(), system_combo.currentText(), angle_spin.value())
                
                # 更新可视化
                self.update_visualization()
                self.control_panel.update_point_table(self.points)
                
                # 添加日志
                self.add_log(f"点 '{point_name}' 已更新", "info")
                
        except Exception as e:
            QMessageBox.warning(self, "错误", f"编辑点失败: {str(e)}")

    def on_point_name_changed(self, row, old_name, new_name):
        """
        处理点名称变化（直接编辑表格）
        
        参数:
        row (int): 行号
        new_name (str): 新名称
        """
        try:
            print(f"🔍 收到重命名请求：{old_name} -> {new_name}, row={row}")
            
            # 验证旧名称
            if not old_name or old_name not in self.points:
                print(f"⚠️ 旧名称无效或不存在：{old_name}")
                # 恢复表格中的名称
                table = self.control_panel.point_panel.point_table
                if table.item(row, 1):
                    table.item(row, 1).setText(old_name if old_name else '')
                return
            
            new_name = new_name.strip()
            
            # 验证新名称
            if not new_name:
                QMessageBox.warning(self, "警告", "点名称不能为空")
                # 恢复旧名称
                table = self.control_panel.point_panel.point_table
                if table.item(row, 1):
                    table.item(row, 1).setText(old_name)
                return
            
            # 检查名称是否已存在
            if new_name in self.points and new_name != old_name:
                QMessageBox.warning(self, "警告", f"点名称 '{new_name}' 已存在")
                # 恢复旧名称
                table = self.control_panel.point_panel.point_table
                if table.item(row, 1):
                    table.item(row, 1).setText(old_name)
                return
            
            # 如果名称没有改变，直接返回
            if new_name == old_name:
                print(f"ℹ️ 名称未改变")
                return
            
            print(f"✅ 开始重命名：{old_name} -> {new_name}")
            
            # ✅ 关键修复：直接修改字典的键，保持插入顺序不变
            # 方法：获取所有 keys，找到旧名称的位置，重建字典
            points_items = list(self.points.items())
            
            # 找到旧名称对应的索引和数据
            target_data = None
            for i, (name, data) in enumerate(points_items):
                if name == old_name:
                    target_data = data.copy()
                    break
            
            if target_data is None:
                print(f"❌ 未找到点数据")
                return
            
            # 重建字典，将旧名称替换为新名称，保持其他项的顺序不变
            self.points.clear()
            for name, data in points_items:
                if name == old_name:
                    self.points[new_name] = target_data
                else:
                    self.points[name] = data.copy()
            
            print(f"   points keys: {list(self.points.keys())}")
            
            # ✅ 更新点管理器：先删除旧的，再添加新的
            self.point_manager.remove_point(old_name)
            self.point_manager.add_point(new_name, target_data['x'], target_data['y'],
                                       target_data['system'], target_data.get('angle', 0.0))
            
            # ✅ 刷新表格（会保持正确的顺序）
            self.control_panel.update_point_table(self.points)
            
            # ✅ 刷新画布
            # self.canvas.update_view()
            # ✅ 关键修复：立即刷新画布，确保点名称同步显示
            self.update_visualization()
            
            # ✅ 标记有未保存的更改
            self.on_change_detected()
            
            self.add_log(f"点 '{old_name}' 已重命名为 '{new_name}'", "info")
            
        except Exception as e:
            error_msg = f"修改点名称失败：{str(e)}"
            print(error_msg)
            self.add_log(error_msg, "error")
            import traceback
            traceback.print_exc()
    
    def on_update_point_from_table(self, point_name, x, y, angle, system):
        """
        ✅ 从表格更新点信息的处理函数（处理坐标值变化）
        
        参数:
        point_name (str): 点名称
        x (float): X 坐标
        y (float): Y 坐标
        angle (float): 角度
        system (str): 坐标系
        """
        try:
            print(f"🔍 收到坐标更新：点={point_name}, x={x}, y={y}, angle={angle}")
            
            if point_name not in self.points:
                print(f"   ⚠️ 点 {point_name} 不存在")
                return
            
            # ✅ 更新点数据
            self.points[point_name] = {
                'x': x,
                'y': y,
                'angle': angle,
                'system': system
            }
            
            # ✅ 更新点管理器
            self.point_manager.update_point(point_name, x, y, system, angle)
            
            # ✅ 刷新画布
            self.update_visualization()
            
            # ✅ 标记有未保存的更改
            self.on_change_detected()
            
            print(f"✅ 点 '{point_name}' 坐标已更新：({x:.2f}, {y:.2f}, {angle:.1f}°)")
            self.add_log(f"点 '{point_name}' 坐标已更新：({x:.2f}, {y:.2f}, {angle:.1f}°)", "info")
            
        except Exception as e:
            error_msg = f"更新点坐标失败：{str(e)}"
            print(error_msg)
            self.add_log(error_msg, "error")
            import traceback
            traceback.print_exc()


    def _get_point_name_by_row(self, row):
        """
        根据行号获取点名称
        
        参数:
        row (int): 行号
        
        返回:
        str: 点名称，如果不存在则返回 None
        """
        table = self.control_panel.point_panel.point_table
        name_item = table.item(row, 1)
        return name_item.text() if name_item else None
    

    def on_remove_point(self):
        """删除点的处理函数"""
        try:
            # 获取选中的行
            selected_rows = self.control_panel.get_selected_point_rows()
            
            if not selected_rows:
                QMessageBox.warning(self, "警告", "请先选择要删除的点！")
                return
            
            # 获取点名称并删除
            deleted_count = 0
            for row in selected_rows:
                try:
                    name = self.control_panel.get_point_name_at_row(row)
                    if name in self.points:
                        del self.points[name]
                        self.point_manager.remove_point(name)
                        deleted_count += 1
                except Exception as e:
                    print(f"删除点时出错: {e}")
            
            if deleted_count > 0:
                # 更新点表格
                self.control_panel.update_point_table(self.points)
                
                # 更新可视化
                self.update_visualization()
                
                QMessageBox.information(self, "成功", f"成功删除 {deleted_count} 个点！")
            else:
                QMessageBox.warning(self, "警告", "没有找到可删除的点！")
                
        except Exception as e:
            QMessageBox.warning(self, "错误", f"删除点失败: {str(e)}")
    
    def on_clear_points(self):
        """清空所有点的处理函数"""
        try:
            # 确认清空
            reply = QMessageBox.question(self, "确认", "确定要清空所有点吗？",
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                # 清空点列表
                self.points.clear()
                self.point_manager.clear_points()
                
                # 更新点表格
                self.control_panel.update_point_table(self.points)
                
                # 更新可视化
                self.update_visualization()
                
                QMessageBox.information(self, "成功", "所有点已清空！")
                
        except Exception as e:
            QMessageBox.warning(self, "错误", f"清空点失败: {str(e)}")
    
    def on_batch_transform(self):
        """批量转换选中点的处理函数"""
        try:
            # 获取目标坐标系
            target_name = self.control_panel.get_target_system()
            print(f"目标坐标系：{target_name}")
            
            # 获取选中的行
            selected_rows = self.control_panel.get_selected_point_rows()
            
            if not selected_rows:
                QMessageBox.warning(self, "警告", "请先选择要转换的点！")
                return
            
            # ✅ 修复问题 1：正确的批量转换逻辑
            # 批量转换表格中的点坐标是世界坐标系下的值
            # 直接将世界坐标系下的点转换到目标坐标系
            for row in selected_rows:
                name = self.control_panel.get_point_name_at_row(row)
                if name in self.points:
                    # 获取世界坐标系下的坐标（从表格中读取）
                    x_item = self.control_panel.point_panel.point_table.item(row, 2)
                    y_item = self.control_panel.point_panel.point_table.item(row, 3)
                    angle_item = self.control_panel.point_panel.point_table.item(row, 4)
                    
                    if x_item and y_item and angle_item:
                        try:
                            world_x = float(x_item.text())
                            world_y = float(y_item.text())
                            world_angle = float(angle_item.text())
                        except ValueError:
                            continue
                        
                        try:
                            # 从世界坐标系转换到目标坐标系
                            target_sys = self.transformer.get_coordinate_system(target_name)
                            
                            if target_sys is None:
                                # 目标坐标系不存在
                                self.control_panel.point_panel.point_table.setItem(row, 5, QTableWidgetItem(f"坐标系'{target_name}'不存在"))
                                self.control_panel.point_panel.point_table.setItem(row, 6, QTableWidgetItem(f"坐标系'{target_name}'不存在"))
                                self.control_panel.point_panel.point_table.setItem(row, 7, QTableWidgetItem(f"坐标系'{target_name}'不存在"))
                                continue
                            
                            # ✅ 验证目标坐标系对象是否有 point_from_world 方法
                            if not hasattr(target_sys, 'point_from_world'):
                                print(f"Error: 坐标系 '{target_name}' 没有 point_from_world 方法")
                                self.control_panel.point_panel.point_table.setItem(row, 5, QTableWidgetItem("转换方法不存在"))
                                self.control_panel.point_panel.point_table.setItem(row, 6, QTableWidgetItem("转换方法不存在"))
                                self.control_panel.point_panel.point_table.setItem(row, 7, QTableWidgetItem("转换方法不存在"))
                                continue
                            
                            # ✅ 执行坐标转换
                            try:
                                tx, ty = target_sys.point_from_world(world_x, world_y)
                                
                                # 转换角度
                                t_angle = (world_angle - target_sys.x_angle) % 360
                                if t_angle > 180:
                                    t_angle -= 360
                                t_angle = self._display_angle_for_transform_target(t_angle, target_name)
                                
                                # ✅ 打印调试信息
                                print(f"点 {name}: 世界坐标 ({world_x:.2f}, {world_y:.2f}) -> "
                                      f"{target_name}坐标 ({tx:.2f}, {ty:.2f}), 角度：{t_angle:.2f}°")
                                
                                # 更新表格中对应的目标坐标
                                self.control_panel.point_panel.update_transformed_point(row, tx, ty, t_angle)
                            except Exception as transform_error:
                                print(f"转换点 {name} 时出错：{transform_error}")
                                import traceback
                                traceback.print_exc()
                                self.control_panel.point_panel.point_table.setItem(row, 5, QTableWidgetItem(f"转换错误：{str(transform_error)}"))
                                self.control_panel.point_panel.point_table.setItem(row, 6, QTableWidgetItem(f"转换错误：{str(transform_error)}"))
                                self.control_panel.point_panel.point_table.setItem(row, 7, QTableWidgetItem(f"转换错误：{str(transform_error)}"))
                        except Exception as e:
                            print(f"Error transforming point {name}: {e}")
                            import traceback
                            traceback.print_exc()
                            self.control_panel.point_panel.point_table.setItem(row, 5, QTableWidgetItem("错误"))
                            self.control_panel.point_panel.point_table.setItem(row, 6, QTableWidgetItem("错误"))
                            self.control_panel.point_panel.point_table.setItem(row, 7, QTableWidgetItem("错误"))

            # 更新点表格的样式
            for row in selected_rows:
                for col in [5, 6, 7]:
                    item = self.control_panel.point_panel.point_table.item(row, col)
                    if item and item.text() in ["目标坐标系不存在", "错误"]:
                        item.setBackground(QColor(255, 200, 200))  # 红色背景提示
            
            QMessageBox.information(self, "成功", f"成功转换 {len(selected_rows)} 个点！")

        except Exception as e:
            QMessageBox.warning(self, "错误", f"批量转换失败：{str(e)}")
    
    def on_import_points(self):
        """导入点的处理函数"""
        try:
            # 打开文件对话框
            from PyQt5.QtWidgets import QFileDialog
            filename, _ = QFileDialog.getOpenFileName(
                self, "导入点", "", "CSV Files (*.csv);;All Files (*)")
            
            if not filename:
                return
            
            # 导入点
            count = self.point_manager.import_points(filename, self.transformer)
            
            # 更新点列表
            self.points = self.point_manager.get_all_points()
            
            # 更新点表格
            self.control_panel.update_point_table(self.points)
            
            # 同时更新坐标转换面板的批量转换表格
            self.control_panel.point_panel.update_points_display(self.points)
            
            # 更新可视化
            self.update_visualization()
            
            QMessageBox.information(self, "成功", f"成功导入 {count} 个点！")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"导入点失败: {str(e)}")
    
    def on_export_points(self):
        """导出点的处理函数"""
        try:
            # 打开文件对话框
            from PyQt5.QtWidgets import QFileDialog
            filename, _ = QFileDialog.getSaveFileName(
                self, "导出点", "", "CSV Files (*.csv);;All Files (*)")
            
            if not filename:
                return
            
            # 导出点
            self.point_manager.export_points(filename)
            
            QMessageBox.information(self, "成功", "点导出成功！")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"导出点失败: {str(e)}")
    

    def initialize_default_coordinate_systems(self):
        """初始化默认坐标系"""
        # 添加世界坐标系（原点在中心，角度为0）
        world_system = CoordinateSystem("世界坐标系", 0, 0, 0)
        world_system.color = (0.2, 0.5, 0.8)  # 蓝色
        self.transformer.add_coordinate_system(world_system)
        
        # 添加图像坐标系（原点在左上角，角度为0）
        image_system = CoordinateSystem("图像坐标系", -2, -2, 0)
        image_system.color = (0.2, 0.7, 0.3)  # 绿色
        self.transformer.add_coordinate_system(image_system)
        
        # 添加工具坐标系（作为示例）
        tool_system = CoordinateSystem("工具坐标系", 1, 1, 30)
        tool_system.color = (0.8, 0.4, 0.2)  # 橙色
        self.transformer.add_coordinate_system(tool_system)
        
        # 初始化机械臂
        self.robot_arm = RobotArm("机械臂1", 0, 0, 0, 3.0, 'gray') #3.0为默认长度
        self.robot_arms["机械臂1"] = self.robot_arm
        
        # 更新坐标系列表，确保UI显示所有坐标系
        self.update_system_list()
    
    def update_visualization(self):
        """更新可视化，彻底重新设计标签显示系统"""
        # 保存当前视图范围
        current_xlim = self.canvas.ax.get_xlim()
        current_ylim = self.canvas.ax.get_ylim()
        
        # 清除画布
        self.canvas.clear()
        
        # 获取当前视图范围
        x_min, x_max = current_xlim
        y_min, y_max = current_ylim
        
        # 定义标签安全显示区域（考虑文本大小）
        text_margin = 0.3  # 文本安全边距
        safe_x_min = x_min + text_margin
        safe_x_max = x_max - text_margin
        safe_y_min = y_min + text_margin
        safe_y_max = y_max - text_margin


        # ✅ 关键修复：在每个绘制中文的地方强制设置字体
        font_properties = {
            'family': 'SimHei',  # 使用黑体
            'weight': 'bold',
            'size': 8
        }
        
        # 绘制所有坐标系
        for name, system in self.transformer.get_all_coordinate_systems().items():
            # 绘制坐标系
            system.draw(self.canvas.ax)
            
            # 计算标签位置 - 直接在原点上方显示
            text_x = system.origin_x - 1.5  # 固定在原点左侧
            text_y = system.origin_y + 0.5  # 固定在原点上方
            
            # 严格检查：确保标签完全在安全区域内
            if (safe_x_min <= text_x <= safe_x_max and 
                safe_y_min <= text_y <= safe_y_max):
                # 使用背景框确保标签清晰可见
                self.canvas.ax.text(text_x, text_y, name, 
                                   color=system.color, fontsize=8, fontweight='bold',
                                   fontname='SimHei',  # ✅ 强制指定字体
                                   ha='center', va='bottom',
                                   bbox=dict(boxstyle='round,pad=0.1', facecolor='white', alpha=0.7, edgecolor='none'))
        
        # 绘制机械臂
        self.robot_arm.draw(self.canvas.ax)
        
        # 检查机械臂位置是否在视图范围内
        # gripper_x = self.robot_arm.base_x + self.robot_arm.length * math.cos(math.radians(self.robot_arm.angle))
        # gripper_y = self.robot_arm.base_y + self.robot_arm.length * math.sin(math.radians(self.robot_arm.angle))
        gripper_x = self.robot_arm.base_x + self.robot_arm.radius * math.cos(math.radians(self.robot_arm.angle))
        gripper_y = self.robot_arm.base_y + self.robot_arm.radius * math.sin(math.radians(self.robot_arm.angle))
      


        # 计算机械臂角度标签位置 - 固定在机械臂旋转轴下方
        angle_text = f"旋转轴角度: {self.robot_arm.angle:.2f}°"
        text_x = self.robot_arm.base_x
        text_y = self.robot_arm.base_y - 0.3  # 固定在旋转轴下方
        
        # 严格检查：确保标签完全在安全区域内
        if (safe_x_min <= text_x <= safe_x_max and 
            safe_y_min <= text_y <= safe_y_max):
            # 使用背景框确保标签清晰可见
            # ✅ 使用背景框确保标签清晰可见，并强制指定字体
            self.canvas.ax.text(text_x, text_y, angle_text, 
                               color=self.robot_arm.color, fontsize=7,
                               fontname='SimHei',  # ✅ 强制指定字体
                               ha='center', va='top',
                               bbox=dict(boxstyle='round,pad=0.1', facecolor='white', alpha=0.7, edgecolor='none'))
        
        # 绘制点
        for name, point in self.points.items():
            system = self.transformer.get_coordinate_system(point['system'])
            if system:
                wx, wy = system.point_to_world(point['x'], point['y'])
                
                # 绘制点
                self.canvas.ax.plot(wx, wy, 'o', color=system.color, markersize=5)
                
                # 绘制点的角度方向箭头
                # 获取点的角度信息，如果没有则默认为0度
                point_angle = point.get('angle', 0.00)
                arrow_length = 0.3  # 箭头长度
                
                # 计算箭头终点坐标
                # 角度定义：x轴正方向指向y轴正方向为角度正方向
                # 0度指向x轴正方向，-90度指向y轴正方向
                arrow_angle = math.radians(point_angle)
                arrow_end_x = wx + arrow_length * math.cos(arrow_angle)
                arrow_end_y = wy + arrow_length * math.sin(arrow_angle)
                
                # 绘制箭头，使用与点相同的颜色
                self.canvas.ax.arrow(wx, wy, 
                                   arrow_end_x - wx, arrow_end_y - wy,
                                   head_width=0.1, head_length=0.1, 
                                   fc=system.color, ec=system.color, 
                                   alpha=0.8) #head_width=0.1, head_length=0.1,作用是箭头大小，0.1为默认大小，可以自己调
                
                # 计算点标签位置 - 固定在点的右侧
                text_x = wx + 0.2  # 固定在点的右侧
                text_y = wy        # 与点同一水平位置
                
                # 严格检查：确保标签完全在安全区域内
                if (safe_x_min <= text_x <= safe_x_max and 
                    safe_y_min <= text_y <= safe_y_max):
                    # ✅ 使用背景框确保标签清晰可见，并强制指定字体
                    self.canvas.ax.text(text_x, text_y, name, 
                                       color=system.color, fontsize=8,
                                       fontname='SimHei',  # ✅ 强制指定字体
                                       ha='left', va='center',
                                       bbox=dict(boxstyle='round,pad=0.1', facecolor='white', alpha=0.7, edgecolor='none'))
        
        # 恢复之前的视图范围，保持网格缩放状态
        self.canvas.ax.set_xlim(current_xlim)
        self.canvas.ax.set_ylim(current_ylim)
        
        # 更新网格显示
        self.canvas.update_grid_display()
        
        # 更新画布
        self.canvas.update_view()


def main():
    """主函数"""
    # ✅ 添加全局异常处理
    import traceback
    
    try:
        # 创建应用程序
        app = QApplication(sys.argv)
        
        # 设置应用程序样式
        app.setStyle('Fusion')
        
        # 创建并显示主窗口
        simulator = RobotArmSimulator()
        simulator.show()
        
        # 运行应用程序
        sys.exit(app.exec_())
        
    except Exception as e:
        # ✅ 捕获所有未处理的异常
        error_msg = f"程序启动失败：{str(e)}\n\n详细信息:\n{traceback.format_exc()}"
        print(error_msg)
        
        # 显示错误对话框（如果可能）
        try:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(None, "致命错误", error_msg)
        except:
            pass
        
        sys.exit(1)


if __name__ == "__main__":
    main()