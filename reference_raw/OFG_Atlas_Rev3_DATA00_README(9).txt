OFG DEFINITIVE ENGINEERING ATLAS REV3 — MACHINE DATA LAYER
Configuration cut: 2031-04-19

This directory is intentionally program-facing. Human-readable engineering interpretation is in the Rev3 DOCX volumes.

DATA01 Controlled Asset Register
  22,647 asset rows. Source status fields retained. Not self-authenticating canon.

DATA02 Master Event Timeline
  128,986 through-cut event rows. Status fields retained. Narrative locked canon controls.

DATA03 Site Geometry (GeoJSON)
  Local OFG-GRID-2031 E-layer building envelopes. Not surveyed coordinates.

DATA04 Parametric 3D Geometry (JSON)
  MC-0, 16 x 22.5-degree sector topology, 80 blanket assemblies, 48 divertor cassettes, port families,
  and explicit OPEN metric dimensions where source geometry is absent.

DATA05 Relationship Graph
  Program-readable component/interface graph.

DATA06 Physical Object JSON Schema
  Contract for CAD/BIM/digital-thread objects.

DATA07 SQLite Digital Thread
  Relational integration of assets, events, geometry, relationships, every table extracted from the 19 definitive Rev3 DOCX volumes,
  and 238 controlled engineering CSV datasets recovered from the prior Atlas research/verification corpus.
  Source hashes and control notes are retained.

DATA08 QA
  Row/table/source counts for release verification.

CRITICAL STATUS RULE
  C = controlled source/canon
  V/R = verified real-world precedent
  E = controlled fictional engineering reconstruction
  OPEN/O = unresolved
No E coordinate, sensitivity-study number, or precedent value is silently promoted to surveyed/project historical truth.
