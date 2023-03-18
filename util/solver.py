import re
import time
import subprocess as sp
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple
from .formula import to_dimacs


@dataclass
class DimacsOutput:
    result: str
    runtime: float


@dataclass
class SolverOpt:
    solver: str = 'kissat'
    timeout: float | None = None
    args: Tuple[str] = ()


def parse_output(output) -> DimacsOutput:
    """Parse dimacs output."""
    result = re.search(r'^s (SAT|UNSAT)', output, re.MULTILINE).group(1)
    # runtime = re.search(r'^c total real time since initialization:\s+([\d\.]+)\s+seconds', output, re.MULTILINE).group(1)
    # runtime = float(runtime)
    return DimacsOutput(result, 0)


def solve_file(input_file, solver_opt: SolverOpt = SolverOpt()) -> DimacsOutput:
    """Solve `input_file` with `solver`, return DimacsOutput."""
    try:
        time_begin = time.time()
        completed = sp.run([solver_opt.solver] + list(solver_opt.args) + [input_file],
                           capture_output=True, timeout=solver_opt.timeout)
        time_end = time.time()
        dimacs_output = parse_output(completed.stdout.decode())
        dimacs_output.runtime = time_end - time_begin
        return dimacs_output
    except sp.TimeoutExpired:
        # use timeout*2 as runtime, similar to PAR2 score in SAT-COMP
        return DimacsOutput('UNKNOWN', solver_opt.timeout*2)


def solve_clauses(clauses, tmp_file='test.cnf', comment='', solver_opt: SolverOpt = SolverOpt()) -> DimacsOutput:
    """Solve `clauses` with `solver`, return DimacsOutput."""
    comment = re.sub('^', 'c ', comment, re.M)
    input_file = tmp_file
    with open(input_file, 'w') as f:
        f.write(comment + '\n' + to_dimacs(clauses))
    return solve_file(input_file, solver_opt)
