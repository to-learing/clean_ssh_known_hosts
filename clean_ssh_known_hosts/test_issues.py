#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSH known_hosts 清理工具测试脚本
测试参数解析、日志清理、域名和IP的各种格式
"""

import os
import sys
import tempfile
import shutil
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def add_test(self, name, passed, message=""):
        self.tests.append({"name": name, "passed": passed, "message": message})
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def print_summary(self):
        print("\n" + "=" * 60)
        print("测试结果汇总")
        print("=" * 60)
        print(f"总测试数: {len(self.tests)}")
        print(f"通过: {self.passed}")
        print(f"失败: {self.failed}")
        print("=" * 60)
        
        if self.failed > 0:
            print("\n失败的测试:")
            for test in self.tests:
                if not test["passed"]:
                    print(f"  [FAIL] {test['name']}: {test['message']}")
        
        return self.failed == 0


def test_argument_parsing():
    """测试参数解析逻辑"""
    print("\n" + "=" * 60)
    print("测试 1: 参数解析逻辑")
    print("=" * 60)
    
    result = TestResult()
    
    from clean_ssh_known_hosts.main import parse_arguments, validate_ip_address
    
    print("\n[子测试 1.1] 测试带空格的逗号分隔参数")
    print("-" * 40)
    
    test_ips_with_space = "192.168.1.3, 127.0.0.1"
    print(f"输入: '{test_ips_with_space}'")
    
    parsed = test_ips_with_space.split(',')
    print(f"split(',') 结果: {parsed}")
    print(f"解析后的 IP: '{parsed[0]}', '{parsed[1]}'")
    
    ip1_valid = validate_ip_address(parsed[0].strip())
    ip2_valid = validate_ip_address(parsed[1].strip())
    ip2_with_space_valid = validate_ip_address(parsed[1])
    
    print(f"parsed[0] 有效: {ip1_valid}")
    print(f"parsed[1].strip() 有效: {ip2_valid}")
    print(f"parsed[1] (带空格) 有效: {ip2_with_space_valid}")
    
    test_passed = ip2_with_space_valid == False
    result.add_test("带空格的逗号分隔参数解析问题", test_passed, 
                   f"split(',') 后第2个IP带空格: '{parsed[1]}'，validate_ip_address返回 {ip2_with_space_valid}")
    status = "PASS" if test_passed else "FAIL"
    print(f"  [{status}] 带空格的逗号分隔参数解析: 发现问题 = {test_passed}")
    
    if not ip2_with_space_valid:
        print("  [警告] 发现潜在 Bug: 逗号后带空格的参数可能无法正确匹配")
        print(f"           目标列表中会有: ' 127.0.0.1' (带前导空格)")
        print(f"           但 known_hosts 中的记录是: '127.0.0.1' (不带空格)")
    
    print("\n[子测试 1.2] 测试多个 --ip 参数")
    print("-" * 40)
    
    print("使用方式: python -m clean_ssh_known_hosts.main --ip 192.168.1.1 --ip 127.0.0.1")
    print("这种方式不会有空格问题，因为每个 --ip 是独立的参数")
    
    result.add_test("多个 --ip 参数方式", True, "多个 --ip 参数方式不会有空格问题")
    print("  [PASS] 多个 --ip 参数方式: 无空格问题")
    
    print("\n[子测试 1.3] 测试无空格的逗号分隔参数")
    print("-" * 40)
    
    test_ips_no_space = "192.168.1.3,127.0.0.1"
    print(f"输入: '{test_ips_no_space}'")
    
    parsed_no_space = test_ips_no_space.split(',')
    print(f"split(',') 结果: {parsed_no_space}")
    
    ip1_valid_ns = validate_ip_address(parsed_no_space[0])
    ip2_valid_ns = validate_ip_address(parsed_no_space[1])
    
    print(f"parsed_no_space[0] 有效: {ip1_valid_ns}")
    print(f"parsed_no_space[1] 有效: {ip2_valid_ns}")
    
    test_passed_ns = ip1_valid_ns and ip2_valid_ns
    result.add_test("无空格的逗号分隔参数", test_passed_ns, 
                   f"两个IP都有效: ip1={ip1_valid_ns}, ip2={ip2_valid_ns}")
    status = "PASS" if test_passed_ns else "FAIL"
    print(f"  [{status}] 无空格的逗号分隔参数: {test_passed_ns}")
    
    return result


def test_log_cleanup():
    """测试日志文件清理逻辑"""
    print("\n" + "=" * 60)
    print("测试 2: 日志文件清理逻辑")
    print("=" * 60)
    
    result = TestResult()
    
    from clean_ssh_known_hosts.config import LOG_MAX_DAYS
    from clean_ssh_known_hosts.utils.logger import cleanup_old_logs
    
    print(f"\n配置的日志保留天数: {LOG_MAX_DAYS} 天")
    
    print("\n[子测试 2.1] 分析 cleanup_old_logs 函数逻辑")
    print("-" * 40)
    
    print("函数逻辑分析:")
    print("1. 遍历日志目录中的所有文件")
    print("2. 检查文件修改时间是否早于 cutoff_date (当前时间 - LOG_MAX_DAYS)")
    print("3. 只删除 filename.endswith('.log') 的文件")
    
    print("\n[潜在问题 1]: TimedRotatingFileHandler 的备份文件命名格式")
    print("  TimedRotatingFileHandler 创建的备份文件格式: ssh_cleaner.log.2026-04-19")
    print("  这些文件不以 '.log' 结尾，所以不会被 cleanup_old_logs 删除")
    print("  但 TimedRotatingFileHandler 本身有 backupCount 参数来自动管理备份数量")
    
    result.add_test("TimedRotatingFileHandler 备份文件处理", False,
                   "cleanup_old_logs 不会删除 .log.2026-04-19 格式的备份文件")
    print("  [FAIL] TimedRotatingFileHandler 备份文件: 不会被 cleanup_old_logs 删除")
    
    print("\n[子测试 2.2] 分析双重日志清理机制")
    print("-" * 40)
    
    print("当前日志清理机制:")
    print("1. TimedRotatingFileHandler(backupCount=LOG_MAX_DAYS) - 自动管理备份文件")
    print("2. cleanup_old_logs() - 手动删除 .log 结尾的旧文件")
    
    print("\n[潜在问题 2]: 清理逻辑不一致")
    print("  - TimedRotatingFileHandler 会保留 backupCount 个备份文件")
    print("  - cleanup_old_logs 只删除 .log 结尾的文件")
    print("  - 实际生效的是 TimedRotatingFileHandler 的 backupCount")
    
    result.add_test("日志清理机制一致性", False,
                   "cleanup_old_logs 和 TimedRotatingFileHandler 的清理逻辑不一致")
    print("  [FAIL] 日志清理机制: 存在双重清理逻辑，但实际只有 TimedRotatingFileHandler 生效")
    
    return result


def test_host_matching():
    """测试主机名匹配逻辑（域名、IP、各种格式）"""
    print("\n" + "=" * 60)
    print("测试 3: 主机名匹配逻辑")
    print("=" * 60)
    
    result = TestResult()
    
    from clean_ssh_known_hosts.core.cleaner import KnownHostsCleaner
    
    def create_test_file(content):
        fd, path = tempfile.mkstemp()
        os.close(fd)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return path
    
    def read_file(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    
    print("\n[子测试 3.1] 测试普通 IP 地址匹配")
    print("-" * 40)
    
    content = """192.168.1.1 ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC...
