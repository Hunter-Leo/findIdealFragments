import sys
sys.path.append('.')

import numpy as np
import random
import json

random.seed(0)
np.random.seed(0)

from src.finder.wordratio import findIdealWordRatioInSlidingWindow, wordSeqBundle, wordSeqItem

def test_simple():
    # simple test
    dna = 'GCAATGGATTAGCTAGGTTCGAAAGTA'
    seq_bundle = wordSeqBundle(
        id='test',
        seqs=[
            wordSeqItem(id='test-dna', seq=dna),
            wordSeqItem(id='copy', seq=dna)
        ]
    )
    word_dict = {
        'A': 0,
        'T': 0,
        'G': 1,
        'C': 1,
    }
    finder = findIdealWordRatioInSlidingWindow(
        word_bundle=seq_bundle,
        word_dict=word_dict,
        window=4,
        top=6,
        ideal_value=1,
        window_apply_method='mean',
        filter_out_partial_overlapped_result=True
    )
    result = finder.find()
    print(json.dumps([i.model_dump() for i in result], indent=2))
    '''output
    [
        {
            "seq_id": "test-dna",
            "start_idx": 0,
            "end_idx": 4,
            "consecutive_window_length": 1,
            "score": 0.5,
            "score_diff": 0.5
        },
        {
            "seq_id": "copy",
            "start_idx": 0,
            "end_idx": 4,
            "consecutive_window_length": 1,
            "score": 0.5,
            "score_diff": 0.5
        },
        {
            "seq_id": "test-dna",
            "start_idx": 4,
            "end_idx": 9,
            "consecutive_window_length": 2,
            "score": 0.5,
            "score_diff": 0.5
        },
        {
            "seq_id": "copy",
            "start_idx": 4,
            "end_idx": 9,
            "consecutive_window_length": 2,
            "score": 0.5,
            "score_diff": 0.5
        },
        {
            "seq_id": "test-dna",
            "start_idx": 9,
            "end_idx": 23,
            "consecutive_window_length": 11,
            "score": 0.5,
            "score_diff": 0.5
        },
        {
            "seq_id": "copy",
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