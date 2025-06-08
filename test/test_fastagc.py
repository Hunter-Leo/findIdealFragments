import sys
sys.path.append('.')
import os
import json
import tempfile
from src.tool.gccontent import findIdealGCContentSegmentsonFasta

def create_test_fasta(file_path):
    """创建一个测试用的FASTA文件"""
    with open(file_path, 'w') as f:
        f.write(">sequence1\n")
        f.write("ATGCGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGC\n")  # 混合序列
        f.write(">sequence2\n")
        f.write("GCGCGCGCGCGCGCGCGCGCGCGC\n")  # 高GC含量序列
        f.write(">sequence3\n")
        f.write("ATATATATATATATATATATATATATA\n")  # 高AT含量序列

def test_gc_content_finder():
    """测试GC含量查找器"""
    # 创建临时文件
    with tempfile.NamedTemporaryFile(suffix='.fasta', delete=False) as temp_file:
        temp_fasta = temp_file.name
    
    # 创建测试FASTA文件
    create_test_fasta(temp_fasta)
    print(f"创建测试FASTA文件: {temp_fasta}")
    
    # 创建输出文件路径
    temp_output = temp_fasta.replace('.fasta', '_output.json')
    
    # 测试用例1：寻找理想GC含量为0.5的片段
    print("\n测试1: 寻找理想GC含量为0.5的片段")
    finder1 = findIdealGCContentSegmentsonFasta(
        fasta_file=temp_fasta,
        window=10,
        top=3,
        ideal_value=0.5,
        dict_mode='GC',
        window_apply_method='mean',
        filter_out_partial_overlapped_result=True,
        cache=False
    )
    result1 = finder1.find(save_path=temp_output)
    
    # 打印结果
    print(f"找到 {len(result1)} 个片段:")
    for i, segment in enumerate(result1):
        print(f"片段 {i+1}: {segment}")
    result1.close()
    
    # 测试用例3：寻找高AT含量的片段
    print("\n测试3: 寻找高AT含量的片段 (使用AT字典模式)")
    finder3 = findIdealGCContentSegmentsonFasta(
        fasta_file=temp_fasta,
        window=10,
        top=2,
        ideal_value=1.0,
        dict_mode='AT',
        window_apply_method='mean',
        filter_out_partial_overlapped_result=True,
        cache=False
    )
    result3 = finder3.find(save_path=temp_output)
    
    print(f"找到 {len(result3)} 个片段:")
    for i, segment in enumerate(result3):
        print(f"片段 {i+1}: {segment}")
    
    # 清理临时文件
    try:
        os.remove(temp_fasta)
        os.remove(temp_output)
        jsonl_file = temp_fasta.rsplit('.', 1)[0] + '.jsonl'
        if os.path.exists(jsonl_file):
            os.remove(jsonl_file)
        print("\n临时文件已清理")
    except Exception as e:
        print(f"清理临时文件时出错: {e}")

if __name__ == "__main__":
    print("开始测试findIdealGCContentSegmentsonFasta类...")
    test_gc_content_finder()
    print("测试完成!")
