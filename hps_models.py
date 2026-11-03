"""Deterministic, testable Mendelian and meiosis teaching models.

The software models a simplified diploid, fully dominant single-locus system.
No data generated here are real biological observations.
"""
import random
from collections import Counter

ALLELES = {'A','a'}
VALID_GENOTYPES = ('AA','Aa','aa')


def genotype(g):
    if g not in VALID_GENOTYPES: raise ValueError('只支持AA、Aa和aa')
    return g


def gametes(g):
    genotype(g)
    return list(g)  # both entries count, so AA -> A,A, Aa -> A,a


def offspring_distribution(mother, father):
    gm, gf = gametes(mother), gametes(father)
    counts = Counter(''.join(sorted((a,b),key=lambda x:(x=='a',x))) for a in gm for b in gf)
    return {g:counts[g]/4 for g in VALID_GENOTYPES}


def expected_phenotypes(mother, father):
    dist=offspring_distribution(mother,father)
    return {'高茎':dist['AA']+dist['Aa'],'矮茎':dist['aa']}


def simulate_cross(mother, father, sample_size=64, seed=42):
    genotype(mother);genotype(father)
    if type(sample_size) is not int or sample_size<4 or sample_size>2000:raise ValueError('样本数须在4—2000之间')
    if type(seed) is not int or not 0<=seed<=2**31-1:raise ValueError('随机种子必须为合法整数')
    rng=random.Random(seed)
    gm,gf=gametes(mother),gametes(father)
    genos=Counter()
    for _ in range(sample_size):
        a=rng.choice(gm); b=rng.choice(gf)
        child=''.join(sorted((a,b),key=lambda x:(x=='a',x)))
        genos[child]+=1
    assert sum(genos.values())==sample_size
    return {'mother':mother,'father':father,'n':sample_size,'seed':seed,
            'genotypes':{g:genos[g] for g in VALID_GENOTYPES},
            'phenotypes':{'高茎':genos['AA']+genos['Aa'],'矮茎':genos['aa']},
            'expected':expected_phenotypes(mother,father),
            'model':'单基因完全显性、随机配子结合'}


def comparison_for_numbers(n,seed):
    """Independent seeded draws for F2 and testcross, for evidence charts."""
    return (simulate_cross('Aa','Aa',n,seed),simulate_cross('Aa','aa',n,seed+1))


# Counts are per *one cell* unless the stage explicitly is a gamete or zygote.
# Chromatids follow standard high-school convention: attached sisters count after replication,
# whereas after centromere separation chromatids are no longer counted as attached chromatids.
MEIOSIS_STAGES=[
 {'id':'G1','title':'复制前','count':(4,4,0),'cells':1,
  'action':'辨认两对同源染色体','right':'按长度和来源辨认两对同源染色体',
  'wrong':['把两条相同颜色的复制产物当成同源染色体','把四条任意配成两对'],
  'explain':'这个简化模型中，两对同源染色体长短不同；每一对来自父母双方的对应染色体。复制前单个细胞含4条染色体与4个DNA分子。'},
 {'id':'S','title':'完成DNA复制','count':(4,8,8),'cells':1,
  'action':'判断复制后数量','right':'染色体仍为4条，DNA分子变为8个',
  'wrong':['染色体变成8条，DNA仍是4个','染色体和DNA都不变'],
  'explain':'DNA复制后，每条染色体由两条姐妹染色单体构成，着丝粒未分裂，故染色体仍是4条。'},
 {'id':'PAIR','title':'减Ⅰ前期：联会','count':(4,8,8),'cells':1,
  'action':'正确选择联会对象','right':'长红与长蓝配对，短红与短蓝配对',
  'wrong':['将两条姐妹染色单体当成一对同源','长染色体与短染色体任意配对'],
  'explain':'联会是两条同源染色体配对，一对复制后的同源染色体构成一个四分体，含4条染色单体。'},
 {'id':'MI','title':'减Ⅰ后期：同源分离','count':(4,8,8),'cells':1,
  'action':'判断本次分离的对象','right':'同源染色体分向两极，姐妹染色单体仍相连',
  'wrong':['姐妹染色单体先分开','染色体先全部消失'],
  'explain':'减数第一次分裂的关键是同源染色体分离；每条染色体的两条姐妹染色单体在此阶段仍连在一起。'},
 {'id':'END1','title':'减Ⅰ结束：两个细胞','count':(2,4,4),'cells':2,
  'action':'按每个子细胞计数','right':'每个子细胞2条染色体、4个DNA分子',
  'wrong':['每个子细胞4条染色体、8个DNA分子','每个子细胞2条染色体、2个DNA分子'],
  'explain':'减Ⅰ结束形成两个细胞；对每一个细胞计数，染色体减半但仍保持复制状态。'},
 {'id':'MII','title':'减Ⅱ后期：姐妹分离','count':(4,4,0),'cells':2,
  'action':'判断着丝粒分裂的结果','right':'在尚未分裂完成的单个细胞中，染色体暂为4条',
  'wrong':['在任何阶段单个细胞染色体一直是2条','同源染色体第二次分离'],
  'explain':'减Ⅱ后期着丝粒分裂，姐妹染色单体成为独立染色体，所以在同一个尚未分裂的细胞内染色体数暂时增加。'},
 {'id':'GAMETES','title':'四个配子','count':(2,2,0),'cells':4,
  'action':'检查配子的染色体组成','right':'每个配子含2条染色体，且每对同源仅取一条',
  'wrong':['每个配子含4条染色体','每个配子必有来自父母双方的全部同源染色体'],
  'explain':'从一个起始细胞的模型中得到4个单倍体细胞（相当于精子形成过程的简化展示）；真实卵细胞发生过程存在不均等分裂。'},
 {'id':'FERT','title':'受精恢复二倍体','count':(4,4,0),'cells':1,
  'action':'解释染色体数目的恢复','right':'两个各n=2的配子结合，受精卵恢复2n=4',
  'wrong':['受精使每个配子都先复制一次染色体','染色体数目不与配子形成有关'],
  'explain':'减数分裂形成n的配子，受精结合使二倍体染色体数恢复2n；两过程共同保证有性生殖中的数目延续。'},
]


def meiosis_step(stage_id,choice):
    stage=next((s for s in MEIOSIS_STAGES if s['id']==stage_id),None)
    if stage is None:raise ValueError('无效的分裂阶段')
    if choice not in [stage['right']]+stage['wrong']: raise ValueError('无效的实验操作')
    return {'stage':stage_id,'correct':choice==stage['right'],
            'explanation':stage['explain'],'chromosomes':stage['count'][0],
            'dna':stage['count'][1],'chromatids':stage['count'][2],
            'cells':stage['cells']}
