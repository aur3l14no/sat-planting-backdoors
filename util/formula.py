import math
from enum import Enum
from typing import List, Tuple, Union

# n := v | ~v | \land ns | \lor ns | n -> n

class FormulaNode:
    """Tree-like data structure for SAT formula.
    - LIT, int
    - NOT, [Node]
    - AND, [Node, Node, ...]
    - OR,  [Node, Node, ...]
    - TO,  [Node, Node]
    """

    class Type(Enum):
        LIT = 0  # special
        NOT = 1  # 1-ary
        AND = 2  # n-ary
        OR = 3  # n-ary
        TO = 4  # 2-ary

    def __init__(self, type: Type, children: Union[List, int]) -> None:
        self.type = type
        self.children = children

    @staticmethod
    def make(type: str, children: Union[List, int]) -> 'FormulaNode':
        if type == 'LIT':
            return FormulaNode(FormulaNode.Type.LIT, children)
        elif type == 'NOT':
            return FormulaNode(FormulaNode.Type.NOT, children)
        elif type == 'AND':
            return FormulaNode(FormulaNode.Type.AND, children)
        elif type == 'OR':
            return FormulaNode(FormulaNode.Type.OR, children)
        elif type == 'TO':
            return FormulaNode(FormulaNode.Type.TO, children)
        else:
            raise Exception('Wrong type', type)

    def braced(self) -> str:
        if self.type == FormulaNode.Type.LIT:
            return f'{self!s}'
        else:
            return f'({self!s})'

    def __str__(self) -> str:
        if self.type == FormulaNode.Type.LIT:
            return str(self.children)
        elif self.type == FormulaNode.Type.NOT:
            return '-' + self.children.braced()
        elif self.type == FormulaNode.Type.AND:
            return ' /\\ '.join(map(lambda x: x.braced(), self.children))
        elif self.type == FormulaNode.Type.OR:
            return ' \\/ '.join(map(lambda x: x.braced(), self.children))
        elif self.type == FormulaNode.Type.TO:
            return self.children[0].braced() + ' -> ' + self.children[1].braced()

    def max_var(self) -> int:
        if self.type == FormulaNode.Type.LIT:
            return abs(self.children)
        else:
            return max(map(lambda x: x.max_var(), self.children))

    @staticmethod
    def from_cnf(clauses: List[Tuple]) -> 'FormulaNode':
        return FormulaNode(FormulaNode.Type.AND, [
            FormulaNode(FormulaNode.Type.OR, [
                FormulaNode(FormulaNode.Type.LIT, literal)
                for literal in clause
            ])
            for clause in clauses])

    def simplify(self) -> 'FormulaNode':
        """Eliminate unnecessary nestings like --x and (a or (b or c)).
        Update `self` and return updated `self`.
        """
        if self.type != FormulaNode.Type.LIT:
            for child in self.children:
                child.simplify()
        if self.type == FormulaNode.Type.NOT:
            if self.children.type == FormulaNode.Type.NOT:
                self.type = self.children.children[0].type
                self.children = self.children.children[0].children
            elif self.children.type == FormulaNode.Type.LIT:
                self.type = FormulaNode.Type.LIT
                self.children = self.children.children
        elif self.type == FormulaNode.Type.OR:
            children = []
            for child in self.children:
                if child.type == FormulaNode.Type.OR:
                    children.extend(child.children)
                else:
                    children.append(child)
            self.children = children
        elif self.type == FormulaNode.Type.AND:
            children = []
            for child in self.children:
                if child.type == FormulaNode.Type.AND:
                    children.extend(child.children)
                else:
                    children.append(child)
            self.children = children
        # elif self.type == FormulaNode.Type.TO:
        #     self.children = self.children[0]
        #     # TODO

    def tseitin_transform(self) -> List[Tuple]:
        def make_sym():
            make_sym.counter += 1
            return make_sym.counter

        def rec(node: FormulaNode):
            if node.type == FormulaNode.Type.LIT:
                return node.children, []
            elif node.type == FormulaNode.Type.NOT:
                sym, clauses = rec(node.children)
                # x <-> -sym
                new_sym = make_sym()
                return new_sym, clauses + \
                    [(sym, new_sym), (-sym, -new_sym)]
            elif node.type == FormulaNode.Type.AND:
                result = [rec(x) for x in node.children]
                syms = [r[0] for r in result]
                clauses = [item for r in result for item in r[1]]
                # x <-> /\ syms
                new_sym = make_sym()
                return new_sym, clauses + \
                    [tuple([-s for s in syms] + [new_sym])] + \
                    [(-new_sym, s) for s in syms]
            elif node.type == FormulaNode.Type.OR:
                result = [rec(x) for x in node.children]
                syms = [r[0] for r in result]
                clauses = [item for r in result for item in r[1]]
                # x <-> \/ syms
                new_sym = make_sym()
                return new_sym, clauses + \
                    [tuple(syms + [-new_sym])] + \
                    [(new_sym, -s) for s in syms]
            elif node.type == FormulaNode.Type.TO:
                l_sym, l_clauses = rec(node.children[0])
                r_sym, r_clauses = rec(node.children[1])
                # x <-> l_sym -> r_sym
                new_sym = make_sym()
                return new_sym, l_clauses + r_clauses + \
                    [(-new_sym, -l_sym, r_sym), (l_sym, new_sym), (-r_sym, new_sym)]

        make_sym.counter = self.max_var()
        # if self.type == FormulaNode.Type.AND:
        #     clauses = []
        #     for child in self.children:
        #         sym, cs = rec(child)
        #         clauses.extend(cs)
        sym, clauses = rec(self)
        return [(sym, )] + clauses

