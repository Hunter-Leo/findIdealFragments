import sys
sys.path.append('.')
import os
import json
import tempfile
from click.testing import CliRunner
from src.tool.gccontent import run_tool
from src.io.jsonl import JsonlIO

def create_example_fasta(file_path):
    """创建一个简单的示例FASTA文件，包含明确的GC和AT含量区域"""
    with open(file_path, 'w') as f:
        f.write(">example_sequence\n")
        # 区域1: 高GC含量区域 (100% GC)
        f.write("GCGCGCGCGCGCGCGC")
        # 区域2: 高AT含量区域 (100% AT)
        f.write("ATATATATATATAT")

def test_gccontent_cli():
    """使用CliRunner测试GC Content命令行工具"""
    print("===== GC Content 命令行工具简单测试 =====")
    
    # 创建临时测试文件
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建测试FASTA文件
        fasta_file = os.path.join(temp_dir, "example.fasta")
        create_example_fasta(fasta_file)
        print(f"创建了示例FASTA文件: {fasta_file}")
        
        # 创建输出文件路径
        gc_output_file = os.path.join(temp_dir, "gc_results.json")
        at_output_file = os.path.join(temp_dir, "at_results.json")
        
        # 初始化CliRunner
        runner = CliRunner()
        
        # 测试1: 高GC含量的例子
        print("\n测试1: 寻找高GC含量区域")
        args = [
            '-i', fasta_file,
            '-w', '8',        # 窗口大小
            '-t', '1',        # 只返回最佳匹配
            '-v', '1.0',      # 理想GC含量为100%
            '-d', 'GC',       # 使用GC字典模式
            '-o', gc_output_file,
            '-c', 'False'     # 不使用缓存
        ]
        
        # 执行命令
        result = runner.invoke(run_tool, args)
        print(f"命令执行状态码: {result.exit_code}")
        
        # 检查结果文件
        if os.path.exists(gc_output_file):
            gc_results = JsonlIO(dict,file_path=gc_output_file)
            print(f"找到 {len(gc_results)} 个高GC含量片段:")
            for i, segment in enumerate(gc_results):
                print(f"  片段 {i+1}: {segment}")
        else:
            print(f"错误: 输出文件 {gc_output_file} 不存在")
        
        # 测试2: 高AT含量的例子
        print("\n测试2: 寻找高AT含量区域")
        args = [
            '-i', fasta_file,
            '-w', '8',        # 窗口大小
            '-t', '1',        # 只返回最佳匹配
            '-v', '1.0',      # 理想AT含量为100%
            '-d', 'AT',       # 使用AT字典模式
            '-o', at_output_file,
            '-c', 'False'     # 不使用缓存
        ]
        
        # 执行命令
        result = runner.invoke(run_tool, args)
        print(f"命令执行状态码: {result.exit_code}")
        
        if os.path.exists(gc_output_file):
            gc_results = JsonlIO(dict,file_path=gc_output_file)
            print(f"找到 {len(gc_results)} 个高GC含量片段:")
            for i, segment in enumerate(gc_results):
                print(f"  片段 {i+1}: {segment}")
        else:
            print(f"错误: 输出文件 {at_output_file} 不存在")

if __name__ == "__main__":
    test_gccontent_cli()
    print("\n测试完成!")
