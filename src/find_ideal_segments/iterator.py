import numpy as np
from typing import List, Tuple, Literal
from .core import SequenceNumRotateCalculation
import logging
import uuid
import pathlib
logger = logging.getLogger(__name__)

class IterableSequenceNumRotateCalculation:
    def __init__(
        self, 
        window: int, 
        arr: np.ndarray,
        excluding_window_list: List[List[Tuple[int, int]]]=[],
        cache_id: str= None
    ):
        """
        初始化滑动窗口计算类
        
        Args:
            window: 窗口大小
            arr: 输入数组，可以是numpy数组或可迭代对象
            exculding_region_list: 排除区域列表，每个元素为每一轮挑选到的靠近理想值的区域列表(起始索引, 连续窗口数量)
        """
        self.window = window
        # 使用弱引用存储原始数组，避免复制大数组
        self.arr = arr if isinstance(arr, np.ndarray) else np.array(arr)
        self.length = len(arr)
        # assert window <= self.length, 'window must be less than or equal to the length of the array'
        if window > self.length:
            logging.warning(f'Sequence length {self.length} is smaller than window size {window}.')
        self.excluding_window_list = excluding_window_list
        self.cache_id = cache_id if cache_id is not None else str(uuid.uuid4())
    
    def get_sub_arrs(self, arr:np.ndarray, excluding_window_list:List[List[Tuple[int, int]]]):
        """
        获取排除区域后的子数组列表

        Args:
            arr: 输入数组
            excluding_window_list: 排除区域列表，每个元素为每一轮挑选到的靠近理想值的区域列表(起始索引, 连续窗口数量)

        Returns:
            List[int, np.ndarray]列表，每个元素为子序列在原序列的起始位置以及子序列
        """
        all_windows = sorted([i for x in excluding_window_list for i in x], key=lambda i: i[0])
        sub_arrs = []
        last_end = 0
        for start, length in all_windows:
            if start > last_end:
                sub_arr = arr[last_end:start]
                if len(sub_arr)>=self.window:
                    sub_arrs.append((last_end, sub_arr))
            last_end = start + length + self.window -1
        if last_end < len(arr):
            sub_arr = arr[last_end:]
            if len(sub_arr)>=self.window:
                sub_arrs.append((last_end, sub_arr))
        return sub_arrs
    
    def rotate_on_whole_sequence_(self, window_apply_method: Literal['sum', 'mean'] = 'mean', chunk_size: int = 10**6):
        """计算原始序列上的完整窗口值，并缓存到本地
        """
        arr = self.arr
        chunk_size = max(chunk_size, self.window)
        total_chunks = (self.length - self.window + chunk_size) // chunk_size
        rotate_window_values = np.zeros(self.length-self.window + 1, dtype=np.float64) - 1
        for chunk_idx in range(total_chunks):
            start_idx = chunk_idx * chunk_size
            end_idx = min(start_idx + chunk_size +self.window -1, self.length)
            chunk_arr = arr[start_idx:end_idx].astype(np.float64)
            arr_rotator = SequenceNumRotateCalculation(self.window, chunk_arr)
            chunk_window_values = arr_rotator.rotate_on_window(chunk_arr, method=window_apply_method)
            rotate_window_values[start_idx:start_idx+len(chunk_window_values)] = chunk_window_values
        return rotate_window_values
    
    def load_whole_sequence_rotate_window_values(self, window_apply_method: Literal['sum','mean'] ='mean'):
        cache_dir = '.rotate_windows'
        pathlib.Path(cache_dir).mkdir(exist_ok=True)
        cache_file = f'.rotate_windows/{self.cache_id}_{window_apply_method}.npy'
        if not pathlib.Path(cache_file).exists():
            logger.info(f'Caching rotate window values - "{cache_file}"...')
            rotate_window_values = self.rotate_on_whole_sequence_(window_apply_method=window_apply_method)
            np.save(cache_file, rotate_window_values)
        else:
            rotate_window_values = np.load(cache_file)
        return rotate_window_values
    
    def find_next_ideal_windows(
        self,
        ideal_value: float,
        window_apply_method: Literal['sum', 'mean'] = 'mean',
        filter_out_partial_overlapped_result: bool = True,
    )->Tuple[float, List[Tuple[int, int]]]:
        """
        查找下一轮理想窗口

        Args:
            ideal_value: 理想值
            window_apply_method: 窗口计算方法
            filter_out_partial_overlapped_result: 是否过滤部分重叠的结果

        Returns:
            列表，每个元素为(起始索引, 连续窗口数量)
        """
        whole_sequence_rotate_window_values = self.load_whole_sequence_rotate_window_values(window_apply_method=window_apply_method)
        sub_arrs = self.get_sub_arrs(self.arr, self.excluding_window_list)
        sub_arrs = [(start, SequenceNumRotateCalculation(self.window, arr)) for start, arr in sub_arrs]
        result = []
        closest_score = None
        min_diff = float('inf')
        for start, arr_rotator in sub_arrs:
            cached_rotate_window_values_length = len(arr_rotator.arr) - self.window + 1
            cached_rotate_window_values = whole_sequence_rotate_window_values[start:start+cached_rotate_window_values_length]
            sub_score, sub_windows = arr_rotator.find_ideal_consecutive_windows(
                ideal_value=ideal_value,
                window_apply_method=window_apply_method,
                filter_out_partial_overlapped_result=filter_out_partial_overlapped_result,
                cached_rotate_window_values=cached_rotate_window_values
            )
            sub_diff = abs(sub_score - ideal_value)
            if sub_diff < min_diff:
                closest_score = sub_score
                min_diff = sub_diff
                result = []
            if sub_diff == min_diff:
                result.extend([(start+i, l) for i, l in sub_windows])
        return closest_score, result

    
