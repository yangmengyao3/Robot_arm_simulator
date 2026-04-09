"""
点管理器模块
用于管理坐标点及其相关操作
"""

import csv


class PointManager:
    """点管理器类，用于管理坐标点"""
    
    def __init__(self):
        """初始化点管理器"""
        self.points = {}
        self.current_system = None
    
    def add_point(self, name, x, y, system_name, angle=0.0):
        """
        添加点
        
        参数:
        name (str): 点名称
        x (float): 点的X坐标
        y (float): 点的Y坐标
        system_name (str): 坐标系名称
        angle (float, optional): 角度信息，默认为0.0
        """
        self.points[name] = {
            'x': x,
            'y': y,
            'angle': angle,
            'system': system_name
        }
    
    def remove_point(self, name):
        """
        移除点
        
        参数:
        name (str): 点名称
        """
        if name in self.points:
            del self.points[name]
    
    def update_point(self, name, x, y, system_name=None, angle=None):
        """
        更新点
        
        参数:
        name (str): 点名称
        x (float): 新的X坐标
        y (float): 新的Y坐标
        system_name (str, optional): 新的坐标系名称
        """
        if name in self.points:
            self.points[name]['x'] = x
            self.points[name]['y'] = y
            if system_name is not None:
                self.points[name]['system'] = system_name
            if angle is not None:
                self.points[name]['angle'] = angle
    
    def get_point(self, name):
        """
        获取点信息
        
        参数:
        name (str): 点名称
        
        返回:
        dict: 点信息，包含 x, y, system
        """
        if name in self.points:
            return self.points[name].copy()
        return None
    
    def get_all_points(self):
        """
        获取所有点
        
        返回:
        dict: 所有点的字典
        """
        return self.points.copy()
    
    def get_points_by_system(self, system_name):
        """
        获取指定坐标系中的所有点
        
        参数:
        system_name (str): 坐标系名称
        
        返回:
        dict: 该坐标系中的所有点
        """
        return {name: point for name, point in self.points.items() 
                if point['system'] == system_name}
    
    def set_current_system(self, system_name):
        """
        设置当前坐标系
        
        参数:
        system_name (str): 坐标系名称
        """
        self.current_system = system_name
    
    def get_current_system(self):
        """
        获取当前坐标系
        
        返回:
        str: 当前坐标系名称
        """
        return self.current_system
    
    def clear_points(self):
        """清空所有点"""
        self.points.clear()
    
    def export_points(self, filename, system_name=None):
        """
        导出点到CSV文件
        
        参数:
        filename (str): 文件名
        system_name (str, optional): 导出的坐标系名称，None表示导出所有点
        """
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['name', 'x', 'y', 'system']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            # 如果指定了坐标系，只导出该坐标系的点
            if system_name:
                points_to_export = self.get_points_by_system(system_name)
            else:
                points_to_export = self.points
            
            for name, point in points_to_export.items():
                row = {
                    'name': name,
                    'x': point['x'],
                    'y': point['y'],
                    'system': point['system']
                }
                writer.writerow(row)
    
    def import_points(self, filename, transformer=None, target_system=None):
        """
        从CSV文件导入点
        
        参数:
        filename (str): 文件名
        transformer (CoordinateTransformer, optional): 坐标转换器，用于转换坐标系
        target_system (str, optional): 目标坐标系名称
        
        返回:
        int: 导入的点数量
        """
        count = 0
        try:
            with open(filename, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    name = row['name']
                    x = float(row['x'])
                    y = float(row['y'])
                    system = row['system']
                    
                    # 如果提供了转换器和目标坐标系，进行坐标转换
                    if transformer and target_system and system != target_system:
                        try:
                            x, y = transformer.transform_point(x, y, system, target_system)
                            system = target_system
                        except ValueError:
                            # 如果转换失败，使用原始坐标
                            pass
                    
                    self.add_point(name, x, y, system)
                    count += 1
            return count
        except Exception as e:
            raise Exception(f"导入点失败: {str(e)}")