#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
调试脚本：用于重现和分析用户报告的问题
"""

import sys
import os
import json
import traceback

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtCore import Qt, QTimer

from main import RobotArmSimulator

class DebugRobotArmSimulator(RobotArmSimulator):
    """用于调试的机器人模拟器类"""
    
    def __init__(self):
        super().__init__()
        self.debug_timer = QTimer(self)
        self.debug_timer.timeout.connect(self.run_debug)
        self.debug_timer.start(3000)  # 3秒后开始调试
    
    def run_debug(self):
        """运行调试"""
        self.debug_timer.stop()
        
        try:
            print("\n" + "="*60)
            print("🐛 开始调试用户报告的问题...")
            print("="*60)
            
            # 调试1: 检查坐标转换面板
            self.debug_point_conversion_panel()
            
            # 调试2: 检查坐标系初始化
            self.debug_coordinate_systems()
            
            # 调试3: 测试场景加载
            self.debug_scene_loading()
            
            # 调试4: 测试添加点功能
            self.debug_add_point()
            
            print("\n" + "="*60)
            print("✅ 调试完成！")
            print("="*60)
            
        except Exception as e:
            error_msg = f"调试过程中出错: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            QMessageBox.critical(self, "调试错误", error_msg)
    
    def debug_point_conversion_panel(self):
        """调试坐标转换面板"""
        print("\n🔍 调试1: 检查坐标转换面板...")
        
        try:
            # 检查坐标转换面板是否存在
            if hasattr(self.control_panel, 'point_conversion_panel'):
                conversion_panel = self.control_panel.point_conversion_panel
                print("✅ 坐标转换面板存在")
                
                # 检查源坐标系下拉框
                source_count = conversion_panel.source_system_combo.count()
                target_count = conversion_panel.target_system_combo.count()
                
                print(f"📊 源坐标系下拉框项目数: {source_count}")
                print(f"📊 目标坐标系下拉框项目数: {target_count}")
                
                # 获取下拉框内容
                source_items = []
                target_items = []
                for i in range(source_count):
                    source_items.append(conversion_panel.source_system_combo.itemText(i))
                for i in range(target_count):
                    target_items.append(conversion_panel.target_system_combo.itemText(i))
                
                print(f"📋 源坐标系项目: {source_items}")
                print(f"📋 目标坐标系项目: {target_items}")
                
                if source_count == 0 or target_count == 0:
                    print("❌ 坐标系下拉框为空！")
                    # 尝试手动更新
                    print("🔧 尝试手动更新坐标系列表...")
                    system_names = self.transformer.get_system_names()
                    print(f"获取到的坐标系名称: {system_names}")
                    conversion_panel.update_system_list(system_names)
                    
                    # 重新检查
                    new_source_count = conversion_panel.source_system_combo.count()
                    new_target_count = conversion_panel.target_system_combo.count()
                    print(f"更新后源坐标系项目数: {new_source_count}")
                    print(f"更新后目标坐标系项目数: {new_target_count}")
                else:
                    print("✅ 坐标系下拉框不为空")
                    
            else:
                print("❌ 坐标转换面板不存在！")
                print(f"控制面板属性: {dir(self.control_panel)}")
                
        except Exception as e:
            print(f"❌ 调试坐标转换面板时出错: {str(e)}")
    
    def debug_coordinate_systems(self):
        """调试坐标系初始化"""
        print("\n🔍 调试2: 检查坐标系初始化...")
        
        try:
            # 获取所有坐标系
            all_systems = self.transformer.get_all_coordinate_systems()
            system_names = self.transformer.get_system_names()
            
            print(f"📊 坐标系总数: {len(all_systems)}")
            print(f"📋 坐标系名称列表: {system_names}")
            
            # 打印每个坐标系的详细信息
            for name, system in all_systems.items():
                print(f"📈 坐标系 '{name}': 原点=({system.origin_x}, {system.origin_y}), 角度=({system.x_angle}, {system.y_angle})")
            
            # 检查是否包含必要的坐标系
            required_systems = ["世界坐标系", "图像坐标系"]
            for system in required_systems:
                if system in system_names:
                    print(f"✅ 包含 '{system}'")
                else:
                    print(f"❌ 缺少 '{system}'")
                    
        except Exception as e:
            print(f"❌ 调试坐标系时出错: {str(e)}")
    
    def debug_scene_loading(self):
        """调试场景加载"""
        print("\n🔍 调试3: 测试场景加载...")
        
        try:
            # 创建一个简单的测试场景
            test_data = {
                "scene_name": "调试场景",
                "points": {
                    "测试点1": {"x": 10.0, "y": 20.0, "angle": 30.0, "system": "世界坐标系"},
                    "测试点2": {"x": 30.0, "y": 40.0, "angle": 60.0, "system": "图像坐标系"}
                },
                "robot_arm": {
                    "base_x": 0,
                    "base_y": 0,
                    "angle": 45,
                    "length": 2,
                    "color": "red"
                },
                "coordinate_systems": {
                    "世界坐标系": {
                        "origin_x": 0, "origin_y": 0, "x_angle": 0, 
                        "y_angle": 90, "x_scale": 1, "y_scale": 1, "color": "black"
                    },
                    "图像坐标系": {
                        "origin_x": 2, "origin_y": 2, "x_angle": 30, 
                        "y_angle": 120, "x_scale": 1.5, "y_scale": 1.5, "color": "blue"
                    }
                }
            }
            
            # 保存测试场景
            save_dir = os.path.join(os.path.expanduser("~"), ".robot_arm_simulator", "scenes")
            os.makedirs(save_dir, exist_ok=True)
            test_file_path = os.path.join(save_dir, "debug_scene.json")
            
            with open(test_file_path, 'w', encoding='utf-8') as f:
                json.dump(test_data, f, ensure_ascii=False, indent=2)
            
            print(f"📝 创建测试场景文件: {test_file_path}")
            
            # 尝试加载场景
            print("🔧 尝试加载测试场景...")
            success = self.load_data("debug_scene")
            
            if success:
                print("✅ 场景加载成功！")
                print(f"📊 加载后的点数量: {len(self.points)}")
                print(f"📊 加载后的坐标系数量: {len(self.transformer.get_all_coordinate_systems())}")
            else:
                print("❌ 场景加载失败！")
                
        except Exception as e:
            print(f"❌ 调试场景加载时出错: {str(e)}")
            traceback.print_exc()
    
    def debug_add_point(self):
        """调试添加点功能"""
        print("\n🔍 调试4: 测试添加点功能...")
        
        try:
            # 保存当前点数量
            current_points_count = len(self.points)
            print(f"📊 当前点数量: {current_points_count}")
            
            # 检查坐标转换面板
            if hasattr(self.control_panel, 'point_conversion_panel'):
                conversion_panel = self.control_panel.point_conversion_panel
                
                # 设置输入点
                conversion_panel.set_input_point(15.5, 25.5, 45.0)
                
                # 获取当前选中的坐标系
                source_system = conversion_panel.source_system_combo.currentText()
                print(f"📍 选中的源坐标系: {source_system}")
                
                # 尝试添加点
                print("🔧 尝试添加点...")
                self.on_add_point()
                
                # 检查点数量是否增加
                new_points_count = len(self.points)
                print(f"📊 添加后点数量: {new_points_count}")
                
                if new_points_count > current_points_count:
                    print("✅ 添加点功能正常！")
                    
                    # 检查批量转换表格
                    if hasattr(conversion_panel, 'point_table'):
                        table_row_count = conversion_panel.point_table.rowCount()
                        print(f"📊 批量转换表格行数: {table_row_count}")
                        
                        if table_row_count > 0:
                            print("✅ 批量转换表格已更新！")
                        else:
                            print("❌ 批量转换表格未更新！")
                    else:
                        print("❌ 批量转换表格不存在！")
                        
                else:
                    print("❌ 添加点后数量未增加！")
                    
            else:
                print("❌ 坐标转换面板不存在，无法测试添加点功能！")
                
        except Exception as e:
            print(f"❌ 调试添加点功能时出错: {str(e)}")
            traceback.print_exc()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置中文显示
    font = app.font()
    font.setFamily("SimHei")
    app.setFont(font)
    
    print("🚀 启动调试版本的工业机械臂运动模拟器...")
    print("⏳ 3秒后开始自动调试...")
    
    window = DebugRobotArmSimulator()
    window.show()
    
    sys.exit(app.exec_())