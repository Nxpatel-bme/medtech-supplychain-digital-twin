# MedTech Supply Chain Digital Twin

A supply-chain digital twin that optimizes (s, S) inventory policies to hit 95% service with ~18% lower cost under uncertain lead times.

> Personal project simulating a hypothetical MedTech supply chain to explore inventory policy optimization.
> Built to explore stochastic systems, inventory theory, and cost–service trade-offs.

---

## Features
- **Simulator**: Python + SimPy model of a multi-echelon inventory system (Supplier → Distribution Center → Clinics-ready design)
- **Policy Search**: Grid search over (s, S) reorder policies
- **Optimization**: Finds the lowest-cost policy that meets a target service level (default ≥95%)
- **Visualization**: Cost vs. fill-rate curve with best policy highlighted
- **Optional UI**: Streamlit dashboard for interactive “what-if” analysis

---

## Repo Layout
digital_twin_v1.py      # Core simulator
policy_search_v1.py     # Grid search + plotting
requirements.txt        # Project dependencies
README.md               # Project overview
results/
  cost_vs_fill.png      # Example output plot


## Installation & Usage

1. ** Clone this repo**
```bash
git clone https://github.com/Nxpatel-bme/medtech-supplychain-digital-twin.git
cd medtech-supplychain-digital-twin

2. pip install -r requirements.txt

3. python policy_search_v1.py
