"""Tests for dispute history summaries."""

import csv

from src.csv_export import export_dispute_history
from src.module_data.dispute import format_dispute_rows, summarize_disputes


def test_summarize_disputes_tracks_fund_flow():
    disputes = [
        {
            "disputeId": "1",
            "metadata": {
                "dispute_id": "1",
                "dispute_category": "DISPUTE_CATEGORY_WARNING",
                "dispute_status": "DISPUTE_STATUS_RESOLVED",
                "open": False,
                "fee_total": "3000000",
                "slash_amount": "10000000",
                "burn_amount": "7000000",
                "voter_reward": "2000000",
            },
        },
        {
            "disputeId": "2",
            "metadata": {
                "dispute_id": "2",
                "dispute_category": "DISPUTE_CATEGORY_MINOR",
                "dispute_status": "DISPUTE_STATUS_VOTING",
                "open": True,
                "fee_total": "1000000",
                "slash_amount": "0",
                "burn_amount": "0",
                "voter_reward": "0",
            },
        },
    ]

    history = summarize_disputes(
        disputes,
        vote_results={
            1: "VOTE_RESULT_SUPPORT",
            2: "VOTE_RESULT_INVALID",
        },
    )

    assert history.total_disputes == 2
    assert history.open_disputes == 1
    assert history.total_fee_paid_loya == 4_000_000
    assert history.total_slash_amount_loya == 10_000_000
    assert history.total_burn_amount_loya == 7_000_000
    assert history.total_voter_reward_loya == 2_000_000
    assert history.total_burned_loya == 5_000_000
    assert history.counts_by_category["DISPUTE_CATEGORY_WARNING"] == 1
    assert history.counts_by_vote_result["VOTE_RESULT_SUPPORT"] == 1


def test_format_dispute_rows_shows_recent_fund_flow():
    history = summarize_disputes(
        [
            {
                "disputeId": "7",
                "metadata": {
                    "dispute_status": "DISPUTE_STATUS_RESOLVED",
                    "fee_total": "1500000",
                    "slash_amount": "3000000",
                    "burn_amount": "2500000",
                    "voter_reward": "500000",
                },
            }
        ],
        vote_results={7: "VOTE_RESULT_SUPPORT"},
    )

    headers, rows = format_dispute_rows(history)

    assert headers == [
        "ID",
        "Status",
        "Vote Result",
        "Fee Paid",
        "Slashed",
        "Burned",
        "Voter Rewards",
    ]
    assert rows == [
        [
            "7",
            "DISPUTE_STATUS_RESOLVED",
            "VOTE_RESULT_SUPPORT",
            "1.500 TRB",
            "3.000 TRB",
            "2.000 TRB",
            "0.500 TRB",
        ]
    ]


def test_export_dispute_history_writes_rows_and_summary(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    history = summarize_disputes(
        [
            {
                "disputeId": "3",
                "metadata": {
                    "fee_total": "2000000",
                    "slash_amount": "4000000",
                    "burn_amount": "3000000",
                    "voter_reward": "1000000",
                },
            }
        ]
    )

    export_dispute_history(history)

    with open(tmp_path / "data" / "dispute_history.csv", newline="") as csvfile:
        rows = list(csv.DictReader(csvfile))
    assert rows[0]["dispute_id"] == "3"
    assert rows[0]["fee_paid_trb"] == "2.000000"
    assert rows[0]["burned_trb"] == "2.000000"

    with open(tmp_path / "data" / "dispute_summary.csv", newline="") as csvfile:
        summary_rows = list(csv.DictReader(csvfile))
    assert summary_rows[0]["total_disputes"] == "1"
    assert summary_rows[0]["total_burned_trb"] == "2.000000"
