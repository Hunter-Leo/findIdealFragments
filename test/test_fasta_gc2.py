import sys
sys.path.append('.')

from src.find_ideal_segments.tool.gccontent import findIdealGCContentSegmentsonFasta

def test_findIdealGCContentSegmentsonFasta():
    fasta_file = 'test.fasta'
    finder = findIdealGCContentSegmentsonFasta(
        fasta_file=fasta_file,
        window=10,
        top=10,
        ideal_value=0.5,
    )
    result = finder.find(save_path='result.jsonl')
    pass

if __name__ == '__main__':
    test_findIdealGCContentSegmentsonFasta()