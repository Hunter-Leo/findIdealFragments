from ..io.jsonl import JsonlIO
from ..finder.file.wordratio import findIdealWordRatioInSlidingWindow, wordSeqItem
from Bio import SeqIO
from Bio.SeqRecord import SeqRecord
import click
import json
from typing import Literal, Iterator
import pathlib
import logging
logger = logging.getLogger(__name__)
# 创建一个基本的日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class findIdealGCContentSegmentsonFasta(findIdealWordRatioInSlidingWindow):
    def __init__(
        self, 
        fasta_file: str, 
        window: int, 
        top:int,
        ideal_value: float,
        beyond_word_dict_value: float|int = 0,
        dict_mode: Literal['GC', 'AT']|dict = 'GC',
        window_apply_method: Literal['sum', 'mean'] = 'mean',
        filter_out_partial_overlapped_result: bool = True,
        cache: bool = True
    ):
        # generate class annotation below
        '''Find the ideal GC content segments in the DNA fasta file.
        '''
        if isinstance(dict_mode, dict):
            word_dict = dict_mode
        elif dict_mode == 'GC':
            word_dict = {'G': 1, 'C': 1, 'g':1, 'c':1}
        else:
            word_dict = {'A': 1, 'T': 1, 'a':1, 't':1}

        self.cache = cache
        self.cache_jsonl_file = fasta_file.rsplit('.',1)[0] + '.jsonl'
        if cache or (not pathlib.Path(self.cache_jsonl_file).exists()):
            self.fasta2jsonl(fasta_file, jsonl_file=self.cache_jsonl_file)

        super().__init__(
            word_file=self.cache_jsonl_file,
            word_dict=word_dict,
            window=window,
            top=top,
            ideal_value=ideal_value,
            window_apply_method=window_apply_method,
            filter_out_partial_overlapped_result=filter_out_partial_overlapped_result,
            beyond_word_dict_value=beyond_word_dict_value,
            cache_numeric_file=cache
        )
    
    @classmethod
    def fasta2jsonl(cls, fasta_file: str, jsonl_file:str):
        '''Convert the DNA fasta file to jsonl file.
        '''
        logger.info(f'Converting "{fasta_file}" to "{jsonl_file}"...')
        with JsonlIO(wordSeqItem, file_path=jsonl_file, mode='w') as jio:
            jio.empty()
            parser: Iterator[SeqRecord] = SeqIO.parse(fasta_file, 'fasta')
            for seq in parser:
                jio.add_line(wordSeqItem(id=seq.id, seq=str(seq.seq)))
    

    def find(self, save_path = None):
        result = super().find(save_path=save_path)
        if not self.cache:
            pathlib.Path(self.cache_jsonl_file).unlink()
        return result

@click.command()
@click.option('-i', '--input', 'input_file', required=True, help='The input DNA fasta file.')
@click.option('-w', '--window', 'window', required=True, type=int, help='The sliding window size.')
@click.option('-t', '--top', 'top', required=False, type=int, default=10, help='The top number of the ideal segments.')
@click.option('-v', '--value', 'ideal_value', required=True, type=float, help='The ideal value of the sliding window.')
@click.option('-o', '--output', 'output_file', required=True, help='The output file.')
@click.option('-d', '--dict', 'dict_mode', required=False, default='GC',type=click.Choice(['GC', 'AT']), help='The dictionary mode. It can be "GC" or "AT".')
@click.option('-m', '--method', 'window_apply_method', required=False, default='mean',type=click.Choice(['mean', 'sum']), help='The method to apply the sliding window. It can be "sum" or "mean".')
@click.option('-f', '--filter', 'filter_out_partial_overlapped_result', required=False, default=True,type=click.BOOL, help='Whether to filter out the partial overlapped result.')
@click.option('-b', '--beyond', 'beyond_word_dict_value', required=False, default=0, type=float, help='The value of the beyond word dict.')
@click.option('-c', '--cache', 'cache', required=False, default=True, type=click.BOOL, help='Whether to cache the jsonl file.')
def run_tool(input_file, window, top, ideal_value, output_file, dict_mode, window_apply_method, filter_out_partial_overlapped_result, beyond_word_dict_value, cache):
    finder = findIdealGCContentSegmentsonFasta(
        fasta_file=input_file,
        window=window,
        top=top,
        ideal_value=ideal_value,
        dict_mode=dict_mode,
        window_apply_method=window_apply_method,
        filter_out_partial_overlapped_result=filter_out_partial_overlapped_result,
        beyond_word_dict_value=beyond_word_dict_value,
        cache=cache
    )
    result = finder.find(save_path=output_file)
    logger.info(f'Found {len(result)} ideal segments, result saved in "{output_file}".')

if __name__ == '__main__':
    run_tool()