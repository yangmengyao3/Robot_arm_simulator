"""
坐标系模型模块
定义了坐标系类及其相关操作
"""

import math
import numpy as np


class CoordinateSystem:
    """坐标系类，用于表示和处理坐标系"""
    
    def __init__(self, name, origin_x=0, origin_y=0, x_angle=0, y_angle=90, x_scale=1, y_scale=1, color='blue'):
        """
        初始化坐标系
        
        参数:
        name (str): 坐标系名称
        origin_x (float): 原点X坐标
        origin_y (float): 原点Y坐标
        x_angle (float): X轴角度（度）
        y_angle (float): Y轴角度（度）
        x_scale (float): X轴比例因子
        y_scale (float): Y轴比例因子
        color (str): 坐标系颜色
        """
        self.name = name
        self.origin_x = origin_x
        self.origin_y = origin_y
        self.x_angle = x_angle
        self.y_angle = y_angle
        self.x_scale = x_scale
        self.y_scale = y_scale
        self.color = color
        
        # 计算转换矩阵
        self.update_transform_matrix()
    
    def update_transform_matrix(self):
        """更新坐标系转换矩阵"""
        # 将角度转换为弧度
        x_rad = math.radians(self.x_angle)
        y_rad = math.radians(self.y_angle)
        
        # 计算转换矩阵 (从该坐标系到世界坐标系)
        self.to_world_matrix = np.array([
            [self.x_scale * math.cos(x_rad), self.y_scale * math.cos(y_rad), self.origin_x],
            [self.x_scale * math.sin(x_rad), self.y_scale * math.sin(y_rad), self.origin_y],
            [0, 0, 1]
        ])
        
        # 计算逆转换矩阵 (从世界坐标系到该坐标系)
        try:
            # 提取旋转和缩放部分
            rot_scale = self.to_world_matrix[:2, :2]
            # 计算逆矩阵
            rot_scale_inv = np.linalg.inv(rot_scale)
            # 计算平移部分
            origin = np.array([self.origin_x, self.origin_y])
            origin_inv = -np.dot(rot_scale_inv, origin)
            
            # 构建逆矩阵
            self.from_world_matrix = np.array([
                [rot_scale_inv[0, 0], rot_scale_inv[0, 1], origin_inv[0]],
                [rot_scale_inv[1, 0], rot_scale_inv[1, 1], origin_inv[1]],
                [0, 0, 1]
            ])
        except np.linalg.LinAlgError:
            # 如果矩阵不可逆，使用伪逆
            self.from_world_matrix = np.linalg.pinv(self.to_world_matrix)
    
    def point_to_world(self, x, y):
        """
        将该坐标系中的点转换到世界坐标系
        
        参数:
        x (float): 点的X坐标
        y (float): 点的Y坐标
        
        返回:
        tuple: 转换后的点坐标 (wx, wy)
        """
        point = np.array([x, y, 1])
        world_point = np.dot(self.to_world_matrix, point)
        return (world_point[0], world_point[1])
    
    def point_from_world(self, wx, wy):
        """
        将世界坐标系中的点转换到该坐标系
        
        参数:
        wx (float): 世界坐标系中点的X坐标
        wy (float): 世界坐标系中点的Y坐标
        
        返回:
        tuple: 转换后的点坐标 (x, y)
        """
        world_point = np.array([wx, wy, 1])
        point = np.dot(self.from_world_matrix, world_point)
        return (point[0], point[1])
    
    def transform_point(self, x, y, target_system):
        """
        将该坐标系中的点转换到目标坐标系
        
        参数:
        x (float): 点的X坐标
        y (float): 点的Y坐标
        target_system (CoordinateSystem): 目标坐标系
        
        返回:
        tuple: 转换后的点坐标 (tx, ty)
        """
        # 先转换到世界坐标系
        wx, wy = self.point_to_world(x, y)
        # 再从世界坐标系转换到目标坐标系
        return target_system.point_from_world(wx, wy)
    
    def draw(self, ax, show_label=True):
        """
        在Matplotlib轴上绘制坐标系
        
        参数:
        ax (matplotlib.axes.Axes): Matplotlib轴对象
        show_label (bool): 是否显示标签
        """
        # ✅ 修改：增加坐标轴长度倍数
        axis_length_multiplier = 3.0  # 将坐标轴长度放大 3 倍
        
        # 绘制原点 - 使原点可点击
        origin_scatter = ax.scatter(self.origin_x, self.origin_y, color=self.color, s=100, 
                                   edgecolor='black', linewidth=1, zorder=10)
        origin_scatter.set_picker(True)
        origin_scatter.set_pickradius(5)
        origin_scatter.set_gid(f"origin_{self.name}")
        
        # 计算轴的终点 - ✅ 使用放大倍数
        x_axis_end = (self.origin_x + self.x_scale * axis_length_multiplier * math.cos(math.radians(self.x_angle)),
                      self.origin_y + self.x_scale * axis_length_multiplier * math.sin(math.radians(self.x_angle)))
        y_axis_end = (self.origin_x + self.y_scale * axis_length_multiplier * math.cos(math.radians(self.y_angle)),
                      self.origin_y + self.y_scale * axis_length_multiplier * math.sin(math.radians(self.y_angle)))
        
        # 绘制 X 轴
        x_axis_line = ax.plot([self.origin_x, x_axis_end[0]], [self.origin_y, x_axis_end[1]], '-', 
                color=self.color, linewidth=2)
        x_axis_line[0].set_gid(f"x_axis_{self.name}")
        
        # 绘制 Y 轴
        y_axis_line = ax.plot([self.origin_x, y_axis_end[0]], [self.origin_y, y_axis_end[1]], '-', 
                color=self.color, linewidth=2)
        y_axis_line[0].set_gid(f"y_axis_{self.name}")
        
        # 绘制箭头 - ✅ 使用放大后的终点
        ax.arrow(self.origin_x, self.origin_y, 
                x_axis_end[0] - self.origin_x, x_axis_end[1] - self.origin_y,
                head_width=0.1, head_length=0.1, fc=self.color, ec=self.color)
        ax.arrow(self.origin_x, self.origin_y, 
                y_axis_end[0] - self.origin_x, y_axis_end[1] - self.origin_y,
                head_width=0.1, head_length=0.1, fc=self.color, ec=self.color)
        
        # 显示标签
        if show_label:
            ax.text(x_axis_end[0] + 0.1, x_axis_end[1] + 0.1, f'{self.name}-X', 
                   color=self.color, fontsize=9)
            ax.text(y_axis_end[0] + 0.1, y_axis_end[1] + 0.1, f'{self.name}-Y', 
                   color=self.color, fontsize=9)
            # ax.text(self.origin_x - 0.3, self.origin_y - 0.3, self.name, 
            #        color=self.color, fontweight='bold', fontsize=10)
    
    def update_parameters(self, origin_x=None, origin_y=None, x_angle=None, y_angle=None, 
                         x_scale=None, y_scale=None, color=None):
        """
        更新坐标系参数
        
        参数:
        origin_x (float, optional): 新的原点X坐标
        origin_y (float, optional): 新的原点Y坐标
        x_angle (float, optional): 新的X轴角度
        y_angle (float, optional): 新的Y轴角度
        x_scale (float, optional): 新的X轴比例因子
        y_scale (float, optional): 新的Y轴比例因子
        color (str, optional): 新的颜色
        """
        if origin_x is not None:
            self.origin_x = origin_x
        if origin_y is not None:
            self.origin_y = origin_y
        if x_angle is not None:
            self.x_angle = x_angle
        if y_angle is not None:
            self.y_angle = y_angle
        if x_scale is not None:
            self.x_scale = x_scale
        if y_scale is not None:
            self.y_scale = y_scale
        if color is not None:
            self.color = color
        
        # 更新转换矩阵
        self.update_transform_matrix()
    
    def get_parameters(self):
        """
        获取坐标系参数
        
        返回:
        dict: 包含所有参数的字典
        """
        return {
            'name': self.name,
            'origin_x': self.origin_x,
            'origin_y': self.origin_y,
            'x_angle': self.x_angle,
            'y_angle': self.y_angle,
            'x_scale': self.x_scale,
            'y_scale': self.y_scale,
            'color': self.color
        }