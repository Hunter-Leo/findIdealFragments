from ...iterator import IterableSequenceNumRotateCalculation
from typing import List, Literal, Annotated
from typing import Tuple
import json
import pandas as pd
from ...io.jsonl import JsonlIO
from pydantic import BaseModel
import time
import logging
logger = logging.getLogger(__name__)

class iterResult(BaseModel):
    score: float | None
    windows: List[Tuple[int, int]]

class seqItem(BaseModel):
    id: str
    seq: List[int|float]
    iter_results:List[iterResult] = []

class selectedWindow(BaseModel):
    seq_id: str
    start_idx: int
    end_idx: int
    consecutive_window_length: int
    score: float
    score_diff: float

class windowFinderinJsonl:

    def __init__(
        self, 
        file: str, 
        window: int, 
        top:int,
        ideal_value: float,
        window_apply_method: Literal['sum', 'mean'] = 'mean',
        filter_out_partial_overlapped_result: bool = True,
        sort_chunk_size: int = 10_000_000,
        precision:int = 4
    ):
        self.file: JsonlIO[seqItem]= JsonlIO(seqItem, file_path=file, mode='r')
        self.window = window
        self.top = top
        self.ideal_value = ideal_value
        self.window_apply_method = window_apply_method
        self.filter_out_partial_overlapped_result = filter_out_partial_overlapped_result
        self.sort_chunk_size = sort_chunk_size
        self.precision = precision
    
    def find(self, save_path:str=None)-> JsonlIO[selectedWindow]:
        selected_windows: JsonlIO[selectedWindow] = JsonlIO(selectedWindow, file_path=save_path)
        selected_windows.empty()
        selected_bundle: JsonlIO[seqItem] = self.file
        selected_max_diff = float('-inf')

        round_num = 0
        found_num = len(selected_windows)
        seqs_to_seek = len(selected_bundle)

        sum_find_window_time_consume = 0
        sum_find_window_num = 0
        sum_file_time_consume = 0

        while seqs_to_seek>0:
            current_max_diff = selected_max_diff
            left = self.top - found_num
            current_candidates_windows: JsonlIO[selectedWindow] = JsonlIO(selectedWindow)
            current_candidates_bundle: JsonlIO[seqItem] = JsonlIO(seqItem)

            logger.info(f'Running round {round_num}: {seqs_to_seek} sequences to seek, {left} windows to find...')

            current_candidates_windows_num = 0
            find_window_time_consume = 0
            find_window_num = 0
            file_time_consume = 0

            # 这一轮要找 n 个窗口
            for seq in selected_bundle:
                find_time_start = time.time()
                pre_finded_windows = [i.windows for i in seq.iter_results]
                rotator = IterableSequenceNumRotateCalculation(
                    window=self.window,
                    arr=seq.seq,
                    excluding_window_list=pre_finded_windows,
                    cache_id=seq.id
                )
                score, windows = rotator.find_next_ideal_windows(
                    ideal_value=self.ideal_value,
                    window_apply_method=self.window_apply_method,
                    filter_out_partial_overlapped_result=self.filter_out_partial_overlapped_result
                )
                seq.iter_results.append(iterResult(score=score, windows=windows))

                windows_num = len(windows)
                find_window_num += windows_num
                find_time_end = time.time()
                find_window_time_consume += (find_time_end - find_time_start)

                if score is None: # 该序列已经全部分割完成
                    continue


                score = round(score, self.precision)
                diff = round(abs(score - self.ideal_value), self.precision)

                is_smaller_diff = (diff <= current_max_diff)
                
                if (len(current_candidates_windows)<left) or (is_smaller_diff):
                    if not is_smaller_diff:
                        current_max_diff = diff
                    file_time_start = time.time()
                    [current_candidates_windows.add_line(selectedWindow(
                        seq_id=seq.id,
                        start_idx=i[0],
                        end_idx=i[0]+i[1]+self.window-1,
                        consecutive_window_length=i[1],
                        score=score,
                        score_diff=diff
                    )) for i in windows]
                    current_candidates_bundle.add_line(seq)
                    current_candidates_windows_num += windows_num
                    file_time_end = time.time()
                    file_time_consume += (file_time_end - file_time_start)

            file_time_start_ = time.time()
            current_candidates_windows.sort_by_fileds(('score_diff', 'start_idx'), chunk_size=self.sort_chunk_size)
            current_candidates_windows.head(left)
            [selected_windows.add_line(line) for line in current_candidates_windows]
            current_candidates_windows.close()
            for last_window in selected_windows:
                selected_max_diff = last_window.score_diff
            selected_bundle.close()
            selected_bundle = current_candidates_bundle

            found_num = len(selected_windows)
            seqs_to_seek = len(selected_bundle)

            file_time_end_ = time.time()
            file_time_consume += (file_time_end_ - file_time_start_)
            logger.info(f'Round {round_num} finished: {find_window_num} windows found, {current_candidates_windows_num} windows added to candidates, {file_time_consume} seconds file time consume, {find_window_time_consume} seconds find window time consume.')

            sum_find_window_time_consume += find_window_time_consume
            sum_find_window_num += find_window_num
            sum_file_time_consume += file_time_consume
            round_num += 1

        logger.info(f'All rounds finished: {sum_find_window_num} windows found, {sum_file_time_consume/3600:.2f} hours file time consume, {sum_find_window_time_consume/3600:.2f} hours find window time consume.')
        return selected_windows