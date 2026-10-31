import argparse
import logging
import secrets
import sys
from collections import Counter
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend
import math

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_argparse():
    """
    Sets up the argument parser for the command-line interface.
    """
    parser = argparse.ArgumentParser(description="Tests the output of deterministic random number generators (DRNGs).")
    parser.add_argument("--generator", type=str, default="secrets", choices=["secrets", "hkdf", "seeded"],
                        help="The DRNG to test: secrets (secrets.token_bytes), hkdf (HKDF with fresh random input), or seeded (HKDF with the --seed value as input keying material, a fixed salt and a fixed info string). Defaults to secrets.")
    parser.add_argument("--seed", type=str, default="",
                        help="Seed value for the seeded generator. Required when --generator is seeded. The seed string is used as the HKDF input keying material.")
    parser.add_argument("--output_length", type=int, default=1024,
                        help="The length of the output to generate in bytes. Defaults to 1024.")
    parser.add_argument("--iterations", type=int, default=1000,
                        help="The number of iterations to run the test. Defaults to 1000.")
    parser.add_argument("--hkdf_salt", type=str, default="",
                        help="The salt to use for HKDF. If not provided, a random salt is generated.")
    parser.add_argument("--hkdf_info", type=str, default="example_info",
                        help="The info to use for HKDF. Defaults to 'example_info'.")
    parser.add_argument("--hkdf_length", type=int, default=32,
                        help="The length of the output for HKDF. Defaults to 32.")
    parser.add_argument("--entropy_check", action="store_true", help="Enable a basic entropy check (Shannon Entropy).")

    return parser.parse_args()

def generate_secrets_output(output_length):
    """
    Generates random bytes using the secrets module.
    """
    try:
        random_bytes = secrets.token_bytes(output_length)
        return random_bytes
    except Exception as e:
        logging.error(f"Error generating secrets output: {e}")
        return None

def generate_hkdf_output(output_length, salt="", info="example_info", length=32):
    """
    Generates random bytes using HKDF.
    """
    try:
        if not salt:
            salt = secrets.token_bytes(16)  # Generate a random salt if none is provided
        else:
            salt = salt.encode('utf-8')  # Ensure salt is bytes

        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=length,
            salt=salt,
            info=info.encode('utf-8'),
            backend=default_backend()
        )
        random_bytes = hkdf.derive(secrets.token_bytes(32)) #Use strong entropy as input
        return random_bytes

    except Exception as e:
        logging.error(f"Error generating HKDF output: {e}")
        return None

SEEDED_SALT = b"deterministic-rng-tester-salt"
SEEDED_INFO = b"deterministic-rng-tester-seeded"

def generate_seeded_output(seed, output_length):
    """
    Generates bytes deterministically from a seed through HKDF.
    The seed string is the input keying material. The salt is the
    fixed value SEEDED_SALT and the info is the fixed value
    SEEDED_INFO, both stated here and in the README, so the same
    seed always produces the same output.
    """
    try:
        if not seed:
            logging.error("The seeded generator requires a --seed value.")
            return None
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=output_length,
            salt=SEEDED_SALT,
            info=SEEDED_INFO,
            backend=default_backend()
        )
        return hkdf.derive(seed.encode('utf-8'))
    except Exception as e:
        logging.error(f"Error generating seeded output: {e}")
        return None

def calculate_entropy(data):
    """
    Calculates the Shannon entropy of the given data.
    """
    if not data:
        return 0

    # Counter in one pass instead of data.count(x) for all 256 values,
    # which rescanned the whole buffer each time for the same counts.
    entropy = 0
    for count in Counter(data).values():
        p_x = count / len(data)
        entropy += - p_x * math.log2(p_x)
    return entropy

def run_statistical_tests(data, entropy_check):
    """
    Runs basic statistical tests on the generated data.
    """
    try:
      # Byte frequency test. The sum has to run over all 256 byte values,
      # including values that never appeared: a missing value is a full
      # average_count below expectation, and summing only over the values
      # present silently dropped that term and understated the statistic
      # exactly when the output was biased.
      byte_counts = Counter(data)

      average_count = len(data) / 256.0
      chi_squared = sum((byte_counts.get(value, 0) - average_count) ** 2 / average_count for value in range(256))

      logging.info(f"Chi-squared test: {chi_squared}")
      # Critical value for 255 degrees of freedom at the 0.05
      # significance level is 293.25 (standard chi-squared table).
      critical_value = 293.25
      if chi_squared <= critical_value:
          logging.info(f"Chi-squared verdict: PASS, {chi_squared:.2f} is at or below the critical value 293.25 for 255 degrees of freedom at the 0.05 significance level.")
      else:
          logging.warning(f"Chi-squared verdict: BIAS WARNING, {chi_squared:.2f} exceeds the critical value 293.25 for 255 degrees of freedom at the 0.05 significance level. Potential bias detected.")


      if entropy_check:
          entropy = calculate_entropy(data)
          logging.info(f"Entropy: {entropy}")
          if entropy < 7.0:
              logging.warning("Low entropy detected. Possible bias.")
          else:
            logging.info("Entropy check passed.")

    except Exception as e:
        logging.error(f"Error running statistical tests: {e}")

def main():
    """
    Main function to orchestrate the DRNG testing.
    """
    args = setup_argparse()

    if args.iterations <= 0 or args.output_length <= 0 or args.hkdf_length <= 0:
        # Zero iterations used to "complete" with a chi-squared of 0 over
        # no data, and a negative length only failed deep inside the
        # generator and still exited 0. Reject the numbers up front.
        logging.error("Iterations, output length and HKDF length must all be positive.")
        sys.exit(1)

    logging.info(f"Testing DRNG: {args.generator}")
    logging.info(f"Output length: {args.output_length}")
    logging.info(f"Iterations: {args.iterations}")

    if args.generator == "seeded":
        if not args.seed:
            logging.error("The seeded generator requires a --seed value.")
            sys.exit(1)
        first = generate_seeded_output(args.seed, args.output_length)
        second = generate_seeded_output(args.seed, args.output_length)
        if first is None or second is None:
            logging.error("Failed to generate seeded data.")
            sys.exit(1)
        if first == second:
            logging.info("Determinism check: outputs match. The seeded generator produced identical output on two runs with the same seed.")
        else:
            logging.warning("Determinism check: outputs do not match. The seeded generator produced different output on two runs with the same seed.")
        run_statistical_tests(first, args.entropy_check)
        logging.info("Testing completed.")
        return

    try:
        all_data = b""  # Collect all generated data for statistical tests

        for i in range(args.iterations):
            if args.generator == "secrets":
                random_data = generate_secrets_output(args.output_length)
            elif args.generator == "hkdf":
                # For HKDF the per-iteration size is --hkdf_length, not
                # --output_length: the derive call takes its own length,
                # and generate_hkdf_output ignores the first argument.
                random_data = generate_hkdf_output(args.output_length, args.hkdf_salt, args.hkdf_info, args.hkdf_length)
            else:
                logging.error("Invalid generator specified.")
                return

            if random_data:
                # Accumulate all generated data
                all_data += random_data
            else:
                logging.error("Failed to generate random data.")
                sys.exit(1)

        run_statistical_tests(all_data, args.entropy_check)
        logging.info("Testing completed.")

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()