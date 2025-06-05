import sys
sys.path.append('.')

import numpy as np
import random
import json

random.seed(0)
np.random.seed(0)

from src.finder.base import windowFinderinBundleSeqs, seqBundle, seqItem

def test_simple():
    # simple test
    arr = [1,1,0,0,0,1,1, 0,0,0,0, 1,1,0,0,1,1,0,0,1,1, 0,0,0,1,0,0]
    seq_bundle = seqBundle(
        id='test',
        seqs=[
            seqItem(id='test-number', seq=arr)
        ]
    )
    finder = windowFinderinBundleSeqs(
        bundle=seq_bundle,
        window=4,
        top=3,
        ideal_value=1,
        window_apply_method='mean',
        filter_out_partial_overlapped_result=True
    )
    result = finder.find()
    print(json.dumps([i.model_dump() for i in result], indent=2))
    '''output
    [
        {
            "seq_id": "test-number",
            "start_idx": 0,
            "end_idx": 4,
            "consecutive_window_length": 1,
            "score": 0.5,
            "score_diff": 0.5
        },
        {
            "seq_id": "test-number",
            "start_idx": 4,
            "end_idx": 9,
            "consecutive_window_length": 2,
            "score": 0.5,
            "score_diff": 0.5
        },
        {
            "seq_id": "test-number",
            "start_idx": 9,
            "end_idx": 23,
            "consecutive_window_length": 11,
            "score": 0.5,
            "score_diff": 0.5
        }
    ]
    '''
    pass

if __name__ == '__main__':
    test_simple()