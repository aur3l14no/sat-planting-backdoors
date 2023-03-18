import random

def random_backdoor_tree(vars, n_clauses):
    n_vars = len(vars)
    clauses = [[vars[0]], [-vars[0]]]

    for _ in range(n_clauses - 2):
        candidate_clauses = [c for c in clauses if len(c) < n_vars]
        if candidate_clauses:
            # randomly grow a leaf to a tree node
            clause = random.choice(candidate_clauses)
            rest = [v for v in vars
                    if v not in clause and -v not in clause]
            clauses.remove(clause)
            var = random.choice(rest)
            clauses.append(clause + [var])
            clauses.append(clause + [-var])

    for clause in clauses:
        yield tuple(clause)

if __name__ == '__main__':
    vars = random.sample(range(1, 101), k=10)
    print('Generating backdoor tree from vars:', vars)
    for clause in random_backdoor_tree(vars, 50):
        print(clause)
