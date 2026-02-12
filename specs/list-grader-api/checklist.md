# Checklist: List Grader API

## Functional Requirements

- [ ] **CHK-001**: `POST /grade` accepts valid JSON and returns 200
- [ ] **CHK-002**: Response includes `grade`, `score`, `analysis`, `council_verdict`
- [ ] **CHK-003**: Response time under 30 seconds
- [ ] **CHK-004**: Invalid JSON returns 400
- [ ] **CHK-005**: Scoring formula: `0.6 * council + 0.4 * primordia`
- [ ] **CHK-006**: Grade scale: A=90-100, B=75-89, C=60-74, D=40-59, F=0-39
- [ ] **CHK-007**: Council executes 3 rounds with 5 agents

## Error Handling

- [ ] **CHK-008**: Empty units returns 400
- [ ] **CHK-009**: Unknown faction returns 400
- [ ] **CHK-010**: Quota exhaustion returns 429
- [ ] **CHK-011**: Ollama timeout returns 504

## Integration

- [ ] **CHK-012**: Full 5-agent council debate triggered
- [ ] **CHK-013**: Each agent appears in `analysis`
- [ ] **CHK-014**: `consensus_agents` lists agreeing agents
- [ ] **CHK-015**: Agent-Auditor quota check runs before debate
