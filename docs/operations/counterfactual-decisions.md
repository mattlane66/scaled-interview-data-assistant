# Counterfactual product decisions

Use reviewed human JTBD interviews to identify **which product-design assumption is worth
testing next**. This optional workflow follows the original A→B interview synthesis and does
not depend on a model run, SSR, or a population forecast.

## If the job cluster contains different behavioral mechanisms

Before shaping a particular intervention, use the
[Behavioral Mechanism Map](mechanism-map.md) to compare conditional hypotheses,
rival explanations, and contradictory or unassessed cases across episodes.
Its proposed operating model `M` can inform the current situation and design
boundaries, but is **not** an accepted product requirement.

This counterfactual workflow remains focused on a specific design move and
the observation that could disprove it. Neither tool selects a solution shape.

## Principle

**Observe what happened → understand the struggle and hoped-for progress → change a design
condition → specify what would have to be true → find the observation that could prove it
wrong.**

A counterfactual is a question, not an estimate of causal effect. The brief is an analyst
hypothesis framed by observed interview evidence. A later simulation may supply more possible
explanations, but cannot establish the real-world response on its own.

## Two operating levels

1. **Evidence-first (default).** Build a decision brief from an analyst's reviewed
   `design_hypothesis`, reviewed A→B links, and a checkpoint. It requires no external model.
2. **Simulation-augmented (optional).** After generating and recording a simulation via
   [the existing simulation workflow](simulation.md), produce the same decision brief with
   candidate mechanisms, objections, and experiments. The extra material is labeled
   `SIMULATED_ESTIMATE` and remains unvalidated.

## Preparing a design hypothesis

Start from the ordinary reviewed `CHECKPOINT.json` and approved episode/evidence references.

~~~bash
python scripts/simulation_cli.py init \
  --checkpoint outputs/CHECKPOINT.json \
  --episode D01 --evidence E001 --evidence E002 \
  --counterfactual --output data/decision-scenario.json
~~~

Edit the scenario and complete its existing `decision`, `decision_owner`,
`consequence_if_wrong`, `baseline`, `intervention`, `outcome_space`,
`held_constant`, and `design_hypothesis` fields. The new block has five questions:

~~~json
{
  "design_hypothesis": {
    "product_change": "Provide assisted migration, not additional reporting features",
    "critical_assumption": "Migration effort is the main reason customers defer switching",
    "predicted_behavior": "More customers will attempt a switch when the effort is removed",
    "disconfirming_observation": "People still refuse migration when assistance is provided",
    "if_disconfirmed": "Explore security, trust and reversibility before adding more assistance"
  }
}
~~~

**Illustrative only.** These are hypothetical design assumptions, not interview findings.
The actual A→B links come from your own reviewed checkpoint. Complete every required
review attestation after real human review; do not turn review flags on automatically.

The design hypothesis must be set **before** the scenario is approved or a simulation run
is generated, because its content is part of the scenario hash.

## 1. Build a decision brief with no model call

~~~bash
python scripts/simulation_cli.py counterfactual \
  --checkpoint outputs/CHECKPOINT.json \
  --scenario data/decision-scenario.json \
  --output outputs/decision-brief.md \
  --json-output outputs/decision-brief.json
~~~

The brief contains:

- Real `D##` episode and `E###` evidence references, linked to reviewed `L###` A→B
  interpretations and definitions in the source codebook
- The current Path Y, an observed result or `UNKNOWN`, and coverage gaps
- One explicit design move, what is held constant, and the critical assumption
- Predicted behavioral difference clearly marked as an **analyst hypothesis**
- A disconfirming observation and the design direction to examine if it occurs

Only links fully supported by the **selected scenario evidence** are displayed.
The brief flags other links in scope that have not been included. If none have full
support, the command fails rather than producing an ungrounded design narrative.

## 2. Optionally challenge it with a simulation

Use `prepare`, an explicitly authorized external model, and `record` as described in
[simulation.md](simulation.md). Supply the resulting `outputs/sim-run.json` to the
`counterfactual` command using `--run`.

~~~bash
python scripts/simulation_cli.py counterfactual \
  --checkpoint outputs/CHECKPOINT.json \
  --scenario data/decision-scenario.json \
  --run outputs/sim-run.json \
  --output outputs/decision-brief-with-simulation.md
~~~

The recorded candidate mechanisms and objections **do not** become source evidence,
validated causal effects, or estimated adoption rates. Use them to find rival
explanations and observations worth seeking in a real test.

## 3. Compare two design approaches over the same human evidence

Create and approve a separate scenario for each intervention. Keep the same checkpoint,
decision, selected episodes and evidence IDs, baseline, target, and outcome space.
Each alternative has a distinct scenario ID and its own intervention and critical assumption.

~~~bash
python scripts/simulation_cli.py compare \
  --checkpoint outputs/CHECKPOINT.json \
  --scenario data/assisted-migration.json \
  --scenario data/reversible-migration.json \
  --output outputs/design-comparison.md
~~~

If both alternatives have recorded runs, also supply matching, ordered `--run` paths,
one for each `--scenario`. Do not mix a run from one scenario with another.

The comparison shows each proposed product move, the changed variable, its critical
assumption, and the disconfirming observation. It issues a warning when held-constant
conditions differ. The report **does not rank alternatives**, convert synthetic
confidence into causal effects, or call the comparison controlled evidence.

## Decisions and review gates

A useful counterfactual need not be proven before making a small reversible prototype.
But it should specify what observation would change the direction of product shaping.
Use experimental interventions or fresh human observation before treating the scenario
as evidence of a behavioral effect.

The human research bank, codebook, links, and original checkpoint are **read-only**
throughout. Scenario, brief, and report artifacts belong under ignored `data/` or
`outputs/`, not in the public repository when containing research data.

### Not supported

This extension does not discover new jobs by itself, establish the cause of a customer's
past behavior, quantify actual purchasing probabilities, prove a population effect,
estimate a market, or replace prospective validation. It deliberately avoids inventing
a product ranking from synthetic responses.

To test whether this method improves real decisions, compare resulting prioritization
and experiments against held-out interviews and observed switching outcomes.
See [prospective validation issue #5](https://github.com/mattlane66/scaled-interview-data-assistant/issues/5).
