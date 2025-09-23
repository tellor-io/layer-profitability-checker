DAILY_MINT_RATE = 146940000  # loya per day
MILLISECONDS_IN_DAY = 24 * 60 * 60 * 1000


# recreate mint module logic
class Minter:
    def __init__(self, bond_denom="loya"):
        self.bond_denom = bond_denom
        self.previous_block_time = None

    def validate(self):
        if self.previous_block_time is None:
            raise ValueError("previous block time cannot be None")
        if not self.bond_denom:
            raise ValueError("bond denom should not be empty string")

    # gets rewards minted for the most recent block
    def calculate_block_provision(self, time_diff: int):
        if time_diff <= 0:
            raise ValueError(f"time_diff {time_diff} cannot be negative")

        # Calculate time elapsed in milliseconds
        time_elapsed_ms = int(time_diff * 1000)

        # Calculate mint amount using Layer's formula
        mint_amount = DAILY_MINT_RATE * time_elapsed_ms // MILLISECONDS_IN_DAY

        return mint_amount
