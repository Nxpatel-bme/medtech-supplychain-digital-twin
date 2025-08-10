from digital_twin_v1 import simulate_single_echelon
import pandas as pd

def grid_search(s_values, S_offsets, target_fill=0.95, **sim_kwargs):
    rows = []
    for s in s_values:
        for off in S_offsets:
            S = s + off
            if S <= s: continue
            r = simulate_single_echelon(s=s, S=S, **sim_kwargs)
            rows.append({"s": s, "S": S, "fill_rate": r["fill_rate"], "total_cost": r["total_cost"],
                         "holding_cost": r["holding_cost"], "backorder_cost": r["backorder_cost"],
                         "ordering_cost": r["ordering_cost"]})
    df = pd.DataFrame(rows).sort_values("total_cost")
    feasible = df[df["fill_rate"] >= target_fill].copy()
    return df, feasible

if __name__ == "__main__":
    s_vals = list(range(80, 401, 20))
    S_offs = list(range(40, 401, 20))
    all_df, feas_df = grid_search(
        s_values=s_vals, S_offsets=S_offs, target_fill=0.95,
        demand_mean_per_day=30, leadtime_mean=7, leadtime_cv=0.4,
        horizon_days=365, warmup_days=60,
        holding_cost_per_unit_per_day=0.02, backorder_cost_per_unit_per_day=0.50,
        order_fixed_cost=50.0, order_unit_cost=0.0,
    )
    print("\nTop 5 policies by total cost (any fill rate):")
    print(all_df.head(5).to_string(index=False))
    if not feas_df.empty:
        best = feas_df.sort_values("total_cost").iloc[0]
        print("\nBest policy meeting ≥95% fill rate:")
        print(best.to_string(index=False))
    else:
        print("\nNo policy met the ≥95% target—try increasing S offsets or s range.")
