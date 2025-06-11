import sys
sys.path.append('.')

from src.find_ideal_segments.finder.file.wordratio import selectedWindowExtended
from src.find_ideal_segments.io.jsonl import JsonlIO
import numpy as np
from typing import Literal, Tuple, List

def rotate_on_window(window:int, arr:np.ndarray, method: Literal['sum', 'mean'] = 'mean') -> np.ndarray:
    """
    计算滑动窗口值
    
    Args:
        method: 计算方法，'sum'或'mean'
        
    Returns:
        包含所有窗口计算值的numpy数组
    """
    cumsum = np.cumsum(arr, axis=-1)
    window_sum = cumsum[window - 1:] - np.concatenate(([0.], cumsum[:-window]))
    if method == 'sum':
        result = window_sum
    else:  # mean
        result = window_sum / window
    return result

def calculate_gc(seq:str):
    return sum(1 for i in seq if i in 'GCgc') / len(seq)
    # return seq.count('G') + seq.count('C') + seq.count('g') + seq.count('c')

if __name__ == '__main__':
    result_file = 'testResult.jsonl'
    window = 2000
    with JsonlIO(selectedWindowExtended,result_file) as jio:
        for item in jio:
            arr = np.array([int(i in 'GCgc') for i in item.seq])
            score_win = rotate_on_window(window, arr, method='mean')
            print(item.score, item.consecutive_window_length, score_win)

            print(f'overall: {calculate_gc(item.seq)}')
            for i in range(0, len(item.seq)-window+1, 1):
                print(f'{i}: {calculate_gc(item.seq[i:i+window])}')