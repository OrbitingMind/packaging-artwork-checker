PROJECT: AI packaging artwork checker for Esko hackathon (Track 2).
GOAL: Upload packaging image + approved spec -> system checks against
FSSAI labelling rules -> outputs PASS / FAIL / NEEDS REVIEW per rule with
evidence (text found, location box on image, expected value, rule clause).
SCOPE: Packaged food, India, 10 rules (R01-R10) only. Depth over breadth.
STACK: Python 3.11, Streamlit, EasyOCR, Anthropic API (Claude vision),
YAML for rules, pytest. Runs locally.
PRINCIPLES: Avoid false alarms. Every finding must show evidence.
Use deterministic code where possible; LLM only for fuzzy judgments.
If unsure, return NEEDS REVIEW, never guess.
SUCCESS METRIC: precision, recall, false-alarm rate on the dataset
(dev/test split in dataset/split.json), compared to a naive
single-prompt baseline.
RULES: R01 net quantity present, R02 net quantity matches spec,
R03 correct unit, R04 veg mark present, R05 allergen section present,
R06 allergens match spec, R07 ingredients match spec,
R08 manufacturer name and address present, R09 FSSAI number is
14 digits, R10 MRP and best-before present.
rules.yaml and loader done and committed. Next: environment setup
(Python 3.12 venv, requirements, .env), then extract.py.
dataset/specs. Next: rules.yaml.
MY LEVEL: Strong in C++/DSA, learning Python. Explain Python-specific
parts briefly and comment the code.