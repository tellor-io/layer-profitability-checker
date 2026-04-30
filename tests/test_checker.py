"""Tests for checker CLI selection flow."""

from src import checker


def test_interactive_network_selection_reprompts_on_invalid_choice(
    monkeypatch, sample_config
):
    answers = iter(["9", "2"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    network = checker.interactive_network_selection(sample_config)

    assert network["name"] == "testnet"


def test_main_interactive_mode_prompts_for_mode_then_network(
    monkeypatch, sample_config
):
    calls = []
    answers = iter(["1", "2"])

    monkeypatch.setattr(checker, "load_config", lambda _: sample_config)
    monkeypatch.setattr("sys.argv", ["prof-check"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    monkeypatch.setattr(
        checker,
        "run_profitability_mode",
        lambda config, network, stake_trb=None: calls.append(
            ("profitability", config, network["name"], stake_trb)
        ),
    )

    checker.main()

    assert calls == [("profitability", sample_config, "testnet", None)]


def test_direct_profitability_tty_prompts_for_network(monkeypatch, sample_config):
    calls = []
    answers = iter(["2"])

    monkeypatch.setattr(checker, "load_config", lambda _: sample_config)
    monkeypatch.setattr("sys.argv", ["prof-check", "--profitability"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr(
        checker,
        "run_profitability_mode",
        lambda config, network, stake_trb=None: calls.append(
            ("profitability", network["name"], stake_trb)
        ),
    )

    checker.main()

    assert calls == [("profitability", "testnet", None)]


def test_direct_rewards_tty_prompts_for_network(monkeypatch, sample_config):
    calls = []
    answers = iter(["1"])

    monkeypatch.setattr(checker, "load_config", lambda _: sample_config)
    monkeypatch.setattr("sys.argv", ["prof-check", "--rewards", "tellor1abc"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr(
        checker,
        "run_rewards_mode",
        lambda address, config, network: calls.append((address, network["name"])),
    )

    checker.main()

    assert calls == [("tellor1abc", "mainnet")]


def test_direct_profitability_non_tty_defaults_to_mainnet(
    monkeypatch, sample_config
):
    calls = []

    monkeypatch.setattr(checker, "load_config", lambda _: sample_config)
    monkeypatch.setattr("sys.argv", ["prof-check", "--profitability"])
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    monkeypatch.setattr(
        checker,
        "run_profitability_mode",
        lambda config, network, stake_trb=None: calls.append(
            ("profitability", network["name"], stake_trb)
        ),
    )

    checker.main()

    assert calls == [("profitability", "mainnet", None)]