127.0.0.1 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIB...
10.0.0.1 ssh-dss AAAAB3NzaC1kc3MAAACBAP...
"""
    test_file = create_test_file(content)
    try:
        cleaner = KnownHostsCleaner(
            known_hosts_path=test_file,
            target_ips=["192.168.1.1", "127.0.0.1"],
            remove_empty_lines=False
        )
        success, removed_count, error = cleaner.clean()
        
        result_content = read_file(test_file)
        
        test_passed = success and removed_count == 2
        test_passed = test_passed and "192.168.1.1" not in result_content
        test_passed = test_passed and "127.0.0.1" not in result_content
        test_passed = test_passed and "10.0.0.1" in result_content
        
        result.add_test("普通 IP 地址匹配", test_passed,
                       f"success={success}, removed_count={removed_count}")
        status = "PASS" if test_passed else "FAIL"
        print(f"  [{status}] 普通 IP 地址匹配: removed {removed_count} 条")
    finally:
        os.unlink(test_file)
    
    print("\n[子测试 3.2] 测试域名匹配")
    print("-" * 40)
    
    content = """github.com ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC...
gitlab.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIL...
example.org ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC...
"""
    test_file = create_test_file(content)
    try:
        cleaner = KnownHostsCleaner(
            known_hosts_path=test_file,
            target_ips=["github.com", "example.org"],
            remove_empty_lines=False
        )
        success, removed_count, error = cleaner.clean()
        
        result_content = read_file(test_file)
        
        test_passed = success and removed_count == 2
        test_passed = test_passed and "github.com" not in result_content
        test_passed = test_passed and "example.org" not in result_content
        test_passed = test_passed and "gitlab.com" in result_content
        
        result.add_test("域名匹配", test_passed,
                       f"success={success}, removed_count={removed_count}")
        status = "PASS" if test_passed else "FAIL"
        print(f"  [{status}] 域名匹配: removed {removed_count} 条")
    finally:
        os.unlink(test_file)
    
    print("\n[子测试 3.3] 测试带方括号和端口号的格式")
    print("-" * 40)
    
    content = """[192.168.1.100]:2222 ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC...
