- 非平衡二叉树
- 通过 Tseitin 变换将生成公式准确固定在 phase transition 空间内 (3SAT)
- EasySAT dump clause_DB
- 改用 DNF
- 3-9 安全/软工(FSE,ASE)/逆向会议

## Backdoor Tree + Random-k-SAT Leaves

```python
trial_loop_backdoor_plus_random_tail(n_vars=1000, dnf_size=4, backdoor_size=2, tail_n_clause=4000, tail_min_len=3, tail_max_len=3)
```

Works.


## How about converting to K-SAT?

n_vars, n_clauses

->

Each clause whose length is > k now produces |clause|-k vars and |clause|-k clauses

roughly

n_vars <- n_vars + n_clause * (|clause| - k)
n_clauses <- n_clauses + n_clause * (|clause| - k)

We want n_clauses / n_vars -> p
