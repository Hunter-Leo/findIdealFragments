import sys
sys.path.append('.')

import numpy as np
import random
import time

random.seed(0)
np.random.seed(0)

from src.iterator import IterableSequenceNumRotateCalculation

def test_first_run():
    # 测试小数组
    arr = np.array([1,1,0,0,0,1,1, 0,0,0,0, 1,1,0,0,1,1,0,0,1,1])
    arr_rotator = IterableSequenceNumRotateCalculation(4, arr)
    print(f'{arr=}')
    print(f'{arr_rotator.find_next_ideal_windows(1, "mean",  True)=}')
    pass

def test_multi_run():
    # 测试大数组
    arr = np.array([1,1,0,0,0,1,1, 0,0,0,0, 1,1,0,0,1,1,0,0,1,1, 0,0,0,1,0,0])
    first_rotator = IterableSequenceNumRotateCalculation(4, arr)
    first_run_score, first_run_windows = first_rotator.find_next_ideal_windows(1, "mean", True)
    print(f'{arr=}')
    print(f'{first_run_score=}, {first_run_windows=}')

    second_rotator = IterableSequenceNumRotateCalculation(4, arr, excluding_window_list=[first_run_windows])
    second_run_score, second_run_windows = second_rotator.find_next_ideal_windows(1, "mean", True)
    print(f'{second_run_score=}, {second_run_windows=}')

    third_rotator = IterableSequenceNumRotateCalculation(4, arr, excluding_window_list=[first_run_windows, second_run_windows])
    third_run_score, third_run_windows = third_rotator.find_next_ideal_windows(1, "mean", True)
    print(f'{third_run_score=}, {third_run_windows=}')

    '''output: 
    arr=array([1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0,
       0, 0, 1, 0, 0])
    first_run_score=0.5, first_run_windows=[(0, 1), (4, 2), (9, 11)] # 第一轮共找到三个连续窗口， 长度分别为 1,2,11，每个窗口的分值都是 0.5。
    second_run_score=0.25, second_run_windows=[(23, 1)] # 第二轮找到 1个连续窗口，每个窗口的分值都是 0.25。
    third_run_score=None, third_run_windows=[] # 此时整个队列已经分割完成
    '''
    pass

if __name__ == '__main__':
    test_multi_run()