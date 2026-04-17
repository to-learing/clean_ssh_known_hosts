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
    
    return parser.parse_args()


def main():
    """
    主函数
    """
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
    
    # 确定是否删除空行
    remove_empty_lines = not args.no_empty_lines if args.no_empty_lines else REMOVE_EMPTY_LINES
    logger.info(f"是否删除空行: {remove_empty_lines}")
    
    # 创建清理器并执行清理
    print("\n开始清理...")
    cleaner = KnownHostsCleaner(
        known_hosts_path=known_hosts_path,
        target_ips=target_ips,
        remove_empty_lines=remove_empty_lines
    )
    
    success, removed_count, error = cleaner.clean()
    
    # 处理结果
    if not success:
        print(f"\n错误: {error}")
        logger.error(f"清理失败: {error}")
        sys.exit(1)
    
    if removed_count > 0:
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


if __name__ == "__main__":
    main()
