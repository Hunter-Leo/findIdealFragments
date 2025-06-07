from .base import windowFinderinJsonl, JsonlIO, seqItem
from typing import Literal, List, Dict
import pathlib

class wordSeqItem(seqItem):
    seq: str

class findIdealWordRatioInSlidingWindow(windowFinderinJsonl):
    def __init__(
        self, 
        word_file: str, 
        word_dict: Dict[str, float|int],
        window: int, 
        top:int,
        ideal_value: float,
        window_apply_method: Literal['sum', 'mean'] = 'mean',
        filter_out_partial_overlapped_result: bool = True,
        beyond_word_dict_value: float|int = 0,
        cache_numeric_file: bool|str = False
    ):
        self.word_file:JsonlIO[wordSeqItem] = JsonlIO(wordSeqItem, file_path=word_file, mode='r')
        self.word_dict = word_dict
        self.beyond_word_dict_value = beyond_word_dict_value
        self.cache_numeric_file = cache_numeric_file
        self.load_numeric_file()
        super().__init__(self.numeric_file.file_path, window, top, ideal_value, window_apply_method, filter_out_partial_overlapped_result)
    
    def load_numeric_file(self):
        if self.cache_numeric_file:
            cache_file_path = self.cache_numeric_file \
                if isinstance(self.cache_numeric_file, str) \
                    else (self.word_file.file_path.rsplit('.',1)[0] + '.numeric.jsonl')
            
            if pathlib.Path(cache_file_path).exists():
                self.numeric_file = JsonlIO(seqItem, file_path=cache_file_path)
            else:
                self.numeric_file = self.to_numeric_file(self.word_file, self.word_dict, self.beyond_word_dict_value, save_path=cache_file_path)

        else:
            self.numeric_file = self.to_numeric_file(self.word_file, self.word_dict, self.beyond_word_dict_value)

    @classmethod
    def to_numeric_file(
        cls, 
        word_file: JsonlIO[wordSeqItem], 
        word_dict: Dict[str, float|int], 
        beyond_word_dict_value: float|int = 0,
        save_path: str = None
    )->JsonlIO[seqItem]:
        def word2num(word: str)->float|int:
            if word in word_dict:
                return word_dict[word]
            else:
                return beyond_word_dict_value
        numeric_file: JsonlIO[seqItem] = JsonlIO(seqItem, file_path=save_path)
        for seq in word_file:
            item = seqItem(
                id=seq.id,
                seq=[word2num(i) for i in seq.seq]
            )
            numeric_file.add_line(item)
        return numeric_file
    
    def find(self, save_path = None):
        result = super().find(save_path=save_path)
        self.numeric_file.close()
        self.word_file.close()
        return result
