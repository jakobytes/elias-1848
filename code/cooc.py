import argparse
import csv
import math
import numpy as np
from scipy.sparse import dok_matrix
import sys
import tqdm


def progress(x, show_progress=False):
    return tqdm.tqdm(x) if show_progress else x


def _key(d, key_cols):
    #return (d['poem_id'], d['pos'])
    return tuple(d[k] for k in key_cols)


def read_input(stream):
    return list(csv.DictReader(stream))


class CoocCounter:
    def __init__(self, vocab, window_size=0):
        self.vocab = vocab
        self.window_size = window_size
        self.word_ids = { word: i for i, word in enumerate(vocab) }
        self.m = dok_matrix((len(vocab), len(vocab)), dtype=np.uint32)
        self.freqs = np.zeros(len(vocab))
        self.total = 0

    def add(self, words):
        if self.window_size == 0 or self.window_size >= len(words):
            self.add_window(words)
        else:
            for i in range(len(words)-self.window_size):
                self.add_window(words[i:i+self.window_size])

    def add_window(self, words):
        words_s = set(words)
        for w1 in words_s:
            for w2 in words_s:
                if w1 != w2:
                    self.m[self.word_ids[w1],self.word_ids[w2]] += 1
            self.freqs[self.word_ids[w1]] += 1
        self.total += 1

    def items(self):
        x, y = self.m.nonzero()
        return [(self.vocab[x[i]], self.vocab[y[i]]) for i in range(x.shape[0])]

    def get(self, x, y):
        n_xy = self.m[self.word_ids[x], self.word_ids[y]]
        n_x = self.freqs[self.word_ids[x]]
        n_y = self.freqs[self.word_ids[y]]
        n = self.total
        return n_xy, n_x, n_y, n

    def freq(self, x, y):
        return self.m[self.word_ids[x], self.word_ids[y]]

    def dice(self, x, y):
        n_xy, n_x, n_y, n = self.get(x, y)
        return 2*n_xy / (n_x + n_y)

    def mutinf(self, x, y):
        n_xy, n_x, n_y, n = self.get(x, y)
        return math.log((n*n_xy)/(n_x*n_y))

    def logl(self, x, y):
    
        # this calculates an expression of type x*log(x)
        # that often repeats in the formula
        def xlogx(x):
            return x*math.log(x) if x > 0 else 0

        n_xy, n_x, n_y, n = self.get(x, y)
        logl = xlogx(n) - xlogx(n_x) - xlogx(n_y) + xlogx(n_xy) \
               + xlogx(n-n_x-n_y+n_xy) \
               + xlogx(n_x-n_xy) + xlogx(n_y-n_xy) \
               - xlogx(n-n_x) - xlogx(n-n_y)
        return 2*logl

# Co-occurrence significance measures

#def dice(n_ab, n_a, n_b, n):
#    return 2*n_ab / (n_a + n_b)
#
#
#def mutinf(n_ab, n_a, n_b, n):
#    return math.log((n*n_ab)/(n_a*n_b))
#
#
#def logl(n_ab, n_a, n_b, n):
#    
#    # this calculates an expression of type x*log(x)
#    # that often repeats in the formula
#    def xlogx(x):
#        return x*math.log(x) if x > 0 else 0
#    
#    logl = xlogx(n) - xlogx(n_a) - xlogx(n_b) + xlogx(n_ab) \
#           + xlogx(n-n_a-n_b+n_ab) \
#           + xlogx(n_a-n_ab) + xlogx(n_b-n_ab) \
#           - xlogx(n-n_a) - xlogx(n-n_b)
#    
#    return 2*logl


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Verse-level co-occurrence computation.')
    parser.add_argument(
        '-k', '--key',
        help='The columns (comma-separated) to treat as the ID of a text unit')
    parser.add_argument(
        '-p', '--show-progress', action='store_true',
        help='Show progress bars..')
    parser.add_argument(
        '--word-col', default='text', help='The column to treat as the word (the co-occurring unit).')
    parser.add_argument(
        '-t', '--threshold', type=float, default=3.84,
        help='Log-likelihood threshold to output co-occurrences.')
    parser.add_argument(
        '-w', '--window-size', type=int, default=0,
        help='Window size (0=the whole text unit).')
    return parser.parse_args()


def main():
    args = parse_arguments()
    key_cols = args.key.split(',')
    data = read_input(sys.stdin)
    words = list(set(d[args.word_col] for d in data))
    counter = CoocCounter(words, window_size=args.window_size)
    #word_ids = { word: i for i, word in enumerate(words) }
    #m = dok_matrix((len(words), len(words)), dtype=np.uint32)
    #freqs = np.zeros(len(words))
    #key, words, total = None, [], 0
    key, cur_words = None, []
    for d in progress(data, args.show_progress):
        if _key(d, key_cols) != key:
            if cur_words:
                counter.add(cur_words)
            key, cur_words = _key(d, key_cols), []
        cur_words.append(d[args.word_col])
    if cur_words:
        counter.add(cur_words)
    writer = csv.DictWriter(
        sys.stdout, lineterminator='\n',
        fieldnames=(args.word_col+'_1', args.word_col+'_2',
                    'freq', 'logl', 'dice', 'mutinf'))
    writer.writeheader()
    for x, y in progress(counter.items(), args.show_progress):
        ll = counter.logl(x, y)
        if ll > args.threshold:
            writer.writerow({
                args.word_col+'_1': x,
                args.word_col+'_2': y,
                'freq': counter.freq(x, y),
                'logl': ll,
                'dice': counter.dice(x, y),
                'mutinf': counter.mutinf(x, y)
            })


if __name__ == '__main__':
    main()

