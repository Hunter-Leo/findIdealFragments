import numpy as np
from typing import Literal, List, Tuple, Optional, Iterator
import itertools

class SequenceNumRotateCalculation:
    def __set__(self, instance, value):
        raise AttributeError("不能修改只读属性")
    
    def __init__(self, window: int, arr: np.ndarray):
        """
        初始化滑动窗口计算类
        
        Args:
            window: 窗口大小
            arr: 输入数组，可以是numpy数组或可迭代对象
        """
        self.window = window
        # 使用弱引用存储原始数组，避免复制大数组
        self.arr = arr
        self.length = len(arr)
        assert window <= self.length, 'window must be less than or equal to the length of the array'
    
    def rotate_on_window(self, arr:np.ndarray=None, method: Literal['sum', 'mean'] = 'mean') -> np.ndarray:
        """
        计算滑动窗口值
        
        Args:
            method: 计算方法，'sum'或'mean'
            
        Returns:
            包含所有窗口计算值的numpy数组
        """
        arr = arr if arr is not None else self.arr
        cumsum = np.cumsum(arr, axis=-1)
        window_sum = cumsum[self.window - 1:] - np.concatenate(([0.], cumsum[:-self.window]))
        if method == 'sum':
            result = window_sum
        else:  # mean
            result = window_sum / self.window
        return result
    
    def find_ideal_consecutive_windows(
        self, 
        ideal_value: float, 
        window_apply_method: Literal['sum', 'mean'] = 'mean',
        filter_out_partial_overlaped_result: bool = True
    ) -> Tuple[float, List[Tuple[int, int]]]:
        """
        查找最接近理想值的连续窗口
        
        Args:
            ideal_value: 理想值
            window_apply_method: 窗口计算方法
            filter_out_partial_overlaped_result: 是否过滤部分重叠的结果
            
        Returns:
            列表，每个元素为(起始索引, 连续窗口数量)
        """
        # 对于超大数组，使用分块处理
        return self._find_ideal_windows_chunked(
                ideal_value, window_apply_method, filter_out_partial_overlaped_result
            )
            
        
    def _find_ideal_windows_chunked(
        self,
        ideal_value: float,
        window_apply_method: Literal['sum', 'mean'] = 'mean',
        filter_out_partial_overlaped_result: bool = True,
        chunk_size: int = 10**6
    ) ->  Tuple[float, List[Tuple[int, int]]]:
        """
        分块处理大数组，查找理想窗口
        
        Args:
            ideal_value: 理想值
            window_apply_method: 窗口计算方法
            filter_out_partial_overlaped_result: 是否过滤部分重叠结果
            chunk_size: 每块大小
            
        Returns:
            列表，每个元素为(起始索引, 连续窗口数量)
        """
        all_candidates = []
        min_diff = float('inf')
        closest_score = None
        
        # 计算总块数
        total_chunks = (self.length - self.window + chunk_size) // chunk_size

        # 增加中间连接块
        total_chunks = total_chunks*2 -1
        half_chunk_size = chunk_size//2
        
        for chunk_idx in range(total_chunks):
            start_idx = chunk_idx * half_chunk_size
            end_idx = min(start_idx + chunk_size + self.window - 1, self.length)
            
            # 提取当前块
            chunk_arr = self.arr[start_idx:end_idx]

            # 计算当前块的窗口值
            chunk_window_values = self.rotate_on_window(arr=chunk_arr, method=window_apply_method)
            
            # 计算与理想值的差异
            chunk_diff = np.abs(chunk_window_values - ideal_value).astype(np.float32)
            chunk_min_diff = np.min(chunk_diff)
            
            # 更新全局最小差异
            if chunk_min_diff < min_diff:
                min_diff = chunk_min_diff
                all_candidates = []
            
            if chunk_min_diff == min_diff:
                # 找到当前块中的候选索引
                chunk_candidates = np.where(chunk_diff == chunk_min_diff)[0]
                closest_score = chunk_window_values[chunk_candidates[0]]
                # 调整索引到原始数组
                adjusted_indices = chunk_candidates + start_idx
                all_candidates.extend(adjusted_indices)
        
        if not all_candidates:
            return []
        
        return float(closest_score), self._group_consecutive_indices(np.array(all_candidates), filter_out_partial_overlaped_result)
    
    def _group_consecutive_indices(
        self, 
        indices: np.ndarray, 
        filter_out_partial_overlaped: bool
    ) -> List[Tuple[int, int]]:
        """
        将连续的索引分组
        
        Args:
            indices: 索引数组
            filter_out_partial_overlaped: 是否过滤部分重叠结果
            
        Returns:
            列表，每个元素为(起始索引, 连续窗口数量)
        """
        if len(indices) == 0:
            return []
            
        # 计算索引差分
        diffs = np.diff(indices)
        # 找到非连续点
        split_points = np.where(diffs > 1)[0]
        # 分组
        groups = np.split(indices, split_points + 1)
        
        # 生成结果
        result = [(int(group[0]), len(group)) for group in groups]
        
        # 过滤重叠窗口
        if filter_out_partial_overlaped:
            result = sorted(result, key=lambda x: x[0])
            filtered_result = [result[0]]
            
            for i in range(1, len(result)):
                next_acceptable_start = filtered_result[-1][0]+filtered_result[-1][1]+self.window-1
                i_end_position = sum(result[i])-1
                if (i_end_position - next_acceptable_start) >= 0:
                    head_strip_num = next_acceptable_start - result[i][0]
                    filtered_result.append((result[i][0]+head_strip_num, result[i][1]-head_strip_num))
            
            result = filtered_result
            
        return result


if __name__ == '__main__':
    import random
    import time
    
    random.seed(0)
    np.random.seed(0)
    
    # 测试小数组
    arr = np.array([1,1,0,0,0,1,1, 0,0,0,0, 1,1,0,0,1,1,0,0,1,1])
    arr_rotator = SequenceNumRotateCalculation(4, arr)
    print(f'{arr=}')
    print(f'{arr_rotator.rotate_on_window(method="mean")=}')
    print(f'{arr_rotator.find_ideal_consecutive_windows(1, "mean",  True)=}')
    
    # 测试性能
    print("Testing performance with bigger array...")
    start = time.time()
    # 使用较小的数组进行测试，避免内存问题
    test_size = 300_000_000  # 3亿
    long_arr = np.random.randint(0, 2, test_size)
    
    arr_rotator = SequenceNumRotateCalculation(2000, long_arr)
    result = arr_rotator.find_ideal_consecutive_windows(1, 'mean', True)
    print(f'Time consumed for sequence with length {test_size}: {time.time()-start:.2f}s')
    print(f'Found {len(result[1])} ideal windows')
    pass
