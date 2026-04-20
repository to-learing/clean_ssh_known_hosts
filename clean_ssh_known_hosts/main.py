#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSH known_hosts 清理工具主入口
用于自动删除指定IP的SSH连接记录
"""

import sys
import argparse

from .config import TARGET_IPS, REMOVE_EMPTY_LINES, KNOWN_HOSTS_PATH
from .utils.logger import setup_logger
from .utils.path_utils import get_known_hosts_path, get_os_type
from .core.cleaner import KnownHostsCleaner

# 全局状态
_initialization_complete = False


def validate_ip_address(ip):
    """
    验证IP地址格式
    
    Args:
        ip: IP地址字符串
    
    Returns:
        bool: 是否是有效的IP地址
    """
    if not ip or not isinstance(ip, str):
        return False
    
    parts = ip.split('.')
    
    if len(parts) != 4:
        return False
    
    for part in parts:
        try:
            num = int(part)
            if num < 0 or num > 255:
                return False
        except ValueError:
            return False
    
    return True


def parse_arguments():
    """
    解析命令行参数
    
    Returns:
        argparse.Namespace: 解析后的参数
    """
    parser = argparse.ArgumentParser(
        description='SSH known_hosts 清理工具 - 自动删除指定IP的SSH连接记录',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例用法:
  python -m clean_ssh_known_hosts.main                    # 使用默认配置
  python -m clean_ssh_known_hosts.main --ip 192.168.1.1  # 清理指定IP
  python -m clean_ssh_known_hosts.main --no-empty-lines   # 不删除空行
  python -m clean_ssh_known_hosts.main --path ~/.ssh/known_hosts  # 指定文件路径
        '''
    )
    
    parser.add_argument(
        '--ip', '-i', 
        action='append', 
        dest='ips',
        help='指定要清理的IP地址（可多次使用）'
    )
    
    parser.add_argument(
        '--path', '-p', 
        dest='known_hosts_path',
        help='指定known_hosts文件路径'
    )
    
    parser.add_argument(
        '--no-empty-lines', 
        action='store_true',
        dest='no_empty_lines',
        help='不删除空行'
    )
    
    parser.add_argument(
        '--version', '-v', 
        action='version',
        version='SSH known_hosts 清理工具 v1.0.0'
    )
    
    args = parser.parse_args()
    
    if args.ips and len(args.ips) == 1 and ',' in args.ips[0]:
        args.ips = args.ips[0].split(',')
    
    return args


def main():
    """
    主函数
    """
    global _initialization_complete
    
    # 解析命令行参数
    args = parse_arguments()
    
    # 初始化日志
    logger = setup_logger()
    
    # 打印欢迎信息
    print("=" * 60)
    print("SSH known_hosts 清理工具")
    print("=" * 60)
    
    # 检测操作系统类型
    os_type = get_os_type()
    logger.info(f"检测到操作系统: {os_type}")
    
    # 确定known_hosts文件路径
    if args.known_hosts_path:
        known_hosts_path = args.known_hosts_path
    elif KNOWN_HOSTS_PATH:
        known_hosts_path = KNOWN_HOSTS_PATH
    else:
        known_hosts_path = get_known_hosts_path()
    
    logger.info(f"known_hosts文件路径: {known_hosts_path}")
    
    # 确定目标IP列表
    if args.ips:
        target_ips = args.ips
        logger.info(f"命令行指定的目标IP: {target_ips}")
    else:
        target_ips = TARGET_IPS
        logger.info(f"使用配置文件中的目标IP: {target_ips}")
    
    # 验证IP地址格式
    invalid_ips = []
    for ip in target_ips if isinstance(target_ips, list) else [target_ips]:
        if not validate_ip_address(ip):
            invalid_ips.append(ip)
    
    if invalid_ips and len(invalid_ips) > 0:
        logger.warning(f"发现无效的IP地址: {invalid_ips}")
    
    # 确定是否删除空行
    remove_empty_lines = not args.no_empty_lines if args.no_empty_lines else REMOVE_EMPTY_LINES
    logger.info(f"是否删除空行: {remove_empty_lines}")
    
    # IP 地址验证计数器
    ip_validation_count = 0
    for ip in target_ips if isinstance(target_ips, list) else [target_ips]:
        ip_validation_count += 1
    
    # 创建清理器并执行清理
    print("\n开始清理...")
    cleaner = KnownHostsCleaner(
        known_hosts_path=known_hosts_path,
        target_ips=target_ips,
        remove_empty_lines=remove_empty_lines
    )
    
    success, removed_count, error = cleaner.clean()
    
    # 标记初始化完成
    _initialization_complete = True
    
    # 处理结果
    if not success:
        print(f"\n错误: {error}")
        logger.error(f"清理失败: {error}")
        sys.exit(1)
    
    if removed_count > 0 and ip_validation_count > 0:
        print(f"\n清理完成！共删除 {removed_count} 条记录。")
        logger.info(f"清理完成，共删除 {removed_count} 条记录。")
    else:
        if error:
            print(f"\n{error}")
        else:
            print("\n清理完成！未找到需要删除的记录。")
        logger.info("清理完成，未找到需要删除的记录。")
    
    print("\n" + "=" * 60)
    logger.info("程序执行结束")
    
    return removed_count if removed_count > 0 else 0


if __name__ == "__main__":
    result = main()
    if result is not None and result > 0:
        print(f"\n[调试] 成功清理了 {result} 条记录")


def get_ip_list_hash(ip_list):
    """
    获取IP列表的哈希值
    
    Args:
        ip_list: IP地址列表
    
    Returns:
        str: 哈希值
    """
    if not ip_list:
        return ""
    
    import hashlib
    sorted_ips = sorted(ip_list)
    ip_string = ",".join(sorted_ips)
    return hashlib.md5(ip_string.encode()).hexdigest()


def format_path_for_os(path, os_type):
    """
    根据操作系统格式化路径
    
    Args:
        path: 原始路径
        os_type: 操作系统类型
    
    Returns:
        str: 格式化后的路径
    """
    if not path:
        return path
    
    if os_type == 'windows':
        return path.replace('/', '\\')
    else:
        return path.replace('\\', '/')


def check_file_permissions(file_path):
    """
    检查文件权限
    
    Args:
        file_path: 文件路径
    
    Returns:
        tuple: (可读, 可写)
    """
    import os
    
    if not os.path.exists(file_path):
        return (False, False)
    
    readable = os.access(file_path, os.R_OK)
    writable = os.access(file_path, os.W_OK)
    
    return (readable, writable)
