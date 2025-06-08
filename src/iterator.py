import numpy as np
from typing import List, Tuple, Literal
from .core import SequenceNumRotateCalculation
import logging
logger = logging.getLogger(__name__)

class IterableSequenceNumRotateCalculation:
    def __init__(
        self, 
        window: int, 
        arr: np.ndarray,
        excluding_window_list: List[List[Tuple[int, int]]]=[]
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
        sub_arrs = self.get_sub_arrs(self.arr, self.excluding_window_list)
        sub_arrs = [(start, SequenceNumRotateCalculation(self.window, arr)) for start, arr in sub_arrs]
        result = []
        closest_score = None
        min_diff = float('inf')
        for start, arr_rotator in sub_arrs:
            sub_score, sub_windows = arr_rotator.find_ideal_consecutive_windows(
                ideal_value=ideal_value,
                window_apply_method=window_apply_method,
                filter_out_partial_overlapped_result=filter_out_partial_overlapped_result
            )
            sub_diff = abs(sub_score - ideal_value)
            if sub_diff < min_diff:
                closest_score = sub_score
                min_diff = sub_diff
                result = []
            if sub_diff == min_diff:
                result.extend([(start+i, l) for i, l in sub_windows])
        return closest_score, result

    
