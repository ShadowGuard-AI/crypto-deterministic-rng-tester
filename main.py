import argparse
import logging
import secrets
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidTag
import statistics
import math

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_argparse():
    """
    Sets up the argument parser for the command-line interface.
    """
    parser = argparse.ArgumentParser(description="Tests the output of deterministic random number generators (DRNGs).")
    parser.add_argument("--generator", type=str, default="secrets", choices=["secrets", "hkdf"],
                        help="The DRNG to test: secrets (secrets.token_bytes) or hkdf (HKDF). Defaults to secrets.")
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

def calculate_entropy(data):
    """
    Calculates the Shannon entropy of the given data.
    """
    if not data:
        return 0

    entropy = 0
    for x in range(256):
        p_x = float(data.count(x)) / len(data)
        if p_x > 0:
            entropy += - p_x * math.log2(p_x)
    return entropy

def run_statistical_tests(data, entropy_check):
    """
    Runs basic statistical tests on the generated data.
    """
    try:
      # Byte frequency test
      byte_counts = {}
      for byte in data:
          byte_counts[byte] = byte_counts.get(byte, 0) + 1

      average_count = len(data) / 256.0
      chi_squared = sum([(count - average_count) ** 2 / average_count for count in byte_counts.values()])

      logging.info(f"Chi-squared test: {chi_squared}")


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

    logging.info(f"Testing DRNG: {args.generator}")
    logging.info(f"Output length: {args.output_length}")
    logging.info(f"Iterations: {args.iterations}")

    try:
        all_data = b""  # Collect all generated data for statistical tests

        for i in range(args.iterations):
            if args.generator == "secrets":
                random_data = generate_secrets_output(args.output_length)
            elif args.generator == "hkdf":
                random_data = generate_hkdf_output(args.output_length, args.hkdf_salt, args.hkdf_info, args.hkdf_length)
            else:
                logging.error("Invalid generator specified.")
                return

            if random_data:
                # Accumulate all generated data
                all_data += random_data
            else:
                logging.error("Failed to generate random data.")
                return

        run_statistical_tests(all_data, args.entropy_check)
        logging.info("Testing completed.")

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()