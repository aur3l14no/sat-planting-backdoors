#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
using namespace pybind11::literals;

#include <getopt.h>
#include <stdlib.h>
#include <iostream>
#include <math.h>
#include <vector>
#include <stdio.h>

using namespace std;

double computeProbability(double Q, int c)
{
	return Q + 1 / (double)c;
}

void computeN2C(vector<int> &n2c, double P, int c, int k)
{
	int rn = rand();
	double rd = ((double)rn) / (RAND_MAX);

	if (rd <= P)
	{ // All variables in the same community
		rn = rand();
		for (int i = 0; i < k; i++)
			n2c[i] = rn % c;
	}
	else
	{ // All variables in distict communitites
		for (int i = 0; i < k; i++)
		{
			bool used = false;
			do
			{
				used = false;
				rn = rand();
				for (int j = 0; j < i && !used; j++)
				{
					if (n2c[j] == rn % c)
						used = true;
				}
			} while (used);
			n2c[i] = rn % c;
		}
	}
}

void computeClause(vector<int> &n2c, vector<int> &clause, int k, int n, int c)
{
	int rn;
	for (int j = 0; j < k; j++)
	{
		// Random variable in the community
		//   avoiding tautologies with previous literals
		int var;
		bool tautology = false;
		do
		{
			tautology = false;
			rn = rand();
			var = rn % (n2c[j] * n / c - (n2c[j] + 1) * n / c) + n2c[j] * n / c + 1;
			for (int l = 0; l < j && !tautology; l++)
			{
				if (abs(clause[l]) == var)
				{
					tautology = true;
				}
			}
		} while (tautology);

		// Polarity of the variable
		if (rn > (RAND_MAX / 2))
			var = -var;

		clause[j] = var;
	}
}

vector<vector<int>> generateFormula(int n, int m, int k, int c, double Q, int seed)
{
	vector<vector<int>> clauses(m, vector<int>(k, 0));

	// Compute the probability P, according to c and Q
	double P = computeProbability(Q, c);

	srand(seed);

	// Iterate for each clause
	for (int i = 0; i < m; i++)
	{

		// n2c is the community of each literal
		vector<int> n2c(k, 0);
		computeN2C(n2c, P, c, k);

		// Compute the clause
		vector<int> clause(k);
		computeClause(n2c, clauses[i], k, n, c);
	}
	return clauses;
}

PYBIND11_MODULE(community_attachment, m)
{
	m.doc() = "SAT formula generator based on community attachment model.";
	m.def("generate", &generateFormula, "Generate formula", "n"_a=1000, "m"_a = 4250, "k"_a = 3, "c"_a = 80, "Q"_a = 0.8, "seed"_a = 0);
}
