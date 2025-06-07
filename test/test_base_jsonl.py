import sys
sys.path.append('.')

import numpy as np
import random
import time

random.seed(0)
np.random.seed(0)

import json
from src.finder.file.base import windowFinderinJsonl, seqItem

def test_simple():
    file = 'test.jsonl'
    with open(file, 'w') as f:
        for i in range(10):
            f.write(seqItem(id=f'test-number-{i}', seq=[1,1,0,0,0,1,1, 0,0,0,0, 1,1,0,0,1,1,0,0,1,1, 0,0,0,1,0,0]).model_dump_json() + '\n')

    finder = windowFinderinJsonl(
        file=file,
        window=4,
        top=5,
        ideal_value=0.25,
        window_apply_method='mean',
        filter_out_partial_overlapped_result=True
    )
    result = finder.find(save_path='result.jsonl')
    result.close()

def test_large():
    row_lines = 100
    max_line_len = 100_000
    window = 200
    top = 5
    
    file = 'test.jsonl'
    with open(file, 'w') as f:
        for i in range(row_lines):
            f.write(seqItem(id=f'mytest_{i}', seq=np.random.randint(0,2,size=random.randint(0, max_line_len))).model_dump_json() + '\n')

    start = time.time()
    finder = windowFinderinJsonl(file, window=window, top=top, ideal_value=1)
    result_file = finder.find('result.jsonl')
    for line in result_file:
        print(line)
    result_file.close()
    print(f'{row_lines=}, {max_line_len=}, {window=}, {top=}, cost time={time.time()-start}')
    pass


if __name__ == '__main__':
    # test_simple()
    test_large()