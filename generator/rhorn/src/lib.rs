use std::collections::BTreeSet;

use pyo3::prelude::*;
use rand::{seq::SliceRandom, Rng};

fn power_random(a: f64, b: f64, g: f64) -> f64 {
    let mut rng = rand::thread_rng();
    let u: f64 = rng.gen();
    (u * (b.powf(g) - a.powf(g)) + a.powf(g)).powf(1.0 / g)
}

/// Generate random horn formula as [[...], [...], ...]
#[pyfunction]
fn generate(
    n_vars: usize,
    n_clauses: usize,
    clause_len_low: usize,
    clause_len_high: usize,
    clause_len_g: f64,
    p_0_pos: f64,
    rename_percent: f64,
) -> PyResult<Vec<Vec<i64>>> {
    let vars: Vec<i64> = (1..=n_vars).map(|x| x as i64).collect();

    let mut rng = rand::thread_rng();

    let mut clauses = Vec::new();
    for _ in 0..n_clauses {
        let length =
            power_random(clause_len_low as f64, clause_len_high as f64, clause_len_g) as usize;
        let mut clause: Vec<i64> = vars.choose_multiple(&mut rng, length).cloned().collect();
        // make every literal negative
        clause.iter_mut().map(|l| *l = -*l).count();
        if rng.gen::<f64>() >= p_0_pos {
            // flip one literal positive
            let i = rng.gen_range(0..length);
            clause[i] = -clause[i];
        }
        clauses.push(clause);
    }

    // flip renamed vars
    let renamed_vars: BTreeSet<i64> = vars
        .choose_multiple(&mut rng, (rename_percent * n_vars as f64).floor() as usize)
        .cloned()
        .collect();
    for clause in &mut clauses {
        for literal in clause {
            if renamed_vars.contains(&literal.abs()) {
                *literal = -*literal;
            }
        }
    }

    Ok(clauses)
}

/// A Python module implemented in Rust.
#[pymodule]
fn rhorn(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(generate, m)?)?;
    Ok(())
}
