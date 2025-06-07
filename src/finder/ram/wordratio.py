from .base import windowFinderinBundleSeqs, seqBundle, seqItem
from typing import Literal, List, Dict

class wordSeqItem(seqItem):
    seq: str

class wordSeqBundle(seqBundle):
    seqs: List[wordSeqItem]

class findIdealWordRatioInSlidingWindow(windowFinderinBundleSeqs):
    def __init__(
        self, 
        word_bundle: wordSeqBundle, 
        word_dict: Dict[str, float|int],
        window: int, 
        top:int,
        ideal_value: float,
        window_apply_method: Literal['sum', 'mean'] = 'mean',
        filter_out_partial_overlapped_result: bool = True,
        beyond_word_dict_value: float|int = 0,
    ):
        self.word_bundle = word_bundle
        self.word_dict = word_dict
        self.beyond_word_dict_value = beyond_word_dict_value
        bundle = self.to_numeric_bundle(word_bundle)
        super().__init__(bundle, window, top, ideal_value, window_apply_method, filter_out_partial_overlapped_result)
    
    def to_numeric_bundle(self, word_bundle: wordSeqBundle)->seqBundle:
        def word2num(word: str)->float|int:
            if word in self.word_dict:
                return self.word_dict[word]
            else:
                return self.beyond_word_dict_value
        bundle = seqBundle(id=word_bundle.id, seqs=[])
        for seq in word_bundle.seqs:
            item = seqItem(
                id=seq.id,
                seq=[word2num(i) for i in seq.seq]
            )
            bundle.seqs.append(item)
        return bundle