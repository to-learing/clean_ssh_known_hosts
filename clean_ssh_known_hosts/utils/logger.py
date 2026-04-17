#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志记录工具模块
提供日志记录功能，支持文件保存和自动清理旧日志
"""

import os
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timedelta

from ..config import LOG_DIR, LOG_FILE, LOG_MAX_DAYS, LOG_LEVEL

# 日志记录器缓存
_logger_cache = {}


def setup_logger(name="ssh_cleaner"):
    """
    配置日志记录器
    
    Args:
        name: 日志记录器名称
    
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 检查缓存
    if name in _logger_cache:
        return _logger_cache[name]
    
    # 确保日志目录存在
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR, exist_ok=True)
    
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL.upper()))
    
    # 避免重复添加处理器
    if logger.handlers:
        _logger_cache[name] = logger
        return logger
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, LOG_LEVEL.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 创建文件处理器（按天滚动）
    file_handler = TimedRotatingFileHandler(
        LOG_FILE,
        when='midnight',  # 每天午夜滚动
        interval=1,        # 间隔1天
        backupCount=LOG_MAX_DAYS,  # 保留的备份文件数量
        encoding='utf-8',
        delay=False
    )
    file_handler.setLevel(getattr(logging, LOG_LEVEL.upper()))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 清理超过保留天数的旧日志文件
    cleanup_old_logs()
    
    # 缓存日志记录器
    _logger_cache[name] = logger
    
    return logger


def cleanup_old_logs():
    """
    清理超过保留天数的旧日志文件
    """
    if not os.path.exists(LOG_DIR):
        return
    
    # 计算截止日期
    cutoff_date = datetime.now() - timedelta(days=LOG_MAX_DAYS)
    
    # 遍历日志目录中的文件
    for filename in os.listdir(LOG_DIR):
        file_path = os.path.join(LOG_DIR, filename)
        
        # 只处理文件，不处理目录
        if not os.path.isfile(file_path):
            continue
        
        # 检查文件修改时间
        try:
            file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
            # 只删除.log文件，保留备份文件
            if file_mtime < cutoff_date and filename.endswith('.log'):
                os.remove(file_path)
                print(f"已删除旧日志文件: {filename}")
        except Exception as e:
            print(f"处理日志文件时出错: {e}")


def get_logger(name="ssh_cleaner"):
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称
    
    Returns:
        logging.Logger: 日志记录器
    """
    return logging.getLogger(name)
