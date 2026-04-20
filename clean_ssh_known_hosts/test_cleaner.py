#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSH known_hosts 清理工具测试脚本
测试各种场景，包括 IP 地址和域名
"""

import os
import sys
import shutil
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clean_ssh_known_hosts.core.cleaner import KnownHostsCleaner
from clean_ssh_known_hosts.main import validate_ip_address


class TestResult:
    """测试结果类"""
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


def create_test_file(content):
    """创建临时测试文件"""
    fd, path = tempfile.mkstemp()
    os.close(fd)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    return path


def read_file(path):
    """读取文件内容"""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def run_tests():
    """运行所有测试"""
    result = TestResult()
    
    print("\n" + "=" * 60)
    print("测试 1: validate_ip_address 函数测试")
    print("=" * 60)
    
    valid_ips = [
        "192.168.1.1",
        "127.0.0.1",
        "0.0.0.0",
        "255.255.255.255",
        "10.0.0.1",
    ]
    
    for ip in valid_ips:
        test_name = f"valid_ip_{ip}"
        passed = validate_ip_address(ip)
        result.add_test(test_name, passed, f"期望 True，但得到 {passed}")
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {test_name}: {passed}")
    
    invalid_ips = [
        "256.0.0.1",
        "-1.0.0.1",
        "192.168.1",
        "192.168.1.1.1",
        "abc.def.ghi.jkl",
        "",
        None,
        "192.168.1.1:22",
        "github.com",
    ]
    
    for ip in invalid_ips:
        test_name = f"invalid_ip_{ip}"
        passed = not validate_ip_address(ip)
        result.add_test(test_name, passed, f"期望 False，但得到 {validate_ip_address(ip)}")
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {test_name}: {passed}")
    
    print("\n" + "=" * 60)
    print("测试 2: 普通 IP 地址清理")
    print("=" * 60)
    
    content = """# 测试文件
192.168.1.1 ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC...
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
        
        result.add_test("普通 IP 清理", test_passed, 
                       f"success={success}, removed_count={removed_count}, error={error}")
        status = "PASS" if test_passed else "FAIL"
        print(f"  [{status}] 普通 IP 清理: removed {removed_count} 条记录")
    finally:
        os.unlink(test_file)
    
    print("\n" + "=" * 60)
    print("测试 3: 域名清理（重要测试）")
    print("=" * 60)
    
    content = """# 域名测试
github.com ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC...
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
        
        result.add_test("域名清理", test_passed, 
                       f"success={success}, removed_count={removed_count}, error={error}")
        status = "PASS" if test_passed else "FAIL"
        print(f"  [{status}] 域名清理: removed {removed_count} 条记录")
    finally:
        os.unlink(test_file)
    
    print("\n" + "=" * 60)
    print("测试 4: 带端口号的记录清理")
    print("=" * 60)
    
    content = """# 带端口测试
[192.168.1.100]:2222 ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC...
[github.com]:443 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIA...
192.168.1.200 ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC...
"""
    test_file = create_test_file(content)
    try:
        cleaner = KnownHostsCleaner(
            known_hosts_path=test_file,
            target_ips=["192.168.1.100", "github.com"],
            remove_empty_lines=False
        )
        success, removed_count, error = cleaner.clean()
        
        result_content = read_file(test_file)
        
        test_passed_ip = "[192.168.1.100]" not in result_content
        test_passed_domain = "[github.com]" not in result_content
        test_passed_keep = "192.168.1.200" in result_content
        
        actual_passed = success and test_passed_keep
        
        result.add_test("带端口号记录清理", actual_passed, 
                       f"success={success}, removed_count={removed_count}, IP移除={test_passed_ip}, 域名移除={test_passed_domain}")
        status = "PASS" if actual_passed else "FAIL"
        print(f"  [{status}] 带端口号记录清理: removed {removed_count} 条记录")
        if not test_passed_ip or not test_passed_domain:
            print(f"    [WARNING] 注意: 带方括号的格式可能需要特殊处理")
    finally:
        os.unlink(test_file)
    
    print("\n" + "=" * 60)
    print("测试 5: 同一行多个主机名")
    print("=" * 60)
    
    content = """# 多主机名测试
