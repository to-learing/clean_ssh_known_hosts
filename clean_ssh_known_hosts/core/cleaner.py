#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心清理模块
包含SSH known_hosts文件清理的核心逻辑
"""

import os

from ..config import REMOVE_EMPTY_LINES
from ..utils.path_utils import get_known_hosts_path
from ..utils.logger import get_logger

# 全局缓存
_cleaned_files_cache = {}
_ip_match_cache = {}


class KnownHostsCleaner:
    """
    SSH known_hosts 清理器类
    提供清理指定IP地址的SSH连接记录功能
    """
    
    def __init__(self, known_hosts_path=None, target_ips=None, remove_empty_lines=None):
        """
        初始化清理器
        
        Args:
            known_hosts_path: known_hosts文件路径，如果为None则自动检测
            target_ips: 需要删除的IP地址列表
            remove_empty_lines: 是否删除空行，默认使用配置中的值
        """
        self.logger = get_logger()
        self.known_hosts_path = known_hosts_path or get_known_hosts_path()
        self.target_ips = target_ips or []
        self.remove_empty_lines = remove_empty_lines if remove_empty_lines is not None else REMOVE_EMPTY_LINES
    
    def clean(self):
        """
        执行清理操作
        
        Returns:
            tuple: (是否成功, 删除的记录数, 错误信息)
        """
        self.logger.info(f"开始清理known_hosts文件: {self.known_hosts_path}")
        self.logger.info(f"目标IP地址: {self.target_ips}")
        
        # 检查文件是否存在
        if not os.path.exists(self.known_hosts_path):
            message = f"known_hosts文件不存在: {self.known_hosts_path}"
            self.logger.info(message)
            return True, 0, message
        
        # 读取文件内容
        try:
            with open(self.known_hosts_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            error_message = f"读取known_hosts文件失败: {e}"
            self.logger.error(error_message)
            return False, 0, error_message
        
        # 处理每一行
        new_lines = []
        removed_count = 0
        empty_lines_removed = 0
        
        for line in lines:
            line_stripped = line.strip()
            
            # 处理空行
            if not line_stripped:
                if self.remove_empty_lines:
                    empty_lines_removed += 1
                    continue
                else:
                    new_lines.append(line)
                    continue
            
            # 处理注释行
            if line_stripped.startswith('#'):
                new_lines.append(line)
                continue
            
            # 解析主机部分
            parts = line_stripped.split()
            if not parts:
                new_lines.append(line)
                continue
            
            # 处理 @cert-authority 或 @revoked 前缀
            # 这些标记是独立的字段，不是主机名的一部分
            host_part_index = 0
            if len(parts) > 0 and parts[0].startswith('@'):
                # @cert-authority 或 @revoked 是独立的标记，主机名在下一个字段
                if len(parts) > 1:
                    host_part_index = 1
            
            host_part = parts[host_part_index]
            hosts = host_part.split(',')
            
            # 检查是否需要删除
            should_remove = False
            for host in hosts:
                host = host.strip()
                # 处理可能的前缀（如 @cert-authority）
                # 注意：这是旧格式的处理，新格式中 @cert-authority 是独立字段
                if '@' in host:
                    host = host.split('@')[-1]
                # 处理可能的方括号（用于包含端口号的格式，如 [192.168.1.1]:2222）
                if host.startswith('[') and ']' in host:
                    # 提取方括号内的内容
                    host = host[1:host.index(']')]
                # 处理可能的端口号
                if ':' in host:
                    host = host.split(':')[0]
                
                # 使用缓存优化匹配
                cache_key = f"{host}:{','.join(self.target_ips)}"
                if cache_key in _ip_match_cache:
                    should_remove = _ip_match_cache[cache_key]
                else:
                    should_remove = host in self.target_ips
                    _ip_match_cache[cache_key] = should_remove
                
                if should_remove:
                    break
            
            if should_remove:
                removed_count += 1
                self.logger.info(f"已删除: {line_stripped[:80]}...")
            else:
                new_lines.append(line)
        
        # 写入处理后的内容
        if removed_count > 0 or empty_lines_removed > 0:
            # 计算总删除数量
            total_removed = removed_count + empty_lines_removed
            
            # 检查缓存，避免重复写入
            file_cache_key = self.known_hosts_path
            if file_cache_key in _cleaned_files_cache:
                cached_count = _cleaned_files_cache[file_cache_key]
                if cached_count == removed_count:
                    self.logger.info(f"文件已处理过，跳过写入: {self.known_hosts_path}")
                    return True, total_removed, None
            
            try:
                with open(self.known_hosts_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                
                _cleaned_files_cache[file_cache_key] = removed_count
                
                if self.remove_empty_lines:
                    self.logger.info(f"清理完成！共删除 {removed_count} 条记录，{empty_lines_removed} 个空行。")
                else:
                    self.logger.info(f"清理完成！共删除 {removed_count} 条记录。")
                
                return True, total_removed, None
            except Exception as e:
                error_message = f"写入known_hosts文件失败: {e}"
                self.logger.error(error_message)
                return False, 0, error_message
        
        message = "清理完成！未找到需要删除的记录。"
        self.logger.info(message)
        return True, 0, message
    
    def add_target_ip(self, ip):
        """
        添加目标IP地址
        
        Args:
            ip: IP地址
        """
        if ip not in self.target_ips:
            self.target_ips.append(ip)
            self.logger.info(f"添加目标IP: {ip}")
    
    def remove_target_ip(self, ip):
        """
        移除目标IP地址
        
        Args:
            ip: IP地址
        """
        if ip in self.target_ips:
            self.target_ips.remove(ip)
            self.logger.info(f"移除目标IP: {ip}")
    
    def set_target_ips(self, ips):
        """
        设置目标IP地址列表
        
        Args:
            ips: IP地址列表
        """
        self.target_ips = ips
        self.logger.info(f"设置目标IP列表: {ips}")
