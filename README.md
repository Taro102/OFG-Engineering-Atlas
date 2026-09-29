# OFG Engineering Atlas

This repository is intentionally public and intended for public distribution. It is the prospective persistent master repository for the OFG Engineering Atlas.

The current migration source is the validated R2 migration bundle, `OFG_EA_Master_Migration_Raw_Data_Retrieval_R2.zip`. GitHub does not become authoritative until repository round-trip validation passes and the authority transition is explicitly recorded. GitHub authority is currently `NOT_YET_ACTIVE`.

The Engineering Atlas is human- and machine-readable. It provides engineering meaning, relationships, design basis, assumptions, provenance, interpretation, and pointers. The Annex is machine-readable and contains structured registers, schemas, parameters, datasets, and code packages.

Raw provenance and normalized state are distinct. Raw sources are immutable provenance inputs; normalized state is version-controlled machine state. Generated retrieval databases, including SQLite indexes, are derivative and rebuildable, not authoritative. Missing records and unresolved engineering identities must remain explicit rather than being invented.

Phase 1 establishes only the repository control plane. The configuration cut is `2031-04-19`, the latest integrated staging is C010, and C011 remains active but not globally integrated. No baseline promotion or global release has occurred. C011 global integration requires all required returns to be accepted and the user's explicit `Commence`. C012 must not be issued before C011 global integration.

The intended repository structure is defined in `control/repository_layout.json`. Directories are created only when they contain actual tracked files. The complete migration ZIP, large raw files, and complete reference corpus are not included in this phase.

Only material intended for public distribution may be committed. Credentials, access tokens, authentication material, private keys, local account identifiers, and transient connector credentials must not be committed. Large-file handling is a separate storage concern for a later phase; the technical nature or size of the OFG project corpus does not itself prohibit its public distribution.