def transform_to_ksat(clauses, k):
    n_vars = max([abs(lit) for clause in clauses for lit in clause])
    result = []
    for clause in clauses:
        if len(clause) <= k:
            result.append(clause)
        else:
            n_vars += 1
            result.append(tuple(clause[:k-1] + (n_vars, )))
            for i in range(k-1, len(clause), k-2):
                if len(clause)-1-i < k-2:
                    result.append(tuple(clause[i:i+k-2]) + (-n_vars,))
                else:
                    result.append(tuple(clause[i:i+k-2]) + (-n_vars, n_vars+1))
                n_vars += 1
    return result

def copysign_int(a, b):
    return abs(a) * (1 if b >= 0 else -1)

def remap(clause, mapping):
    return [copysign_int(mapping[abs(literal)], literal) for literal in clause]

def remap_formula(formula, mapping):
    return [remap(clause, mapping) for clause in formula]

def to_dimacs(clauses):
    n_vars = max([abs(lit) for clause in clauses for lit in clause])
    header = f'p cnf {n_vars} {len(clauses)}\n'
    body = '\n'.join([' '.join(map(str, clause)) + ' 0' for clause in clauses])
    return header + body


if __name__ == '__main__':
    # (x1 /\ x2) -> ((x1 \/ x2 \/ x3) /\ (-x1 \/ x2 \/ x3))
    formula_1 = FormulaNode(FormulaNode.Type.TO, [
        FormulaNode(FormulaNode.Type.AND, [
                    FormulaNode(FormulaNode.Type.LIT, 1),
                    FormulaNode(FormulaNode.Type.LIT, 2)
                    ]),
        FormulaNode(FormulaNode.Type.AND, [
            FormulaNode(FormulaNode.Type.OR, [
                    FormulaNode(FormulaNode.Type.LIT, 1),
                    FormulaNode(FormulaNode.Type.LIT, 2),
                    FormulaNode(FormulaNode.Type.LIT, 3)
                    ]),
            FormulaNode(FormulaNode.Type.OR, [
                FormulaNode(FormulaNode.Type.LIT, -1),
                FormulaNode(FormulaNode.Type.LIT, 2),
                FormulaNode(FormulaNode.Type.LIT, 3)
            ])
        ])
    ])

    # (x1 + -x2 + (S11) + (S12)) * (-x1 + x2 + (S21) + (S22))
    # S11 = (x1 + x2)
    # S12 = (x1 + x3)
    # S21 = (-x1 + -x2)
    # S22 = (-x1 + x3)

    formula_2 = FormulaNode.make('AND', [
        FormulaNode.make('OR', [
            FormulaNode.make('LIT', 1),
            FormulaNode.make('LIT', -2),
            FormulaNode.make('OR', [
                FormulaNode.make('LIT', 1),
                FormulaNode.make('LIT', 2),
            ]),
            FormulaNode.make('OR', [
                FormulaNode.make('LIT', 1),
                FormulaNode.make('LIT', 3),
            ]),
        ]),
        FormulaNode.make('OR', [
            FormulaNode.make('LIT', -1),
            FormulaNode.make('LIT', 2),
            FormulaNode.make('OR', [
                FormulaNode.make('LIT', -1),
                FormulaNode.make('LIT', -2),
            ]),
            FormulaNode.make('OR', [
                FormulaNode.make('LIT', -1),
                FormulaNode.make('LIT', 3),
            ]),
        ])
    ])

    print('Formula 1')
    print(formula_1)
    print(to_dimacs(formula_1.tseitin_transform()))

    print('Formula 2')
    print(formula_2)
    formula_2.simplify()
    print(formula_2)
    print(to_dimacs(formula_2.tseitin_transform()))
