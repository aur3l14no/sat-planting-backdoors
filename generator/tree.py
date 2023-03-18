from dataclasses import dataclass, field
from enum import Enum, auto
import random
import math
import pprint
from typing import Type


class TreeNodeType(Enum):
    DISJOINT = auto()
    VAR = auto()


@dataclass
class TreeNode:
    children: list['TreeNode'] = field(default_factory=list)
    free_vars: frozenset[int] = frozenset()
    assigned_lits: frozenset[int] = frozenset()
    parent: Type['TreeNode'] | None = None
    clauses: list[list[int]] = field(default_factory=list)


@dataclass
class LeafNode(TreeNode):
    pass

@dataclass
class DisjointTreeNode(TreeNode):
    pass


@dataclass
class PivotTreeNode(TreeNode):
    pivot: int | None = None


def grow_leaf(leaf: TreeNode, disjoint_probability=0.5, min_free_vars=10):
    if len(leaf.children) > 0:
        raise Exception('Not a leaf!', leaf)
    if len(leaf.free_vars) < min_free_vars * 2 :
        return None  # failed
    if random.random() < disjoint_probability:
        free_vars_subset = frozenset(random.sample(
            tuple(leaf.free_vars), k=len(leaf.free_vars) // 2))
        new_leaf = DisjointTreeNode(
            parent=leaf.parent,
            free_vars=leaf.free_vars,
            assigned_lits=leaf.assigned_lits,
            children=[
                LeafNode(
                    assigned_lits=leaf.assigned_lits,
                    free_vars=free_vars_subset,
                ),
                LeafNode(
                    assigned_lits=leaf.assigned_lits,
                    free_vars=leaf.free_vars - free_vars_subset
                )
            ]
        )
        for child in new_leaf.children:
            child.parent = new_leaf
        return new_leaf
    else:
        pivot = random.choice(tuple(leaf.free_vars))
        new_leaf = PivotTreeNode(
            parent=leaf.parent,
            free_vars=leaf.free_vars,
            assigned_lits=leaf.assigned_lits,
            pivot=pivot,
            children=[
                LeafNode(
                    free_vars=leaf.free_vars - frozenset([pivot]),
                    assigned_lits=leaf.assigned_lits | frozenset([pivot])
                ),
                LeafNode(
                    free_vars=leaf.free_vars - frozenset([pivot]),
                    assigned_lits=leaf.assigned_lits | frozenset([-pivot])
                )
            ]
        )
        for child in new_leaf.children:
            child.parent = new_leaf
        return new_leaf


def generate_tree(vars: frozenset[int], n_leaves: int, grow_k: float = 0, **kwargs):
    root = LeafNode(free_vars=vars)
    # leaves = [root]
    leaf_depth_pairs = [(root, 1)]
    for _ in range(n_leaves):
        # leaf = random.choice(leaves)
        leaf, depth = random.choices(leaf_depth_pairs,
                                     weights=map(lambda x: math.e ** (grow_k * x[1]),
                                                 leaf_depth_pairs),
                                     k=1)[0]
        new_leaf = grow_leaf(leaf, **kwargs)
        if new_leaf:
            # fix parent.children
            if leaf.parent:  # not root
                leaf.parent.children.remove(leaf)
                leaf.parent.children.append(new_leaf)
            else:
                root = new_leaf
            # add new_leaf.childrent to leaves
            # leaves.remove(leaf)
            # leaves.extend(new_leaf.children)
            leaf_depth_pairs.remove((leaf, depth))
            leaf_depth_pairs.extend([(child, depth+1) for child in new_leaf.children])
    # return root, leaves
    return root, [leaf[0] for leaf in leaf_depth_pairs]


if __name__ == '__main__':
    root, leaves = generate_tree(frozenset(range(10)), 5, grow_k=0, min_free_vars=1)
    pprint.pprint(root)
