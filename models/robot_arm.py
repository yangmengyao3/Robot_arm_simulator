"""
机械臂模型模块
定义了机械臂类及其相关操作
"""

import math


class RobotArm:
    """机械臂类，用于模拟机械臂运动"""
    
    def __init__(self, base_x=0, base_y=0, angle=0, radius=2, color='gray'): 
        """
        初始化机械臂
        
        参数:
        base_x (float): 旋转轴X坐标
        base_y (float): 旋转轴Y坐标
        angle (float): 旋转角度（度）
        radius (float): 抓手到旋转轴的距离
        color (str): 机械臂颜色
        """
        self.base_x = base_x
        self.base_y = base_y
        self.angle = angle
        self.radius = radius
        self.color = color
        self.angle_range = '0-360'
        
        # 计算抓手位置
        self.update_gripper_position()
    
    def update_gripper_position(self):
        """更新抓手位置"""
        angle_rad = math.radians(self.angle)
        self.gripper_x = self.base_x + self.radius * math.cos(angle_rad)
        self.gripper_y = self.base_y + self.radius * math.sin(angle_rad)
    
    def set_base_position(self, x, y):
        """
        设置旋转轴位置
        
        参数:
        x (float): 新的X坐标
        y (float): 新的Y坐标
        """
        self.base_x = x
        self.base_y = y
        self.update_gripper_position()
    
    def set_angle(self, angle):
        """
        设置旋转角度
        
        参数:
        angle (float): 新的角度（度）
        
        角度定义：
        - x轴正方向指向y轴正方向为角度正方向
        - 0度指向x轴正方向
        - -90度指向y轴正方向
        """
        # 根据角度范围设置处理角度值
        # 默认使用0~360度范围
        if hasattr(self, 'angle_range'):
            if self.angle_range == '0-360':
                # 0~360度范围
                self.angle = angle % 360
            elif self.angle_range == '-360-360':
                # -360~360度范围
                while angle > 360:
                    angle -= 720
                while angle < -360:
                    angle += 720
                self.angle = angle
            elif self.angle_range == '-180-180':
                # -180~180度范围
                self.angle = ((angle + 180) % 360) - 180
            else:
                # 默认0~360度
                self.angle = angle % 360
        else:
            # 默认0~360度范围
            self.angle = angle % 360
            
        self.update_gripper_position()
    
    @staticmethod
    def normalize_angle_to_range(angle, angle_range):
        """
        将任意角度（度）规范化到当前角度范围模式的取值区间内（仅数值，不修改实例状态）。
        用于界面展示或与机械臂设置一致的转换结果角度。
        """
        if angle_range == '0-360':
            return angle % 360
        if angle_range == '-360-360':
            a = angle
            while a > 360:
                a -= 720
            while a < -360:
                a += 720
            return a
        if angle_range == '-180-180':
            return ((angle + 180) % 360) - 180
        return angle % 360
    
    def set_angle_range(self, angle_range):
        """
        设置角度范围模式
        
        参数:
        angle_range (str): 角度范围模式，可选值：
            - '0-360': 0~360度范围
            - '-360-360': -360~360度范围
            - '-180-180': -180~180度范围
        """
        self.angle_range = angle_range
        # 重新设置当前角度以应用新的范围
        self.set_angle(self.angle)
    
    def set_radius(self, radius):
        """
        设置抓手到旋转轴的距离
        
        参数:
        radius (float): 新的距离
        """
        self.radius = radius
        self.update_gripper_position()
    
    def move_base(self, dx, dy):
        """
        平移旋转轴
        
        参数:
        dx (float): X方向移动距离
        dy (float): Y方向移动距离
        """
        self.base_x += dx
        self.base_y += dy
        self.update_gripper_position()
    
    def rotate(self, d_angle):
        """
        旋转机械臂
        
        参数:
        d_angle (float): 旋转角度增量（度）
        """
        self.set_angle(self.angle + d_angle)
    
    def get_gripper_position(self):
        """
        获取抓手位置
        
        返回:
        tuple: 抓手坐标 (x, y)
        """
        return (self.gripper_x, self.gripper_y)
    
    def draw(self, ax):
        """
        在Matplotlib轴上绘制机械臂
        
        参数:
        ax (matplotlib.axes.Axes): Matplotlib轴对象
        """
        # 绘制旋转轴 - 使旋转轴可点击
        
        base_scatter = ax.scatter(self.base_x, self.base_y, color=self.color, s=100, 
                                edgecolor='black', linewidth=2, zorder=10)
        base_scatter.set_picker(True)
        base_scatter.set_pickradius(8)
        base_scatter.set_gid("robot_base")
        
        # 绘制机械臂
        arm_line = ax.plot([self.base_x, self.gripper_x], [self.base_y, self.gripper_y], '-', 
                color='gray', linewidth=3)
        arm_line[0].set_gid("robot_arm")
        
        # 绘制抓手 - 使抓手可点击
        
        gripper_scatter = ax.scatter(self.gripper_x, self.gripper_y, color='green', s=100, 
                                   edgecolor='black', linewidth=2, zorder=10) #s是点的大小，linewidth是线的宽度,zorder是图层顺序，越小越靠前
        gripper_scatter.set_picker(True)
        gripper_scatter.set_pickradius(8) #设置点的半径
        gripper_scatter.set_gid("robot_gripper")
        
        # 显示角度
        angle_text = f'{self.angle:.1f}°'
        # ax.text((self.base_x + self.gripper_x) / 2 + 0.1, 
        #         (self.base_y + self.gripper_y) / 2 + 0.1, 
        #         angle_text, color=self.color, fontsize=9)
        
        # 显示抓手坐标
        ax.text(self.gripper_x + 0.1, self.gripper_y + 0.1, 
                f'抓手坐标:({self.gripper_x:.3f}, {self.gripper_y:.3f})', 
                color='green', fontsize=8)
        


    
    def update_parameters(self, base_x=None, base_y=None, angle=None, radius=None, color=None):
        """
        更新机械臂参数
        
        参数:
        base_x (float, optional): 新的旋转轴X坐标
        base_y (float, optional): 新的旋转轴Y坐标
        angle (float, optional): 新的旋转角度
        radius (float, optional): 新的旋转半径
        color (str, optional): 新的颜色
        """
        if base_x is not None:
            self.base_x = base_x
        if base_y is not None:
            self.base_y = base_y
        if angle is not None:
            self.set_angle(angle)
        if radius is not None:
            self.radius = radius
        if color is not None:
            self.color = color
        
        # 更新抓手位置
        self.update_gripper_position()
    
    def get_parameters(self):
        """
        获取机械臂参数
        
        返回:
        dict: 包含所有参数的字典
        """
        return {
            'base_x': self.base_x,
            'base_y': self.base_y,
            'angle': self.angle,
            'radius': self.radius,
            'color': self.color,
            'gripper_x': self.gripper_x,
            'gripper_y': self.gripper_y
        }

    @classmethod
    def from_dict(cls, data):
        """从字典创建实例，支持向后兼容"""
        # ✅ 提供默认值，确保所有属性都存在
        radius = data.get('radius', 2.0)
        length = data.get('length', 2.0)  # ✅ 处理旧版本的 length 属性
        
        # ✅ 如果存在 length 属性，使用它作为 radius
        if 'length' in data:
            radius = length
        
        return cls(
            name=data.get('name', '机械臂'),
            base_x=data.get('base_x', 0),
            base_y=data.get('base_y', 0),
            angle=data.get('angle', 45),
            radius=radius,
            color=data.get('color', 'gray')
        )    