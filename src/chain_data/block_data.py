import random
import subprocess
import sys
import time
from datetime import datetime
from typing import Optional

from .rpc_client import TellorRPCClient


# get current block height and block timestamp
def get_block_height_and_timestamp(layerd_path, rpc_client: Optional[TellorRPCClient] = None):
    if rpc_client is not None:
        # Use RPC client
        try:
            return rpc_client.get_block_height_and_timestamp()
        except Exception as e:
            print(f"Error getting block info via RPC: {e}")
            raise Exception("RPC client is required - layerd binary fallback is disabled") from e
    else:
        raise Exception("RPC client is required - layerd binary fallback is disabled")

def get_block_height_and_timestamp_fallback(layerd_path):
    try:
        # run `layerd query block`
        result = subprocess.run([layerd_path, 'query', 'block'],
                               capture_output=True, text=True, check=True)

        # output cleanup
        lines = result.stdout.strip().split('\n')
        block_height = None
        timestamp = None
        for line in lines:
            if line.strip().startswith('height:'):
                block_height = int(line.split('"')[1])
            elif line.strip().startswith('time:'):
                timestamp_str = line.split('"')[1]

                # Handle nanoseconds by truncating to microseconds (Python only supports up to microseconds)
                if '.' in timestamp_str:
                    if timestamp_str.endswith('Z'):
                        # Format: 2025-05-28T20:35:31.196915692Z
                        base_time = timestamp_str[:-1]  # Remove Z
                        date_part, frac = base_time.split('.')
                        frac = frac[:6].ljust(6, '0')  # Truncate to microseconds
                        timestamp_str = f"{date_part}.{frac}+00:00"
                    elif '+' in timestamp_str:
                        # Format: 2025-05-28T20:35:31.196915692+00:00
                        base_time, tz = timestamp_str.split('+')
                        date_part, frac = base_time.split('.')
                        frac = frac[:6].ljust(6, '0')  # Truncate to microseconds
                        timestamp_str = f"{date_part}.{frac}+{tz}"

                timestamp = datetime.fromisoformat(timestamp_str)

        return block_height, timestamp

    except subprocess.CalledProcessError as e:
        print(f"Error running layerd query: {e}")
        return None, None
    except Exception as e:
        print(f"Error parsing block info: {e}")
        return None, None

# gets the average block time by sampling twice with a 20s sleep
def get_average_block_time(rpc_client: TellorRPCClient):
    sleep_duration = 20
    """Calculate average block time by sampling twice with a 20s sleep interval"""

    height1, time1 = get_block_height_and_timestamp(None, rpc_client)

    if height1 is None or time1 is None:
        print("Failed to get initial block info")
        return None

    print(f"Sample block 1 - Height: {height1}, Time: {time1}")
    print(f"Sleeping for {sleep_duration} seconds...\n")

    sleep_box(sleep_duration)

    height2, time2 = get_block_height_and_timestamp(None, rpc_client)

    if height2 is None or time2 is None:
        print("Failed to get second block info")
        return None

    print(f"\nSample block 2 - Height: {height2}, Time: {time2}")

    # Calculate differences
    block_diff = height2 - height1
    time_diff = (time2 - time1).total_seconds()

    if block_diff == 0:
        print("No new blocks produced during sleep period")
        return None

    avg_block_time = time_diff / block_diff

    return avg_block_time, time_diff, block_diff

def sleep_box(duration=20):
    # Funniest clean jokes of all time
    jokes = [
        ("Why don't scientists trust atoms?", "Because they make up everything!"),
        ("What do you call a fake noodle?", "An impasta!"),
        ("Why did the scarecrow win an award?", "He was outstanding in his field!"),
        ("What do you call a bear with no teeth?", "A gummy bear!"),
        ("Why don't eggs tell jokes?", "They'd crack each other up!"),
        ("What's the best thing about Switzerland?", "I don't know, but the flag is a big plus!"),
        ("Why did the math book look so sad?", "Because it was full of problems!"),
        ("What do you call a sleeping bull?", "A bulldozer!"),
        ("How do you organize a space party?", "You planet!"),
        ("Why can't a bicycle stand up by itself?", "It's two tired!"),
        ("What do you call a fish wearing a bowtie?", "Sofishticated!"),
        ("Why don't skeletons fight each other?", "They don't have the guts!"),
        ("What did the ocean say to the beach?", "Nothing, it just waved!"),
        ("Why did the cookie go to the doctor?", "Because it felt crumbly!"),
        ("What's orange and sounds like a parrot?", "A carrot!"),
        ("Why don't programmers like nature?", "It has too many bugs!")
    ]

    current_joke_lines = 0  # Track how many lines the current joke uses
    current_joke = None  # Track current joke to avoid changing mid-cycle

    for i in range(duration):
        elapsed = i + 1

        # Every 8 seconds, pick a new random joke
        within_cycle = elapsed % 8
        if within_cycle == 1 or within_cycle == 0:  # Start of new 8-second cycle
            if current_joke is None or within_cycle == 0:  # First time or new cycle
                current_joke = random.choice(jokes)

        # Progress bar
        progress = elapsed / duration
        bar_width = 50
        filled = int(progress * bar_width)
        progress_bar = f"📊 [{'█' * filled}{'░' * (bar_width - filled)}] {progress:.1%} | {elapsed}s/{duration}s"

        # Clear previous joke lines if any
        if current_joke_lines > 0:
            for _ in range(current_joke_lines + 1):  # +1 for progress bar
                sys.stdout.write("\033[1A\033[2K")

        # Determine what to show
        if elapsed == duration:
            # Always show punchline at the very end (20-second mark)
            question, answer = current_joke
            print(f"\033[91m🤔 {question}\033[0m")
            print(f"\033[92m😄 {answer}\033[0m")
            current_joke_lines = 2
        elif within_cycle == 0 or within_cycle <= 4:
            # Show question only (first 4 seconds of each 8-second cycle)
            question, _ = current_joke
            print(f"\033[91m🤔 {question}\033[0m")
            current_joke_lines = 1
        else:
            # Show question + answer (next 4 seconds)
            question, answer = current_joke
            print(f"\033[91m🤔 {question}\033[0m")
            print(f"\033[92m😄 {answer}\033[0m")
            current_joke_lines = 2

        print(progress_bar)
        sys.stdout.flush()
        time.sleep(1)
