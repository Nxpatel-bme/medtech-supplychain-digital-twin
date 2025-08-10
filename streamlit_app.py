# streamlit_app.py
import streamlit as st
import plotly.express as px
import pandas as pd

# we reuse your simulator/search
from policy_search_v1 import grid_search

st.set_page_config(page_title="MedTech Supply Chain Digital Twin", layout="wide")

st.title("MedTech Supply Chain — Inventory Policy Explorer")

with st.sidebar:
    st.header("Scenario inputs")

    # demand & lead time uncertainty
    demand = st.slider("Mean daily demand (units)", 1, 200, 30, 1)
    lt_mean = st.slider("Supplier lead time mean (days)", 1, 60, 7, 1)
    lt_cv = st.slider("Supplier lead time CV", 0.05, 1.50, 0.40, 0.05)

    # costs
    h_cost = st.number_input("Holding cost / unit / day ($)", min_value=0.0, value=0.02, step=0.01, format="%.4f")
    b_cost = st.number_input("Backorder penalty / unit / day ($)", min_value=0.0, value=0.50, step=0.05, format="%.2f")
    of_cost = st.number_input("Order fixed cost ($)", min_value=0.0, value=50.0, step=5.0, format="%.2f")
    ou_cost = st.number_input("Order unit cost ($/unit)", min_value=0.0, value=0.00, step=0.10, format="%.2f")

    # service target
    target_fill = st.slider("Target service level (fill rate)", 0.80, 0.99, 0.95, 0.01)

    # search ranges
    st.divider()
    st.caption("Search space")
    s_min, s_max = st.slider("s range (min, max)", 0, 1200, (80, 400), 20)
    s_step = st.select_slider("s step", options=[10, 20, 25, 50, 100], value=20)

    off_min, off_max = st.slider("S - s offset (min, max)", 20, 1200, (40, 400), 20)
    off_step = st.select_slider("offset step", options=[10, 20, 25, 50, 100], value=20)

    # simulation settings
    st.divider()
    horizon = st.slider("Simulation horizon (days)", 90, 1095, 365, 30)
    warmup = st.slider("Warmup days (ignored in metrics)", 0, 180, 60, 10)
    seed = st.number_input("Random seed", value=42, step=1)

run_btn = st.button("Run policy search", type="primary")

if run_btn:
    with st.spinner("Simulating policies…"):
        s_vals = list(range(s_min, s_max + 1, s_step))
        S_offs = list(range(off_min, off_max + 1, off_step))

        # run the grid search (uses your simulator)
        all_df, feas_df = grid_search(
            s_values=s_vals,
            S_offsets=S_offs,
            target_fill=target_fill,
            demand_mean_per_day=demand,
            leadtime_mean=lt_mean,
            leadtime_cv=lt_cv,
            horizon_days=horizon,
            warmup_days=warmup,
            holding_cost_per_unit_per_day=h_cost,
            backorder_cost_per_unit_per_day=b_cost,
            order_fixed_cost=of_cost,
            order_unit_cost=ou_cost,
            seed=seed,
        )

    st.success(f"Simulated {len(all_df)} policies")

    # scatter: cost vs service, color by s, size by S
    fig = px.scatter(
        all_df,
        x="fill_rate", y="total_cost",
        color="s", size="S",
        hover_data=["s", "S", "holding_cost", "backorder_cost", "ordering_cost"],
        title="Cost vs. Fill Rate (all policies)"
    )
    fig.add_vline(x=target_fill, line_dash="dash", annotation_text=f"Target {target_fill:.2f}")
    st.plotly_chart(fig, use_container_width=True)

    # recommended policy
    col1, col2 = st.columns([1, 1])
    if not feas_df.empty:
        best = feas_df.sort_values("total_cost").iloc[0]
        with col1:
            st.subheader("Recommended policy (meets target at lowest cost)")
            st.markdown(f"**(s, S) = ({int(best['s'])}, {int(best['S'])})**")
            st.metric("Fill rate", f"{best['fill_rate']:.3f}")
            st.metric("Total cost", f"${best['total_cost']:.2f}")
        with col2:
            st.caption("Top 10 feasible (sorted by total cost)")
            st.dataframe(feas_df.sort_values("total_cost").head(10), use_container_width=True)
    else:
        st.warning("No policy met the service target. Increase s or the S offset range and try again.")

    # download CSV of results
    def _to_csv(df: pd.DataFrame) -> bytes:
        return df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download all results (CSV)",
        data=_to_csv(all_df),
        file_name="policy_search_results.csv",
        mime="text/csv"
    )
else:
    st.info("Set parameters in the sidebar, then click **Run policy search**.")
  