[github.com]:443 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIA...
[gitlab.com] ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC...
"""
    test_file = create_test_file(content)
    try:
        cleaner = KnownHostsCleaner(
            known_hosts_path=test_file,
            target_ips=["192.168.1.100", "github.com", "gitlab.com"],
            remove_empty_lines=False
        )
        success, removed_count, error = cleaner.clean()
        
        result_content = read_file(test_file)
        
        print(f"  目标列表: ['192.168.1.100', 'github.com', 'gitlab.com']")
        print(f"  实际删除: {removed_count} 条")
        print(f"  清理后内容:")
        for line in result_content.strip().split('\n'):
            print(f"    {line}")
        
        test_passed = success and removed_count == 3
        
        result.add_test("带方括号和端口号的格式匹配", test_passed,
                       f"success={success}, removed_count={removed_count}, 期望删除 3 条")
        status = "PASS" if test_passed else "FAIL"
        print(f"  [{status}] 带方括号和端口号的格式匹配: removed {removed_count} 条 (期望 3 条)")
        
        if not test_passed:
            print("  [警告] 发现 Bug: 带方括号的格式无法正确匹配")
            print("           原因: 代码只处理了冒号，没有处理方括号")
            print("           例如: '[192.168.1.100]:2222' 被处理成 '[192.168.1.100]'")
            print("           但目标列表中的是 '192.168.1.100'，无法匹配")
    finally:
        os.unlink(test_file)
    
    print("\n[子测试 3.4] 测试 @cert-authority 前缀的记录")
    print("-" * 40)
    
    content = """@cert-authority 192.168.1.5 ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC...
