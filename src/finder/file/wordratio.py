from .base import windowFinderinJsonl, JsonlIO, seqItem
from typing import Literal, List, Dict

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
    ):
        self.word_file:JsonlIO[wordSeqItem] = JsonlIO(wordSeqItem, file_path=word_file, mode='r')
        self.word_dict = word_dict
        self.beyond_word_dict_value = beyond_word_dict_value
        self.numeric_file = self.to_numeric_bundle(self.word_file)
        super().__init__(self.numeric_file.file_path, window, top, ideal_value, window_apply_method, filter_out_partial_overlapped_result)
    
    def to_numeric_bundle(self, word_file: JsonlIO[wordSeqItem])->JsonlIO[seqItem]:
        def word2num(word: str)->float|int:
            if word in self.word_dict:
                return self.word_dict[word]
            else:
                return self.beyond_word_dict_value
        numeric_file: JsonlIO[seqItem] = JsonlIO(seqItem)
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
