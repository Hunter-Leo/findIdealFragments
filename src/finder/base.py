from ..iterator import IterableSequenceNumRotateCalculation
from typing import List, Literal, Annotated
from typing import Tuple
import json
import pandas as pd
from pydantic import BaseModel

class iterResult(BaseModel):
    score: float | None
    windows: List[Tuple[int, int]]

class seqItem(BaseModel):
    id: str
    seq: List[int|float]
    iter_results:List[iterResult] = []

class seqBundle(BaseModel):
    id: str
    seqs: List[seqItem]

class selectedWindow(BaseModel):
    seq_id: str
    start_idx: int
    end_idx: int
    consecutive_window_length: int
    score: float
    score_diff: float

class windowFinderinBundleSeqs:

    def __init__(
        self, 
        bundle: seqBundle, 
        window: int, 
        top:int,
        ideal_value: float,
        window_apply_method: Literal['sum', 'mean'] = 'mean',
        filter_out_partial_overlapped_result: bool = True
    ):
        self.bundle = bundle
        self.window = window
        self.top = top
        self.ideal_value = ideal_value
        self.window_apply_method = window_apply_method
        self.filter_out_partial_overlapped_result = filter_out_partial_overlapped_result
    
    def find(self)-> List[selectedWindow]:
        selected_windows: List[selectedWindow] = []
        selected_bundle: List[seqItem] = self.bundle.seqs
        selected_max_diff = float('-inf')

        while (len(selected_windows) < self.top) or (len(selected_bundle)>0):
            current_max_diff = selected_max_diff
            left = self.top - len(selected_windows)
            current_candidates_windows: List[selectedWindow] = []
            current_candidates_bundle: List[seqItem] = []

            # 这一轮要找 n 个窗口
            for seq in selected_bundle:
                pre_finded_windows = [i.windows for i in seq.iter_results]
                rotator = IterableSequenceNumRotateCalculation(
                    window=self.window,
                    arr=seq.seq,
                    excluding_window_list=pre_finded_windows
                )
                score, windows = rotator.find_next_ideal_windows(
                    ideal_value=self.ideal_value,
                    window_apply_method=self.window_apply_method,
                    filter_out_partial_overlapped_result=self.filter_out_partial_overlapped_result
                )
                seq.iter_results.append(iterResult(score=score, windows=windows))

                if score is None: # 该序列已经全部分割完成
                    continue

                diff = abs(score - self.ideal_value)

                is_smaller_diff = diff < current_max_diff
                
                if (len(current_candidates_windows)<left) or (is_smaller_diff):
                    if not is_smaller_diff:
                        current_max_diff = diff
                    current_candidates_windows.extend([selectedWindow(
                        seq_id=seq.id,
                        start_idx=i[0],
                        end_idx=i[0]+i[1]+self.window-1,
                        consecutive_window_length=i[1],
                        score=score,
                        score_diff=diff
                    ) for i in windows])
                    current_candidates_bundle.append(seq)
            
            # 整合上一轮的结果
            selected_windows = sorted(selected_windows + current_candidates_windows, key=lambda i: (i.score_diff, i.start_idx))[:self.top]
            selected_max_diff = selected_windows[-1].score_diff
            selected_bundle = current_candidates_bundle
        return selected_windows