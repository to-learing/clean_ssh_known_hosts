#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置模块
包含SSH known_hosts清理工具的所有配置项
"""

import os

# 基础目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 日志配置
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "ssh_cleaner.log")
LOG_MAX_DAYS = 14  # 日志保留最大天数（2个星期）
LOG_LEVEL = "INFO"  # 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL

# SSH known_hosts 配置
# 可以根据操作系统类型设置不同的默认路径，也可以手动指定
KNOWN_HOSTS_PATH = None  # 如果为None，则自动检测

# 需要删除的IP地址列表
TARGET_IPS = [
    "127.0.0.1"
]

# 清理选项
REMOVE_EMPTY_LINES = True  # 是否删除known_hosts文件中的空行
