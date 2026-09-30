# OFG Engineering Atlas

GitHub main is the persistent control plane. Current authority resolves through `state/current_root.json`, the successor root and `control/master_recovery_cutover.json`. The candidate package has no authority until separately authorized publication and independent remote validation.

The target master is T1-G3 epoch 3. T1-G2 is fenced after validated cutover; existing T2-G2, T4-G2 and T5-G2 generations retain their tasks and original dispatch provenance. Historical compatibility records and transports remain unchanged and cannot activate current authority.

T1-G3 operates as a thin master under `control/master_context_policy.json`; bulk execution and evidence remain external. `control/post_cutover_infrastructure_plan.json` is a roadmap, not implementation or activation.

The engineering pin remains B000 Rev3/RevW3/RevS, C010 integrated staging, configuration cut 2031-04-19. C011 remains unintegrated with zero accepted returns; C012 is absent. WF3 and MRE3 remain inactive. No baseline promotion or global release occurs. T3 remains retired; Rev4 remains quarantined. Raw evidence, open identities and conflicts are preserved.

Use selector-aware programs for current operations with a separately supplied independent readback receipt. `--candidate` permits local validation only. `--historical` retrieves published parent state at the pinned source commit. Original onboarding remains recoverable from Git history. Generated capsules, indexes and transports are derivative and nonauthoritative.
