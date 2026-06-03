## 1. Playbook scaffold

- [ ] 1.1 Create `docs/framework/` with a `README.md` overview: the three-layer
  model (convergence machine / dispatch + deployment / operator discipline), the two
  axes (protects what · enforceable?), and the methodology-vs-deployment legend used
  throughout
- [ ] 1.2 Add the cross-link convention up front (per design D3): the playbook cites
  field-log sections (`docs/ralph-loop-experiment.md`) and the evaluation threads
  (`docs/ralph-loop-evaluation.md`) as evidence, and never duplicates them

## 2. Layer documents (one per capability spec)

- [ ] 2.1 `docs/framework/layer-1-convergence-machine.md` from
  `specs/convergence-machine/spec.md`: contract, commit-as-proof (gate ≡ CI), review
  as orthogonal pillar (artifact-yes / intent-no / external-state-yes), and the two
  integrity guards — each tagged **methodology**, each cross-linked to its evidence
- [ ] 2.2 `docs/framework/layer-2-dispatch-and-deployment.md` from
  `specs/work-dispatch/spec.md`: the work-class dial (cost not correctness), the
  autonomy wrapper as opt-in gated on four preconditions with Thread A's verdict,
  velocity-targets-latency, and enabling patterns — tagged **deployment/configurable**
- [ ] 2.3 `docs/framework/layer-3-operator-discipline.md` from
  `specs/operator-discipline/spec.md`: the unenforceability framing, the
  epistemic/procedural split (consolidating the operator memories), and the
  instrument + checklist teeth-substitutes — tagged **methodology**

## 3. Reuse surface

- [ ] 3.1 `docs/framework/quickstart.md` — the one-page "answer-once defaults" a new
  project imports (per design open-question, leaning yes): the kernel rules, the
  dispatch table shape, the autonomy precondition gate as a checklist
- [ ] 3.2 Add the three pre-action checklists (background a job / reproduce a failure
  / assert a causal "why") as a copy-pasteable block in the Layer 3 doc or quickstart

## 4. Wire-in and validation

- [ ] 4.1 Add a pointer to `docs/framework/` from `docs/index.md` and a one-line
  reference in `CLAUDE.md` §5 (Ralph Loop Strategy) so cold-start sessions find it
- [ ] 4.2 Mark the four threads in `docs/ralph-loop-evaluation.md` as **graduated**
  into `ralph-framework-v1`, closing the loop from evaluation → spec
- [ ] 4.3 `openspec validate ralph-framework-v1` passes; the playbook's
  methodology/deployment tags match the spec requirement tags exactly
- [ ] 4.4 Final read-through: every framework claim traces to a field-log section or
  evaluation thread; no locked CLAUDE.md §2/§3 decision is reopened
