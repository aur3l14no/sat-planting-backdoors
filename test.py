from pysat.solvers import Solver
from pysat.examples.genhard import PHP
from threading import Timer

cnf = PHP(nof_holes=10)  # PHP20 is too hard for a SAT solver
m = Solver(bootstrap_with=cnf.clauses, use_timer=True)

def interrupt(s):
    s.interrupt()

timer = Timer(0.1, interrupt, [m])
timer.start()

print(m.solve_limited(expect_interrupt=True))

print(m.time())

m.delete()
