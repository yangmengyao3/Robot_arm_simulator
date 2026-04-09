"""
坐标转换器模块
用于处理不同坐标系之间的点转换
"""


class CoordinateTransformer:
    """坐标转换器类，用于处理坐标系间的点转换"""
    
    def __init__(self):
        """初始化坐标转换器"""
        self.coordinate_systems = {}
        self.mechanical_system = None  # 机械坐标系引用
    
    def add_coordinate_system(self, system):
        """
        添加坐标系
        
        参数:
        system (CoordinateSystem): 要添加的坐标系
        """
        self.coordinate_systems[system.name] = system
        
        # 如果是机械坐标系，保存引用
        if system.name == "机械坐标系":
            self.mechanical_system = system
    
    def remove_coordinate_system(self, name):
        """
        移除坐标系
        
        参数:
        name (str): 要移除的坐标系名称
        """
        if name in self.coordinate_systems:
            # 如果是机械坐标系，清除引用
            if name == "机械坐标系":
                self.mechanical_system = None
            del self.coordinate_systems[name]
    
    def get_coordinate_system(self, name):
        """
        获取坐标系
        
        参数:
        name (str): 坐标系名称
        
        返回:
        CoordinateSystem: 坐标系对象，如果不存在则返回None
        """
        return self.coordinate_systems.get(name)
    
    def get_all_coordinate_systems(self):
        """
        获取所有坐标系
        
        返回:
        dict: 所有坐标系的字典
        """
        return self.coordinate_systems.copy()
    
    def transform_point(self, x, y, angle, source_name, target_name ):
        """
        将点从源坐标系转换到目标坐标系
        
        参数:
        x (float): 点的X坐标
        y (float): 点的Y坐标
        source_name (str): 源坐标系名称
        target_name (str): 目标坐标系名称
        angle (float, optional): 角度信息，如果提供则也会进行转换
        
        返回:
        tuple: 转换后的点坐标 (tx, ty) 或 (tx, ty, ta) 如果提供了角度
        
        异常:
        ValueError: 当源坐标系或目标坐标系不存在时抛出
        """
        if source_name not in self.coordinate_systems:
            raise ValueError(f"源坐标系 '{source_name}' 不存在")
        
        if target_name not in self.coordinate_systems:
            raise ValueError(f"目标坐标系 '{target_name}' 不存在")
        
        source_system = self.coordinate_systems[source_name]
        target_system = self.coordinate_systems[target_name]
        
        result = source_system.transform_point(x, y, target_system)
        
        # 如果提供了角度信息，计算角度差
        if angle is not None:
            # 计算两个坐标系之间的角度差
            angle_diff = target_system.x_angle - source_system.x_angle
            transformed_angle = angle + angle_diff
            # 标准化角度到 -360 到 360 范围
            while transformed_angle > 360:
                transformed_angle -= 360
            while transformed_angle < -360:
                transformed_angle += 360
            return (result[0], result[1], transformed_angle)
        
        return result
    
    # def transform_points(self, points, source_name, target_name):
    #     """
    #     批量转换点
        
    #     参数:
    #     points (list): 点列表，每个点为 (x, y) 元组
    #     source_name (str): 源坐标系名称
    #     target_name (str): 目标坐标系名称
        
    #     返回:
    #     list: 转换后的点列表
    #     """
    #     return [self.transform_point(x, y, source_name, target_name) for x, y in points]
    
    def image_to_mechanical(self, x, y, angle, image_system_name):
        """
        将图像坐标系中的点转换到机械坐标系
        
        参数:
        x (float): 点的X坐标
        y (float): 点的Y坐标
        image_system_name (str): 图像坐标系名称
        
        返回:
        tuple: 机械坐标系中的点坐标 (mx, my)
        
        异常:
        ValueError: 当图像坐标系或机械坐标系不存在时抛出
        """
        if not self.mechanical_system:
            raise ValueError("机械坐标系不存在")
        
        return self.transform_point(x, y, angle, source_name=image_system_name, target_name="机械坐标系")
    
    def mechanical_to_image(self, mx, my, angle, image_system_name):
        """
        将机械坐标系中的点转换到图像坐标系
        
        参数:
        mx (float): 机械坐标系中的X坐标
        my (float): 机械坐标系中的Y坐标
        image_system_name (str): 图像坐标系名称
        
        返回:
        tuple: 图像坐标系中的点坐标 (x, y)
        
        异常:
        ValueError: 当图像坐标系或机械坐标系不存在时抛出
        """
        if not self.mechanical_system:
            raise ValueError("机械坐标系不存在")
        
        return self.transform_point(mx, my, angle, "机械坐标系", image_system_name)
    
    def get_system_names(self):
        """
        获取所有坐标系名称
        
        返回:
        list: 坐标系名称列表
        """
        return list(self.coordinate_systems.keys())
    
    def get_image_system_names(self):
        """
        获取所有图像坐标系名称（不包括世界坐标系和机械坐标系）
        
        返回:
        list: 图像坐标系名称列表
        """
        return [name for name in self.coordinate_systems.keys() 
                if name not in ["世界坐标系", "机械坐标系"]]