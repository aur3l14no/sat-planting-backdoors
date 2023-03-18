## Generating SAT Formulas with Planted Backdoors

### Usage

Setup [Optuna]([4. Easy Parallelization — Optuna 3.1.0 documentation](https://optuna.readthedocs.io/en/stable/tutorial/10_key_features/004_distributed.html#sphx-glr-tutorial-10-key-features-004-distributed-py))

Change the DB URL in exp_april.

Run

```
seq 10 | python exp_april.py --
```

---

```
python exp_april.py --test --total=200
```

Generate 200 instances to cnfs/april-final

---

```
python test_backdoor.py
```

Run solvers against the generated formulas.

---

Observe the results using *.ipynb.
