import contextlib
import os
from itertools import product


def grid_search(f, kwargs_grid, is_valid=None, random=False):
    """
    kwargs_grid is like { k_1: [arg_11, arg_12, ...],
                          k_2: [arg_21, arg_22, ...],
                          ... }
    Execute f(k_1: arg_11, k_2: arg_21)
            f(k_1: arg_11, k_2: arg_22)
            ...
    """
    list_of_kwargs_items = product(
        *[[(k, arg) for arg in l] for k, l in kwargs_grid.items()])
    list_of_kwargs = [dict(items) for items in list_of_kwargs_items]
    if random:
        list_of_kwargs = random.shuffle(list_of_kwargs)

    with open(os.devnull, 'w') as devnull:
        for kwargs in list_of_kwargs:
            if (is_valid is None or is_valid(**kwargs)):
                print(f'Executing {kwargs}')
                with contextlib.redirect_stdout(devnull):
                    found, stats = f(**kwargs)
                print(f'{found}\n{dict(stats)}\n')
