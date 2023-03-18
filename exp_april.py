import math
import sys
import datetime as dt
import time
from argparse import ArgumentParser
from threading import Timer

import optuna
from pysat.solvers import Solver
from pysat.formula import CNF
from pysat.process import Processor
from rhorn import generate as random_rhorn
from sqlalchemy import NullPool

from joblib import Parallel, delayed

from generator.tree import TreeNode, generate_tree, LeafNode
from util.formula import remap_formula

TIMEOUT = 5


def bloom(node: TreeNode,
          n_leaf_clauses_n_leaf_vars_ratio,
          n_node_clauses_n_node_vars_ratio,
          **rhorn_kwargs):
    n_vars = len(node.free_vars)
    if isinstance(node, LeafNode):
        n_clauses = int(n_vars * n_leaf_clauses_n_leaf_vars_ratio)
    else:
        n_clauses = int(n_vars * n_node_clauses_n_node_vars_ratio)
    clauses = random_rhorn(n_vars=n_vars, n_clauses=n_clauses, **rhorn_kwargs)
    clauses = remap_formula(clauses, [0] + list(node.free_vars))
    node.clauses = clauses
    for child in node.children:
        bloom(child,
              n_leaf_clauses_n_leaf_vars_ratio,
              n_node_clauses_n_node_vars_ratio,
              **rhorn_kwargs)
    return node


def convert_to_cnf(node: TreeNode):
    #    l1 * l2 * l3 -> clause
    # == -l1 + -l2 + l3 + ...clause
    clauses = [
        [-lit for lit in node.assigned_lits] + clause
        for clause in node.clauses
    ]
    if len(node.children) == 0:  # leaf
        return clauses
    return [
        clause
        for child in node.children
        for clause in convert_to_cnf(child)
    ]


def f(trial: optuna.trial.Trial, debug=False, output_path=''):
    if debug:
        print(trial.value)
    n_vars = 1000
    n_repeats = 10
    clause_len_low = 1
    n_leaves = trial.suggest_int('n_leaves', 10, 1000)
    p_disjoint = trial.suggest_float('p_disjoint', 0, 1)
    grow_k = trial.suggest_float('grow_k', -1, 1)

    n_node_clauses_n_node_vars_ratio = trial.suggest_float(
        'n_node_clauses_n_node_vars_ratio', 0, 5)
    n_leaf_clauses_n_leaf_vars_ratio = trial.suggest_float(
        'n_leaf_clauses_n_leaf_vars_ratio', 3, 100)
    len_leaf_clause_high = trial.suggest_int('len_leaf_clause_high', 3, 10)
    neg_len_leaf_clause_g = trial.suggest_float(
        '-len_leaf_clause_g', 1e-13, 10, log=True)
    prob_0_pos_literal = trial.suggest_float('prob_0_pos_literal', 0, 1)
    rename_percent = trial.suggest_float('rename_percent', 0, 1)
    total = 0
    best_cnf = None
    best_score = 0
    for _ in range(n_repeats):
        timestamp = time.time()
        root, leaves = generate_tree(vars=frozenset(range(1, n_vars + 1)),
                                n_leaves=n_leaves,
                                disjoint_probability=p_disjoint,
                                grow_k=grow_k,
                                min_free_vars=len_leaf_clause_high)
        if debug:
            print(f'Growing in {time.time()-timestamp} seconds.')
        timestamp = time.time()
        root = bloom(root,
                     n_leaf_clauses_n_leaf_vars_ratio,
                     n_node_clauses_n_node_vars_ratio,
                     clause_len_low=clause_len_low,
                     clause_len_high=len_leaf_clause_high,
                     clause_len_g=-neg_len_leaf_clause_g,
                     p_0_pos=prob_0_pos_literal,
                     rename_percent=rename_percent)
        if debug:
            print(f'Blooming in {time.time()-timestamp} seconds.')
        timestamp = time.time()
        cnf = convert_to_cnf(root)
        if debug:
            print(f'Collecting in {time.time()-timestamp} seconds.')
        timestamp = time.time()
        cnf = CNF(from_clauses=cnf)
        if debug:
            print(f'To CNF in {time.time()-timestamp} seconds.')
            print(f'CNF has {cnf.nv} vars and {len(cnf.clauses)} clauses.')
        if debug or output_path != '':
            cnf.to_file(output_path)
            with open(output_path.replace('.cnf', '.backdoor'), 'w') as f:
                assignments = [
                    ' '.join(map(str, leaf.assigned_lits))
                    for leaf in leaves
                ]
                f.write('\n'.join(set(assignments)))
        timestamp = time.time()
        # Solve ORIGINAL formula
        with Solver(bootstrap_with=cnf, use_timer=True) as solver:
            timer = Timer(TIMEOUT, lambda s: s.interrupt(), [solver])
            timer.start()
            solver.solve_limited(expect_interrupt=True)
            runtime = solver.time()
            score = math.log(runtime) - math.log(len(cnf.clauses) + 1)
            # score = solver.accum_stats()['decisions']
            timer.cancel()
        total += score
        if score > best_score:
            best_cnf = cnf
            best_score = score
        if debug:
            print(f'Solved in {runtime} seconds.')
    if debug and best_cnf:
        best_cnf.to_file(
            f"cnfs/april-{dt.datetime.now().strftime(r'%Y-%m-%d-%H-%M-%S-%f')}.cnf")
    return total / n_repeats


if __name__ == '__main__':
    # optuna
    url = ''
    storage = optuna.storages.RDBStorage(
        url, engine_kwargs={"poolclass": NullPool})
    study = optuna.create_study(
        study_name="rhorn-pysat-final",
        direction="maximize",
        load_if_exists=True,
        storage=storage,
    )

    # args
    parser = ArgumentParser()
    # test mode?
    parser.add_argument('--test', action='store_true', default=False)
    # which trial's param to use?
    parser.add_argument('--trial', type=int)
    # how many cases to generate?
    parser.add_argument('--total', type=int, default=200)
    # how many cases are kept? (WIP)
    parser.add_argument('--topk', type=int, default=100)
    args = parser.parse_args()
    if args.test:
        base_dir = 'cnfs/april-final'
        Parallel(n_jobs=40, backend='multiprocessing')(delayed(f)(
            study.trials[args.trial]
            if args.trial else
            study.best_trial,
            output_path=f'{base_dir}/{i}.cnf',
            debug=False if args.total > 1 else True
        ) for i in range(args.total))
        # f(study.best_trial, debug=True)
    else:
        study.optimize(f, n_trials=100)
