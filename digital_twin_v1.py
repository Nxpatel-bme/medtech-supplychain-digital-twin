# digital_twin_v1.py
import simpy
import numpy as np
import pandas as pd

def make_poisson_demand(lmbda: float, rng):
    def sample(): return int(rng.poisson(lmbda))
    return sample

def make_lognormal_leadtime(mean_days: float, cv: float, rng, min_day: int = 1):
    sigma_sq = np.log(1.0 + cv**2); sigma = np.sqrt(sigma_sq)
    mu = np.log(mean_days) - 0.5 * sigma_sq
    def sample():
        x = rng.lognormal(mu, sigma)
        return max(min_day, int(round(x)))
    return sample

class SingleEchelonSystem:
    def __init__(self, env, params, rng):
        self.env, self.rng = env, rng
        self.holding_cost = params["holding_cost_per_unit_per_day"]
        self.backorder_cost = params["backorder_cost_per_unit_per_day"]
        self.order_fixed_cost = params.get("order_fixed_cost", 0.0)
        self.order_unit_cost = params.get("order_unit_cost", 0.0)
        self.on_hand = params.get("initial_inventory", 0)
        self.sample_demand = params["demand_sampler"]
        self.sample_leadtime = params["lead_time_sampler"]
        self.backorders = 0; self.pipeline_qty = 0
        self.total_demand = 0; self.total_filled = 0
        self.cost_holding = 0.0; self.cost_backorder = 0.0; self.cost_ordering = 0.0
        self.history = []

    @property
    def inventory_position(self): return self.on_hand + self.pipeline_qty - self.backorders

    def place_order(self, qty):
        if qty <= 0: return
        self.pipeline_qty += qty
        self.cost_ordering += self.order_fixed_cost + self.order_unit_cost * qty
        L = self.sample_leadtime()
        self.env.process(self._delivery_after(L, qty))

    def _delivery_after(self, lead_time_days, qty):
        yield self.env.timeout(lead_time_days)
        self.pipeline_qty -= qty
        if self.backorders > 0:
            used = min(qty, self.backorders)
            self.backorders -= used; qty -= used
        self.on_hand += qty

    def step_day(self, s, S, day, warmup_days):
        demand = self.sample_demand()
        self.total_demand += demand
        filled = min(self.on_hand, demand); self.on_hand -= filled
        self.backorders += demand - filled; self.total_filled += filled
        if self.inventory_position <= s:
            self.place_order(max(0, S - self.inventory_position))
        if day >= warmup_days:
            self.cost_holding += self.on_hand * self.holding_cost
            self.cost_backorder += self.backorders * self.backorder_cost
        self.history.append({"day": day,"on_hand": self.on_hand,"backorders": self.backorders,
                             "pipeline": self.pipeline_qty,"demand": demand,"filled": filled,
                             "IP": self.inventory_position})

def simulate_single_echelon(
    s, S, horizon_days=365, warmup_days=60, seed=42,
    demand_mean_per_day=30, leadtime_mean=7, leadtime_cv=0.4,
    holding_cost_per_unit_per_day=0.02, backorder_cost_per_unit_per_day=0.50,
    order_fixed_cost=50.0, order_unit_cost=0.0, initial_inventory=None,
):
    rng = np.random.default_rng(seed); env = simpy.Environment()
    if initial_inventory is None: initial_inventory = S
    params = {
        "holding_cost_per_unit_per_day": holding_cost_per_unit_per_day,
        "backorder_cost_per_unit_per_day": backorder_cost_per_unit_per_day,
        "order_fixed_cost": order_fixed_cost, "order_unit_cost": order_unit_cost,
        "initial_inventory": initial_inventory,
        "demand_sampler": make_poisson_demand(demand_mean_per_day, rng),
        "lead_time_sampler": make_lognormal_leadtime(leadtime_mean, leadtime_cv, rng, 1),
    }
    sys = SingleEchelonSystem(env, params, rng)

    def run_days():
        day = 0
        while day < horizon_days:
            yield env.timeout(1); day += 1
            sys.step_day(s, S, day, warmup_days)

    env.process(run_days()); env.run()

    eff_dem = sys.total_demand - sum(h["demand"] for h in sys.history if h["day"] <= warmup_days)
    eff_fill = sys.total_filled - sum(h["filled"] for h in sys.history if h["day"] <= warmup_days)
    fill_rate = 0.0 if eff_dem == 0 else eff_fill / eff_dem
    total_cost = sys.cost_holding + sys.cost_backorder + sys.cost_ordering

    return {"s": s, "S": S, "fill_rate": fill_rate,
            "holding_cost": sys.cost_holding, "backorder_cost": sys.cost_backorder,
            "ordering_cost": sys.cost_ordering, "total_cost": total_cost,
            "horizon_days": horizon_days - warmup_days, "history": pd.DataFrame(sys.history)}

if __name__ == "__main__":
    res = simulate_single_echelon(s=150, S=350)
    print(f"(s,S)=({res['s']},{res['S']})  fill_rate={res['fill_rate']:.3f}  total_cost=${res['total_cost']:.2f}")
