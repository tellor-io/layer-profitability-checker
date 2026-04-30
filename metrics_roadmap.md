# Metrics Roadmap

This repo should stay focused on profitability calculations, CLI display, and CSV
exports. The roadmap below tracks useful metrics for the command-line tool and
the data files it produces.

## Available now

- Network stake distribution: active, jailed, unbonding, unbonded, median stake,
  and active validator stake distribution.
- Block-time sampling: average block time, blocks per day, and reporting cadence
  assumptions.
- Time-based rewards: event-based inflationary and extra rewards, split into
  reporter and validator pools.
- Reporting costs: recent submit-value gas and fee analysis, projected daily,
  monthly, and annual reporting costs.
- Reporter APRs: current reporter APR table, weighted average APR, median APR,
  and break-even stake.
- APR by total stake: scenario sweep for current rewards and fees across larger
  total network stake levels.
- Tips: current tips by configured query data, claimable account tips, total tips,
  and user tip totals.
- Historical disputes: all-time dispute count, open disputes, fee paid, slashed
  amount, burned amount, voter rewards, recent dispute rows, and CSV exports.

## Small extensions

- Add date/window filters to dispute exports once the REST response exposes or
  reliably preserves dispute timestamps.
- Add CSV schema tests that verify expected columns for every exported file.
- Add optional CLI flags to skip slow live sections such as tips or disputes.
- Add a single machine-readable run manifest that lists generated CSV files,
  endpoint URLs, chain ID, and sample height range.

## Larger extensions

- Historical time series storage for tips, APRs, and disputes across repeated
  runs.
- Integration value or notional inputs for security coverage ratios.
- TRB price input support for optional USD-denominated operator-cost views.
- Reconciled selector/delegator economics once commission split math is validated
  against the Layer reporter module implementation.
