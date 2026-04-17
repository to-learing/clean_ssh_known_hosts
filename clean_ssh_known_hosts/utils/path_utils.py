#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路径处理工具模块
提供跨平台的路径处理功能
"""

import os
import sys
from pathlib import Path

# 路径缓存
_path_cache = {}
_os_type_cache = None


def get_os_type():
    """
    获取操作系统类型
    
    Returns:
        str: 操作系统类型，可能值为 'windows', 'linux', 'darwin' (macOS), 'other'
    """
    global _os_type_cache
    
    if _os_type_cache is not None:
        return _os_type_cache
    
    platform = sys.platform
    if platform.startswith('win'):
        _os_type_cache = 'windows'
    elif platform.startswith('linux'):
        _os_type_cache = 'linux'
    elif platform == 'darwin':
        _os_type_cache = 'darwin'
    else:
        _os_type_cache = 'other'
    
    return _os_type_cache


def get_known_hosts_path(custom_path=None):
    """
    获取SSH known_hosts文件路径
    支持跨平台路径检测
    
    Args:
        custom_path: 自定义路径，如果提供则直接使用
    
    Returns:
        str: known_hosts文件的绝对路径
    """
    # 如果提供了自定义路径，直接使用
    if custom_path:
        return os.path.abspath(custom_path)
    
    # 检查缓存
    cache_key = "known_hosts_default"
    if cache_key in _path_cache:
        return _path_cache[cache_key]
    
    os_type = get_os_type()
    home_dir = os.path.expanduser("~")
    
    # 根据操作系统类型构建路径
    if os_type == 'windows':
        # Windows系统，SSH目录通常在用户目录下的.ssh文件夹
        ssh_dir = os.path.join(home_dir, ".ssh")
    else:
        # Linux和macOS系统
        ssh_dir = os.path.join(home_dir, ".ssh")
    
    # 确保使用正确的路径分隔符
    known_hosts_path = os.path.join(ssh_dir, "known_hosts")
    
    # 缓存路径
    _path_cache[cache_key] = known_hosts_path
    
    return known_hosts_path


def ensure_directory_exists(path):
    """
    确保目录存在，如果不存在则创建
    
    Args:
        path: 目录路径
    
    Returns:
        bool: 是否成功确保目录存在
    """
    try:
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        print(f"创建目录失败: {e}")
        return False


def get_file_size(file_path):
    """
    获取文件大小（字节）
    
    Args:
        file_path: 文件路径
    
    Returns:
        int: 文件大小（字节），如果文件不存在则返回0
    """
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return os.path.getsize(file_path)
    return 0


def is_file_writable(file_path):
    """
    检查文件是否可写
    
    Args:
        file_path: 文件路径
    
    Returns:
        bool: 文件是否可写
    """
    if os.path.exists(file_path):
        return os.access(file_path, os.W_OK)
    else:
        # 如果文件不存在，检查父目录是否可写
        parent_dir = os.path.dirname(file_path)
        if parent_dir and os.path.exists(parent_dir):
            return os.access(parent_dir, os.W_OK)
        return False


def normalize_path(path):
    """
    规范化路径，处理斜杠、相对路径等
    
    Args:
        path: 原始路径
    
    Returns:
        str: 规范化后的绝对路径
    """
    # 检查缓存
    if path in _path_cache:
        return _path_cache[path]
    
    # 扩展用户目录符号（如 ~）
    path = os.path.expanduser(path)
    # 规范化路径
    path = os.path.normpath(path)
    # 转换为绝对路径
    path = os.path.abspath(path)
    
    # 缓存结果
    _path_cache[path] = path
    
    return path
