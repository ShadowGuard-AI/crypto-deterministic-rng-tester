![Banner](banner.png)

# crypto-deterministic-rng-tester
Tests the output of random number generators used in crypto systems for statistical randomness. The seeded generator is deterministic: it derives bytes through HKDF with the --seed value as the input keying material, a fixed salt (deterministic-rng-tester-salt) and a fixed info string (deterministic-rng-tester-seeded), runs twice on the same seed in one run, and reports whether the two outputs match. The secrets and hkdf generators draw fresh system randomness and are not deterministic. The chi-squared test compares the statistic to the critical value 293.25 for 255 degrees of freedom at the 0.05 significance level and logs a pass line or a bias warning line, flagging potential biases. - Focused on Basic cryptographic operations

## Install
`git clone https://github.com/ShadowStrikeHQ/crypto-deterministic-rng-tester`

## Usage
`./crypto-deterministic-rng-tester [params]`

## Parameters
- `--generator`: The generator to test: secrets, hkdf, or seeded. Defaults to secrets.
- `--seed`: Seed value for the seeded generator. Required when --generator is seeded.
- `--output_length`: The length of the output to generate in bytes. Defaults to 1024.
- `--iterations`: The number of iterations to run the test. Defaults to 1000.
- `--hkdf_salt`: The salt to use for HKDF. If not provided, a random salt is generated.
- `--hkdf_info`: The info to use for HKDF. Defaults to 
- `--hkdf_length`: The length of the output for HKDF. Defaults to 32.
- `--entropy_check`: No description provided

## License
Copyright (c) ShadowStrikeHQ
