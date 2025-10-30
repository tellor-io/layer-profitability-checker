import json
import subprocess


def get_min_gas_price(rpc_client=None, config=None):
    """
    Get minimum gas price using RPC client or config default
    """
    # First try to get from config
    if config and "min_gas_price" in config:
        try:
            return float(config["min_gas_price"])
        except (ValueError, TypeError):
            print(
                f"Warning: Invalid min_gas_price in config: {config['min_gas_price']}"
            )

    if rpc_client is not None:
        # Try multiple approaches to query global fee
        try:
            # Approach 1: Query global fee using Cosmos SDK REST API
            # Try different API versions
            for version in ["v1beta1", "v1", ""]:
                try:
                    if version:
                        url = f"{rpc_client.rest_endpoint}/cosmos/globalfee/{version}/minimum_gas_prices"
                    else:
                        url = f"{rpc_client.rest_endpoint}/cosmos/globalfee/minimum_gas_prices"

                    result = subprocess.run(
                        [
                            "curl",
                            "-s",
                            "-X",
                            "GET",
                            url,
                            "-H",
                            "accept: application/json",
                            "--silent",
                            "--show-error",
                        ],
                        capture_output=True,
                        text=True,
                        check=True,
                        timeout=10,
                    )

                    response = json.loads(result.stdout)
                    minimum_gas_prices = response.get("minimum_gas_prices", [])

                    # Find loya denom
                    for price in minimum_gas_prices:
                        if price.get("denom") == "loya":
                            return float(price.get("amount", "0"))

                    # If we got here, the API worked but no loya found
                    break

                except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
                    continue

            # Approach 2: Try to query app parameters via ABCI
            try:
                # Try different ABCI query paths
                for path in ["/app/params", "app/params", "/params", "params"]:
                    try:
                        result = subprocess.run(
                            [
                                "curl",
                                "-s",
                                "-X",
                                "GET",
                                f"{rpc_client.rpc_endpoint}/abci_query?path={path}&data=0x",
                                "-H",
                                "accept: application/json",
                                "--silent",
                                "--show-error",
                            ],
                            capture_output=True,
                            text=True,
                            check=True,
                            timeout=10,
                        )

                        response = json.loads(result.stdout)
                        if "result" in response and "value" in response["result"]:
                            # This would need to be parsed based on the actual response format
                            # For now, we'll skip this approach
                            pass
                    except (
                        subprocess.CalledProcessError,
                        json.JSONDecodeError,
                        KeyError,
                    ):
                        continue

            except Exception:
                pass

            return None

        except Exception as e:
            print(f"Error querying global fee via RPC: {e}")
            return None

    else:
        print("No RPC client provided")
        return None

    # If all else fails, use a reasonable default based on common Cosmos SDK practices
    # This is a fallback value that should be overridden in config for accuracy
    print("Warning: Could not determine minimum gas price, using default value")
    return 0.000025  # 0.000025 loya per gas unit (common default)
