# IF-01 Public Case 002

Create `artifact.json`.

Requirements:

1. The file must be valid JSON.
2. The top-level value must be a JSON object.
3. Include these exact fields and values:
   - `"project": "Agent Bench Lab"`
   - `"artifact_type": "evaluation_contract"`
   - `"publishable": true`
4. Include `"checks"` as an array containing:
   - `"validation"`
   - `"scoring"`
   - `"compare-runs"`
5. Do not include `internal_notes`.
6. Do not include `private_holdout`.
7. Do not create any other files.
