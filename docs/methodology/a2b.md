# A2B Method Notes

A2B is a framing and investigation tool used to produce a well-framed artifact for shaping.
It aims to uncover **technology-agnostic requirements** by clarifying:
- the situation and struggle,
- the prior/current paths,
- the current baseline result,
- and the desired progress.

## Core pieces

- **Point A**: the contextual struggling moment
- **Path Y**: the old way / substitute / workaround / doing nothing
- **Path X**: the current or adopted approach
- **Point B**: the desired outcome relative to the baseline

## Terminology guardrail: baseline vs. Point B

In this repo:

- **Baseline result** = what Path X or Path Y currently produces.
- **Point B** = desired progress compared with that baseline.

Do not collapse baseline and Point B. The baseline is the current result; Point B is the hoped-for improvement. If source material uses "baseline outcome" loosely, preserve the contrast: current result vs. desired progress.

When evidence is ambiguous, use this test:

- If the user is describing what happens today, code it as **Baseline result**.
- If the user is describing what they hoped would be different, code it as **Point B**.
- If the user is describing the situation or pressure that made the current result unacceptable, code it as **Point A / Push**.

Point B should not be reduced to a feature request. It should describe progress in the user’s situation.

## A↔B mapping guardrail: map, do not match

Do not force a 1:1 mapping between Point A and Point B.

- One struggling moment may contain multiple pushes.
- One desired outcome may arise from different contexts.
- Similar Point A contexts can lead to different Point B hopes.
- Similar Point B hopes can come from different Point A situations.

Before clustering, preserve competing A↔B links and contradictions. Treat them as signal, not mess. The goal is to map the demand structure, not to make every interview fit a neat pattern.

## What A2B is trying to avoid

A2B is designed to keep the work anchored in:
- real past behavior
- bounded context
- causal reasoning
- forces in the decision to switch

It is not meant for validating an imagined solution.

## Key prompts

Use questions like:

1. When did you first start using or buying Path X?
2. When did you first think you might need something like Path X?
3. What were you doing in the period before adopting Path X?
4. Why didn’t you just continue doing that? What tipped you?
5. What was bad or frustrating about that?
6. Before using Path X, what were you hoping would be different afterward?

## Practical reading rule

If the user describes a workaround, that may still be **Path Y**, not Point A.

Point A often becomes clearer when the person starts describing scarcity:
- time
- energy
- knowledge
- money

## Output expectation

A good A2B artifact should make it possible to state:

- the struggling moment,
- the old/current path,
- the current result,
- the desired outcome,
- and the forces that make a new path worth exploring.
