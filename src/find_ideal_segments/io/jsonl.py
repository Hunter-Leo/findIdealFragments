import json
import os
import tempfile
from typing import Dict, Any, Iterator, Optional, Union, List, TypeVar, Generic, Type, Tuple
from io import FileIO
import heapq

from pydantic import BaseModel, Json

T = TypeVar('T', bound=BaseModel)

class JsonlIO(Generic[T]):
    """JSONL 文件读写操作类，支持增加行、读取行、迭代遍历等功能"""
    
    def __init__(self, model_cls: Type[T]=BaseModel, file_path: Optional[str] = None, mode: str = "a+"):
        """
        初始化 JsonlIO 对象
        
        参数:
            file_path: JSONL 文件路径，如果不提供则创建临时文件
            mode: 文件打开模式，默认为 'a+'（读写模式）
        """
        self.model_cls = model_cls
        self.is_temp = file_path is None
        if self.is_temp:
            # 创建临时文件
            self.temp_file = tempfile.NamedTemporaryFile(mode=mode, suffix='.jsonl', delete=False)
            self.file_path = self.temp_file.name
        else:
            self.file_path = file_path
        
        self.file:FileIO = open(self.file_path, mode)
    
    def empty(self) -> None:
        """清空文件内容"""
        mode = self.file.mode
        self.file.close()
        self.file = open(self.file_path, 'w')
        self.file.close()
        self.file = open(self.file_path, mode)
    
    def _calculate_length(self) -> None:
        """计算文件中的行数"""
        current_pos = self.file.tell()
        self.file.seek(0)
        length = sum(1 for _ in self.file)
        self.file.seek(current_pos)
        return length

    def add_line(self, data: Dict[str, Any]|T) -> None:
        """
        添加一行 JSON 对象到文件
        
        参数:
            data: 要添加的 JSON 对象（字典格式）
        """
        if isinstance(data, dict):
            model_instance = self.model_cls(**data)
        elif isinstance(data, self.model_cls):
            model_instance = data
        else:
            raise TypeError(f"数据必须是字典或 {self.model_cls.__name__} 的实例")
        
        # 确保文件指针在末尾
        self.file.seek(0, os.SEEK_END)
        json_str = model_instance.model_dump_json()
        self.file.write(json_str + '\n')
        self.file.flush()
    
    def read_line(self)->T:
        """
        读取当前行的 JSON 对象

        返回:
            当前行的 JSON 对象
        """
        line = self.file.readline()
        data = json.loads(line)
        return self.model_cls(**data)
    
    def __iter__(self) -> Iterator[T]:
        """实现迭代器接口，允许使用 for in 循环遍历文件中的所有 JSON 对象"""
        self.file.seek(0)
        for line in self.file:
            if line.strip():  # 忽略空行
                data = json.loads(line)
                yield self.model_cls(**data)
    
    def close(self) -> None:
        """关闭文件，如果是临时文件则删除"""
        self.file.close()
        if self.is_temp and hasattr(self, 'temp_file'):
            try:
                os.unlink(self.file_path)
            except:
                pass
    
    def __enter__(self):
        """支持 with 语句"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """with 语句结束时关闭文件"""
        self.close()
    
    def __len__(self) -> int:
        """返回文件中的行数"""
        return self._calculate_length()
    
    def sort_by_fileds(self, fields: Tuple[str], reverse: bool = False, chunk_size: int = 10_000_000) -> None:
        """
        对JSONL文件进行外部排序
        
        参数:
            fields: 用于排序的字段名元组，可以是单个字段或多个字段
            reverse: 是否降序排序，默认为False（升序）
            chunk_size: 每个内存块的最大行数，默认为10000行
        """
        # 关闭当前文件，以便稍后重新打开
        self.file.close()
        
        # 创建临时文件列表用于存储排序后的块
        temp_files = []
        
        # 读取并分块排序
        with open(self.file_path, 'r') as input_file:
            while True:
                # 读取一个块的数据
                chunk = []
                for _ in range(chunk_size):
                    line = input_file.readline()
                    if not line:
                        break
                    if line.strip():
                        data = json.loads(line)
                        chunk.append((self.model_cls(**data), line))
                
                if not chunk:
                    break
                    
                # 对块进行排序
                def sort_key(item):
                    obj = item[0]
                    return tuple(getattr(obj, field) for field in fields)
                
                chunk.sort(key=sort_key, reverse=reverse)
                
                # 将排序后的块写入临时文件
                temp_fd, temp_path = tempfile.mkstemp(suffix='.jsonl')
                with os.fdopen(temp_fd, 'w') as temp_file:
                    for _, line in chunk:
                        temp_file.write(line)
                temp_files.append(temp_path)
        
        # 合并排序后的块
        with open(self.file_path, 'w') as output_file:
            file_handles = []
            entries = []
            
            # 打开所有临时文件
            for temp_path in temp_files:
                file_handle:FileIO = open(temp_path, 'r')
                file_handles.append(file_handle)
                line = file_handle.readline()
                if line.strip():
                    data = json.loads(line)
                    obj = self.model_cls(**data)
                    entries.append((obj, line, file_handle))
            
            # 使用堆进行归并排序
            if entries:
                entries_heap = []
                for i, (obj, line, _) in enumerate(entries):
                    sort_value = tuple(getattr(obj, field) for field in fields)
                    # 堆中的元素格式: (排序键, 索引(用于稳定排序), 行数据, 文件索引)
                    heapq.heappush(entries_heap, (sort_value, i, line, i))
                
                while entries_heap:
                    sort_value, _, line, file_idx = heapq.heappop(entries_heap)
                    output_file.write(line)
                    
                    # 从同一文件读取下一行
                    next_line = file_handles[file_idx].readline()
                    if next_line.strip():
                        data = json.loads(next_line)
                        obj = self.model_cls(**data)
                        sort_value = tuple(getattr(obj, field) for field in fields)
                        # 为了维持稳定排序，使用当前堆的大小作为次级比较键
                        heapq.heappush(entries_heap, (sort_value, len(entries_heap), next_line, file_idx))
            
            # 关闭并删除所有临时文件
            for file_handle in file_handles:
                file_handle.close()
            for temp_path in temp_files:
                try:
                    os.unlink(temp_path)
                except:
                    pass
        
        # 重新打开文件
        self.file = open(self.file_path, self.file.mode)
    def head(self, length: int = 10) -> None:
        """
        保留文件的前 n 行数据，并覆盖当前文件
        
        参数:
            length: 要保留的行数，默认为 10
        """
        # 关闭当前文件
        self.file.close()
        
        # 创建临时文件
        temp_fd, temp_path = tempfile.mkstemp(suffix='.jsonl')
        with os.fdopen(temp_fd, 'w') as temp_file:
            # 读取原文件前 n 行
            with open(self.file_path, 'r') as input_file:
                for i in range(length):
                    line = input_file.readline()
                    if not line:  # 文件结束
                        break
                    temp_file.write(line)
        
        # 用临时文件替换原文件
        os.replace(temp_path, self.file_path)
        
        # 重新打开文件
        self.file = open(self.file_path, self.file.mode)


# 使用示例
if __name__ == "__main__":
    # 使用临时文件创建 JsonlIO 对象
    class User(BaseModel):
        name: str
        age: int
    with JsonlIO(User) as jsonl_temp:
        # 添加数据
        jsonl_temp.add_line({"name": "Alice", "age": 30})
        jsonl_temp.add_line({"name": "Bob", "age": 25})
        jsonl_temp.add_line({"name": "Charlie", "age": 35})
        jsonl_temp.add_line({"name": "David", "age": 40})
        
        # 通过迭代器遍历所有数据
        print("所有数据:")
        for item in jsonl_temp:
            print(f"- {item}")
