import random
import numpy as np
import numpy.random as npr
from util.math import power_random


def random_ksat(vars, n_vars, n_clauses, length_low=2, length_high=10):
    """Generate random clauses whose lengths ∝ power_random(lo, hi)"""
    # candidate vars
    vars = npr.sample(vars, k=n_vars)

    # length ∝ log-normal (mu, sigma)
    length = int(power_random(length_low, length_high + 1))

    clauses = npr.choice(vars, (n_clauses, length)) * \
        ((npr.randint(0, 2, (n_clauses, length))) * 2 - 1)

    return clauses


def random_rhorn(n_vars, n_clauses,
                 clause_len_low=1, clause_len_high=10, clause_len_g=-1,
                 p_0_pos=0.1,
                 rename_percent=0.):
    """Generate RHorn Clauses.

    Args:
        n_vars (int): number of vars
        n_clauses (int): number of clauses
        clause_len_* (int, optional): clause_len = int(power_random(length_low, length_high + 1), g=clause_len_g). Defaults to 1.
        p_0_pos (float, optional): probability of having 0 positive literals. Defaults to 0.1.
        rename_percent (float, optional): how many vars are renamed. Defaults to 0..

    Returns:
        list[Clause]: clauses
    """

    # candidate vars
    vars = range(1, n_vars + 1)

    # length ∝ power_random(lo, hi)
    lengths = power_random(clause_len_low, clause_len_high + 1,
                          g=clause_len_g, size=n_clauses).astype(int)

    clauses = [-npr.choice(vars, length, replace=False)
               for length in lengths]

    # bump one literal to be positive (horn)
    for i in range(n_clauses):
        if random.random() >= p_0_pos:
            to_bump = random.randint(0, clauses[i].shape[0] - 1)
            clauses[i][to_bump] = -clauses[i][to_bump]

    rename_vars = random.sample(vars, k=int(rename_percent * n_vars))
    clauses = [
        [-l if abs(l) in rename_vars else l for l in c]
        for c in clauses
    ]
    return clauses



def random_ca(vars, n_vars, n_clauses, length):
    pass


# FIXME?
# def random_valid_clause(vars, n_vars, n_clauses, length_low=1, length_high=10, ratio=0.95, one_valid=False):
#     """Generate 0-valid (default) and 1-valid clauses."""
#     # candidate vars
#     vars = npr.choices(vars, n_vars)

#     # length ∝ power_random(lo, hi)
#     length = int(power_random(length_low, length_high + 1))

#     sign = 1 if one_valid else -1

#     clause = [(-sign if random.random() < ratio else sign) * var
#               for var in random.sample(range(1, n_vars+1), length)]
#     to_bump = random.randint(0, length-1)
#     clause[to_bump] = sign * abs(clause[to_bump])

#     return tuple(clause)

if __name__ == '__main__':
    f = random_rhorn(1000, 5000,
                     clause_len_low=1, clause_len_high=10, clause_len_g=-1,
                     p_0_pos=0.1,
                     rename_percent=0.)
    print(f)
