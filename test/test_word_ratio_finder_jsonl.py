import sys
sys.path.append('.')

import numpy as np
import random
import json

random.seed(0)
np.random.seed(0)

from src.finder.file.wordratio import findIdealWordRatioInSlidingWindow, wordSeqItem
from src.io.jsonl import JsonlIO

def test_simple():
    # simple test
    file = 'test.jsonl'
    # create a jsonl file
    # with JsonlIO(wordSeqItem, file_path=file) as jio:
    #     jio.empty()
    #     for i in range(100):
    #         jio.add_line(wordSeqItem(id=f'mytest_{i}', seq=''.join([random.choice('ATGCN') for _ in range(random.randint(0, 100_000))])))

    word_dict = {
        'A': 0,
        'T': 0,
        'G': 1,
        'C': 1,
    }
    finder = findIdealWordRatioInSlidingWindow(
        word_file=file,
        word_dict=word_dict,
        window=20,
        top=5000,
        ideal_value=1,
        window_apply_method='mean',
        filter_out_partial_overlapped_result=True,
        cache_numeric_file=True
    )
    result = finder.find(save_path='result.jsonl')
    for i in result:
        print(i)
    pass

if __name__ == '__main__':
    test_simple()