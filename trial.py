from dataclasses import dataclass, field
import shutil
import os
import random
import time
import math
from typing import Callable, List, Iterable
import datetime as dt
from generator import community_attachment
from collections import defaultdict
from skopt.callbacks import CheckpointSaver
from skopt import gp_minimize, gbrt_minimize
from skopt.space import Integer
from skopt.space import Real
from skopt.utils import use_named_args
from scipy.optimize import OptimizeResult

from util.formula import to_dimacs, transform_to_ksat, remap_formula
from util.solver import DimacsOutput, solve_file, solve_clauses, SolverOpt
from util.math import power_random
from generator.backdoor import random_backdoor_tree

Clause = Iterable[Iterable[int]]

@dataclass
class GenOpt:
    n_vars: int
    n_backdoor_vars: int
    n_leaves: int
    # 接受 GenOpt 和其余参数 kwargs, 返回 clauses
    leaf_generator: Callable[['GenOpt', dict | None], Clause]
    leaf_generator_kwargs: dict | None


@dataclass
class TrialReport:
    leaves_output: List[DimacsOutput] = field(compare=False)
    whole_output: DimacsOutput = field(compare=False)
    score: float = field(init=False)

    def __post_init__(self):
        leaves_runtime = [x.runtime for x in self.leaves_output]
        self.score = 2 * math.log(1 + self.whole_output.runtime) - math.log(1 + sum(leaves_runtime))

def generate_and_run(name: str, gen_opt: GenOpt, solver_opt: SolverOpt = SolverOpt()) -> TrialReport:
    """生成 SAT 公式 (Backdoor Tree + Leaf)，对每个 leaf 分别跑 solver，最后再对整体公式跑 solver.
    返回总共的统计数据.
    """
    # name = dt.datetime.now().strftime(r'%Y-%m-%d-%H-%M-%S-%f')
    os.mkdir(f'cnfs/{name}')
    backdoor_vars = random.sample(
        range(1, gen_opt.n_vars+1), k=gen_opt.n_backdoor_vars)
    clauses = []
    assert (gen_opt.n_backdoor_vars <= gen_opt.n_vars)
    leaves_output = []

    # Generate main formula
    for i, dnf_clause in enumerate(random_backdoor_tree(backdoor_vars, gen_opt.n_leaves)):
        # 生成叶子节点
        # Generate leaves
        leaf = gen_opt.leaf_generator(gen_opt)
        # Test the hardness of leaves
        res = solve_clauses(leaf, f'cnfs/{name}/leaf-{i}.cnf', '', solver_opt)
        leaves_output.append(res)
        # Append backdoor structure to each clause in the leaf
        for clause in leaf:
            clauses.append([-l for l in dnf_clause] + list(clause))
    # scramble
    mapping = [0] + random.sample(range(1, gen_opt.n_vars+1), gen_opt.n_vars)
    clauses = remap_formula(clauses, mapping)
    whole_output = solve_clauses(
        clauses, f'cnfs/{name}/main.cnf', '', solver_opt)
    report = TrialReport(leaves_output, whole_output)

    # Save info
    with open(f'cnfs/{name}/info.txt', 'w') as f:
        f.write('Generation Options:\n' + str(gen_opt))
        f.write('\n\n')
        f.write('Solver Options:\n' + str(solver_opt))
        f.write('\n\n')
        f.write('Report:\n' + str(report))
    return report

