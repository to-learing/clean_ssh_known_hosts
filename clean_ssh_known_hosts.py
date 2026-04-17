#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSH known_hosts 清理工具
用于自动删除指定IP的SSH连接记录
"""

import os
import sys


# 配置：需要删除的IP地址列表
TARGET_IPS = [
    "127.0.0.1"
]


def get_known_hosts_path():
    """获取SSH known_hosts文件路径"""
    home_dir = os.path.expanduser("~")
    ssh_dir = os.path.join(home_dir, ".ssh")
    known_hosts_path = os.path.join(ssh_dir, "known_hosts")
    return known_hosts_path


def clean_known_hosts(target_ips):
    """
    清理known_hosts文件中指定IP的记录
    
    Args:
        target_ips: 需要删除的IP地址列表
    
    Returns:
        tuple: (是否成功, 删除的记录数, 错误信息)
    """
    known_hosts_path = get_known_hosts_path()
    
    if not os.path.exists(known_hosts_path):
        return True, 0, f"known_hosts文件不存在: {known_hosts_path}"
    
    try:
        with open(known_hosts_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        return False, 0, f"读取known_hosts文件失败: {e}"
    
    new_lines = []
    removed_count = 0
    
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped or line_stripped.startswith('#'):
            new_lines.append(line)
            continue
        
        parts = line_stripped.split()
        if not parts:
            new_lines.append(line)
            continue
        
        host_part = parts[0]
        hosts = host_part.split(',')
        
        should_remove = False
        for host in hosts:
            host = host.strip()
            if '@' in host:
                host = host.split('@')[-1]
            if ':' in host:
                host = host.split(':')[0]
            
            if host in target_ips:
                should_remove = True
                break
        
        if should_remove:
            removed_count += 1
            print(f"  已删除: {line_stripped[:80]}...")
        else:
            new_lines.append(line)
    
    if removed_count > 0:
        try:
            with open(known_hosts_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            return True, removed_count, None
        except Exception as e:
            return False, 0, f"写入known_hosts文件失败: {e}"
    
    return True, 0, None


def main():
    """主函数"""
    print("=" * 60)
    print("SSH known_hosts 清理工具")
    print("=" * 60)
    
    known_hosts_path = get_known_hosts_path()
    print(f"\nknown_hosts文件路径: {known_hosts_path}")
    
    print("\n目标IP地址:")
    for ip in TARGET_IPS:
        print(f"  - {ip}")
    
    print("\n开始清理...")
    success, removed_count, error = clean_known_hosts(TARGET_IPS)
    
    if not success:
        print(f"\n错误: {error}")
        sys.exit(1)
    
    if removed_count > 0:
        print(f"\n清理完成！共删除 {removed_count} 条记录。")
    else:
        print("\n清理完成！未找到需要删除的记录。")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
