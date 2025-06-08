from .base import windowFinderinJsonl, JsonlIO, seqItem, selectedWindow
from typing import Literal, List, Dict
import pathlib
import logging
import shutil
logger = logging.getLogger(__name__)

class wordSeqItem(seqItem):
    seq: str

class selectedWindowExtended(selectedWindow):
    seq: str = None

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
        logger.info(f'Loading numeric file for "{self.word_file.file_path}"...')
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
        logger.info(f'Numeric file loaded from "{self.numeric_file.file_path}".')

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
    
    def find(self, save_path = None, human_readable_idx: bool = True)->JsonlIO[selectedWindowExtended]:
        result = super().find(save_path=save_path)
        logger.info(f'Compute completed. Decyphering result, human readable index:{human_readable_idx}...')
        result = self.decypher_result(self.word_file, result, human_readable_idx)
        self.numeric_file.close()
        self.word_file.close()
        return result
    
    def decypher_result(
        self, word_file:JsonlIO[wordSeqItem], result_file:JsonlIO[selectedWindow], human_readable_idx: bool = True
    )->JsonlIO[selectedWindowExtended]:

        class cache:
            def __init__(self, cache_size:int=100): 
                self.cache_size = cache_size
                self.cache_ = dict()

            def add(self, key, value):
                if len(self.cache_) > self.cache_size:
                    self.cache_.clear()
                self.cache_[key] = value
            
            def get(self, key):
                if key in self.cache_:
                    return self.cache_[key]
                else:
                    return None
        
        first_cache = cache(cache_size=1000)
        second_cache = cache(cache_size=1000)

        def find_seq(id: str)->str:
            first = first_cache.get(id)
            second = second_cache.get(id)
            if (first is not None) or (second is not None):
                value = first or second
                first_cache.add(id, value)
                second_cache.add(id, value)
            else:
                for seq in word_file:
                    second_cache.add(id, seq.seq)
                    if seq.id == id:
                        first_cache.add(id, seq.seq)
                        break
            return first_cache.get(id)
        
        with JsonlIO[selectedWindowExtended](selectedWindowExtended) as tmp_result_file:
            for item in result_file:
                seq = find_seq(item.seq_id)
                seq = seq[item.start_idx:item.end_idx+1]
                if human_readable_idx:
                    item.start_idx += 1
                    item.end_idx += 1
                tmp_result_file.add_line(selectedWindowExtended(**item.model_dump(), seq=find_seq(item.seq_id)))

            result_file_path = result_file.file_path
            result_file.close()
            # 使用临时文件替换原始文件
            shutil.copy2(tmp_result_file.file_path, result_file_path)
            return JsonlIO(selectedWindowExtended,result_file_path)