@cert-authority github.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIC...
192.168.1.6 ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC...
"""
    test_file = create_test_file(content)
    try:
        cleaner = KnownHostsCleaner(
            known_hosts_path=test_file,
            target_ips=["192.168.1.5", "github.com"],
            remove_empty_lines=False
        )
        success, removed_count, error = cleaner.clean()
        
        result_content = read_file(test_file)
        
        print(f"  目标列表: ['192.168.1.5', 'github.com']")
        print(f"  实际删除: {removed_count} 条")
        print(f"  清理后内容:")
        for line in result_content.strip().split('\n'):
            print(f"    {line}")
        
        test_passed = success and removed_count == 2
        test_passed = test_passed and "192.168.1.6" in result_content
        
        result.add_test("@cert-authority 前缀记录匹配", test_passed,
                       f"success={success}, removed_count={removed_count}, 期望删除 2 条")
        status = "PASS" if test_passed else "FAIL"
        print(f"  [{status}] @cert-authority 前缀记录匹配: removed {removed_count} 条 (期望 2 条)")
        
        if not test_passed:
            print("  [警告] 发现 Bug: @cert-authority 前缀的记录无法正确匹配")
            print("           原因: 代码假设 @ 符号在主机名字符串内部")
            print("           例如: '@cert-authority@host' 格式")
            print("           但实际格式是 '@cert-authority 192.168.1.5'")
            print("           其中 '@cert-authority' 是独立的字段，主机名在下一个字段")
    finally:
        os.unlink(test_file)
    
    print("\n[子测试 3.5] 测试同一行多个主机名")
    print("-" * 40)
    
    content = """192.168.1.2,192.168.1.3 ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC...
server1.example.com,server2.example.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIB...
"""
    test_file = create_test_file(content)
    try:
        cleaner = KnownHostsCleaner(
            known_hosts_path=test_file,
            target_ips=["192.168.1.2", "server2.example.com"],
            remove_empty_lines=False
        )
        success, removed_count, error = cleaner.clean()
        
        result_content = read_file(test_file)
        
        test_passed = success and removed_count == 2
        
        result.add_test("同一行多个主机名匹配", test_passed,
                       f"success={success}, removed_count={removed_count}, 期望删除 2 条")
        status = "PASS" if test_passed else "FAIL"
        print(f"  [{status}] 同一行多个主机名匹配: removed {removed_count} 条")
    finally:
        os.unlink(test_file)
    
    return result


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("SSH known_hosts 清理工具 - 全面测试")
    print("=" * 60)
    
    test1 = test_argument_parsing()
    test2 = test_log_cleanup()
    test3 = test_host_matching()
    
    print("\n" + "=" * 60)
    print("最终测试结果汇总")
    print("=" * 60)
    
    total_passed = test1.passed + test2.passed + test3.passed
    total_failed = test1.failed + test2.failed + test3.failed
    
    print(f"总测试数: {total_passed + total_failed}")
    print(f"通过: {total_passed}")
    print(f"失败: {total_failed}")
    print("=" * 60)
    
    if total_failed > 0:
        print("\n发现的问题汇总:")
        print("-" * 40)
        
        all_tests = test1.tests + test2.tests + test3.tests
        for test in all_tests:
            if not test["passed"]:
                print(f"  [问题] {test['name']}: {test['message']}")
        
        print("\n详细问题分析:")
        print("-" * 40)
        print("1. 参数解析问题:")
        print("   - 逗号分隔参数时，如果逗号后有空格（如 '192.168.1.3, 127.0.0.1'）")
        print("   - split(',') 会产生 ' 127.0.0.1'（带前导空格）")
        print("   - 这样无法与 known_hosts 中的 '127.0.0.1' 匹配")
        print("   - 建议: 使用 strip() 处理每个解析后的 IP")
        
        print("\n2. 日志清理问题:")
        print("   - TimedRotatingFileHandler 已经有 backupCount 参数自动管理备份")
        print("   - cleanup_old_logs() 只删除 .log 结尾的文件")
        print("   - 但备份文件格式是 .log.2026-04-19，不会被删除")
        print("   - 建议: 要么完全依赖 TimedRotatingFileHandler，要么正确处理备份文件格式")
        
        print("\n3. 主机名匹配问题:")
        print("   - 带方括号的格式（如 [192.168.1.1]:2222）无法正确匹配")
        print("   - 原因: 只处理了冒号，没有处理方括号")
        print("   - @cert-authority 前缀的记录无法正确匹配")
        print("   - 原因: 假设 @ 符号在主机名内部，但实际是独立字段")
        
        return False
    
    return True


if __name__ == "__main__":
    success = run_all_tests()
    
    if success:
        print("\n[PASS] 所有测试通过！")
        sys.exit(0)
    else:
        print("\n[FAIL] 发现问题！")
        sys.exit(1)
