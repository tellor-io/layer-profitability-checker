"""Dispute module queries and historical dispute fund-flow summaries."""

from __future__ import annotations

import json
import subprocess
import urllib.parse
from dataclasses import dataclass
from typing import Any

from ..chain_data.rpc_client import TellorRPCClient

LOYA_PER_TRB = 1_000_000


@dataclass
class DisputeRecord:
    dispute_id: int
    category: str
    status: str
    is_open: bool
    fee_paid_loya: int
    slash_amount_loya: int
    burn_amount_loya: int
    voter_reward_loya: int
    burned_loya: int
    vote_result: str


@dataclass
class DisputeHistory:
    records: list[DisputeRecord]
    counts_by_category: dict[str, int]
    counts_by_status: dict[str, int]
    counts_by_vote_result: dict[str, int]
    total_fee_paid_loya: int
    total_slash_amount_loya: int
    total_burn_amount_loya: int
    total_voter_reward_loya: int
    total_burned_loya: int

    @property
    def total_disputes(self) -> int:
        return len(self.records)

    @property
    def open_disputes(self) -> int:
        return sum(1 for record in self.records if record.is_open)


def _curl_get_json(url: str, timeout_s: int = 120) -> dict[str, Any]:
    result = subprocess.run(
        [
            "curl",
            "-s",
            "--max-time",
            str(timeout_s),
            "-X",
            "GET",
            url,
            "-H",
            "accept: application/json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    output = result.stdout.strip()
    return json.loads(output) if output else {}


def _int_field(data: dict[str, Any], name: str) -> int:
    try:
        return int(data.get(name) or 0)
    except (TypeError, ValueError):
        return 0


def get_all_disputes(
    rpc_client: TellorRPCClient,
    *,
    limit_per_page: int = 200,
    reverse: bool = False,
    timeout_s: int = 120,
) -> list[dict[str, Any]]:
    """Fetch historical disputes from the Layer REST API."""
    disputes: list[dict[str, Any]] = []
    next_key: str | None = None

    while True:
        params = {
            "pagination.limit": str(limit_per_page),
            "pagination.reverse": "true" if reverse else "false",
        }
        if next_key:
            params["pagination.key"] = next_key

        query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        url = f"{rpc_client.rest_endpoint}/tellor-io/layer/dispute/disputes?{query}"
        response = _curl_get_json(url, timeout_s=timeout_s)

        disputes.extend(response.get("disputes", []) or [])

        pagination = response.get("pagination", {}) or {}
        next_key = pagination.get("next_key")
        if not next_key:
            break

    return disputes


def get_vote_result(
    rpc_client: TellorRPCClient, dispute_id: int, *, timeout_s: int = 120
) -> str | None:
    url = f"{rpc_client.rest_endpoint}/tellor-io/layer/dispute/vote-result/{dispute_id}"
    try:
        response = _curl_get_json(url, timeout_s=timeout_s)
    except (subprocess.SubprocessError, json.JSONDecodeError):
        return None
    return response.get("vote_result")


def summarize_disputes(
    disputes: list[dict[str, Any]],
    vote_results: dict[int, str] | None = None,
) -> DisputeHistory:
    records: list[DisputeRecord] = []
    counts_by_category: dict[str, int] = {}
    counts_by_status: dict[str, int] = {}
    counts_by_vote_result: dict[str, int] = {}

    total_fee_paid_loya = 0
    total_slash_amount_loya = 0
    total_burn_amount_loya = 0
    total_voter_reward_loya = 0
    total_burned_loya = 0

    vote_results = vote_results or {}

    for dispute in disputes:
        metadata = dispute.get("metadata", {}) or {}
        try:
            dispute_id = int(metadata.get("dispute_id") or dispute.get("disputeId") or 0)
        except (TypeError, ValueError):
            dispute_id = 0

        category = metadata.get("dispute_category") or "UNKNOWN"
        status = metadata.get("dispute_status") or "UNKNOWN"
        vote_result = vote_results.get(dispute_id) or "UNKNOWN"
        fee_paid_loya = _int_field(metadata, "fee_total")
        slash_amount_loya = _int_field(metadata, "slash_amount")
        burn_amount_loya = _int_field(metadata, "burn_amount")
        voter_reward_loya = _int_field(metadata, "voter_reward")
        burned_loya = max(0, burn_amount_loya - voter_reward_loya)

        records.append(
            DisputeRecord(
                dispute_id=dispute_id,
                category=category,
                status=status,
                is_open=bool(metadata.get("open")),
                fee_paid_loya=fee_paid_loya,
                slash_amount_loya=slash_amount_loya,
                burn_amount_loya=burn_amount_loya,
                voter_reward_loya=voter_reward_loya,
                burned_loya=burned_loya,
                vote_result=vote_result,
            )
        )

        counts_by_category[category] = counts_by_category.get(category, 0) + 1
        counts_by_status[status] = counts_by_status.get(status, 0) + 1
        counts_by_vote_result[vote_result] = counts_by_vote_result.get(vote_result, 0) + 1
        total_fee_paid_loya += fee_paid_loya
        total_slash_amount_loya += slash_amount_loya
        total_burn_amount_loya += burn_amount_loya
        total_voter_reward_loya += voter_reward_loya
        total_burned_loya += burned_loya

    records.sort(key=lambda record: record.dispute_id)

    return DisputeHistory(
        records=records,
        counts_by_category=counts_by_category,
        counts_by_status=counts_by_status,
        counts_by_vote_result=counts_by_vote_result,
        total_fee_paid_loya=total_fee_paid_loya,
        total_slash_amount_loya=total_slash_amount_loya,
        total_burn_amount_loya=total_burn_amount_loya,
        total_voter_reward_loya=total_voter_reward_loya,
        total_burned_loya=total_burned_loya,
    )


def fetch_dispute_history(
    rpc_client: TellorRPCClient,
    *,
    timeout_s: int = 120,
    vote_result_limit: int = 50,
) -> DisputeHistory:
    disputes = get_all_disputes(rpc_client, timeout_s=timeout_s)
    vote_results: dict[int, str] = {}

    if vote_result_limit <= 0:
        return summarize_disputes(disputes)

    for dispute in disputes[-vote_result_limit:]:
        metadata = dispute.get("metadata", {}) or {}
        try:
            dispute_id = int(metadata.get("dispute_id") or dispute.get("disputeId") or 0)
        except (TypeError, ValueError):
            continue
        if dispute_id <= 0:
            continue
        vote_result = get_vote_result(rpc_client, dispute_id, timeout_s=timeout_s)
        if vote_result:
            vote_results[dispute_id] = vote_result

    return summarize_disputes(disputes, vote_results)


def format_dispute_rows(
    history: DisputeHistory, *, max_rows: int = 10
) -> tuple[list[str], list[list[str]]]:
    headers = [
        "ID",
        "Status",
        "Vote Result",
        "Fee Paid",
        "Slashed",
        "Burned",
        "Voter Rewards",
    ]
    rows: list[list[str]] = []

    for record in history.records[-max_rows:]:
        rows.append(
            [
                str(record.dispute_id),
                "OPEN" if record.is_open else record.status,
                record.vote_result,
                f"{record.fee_paid_loya / LOYA_PER_TRB:,.3f} TRB",
                f"{record.slash_amount_loya / LOYA_PER_TRB:,.3f} TRB",
                f"{record.burned_loya / LOYA_PER_TRB:,.3f} TRB",
                f"{record.voter_reward_loya / LOYA_PER_TRB:,.3f} TRB",
            ]
        )

    return headers, rows
