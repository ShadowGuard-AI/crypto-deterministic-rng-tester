# crypto-deterministic-rng-tester
Tests the output of deterministic random number generators (DRNGs) used in crypto systems for statistical randomness and predictability, flagging potential biases or patterns. - Focused on Basic cryptographic operations

## Install
`git clone https://github.com/ShadowStrikeHQ/crypto-deterministic-rng-tester`

## Usage
`./crypto-deterministic-rng-tester [params]`

## Parameters
- `--generator`: No description provided
- `--output_length`: The length of the output to generate in bytes. Defaults to 1024.
- `--iterations`: The number of iterations to run the test. Defaults to 1000.
- `--hkdf_salt`: The salt to use for HKDF. If not provided, a random salt is generated.
- `--hkdf_info`: The info to use for HKDF. Defaults to 
- `--hkdf_length`: The length of the output for HKDF. Defaults to 32.
- `--entropy_check`: No description provided

## License
Copyright (c) ShadowStrikeHQ
