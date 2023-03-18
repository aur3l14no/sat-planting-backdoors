import pandas as pd
from tqdm import trange


from pysat.formula import CNF
from pysat.solvers import Solver


solvers = {
    'minisat22': [],
    'glucose41': [],
    'cadical153': [],
    'lingeling': []
}

df = pd.DataFrame(columns=['instance_id', 'solver_name',
                           'n_backdoor_leaves', 'backdoor_depth',
                           'whole_runtime', 'whole_decisions', 'whole_propagations',
                           'whole_restarts', 'whole_conflicts',
                           'leaves_runtime', 'leaves_decisions', 'leaves_propagations',
                           'leaves_restarts', 'leaves_conflicts',
                           'tautology_check_runtime'])

for i in trange(200):
    for solver_name in solvers.keys():
        cnf = CNF(from_file=f'cnfs/april-final/{i}.cnf')

        with open(f'cnfs/april-final/{i}.backdoor') as f:
            lines = f.readlines()
            backdoor_dnfs = [[int(l) for l in line.split()] for line in lines]

        # solve whole
        with Solver(name=solver_name, bootstrap_with=cnf, use_timer=True) as solver:
            solver.solve()
            whole_stats = solver.accum_stats()
            whole_runtime = solver.time()

        # check validity of backdoor
        with Solver(name=solver_name, use_timer=True) as solver:
            for backdoor in backdoor_dnfs:
                solver.add_clause([-l for l in backdoor])
            assert(solver.solve() is False)
            tautology_check_runtime = solver.time()

        # solve leaves
        leaves_runtime = 0
        with Solver(name=solver_name, bootstrap_with=cnf, use_timer=True) as solver:
            for backdoor in backdoor_dnfs:
                assert(solver.solve(assumptions=backdoor) is False)
            leaves_runtime += solver.time()
            leaves_stats = solver.accum_stats()

        row = {
            'instance_id': i,
            'solver_name': solver_name,
            'n_backdoor_leaves': len(backdoor_dnfs),
            'backdoor_depth': max(map(len, backdoor_dnfs)),
            'whole_runtime': whole_runtime,
            'whole_decisions': whole_stats['decisions'],
            'whole_propagations': whole_stats['propagations'],
            'whole_restarts': whole_stats['restarts'],
            'whole_conflicts': whole_stats['conflicts'],
            'leaves_runtime': leaves_runtime,
            'leaves_decisions': leaves_stats['decisions'],
            'leaves_propagations': leaves_stats['propagations'],
            'leaves_restarts': leaves_stats['restarts'],
            'leaves_conflicts': leaves_stats['conflicts'],
            'tautology_check_runtime': tautology_check_runtime
        }

        df = df.append(row, ignore_index=True)

df.to_csv('result.csv', index=False)