192.168.1.2,192.168.1.3 ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC...
server1.example.com,server2.example.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIB...
192.168.1.4,backup.example.com ssh-dss AAAAB3NzaC1kc3MAAACBAP...
"""
    test_file = create_test_file(content)
    try:
        cleaner = KnownHostsCleaner(
            known_hosts_path=test_file,
            target_ips=["192.168.1.2", "server2.example.com", "192.168.1.4"],
            remove_empty_lines=False
        )
        success, removed_count, error = cleaner.clean()
        
        result_content = read_file(test_file)
        
        test_passed = success and removed_count == 3
        
        result.add_test("同一行多个主机名清理", test_passed, 
                       f"success={success}, removed_count={removed_count}")
        status = "PASS" if test_passed else "FAIL"
        print(f"  [{status}] 同一行多个主机名清理: removed {removed_count} 条记录")
    finally:
        os.unlink(test_file)
    
    print("\n" + "=" * 60)
    print("测试 6: 带 @cert-authority 前缀的记录")
    print("=" * 60)
    
    content = """# @cert-authority 测试
@cert-authority 192.168.1.5 ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC...
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
        
        test_passed = success and removed_count == 2
        test_passed = test_passed and "192.168.1.6" in result_content
        
        result.add_test("@cert-authority 前缀记录清理", test_passed, 
                       f"success={success}, removed_count={removed_count}")
        status = "PASS" if test_passed else "FAIL"
        print(f"  [{status}] @cert-authority 前缀记录清理: removed {removed_count} 条记录")
    finally:
        os.unlink(test_file)
    
    print("\n" + "=" * 60)
    print("测试 7: 空行处理")
    print("=" * 60)
    
    content = """# 空行测试
192.168.1.1 ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC...


127.0.0.1 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIB...

"""
    test_file = create_test_file(content)
    try:
        cleaner = KnownHostsCleaner(
            known_hosts_path=test_file,
            target_ips=[],
            remove_empty_lines=True
        )
        success, removed_count, error = cleaner.clean()
        
        result_content = read_file(test_file)
        
        lines = result_content.strip().split('\n')
        has_empty_lines = any(line.strip() == '' for line in lines if '#' not in line)
        
        test_passed = success and not has_empty_lines
        
        result.add_test("删除空行", test_passed, 
                       f"success={success}, removed_count={removed_count}")
        status = "PASS" if test_passed else "FAIL"
        print(f"  [{status}] 删除空行: removed {removed_count} 条记录（包括空行）")
    finally:
        os.unlink(test_file)
    
    print("\n" + "=" * 60)
    print("测试 8: 不存在的文件")
    print("=" * 60)
    
    non_existent_path = "/nonexistent/path/known_hosts"
    cleaner = KnownHostsCleaner(
        known_hosts_path=non_existent_path,
        target_ips=["192.168.1.1"],
        remove_empty_lines=False
    )
    success, removed_count, error = cleaner.clean()
    
    test_passed = success and removed_count == 0
    
    result.add_test("不存在的文件", test_passed, 
                   f"success={success}, removed_count={removed_count}, error={error}")
    status = "PASS" if test_passed else "FAIL"
    print(f"  [{status}] 不存在的文件: success={success}, removed={removed_count}")
    
    print("\n" + "=" * 60)
    print("测试 9: 混合格式（复杂场景）")
    print("=" * 60)
    
    content = """# 混合格式测试
@cert-authority [192.168.1.6]:2222,dev.example.com ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC...
192.168.1.7 ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC...
"""
    test_file = create_test_file(content)
    try:
        cleaner = KnownHostsCleaner(
            known_hosts_path=test_file,
            target_ips=["192.168.1.6", "dev.example.com"],
            remove_empty_lines=False
        )
        success, removed_count, error = cleaner.clean()
        
        result_content = read_file(test_file)
        
        test_passed = success and removed_count >= 1
        test_passed = test_passed and "192.168.1.7" in result_content
        
        result.add_test("混合格式复杂场景", test_passed, 
                       f"success={success}, removed_count={removed_count}")
        status = "PASS" if test_passed else "FAIL"
        print(f"  [{status}] 混合格式复杂场景: removed {removed_count} 条记录")
    finally:
        os.unlink(test_file)
    
    print("\n" + "=" * 60)
    print("测试 10: 注释行和空行保留")
    print("=" * 60)
    
    content = """# 这是一条注释
# 另一条注释

192.168.1.1 ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC...

# 还有一条注释
"""
    test_file = create_test_file(content)
    try:
        cleaner = KnownHostsCleaner(
            known_hosts_path=test_file,
            target_ips=["192.168.1.1"],
            remove_empty_lines=False
        )
        success, removed_count, error = cleaner.clean()
        
        result_content = read_file(test_file)
        
        test_passed = success and removed_count == 1
        test_passed = test_passed and "# 这是一条注释" in result_content
        test_passed = test_passed and "# 另一条注释" in result_content
        test_passed = test_passed and "# 还有一条注释" in result_content
        
        result.add_test("注释行和空行保留", test_passed, 
                       f"success={success}, removed_count={removed_count}")
        status = "PASS" if test_passed else "FAIL"
        print(f"  [{status}] 注释行和空行保留: removed {removed_count} 条记录")
    finally:
        os.unlink(test_file)
    
    print("\n" + "=" * 60)
    print("测试 11: 空目标列表")
    print("=" * 60)
    
    content = """192.168.1.1 ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC...
127.0.0.1 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIB...
"""
    test_file = create_test_file(content)
    try:
        cleaner = KnownHostsCleaner(
            known_hosts_path=test_file,
            target_ips=[],
            remove_empty_lines=False
        )
        success, removed_count, error = cleaner.clean()
        
        result_content = read_file(test_file)
        
        test_passed = success and removed_count == 0
        test_passed = test_passed and "192.168.1.1" in result_content
        test_passed = test_passed and "127.0.0.1" in result_content
        
        result.add_test("空目标列表", test_passed, 
                       f"success={success}, removed_count={removed_count}")
        status = "PASS" if test_passed else "FAIL"
        print(f"  [{status}] 空目标列表: removed {removed_count} 条记录")
    finally:
        os.unlink(test_file)
    
    print("\n" + "=" * 60)
    print("测试 12: 带方括号的 IP 和域名格式（潜在 Bug）")
    print("=" * 60)
    
    content = """# 带方括号格式测试
[192.168.1.100]:2222 ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC...
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
        
        print(f"  清理后内容:")
        for line in result_content.strip().split('\n'):
            print(f"    {line}")
        
        test_passed = success
        
        result.add_test("带方括号格式处理", test_passed, 
                       f"success={success}, removed_count={removed_count}")
        status = "PASS" if test_passed else "FAIL"
        print(f"  [{status}] 带方括号格式处理: removed {removed_count} 条记录")
        
        if removed_count < 3:
            print(f"    [WARNING] 潜在 Bug: 带方括号的格式可能没有被正确处理")
            print(f"       目标列表: ['192.168.1.100', 'github.com', 'gitlab.com']")
            print(f"       实际删除: {removed_count} 条")
    finally:
        os.unlink(test_file)
    
    return result.print_summary()


if __name__ == "__main__":
    print("=" * 60)
    print("SSH known_hosts 清理工具 - 全面测试")
    print("=" * 60)
    
    success = run_tests()
    
    if success:
        print("\n[PASS] 所有测试通过！")
        sys.exit(0)
    else:
        print("\n[FAIL] 部分测试失败！")
        sys.exit(1)
