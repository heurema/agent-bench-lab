# v0 Roadmap

## Phase 0: Public starter

- [x] README
- [x] docs skeleton
- [x] task schemas
- [x] core suite config
- [x] public/private split
- [x] leak-check script
- [x] sample public fixtures

## Phase 1: Working artifact scoring

- [ ] make IF-01 scorer fully useful
- [ ] make DATA-01 scorer fully useful
- [x] add smoke-test artifact generator
- [x] add pytest coverage for registry loading, schema validation, and sample scorers

## Phase 2: Stateful tools

- [ ] implement APP-04 mock API
- [ ] add resettable SQLite fixture
- [ ] add state-diff scorer

## Phase 3: Terminal and coding

- [ ] implement TERM-02 runnable service stub
- [ ] implement CODE-01 tiny repo fixture
- [ ] add visible and private hidden tests

## Phase 4: Agent adapters

- [ ] add generic agent adapter interface
- [ ] add local CLI adapter
- [ ] add provider adapters behind user-supplied keys
- [ ] add trace logger around model and tool calls

## Phase 5: Comparison reports

- [ ] run manifests
- [ ] run.json / score.json output
- [ ] paired comparison report
- [ ] leaderboard.csv
