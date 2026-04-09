"""
可缩放画布组件
支持画布的放大缩小和拖动功能
"""

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar
from matplotlib.widgets import RectangleSelector
import matplotlib.pyplot as plt
import math
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal


class ZoomableCanvas(QWidget):
    """可缩放画布组件"""
    
    # 信号定义
    point_clicked = pyqtSignal(float, float)  # 当用户点击画布时发出信号
    canvas_updated = pyqtSignal()  # 当画布更新时发出信号
    
    def __init__(self, parent=None):
        """
        初始化可缩放画布
        
        参数:
        parent (QWidget, optional): 父组件
        """
        super().__init__(parent)
        
        # ✅ 关键修复：更健壮的字体设置
        # 1. 首先尝试注册系统字体
        try:
            from matplotlib import font_manager
            
            # 尝试从多个位置加载 SimHei 字体
            font_paths_to_try = [
                r"C:\Windows\Fonts\simhei.ttf",  # Windows 系统字体
                "fonts/simhei.ttf",  # 项目目录下的字体
                "C:/Windows/Fonts/simhei.ttf",  # 另一种路径格式
            ]
            
            for font_path in font_paths_to_try:
                try:
                    if hasattr(font_manager, 'addfont'):
                        font_manager.fontManager.addfont(font_path)
                        print(f"✅ 成功注册字体：{font_path}")
                        break
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"⚠️ 字体注册失败：{e}")
        
        # 2. 设置 Matplotlib 默认字体
        plt.rcParams["font.sans-serif"] = [
            "SimHei",           # 黑体（优先使用）
            "Microsoft YaHei",  # 微软雅黑
            "Arial Unicode MS", # Arial Unicode
            "DejaVu Sans",      # 备选英文字体
        ]
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
        
        # 3. 强制刷新字体缓存
        try:
            from matplotlib import font_manager
            font_manager._rebuild()
        except Exception:
            pass
        
        
        
        
        # 创建Matplotlib图形
        self.figure = Figure(figsize=(8, 6), dpi=100) # 创建一个6x6的画布
        self.canvas = FigureCanvas(self.figure)
        
        # 创建导航工具栏
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        # 创建布局
        layout = QVBoxLayout(self)
        # layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        
        # ✅ 新增：设置布局的边距为 0，确保画布完全铺满
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # ✅ 新增：设置画布的大小策略，使其能够扩展
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


        # 创建轴
        self.ax = self.figure.add_subplot(111) # 1行1列，第1个子图
        
        # 设置轴的属性
        self.ax.set_aspect('equal') # 等比例
        self.ax.grid(True)
        
        # 1. 设置背景色
        self.ax.set_facecolor('#f5f5f5')

        # 2. 设置网格样式
        self.ax.grid(True, linestyle='--', alpha=0.7)

        # 3. 设置坐标轴范围
        self.ax.set_xlim(-100, 100)
        self.ax.set_ylim(-100, 100)

        # 4. 添加标题
        self.ax.set_title("机械臂工作空间")

        # ✅ 新增：调整图形布局，确保充分利用空间
        self.figure.tight_layout()
        self.figure.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)


        # 连接事件
        self.canvas.mpl_connect('button_press_event', self.on_mouse_press)
        self.canvas.mpl_connect('button_release_event', self.on_mouse_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        self.canvas.mpl_connect('scroll_event', self.on_mouse_scroll)  # 滚轮事件
        
        # 初始化双击检测相关变量
        self.last_click_time = 0
        self.double_click_threshold = 0.5  # 双击时间阈值（秒），增加阈值提高双击检测成功率
        self.click_count = 0  # 点击计数器，用于双击检测
        self._click_timer = None  # 双击检测定时器
        
        # 初始化拖动状态
        self.is_dragging = False
        self.last_x = 0
        self.last_y = 0
        
        # 设置默认视图范围
        self.default_xlim = (-50, 50) # 默认视图范围
        self.default_ylim = (-50, 50)
        self.ax.set_xlim(self.default_xlim)
        self.ax.set_ylim(self.default_ylim)
        
        # 更新画布
        self.canvas.draw()
    
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
        # 这个方法需要在主程序中实现，因为只有主程序知道所有对象的位置
        # 这里返回False作为默认值，主程序会重写这个方法
        return False
    
    def on_mouse_press(self, event):
        """
        处理鼠标按下事件
        
        参数:
        event (MouseEvent): 鼠标事件
        """
        import time
        
        # 处理左键点击和拖动
        if event.button == 1 and event.inaxes == self.ax:  # 左键
            current_time = time.time()
            
            # 检查点击位置是否有对象，如果有对象则不允许拖动
            if not self.has_object_at_position(event.xdata, event.ydata):
                # 立即进入拖动状态，不使用延迟
                self.is_dragging = True
                self.last_x = event.xdata
                self.last_y = event.ydata
                
                # 同时处理双击检测，但不影响拖动功能
                if hasattr(self, 'click_count') and self.click_count == 1:
                    time_diff = current_time - self.last_click_time
                    if time_diff < self.double_click_threshold:
                        # 是双击，调用双击处理函数
                        self.on_mouse_double_click(event)
                        self.click_count = 0  # 重置点击计数
                        # 双击后仍然保持拖动状态，允许用户双击后立即拖动
                        return
                
                # 第一次点击，设置点击计数和时间
                self.click_count = 1
                self.last_click_time = current_time
        
        # 设置定时器，如果在阈值时间内没有第二次点击，则重置计数
        def reset_click_count():
            self.click_count = 0
        
        # 使用单线程定时器
        from threading import Timer
        # 安全地取消之前的定时器
        if hasattr(self, '_click_timer') and self._click_timer is not None:
            try:
                self._click_timer.cancel()
            except:
                pass
        # 创建新的定时器
        self._click_timer = Timer(self.double_click_threshold, reset_click_count)
        self._click_timer.daemon = True
        self._click_timer.start()
    
    def on_mouse_release(self, event):
        """
        处理鼠标释放事件
        
        参数:
        event (MouseEvent): 鼠标事件
        """
        # 如果释放的是左键或右键，结束拖动
        if event.button in [1, 3]:  # 左键或右键
            if self.is_dragging:
                self.is_dragging = False
                # 拖动结束后，完整更新一次网格显示
                self.update_grid_display()
                self.canvas.draw()
                self.canvas_updated.emit()
    
    def on_mouse_double_click(self, event):
        """
        处理鼠标双击事件
        
        参数:
        event (MouseEvent): 鼠标事件
        """
        # 如果双击的是左键，发出点点击信号
        if event.button == 1 and event.inaxes == self.ax:  # 左键双击
            self.point_clicked.emit(event.xdata, event.ydata)
            # 双击后重置拖动状态，确保只有按住鼠标左键才能拖动
            self.is_dragging = False
            self.last_x = None
            self.last_y = None
    
    def on_mouse_scroll(self, event):
        """
        处理鼠标滚轮事件，用于缩放网格规格
        
        参数:
        event (MouseEvent): 鼠标事件
        """
        # 只有当鼠标悬浮在画布上时才处理滚轮事件
        if event.inaxes == self.ax:
            # 获取当前视图范围
            x_min, x_max = self.ax.get_xlim()
            y_min, y_max = self.ax.get_ylim()
            
            # 计算当前范围
            x_range = x_max - x_min
            y_range = y_max - y_min
            
            # 计算中心点
            x_center = (x_min + x_max) / 2
            y_center = (y_min + y_max) / 2
            
            # 根据滚轮方向调整视图范围
            zoom_factor = 0.9 if event.button == 'up' else 1.1
            
            # 计算新的范围（保持中心点不变）
            new_x_range = x_range * zoom_factor
            new_y_range = y_range * zoom_factor
            
            # 设置新的视图范围
            self.ax.set_xlim(x_center - new_x_range/2, x_center + new_x_range/2)
            self.ax.set_ylim(y_center - new_y_range/2, y_center + new_y_range/2)
            
            # 更新网格显示
            self.update_grid_display()
            
            # 更新画布
            self.canvas.draw()
            
            # 发出画布更新信号
            self.canvas_updated.emit()
    
    def update_grid_display(self):
        """
        更新网格显示，确保网格线清晰可见且保持正方形格子
        网格外部大框架保持固定尺寸，但跟随程序页面大小
        """
        # 获取当前视图范围
        x_min, x_max = self.ax.get_xlim()
        y_min, y_max = self.ax.get_ylim()
        
        # 计算当前范围
        x_range = x_max - x_min
        y_range = y_max - y_min
        
        # # ✅ 修改：强制最小范围为100
        # min_range = 100
        # x_range = max(x_range, min_range)
        # y_range = max(y_range, min_range)


        # 根据视图范围计算合适的网格间距，并确保两者一致以保持正方形格子
        x_step = self.calculate_grid_step(x_range)
        y_step = self.calculate_grid_step(y_range)
        
        # 选择较大的步长作为统一的网格间距，确保网格线保持正方形
        grid_step = max(x_step, y_step)
        
        # 设置网格
        self.ax.grid(True, linestyle='-', alpha=0.7) #0.7是透明度，越小越透明
        
        # 设置刻度，使用统一的步长
        self.ax.set_xticks(self.generate_ticks(x_min, x_max, grid_step))
        self.ax.set_yticks(self.generate_ticks(y_min, y_max, grid_step))
        
        # 确保坐标轴比例相等，保持正方形格子
        self.ax.set_aspect('equal')
        
        # 设置刻度标签格式
        self.ax.tick_params(axis='both', which='major', labelsize=8)


        # ✅ 新增：根据缩放级别调整坐标系标签大小
        # zoom_level = self.get_zoom_level()
        # font_size = max(8, int(8 * zoom_level))
        # self.ax.text(0, 0, "世界坐标系", fontsize=font_size, ha='center', va='center')
            
        # 确保网格框架保持固定大小，不随坐标系或机械臂移动而改变
        # 这里保持当前的视图范围不变，只更新网格显示
        # 这样网格外部的大框架就不会跟着变了

        # 1. 添加次级网格（更细的网格线）
        # self.ax.grid(True, which='minor', linestyle=':', alpha=0.3)
        # self.ax.minorticks_on()
    
    def calculate_grid_step(self, range_val):
        """
        根据范围计算合适的网格间距
        
        参数:
        range_val (float): 坐标轴范围
        
        返回:
        float: 合适的网格间距
        """
        # 目标是大约显示10-20个网格线
        target_lines = 20
        raw_step = range_val / target_lines
        
        # 将步长调整为1, 2, 5的倍数，使刻度更美观
        magnitude = 10 ** int(math.log10(raw_step))
        normalized_step = raw_step / magnitude
        
        if normalized_step < 1.5:
            step = magnitude
        elif normalized_step < 3.5:
            step = 2 * magnitude
        elif normalized_step < 7.5:
            step = 5 * magnitude
        else:
            step = 10 * magnitude
        
        # # ✅ 新增：确保最小步长为5
        # return max(step, 5)
        return step
    
    def generate_ticks(self, min_val, max_val, step):
        """
        根据最小值、最大值和步长生成刻度列表
        
        参数:
        min_val (float): 最小值
        max_val (float): 最大值
        step (float): 步长
        
        返回:
        list: 刻度列表
        """
        ticks = []
        current = math.ceil(min_val / step) * step
        
        while current <= max_val:
            ticks.append(current)
            current += step
        
        return ticks
    def on_mouse_move(self, event):
        """
        处理鼠标移动事件
        
        参数:
        event (MouseEvent): 鼠标事件
        """
        # 只有在拖动状态下才更新网格，并且last_x和last_y不为None
        # 这样可以防止双击后鼠标悬浮时意外拖动坐标系或机械臂
        if self.is_dragging and event.inaxes == self.ax and self.last_x is not None and self.last_y is not None:
            try:
                # 计算移动距离
                dx = event.xdata - self.last_x
                dy = event.ydata - self.last_y
                
                # 获取当前轴范围
                xlim = self.ax.get_xlim()
                ylim = self.ax.get_ylim()
                
                # 更新轴范围
                self.ax.set_xlim(xlim[0] - dx, xlim[1] - dx)
                self.ax.set_ylim(ylim[0] - dy, ylim[1] - dy)
                
                # 更新最后位置
                self.last_x = event.xdata
                self.last_y = event.ydata
                
                # 直接重绘，确保拖动流畅
                self.canvas.draw()
                
            except Exception as e:
                # 忽略可能的异常，确保拖动过程稳定
                pass
    
    def clear(self):
        """清除画布"""
        self.ax.clear()
        self.ax.grid(True)
        self.canvas.draw()
    
    def update_view(self):
        """更新视图"""
        self.canvas.draw()
        self.canvas_updated.emit()
    
    def set_axes_limits(self, x_min, x_max, y_min, y_max):
        """
        设置坐标轴范围
        
        参数:
        x_min (float): X轴最小值
        x_max (float): X轴最大值
        y_min (float): Y轴最小值
        y_max (float): Y轴最大值
        """
        self.ax.set_xlim(x_min, x_max)
        self.ax.set_ylim(y_min, y_max)
        self.canvas.draw()
    
    def get_axes_limits(self):
        """
        获取坐标轴范围
        
        返回:
        tuple: (x_min, x_max, y_min, y_max)
        """
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        return (xlim[0], xlim[1], ylim[0], ylim[1])
    
    def add_rectangle_selector(self, onselect):
        """
        添加矩形选择器
        
        参数:
        onselect (function): 选择完成后的回调函数
        
        返回:
        RectangleSelector: 矩形选择器对象
        """
        rect_selector = RectangleSelector(
            self.ax, onselect,
            drawtype='box', useblit=True,
            button=[1, 3],  # 左键和右键
            minspanx=5, minspany=5,
            spancoords='pixels',
            interactive=True
        )
        return rect_selector
    
    def get_zoom_level(self):
        """
        获取当前缩放级别
        
        返回:
        float: 缩放级别（1.0为默认缩放）
        """
        # 获取当前视图范围
        current_xlim = self.ax.get_xlim()
        current_ylim = self.ax.get_ylim()
        
        # 计算当前范围和默认范围的比例
        default_range = self.default_xlim[1] - self.default_xlim[0]
        current_range = current_xlim[1] - current_xlim[0]
        
        # 计算缩放级别（默认缩放为1.0）
        zoom_level = default_range / current_range
        
        return zoom_level
    
    def set_default_view(self):
        """重置为默认视图"""
         # ✅ 修改：设置更大的默认视图范围
        self.ax.set_xlim(-50, 50)
        self.ax.set_ylim(-50, 50)
        self.canvas.draw()
        self.canvas_updated.emit()
    
    def zoom_to_rectangle(self, x1, y1, x2, y2):
        """
        缩放到指定的矩形区域
        
        参数:
        x1, y1 (float): 矩形的一个角
        x2, y2 (float): 矩形的对角
        """
        # 确保x1 < x2, y1 < y2
        x_min = min(x1, x2)
        x_max = max(x1, x2)
        y_min = min(y1, y2)
        y_max = max(y1, y2)
        
        # 添加一些边距
        x_range = x_max - x_min
        y_range = y_max - y_min
        
        # 设置新的视图范围
        self.ax.set_xlim(x_min - x_range * 0.1, x_max + x_range * 0.1)
        self.ax.set_ylim(y_min - y_range * 0.1, y_max + y_range * 0.1)
        
        # 更新画布
        self.canvas.draw()
        self.canvas_updated.emit()
    
    def toggle_grid(self, show=True):
        """
        切换网格显示
        
        参数:
        show (bool): 是否显示网格
        """
        self.ax.grid(show)
        self.canvas.draw()
    
    def toggle_axes(self, show=True):
        """
        切换坐标轴显示
        
        参数:
        show (bool): 是否显示坐标轴
        """
        self.ax.set_axis_on() if show else self.ax.set_axis_off()
        self.canvas.draw()
    
    def set_grid_style(self, style='both'):
        """
        设置网格样式
        
        参数:
        style (str): 网格样式 ('major', 'minor', 'both')
        """
        if style == 'major':
            self.ax.grid(True, which='major')
            self.ax.grid(False, which='minor')
        elif style == 'minor':
            self.ax.grid(False, which='major')
            self.ax.grid(True, which='minor')
        else:  # 'both'
            self.ax.grid(True, which='both')
        
        self.canvas.draw()