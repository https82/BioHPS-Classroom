"""Lightweight reproducible local retrieval for short Chinese biology questions.

Important: character TF-IDF is NOT an embedding model or a neural semantic search.
It is complementary to curated aliases, avoids third-party models and works offline.
"""
from collections import Counter
from functools import lru_cache
import math
import re

STOP = set('为什么为何怎么如何请问什么哪些是否是不是到底能够可以一个一种它们他们这个那个有没如果这种解释简单一下问题原因'.split())
# Topic-specific equivalences. Every mapping is explicit and editable.
EXPANSIONS = [
    ('鲸', '鲸鱼'), ('海豚', '哺乳动物'), ('鲸鱼', '哺乳动物'),
    ('小鱼', '鱼类'), ('鲨鱼', '鱼类'),
    ('光合', '光合作用'), ('光照', '阳光'), ('呼吸', '气体交换'),
    ('心跳', '心脏'), ('心率', '心跳'), ('血管', '血液循环'),
    ('发芽', '萌发'), ('胚', '种子'), ('吃东西', '营养'),
    ('变绿', '叶绿素'), ('向太阳', '向光'), ('弯向光', '生长素'),
    ('变异', '遗传'), ('细胞核', '染色体'), ('免疫', '抗体'),
    ('打疫苗', '疫苗'), ('流汗', '出汗'), ('眼睛', '视觉'),
    ('珊瑚礁', '生态系统'), ('谁吃谁', '食物链'),
]


def normalize(value):
    return ''.join(re.findall(r'[\u4e00-\u9fffA-Za-z0-9]+', str(value or ''))).lower()


def grams(text):
    s = normalize(text)
    if not s:
        return []
    if len(s) <= 2:
        return [s]
    return [s[i:i+2] for i in range(len(s)-1)] + [s[i:i+3] for i in range(len(s)-2)]


def expand_question(question):
    q = normalize(question)
    extra = []
    for trigger, equivalent in EXPANSIONS:
        if normalize(trigger) in q and normalize(equivalent) not in q:
            extra.append(equivalent)
    return q + (' ' + ' '.join(extra) if extra else '')


def _signature(cards):
    return tuple((str(c.get('id','')),str(c.get('title','')),
                  '|'.join(map(str,c.get('keywords',[]))),str(c.get('summary',''))) for c in cards)


@lru_cache(maxsize=12)
def _prepare(signature):
    # Binary TF-IDF avoids a longer card dominating just because it has more text.
    df = Counter()
    documents=[]
    for uid,title,keywords,summary in signature:
        terms=set(grams((title+' ')*3 + (keywords+' ')*2 + summary))
        documents.append(terms)
        df.update(terms)
    size=len(documents)
    idf={term:math.log((1+size)/(1+freq))+1.0 for term,freq in df.items()}
    norms=[math.sqrt(sum(idf[g]**2 for g in doc)) for doc in documents]
    return documents,idf,norms


def cosine_scores(question,cards):
    if not cards:
        return []
    signature=_signature(cards)
    docs,idf,norms=_prepare(signature)
    q_terms=set(grams(expand_question(question)))
    q_terms.intersection_update(idf)
    q_norm=math.sqrt(sum(idf[g]**2 for g in q_terms))
    if not q_norm:
        return [0.0]*len(cards)
    result=[]
    for doc,norm in zip(docs,norms):
        if not norm:
            result.append(0.0)
        else:
            result.append(sum(idf[g]**2 for g in q_terms & doc)/(q_norm*norm))
    return result
