# Turn Order Research Feature Specification

**Status:** Draft

## 1. Purpose

Implement the existing Wingspan Turn Order Research Methodology as a staff-only research feature within Wingspan Portal.

The feature will select qualifying competitive games for two players, prepare those games for analysis, evaluate the predefined turn-order hypotheses, and present the results on a dedicated Research page.

The Turn Order Research Methodology remains the authority for research questions, performance measures, statistical interpretation, and study limitations.

## 2. Access

The Research page is restricted to authenticated Django staff users.

The feature is an internal research tool and is not part of the player-facing statistics experience.

## 3. Research Selection

The Research form will allow staff to select:

- Primary player
- Secondary player
- Optional start date
- Optional end date

The primary and secondary players must be different.

Staff may select from the applicable player population without friendship restrictions.

## 4. Qualifying Games

The research dataset includes only competitive games where:

- both selected players have a result;
- the selected players are the only recorded human participants; and
- the game falls within the selected date range, when provided.

Game selection should follow the same general rationale already used by Feathered Foe, while remaining independently owned by the Research feature.

## 5. Dataset Preparation

Each qualifying game will be converted into a prepared research observation.

The observation will preserve the raw values required by the methodology, including:

- game identifier and date;
- primary and secondary player;
- primary and secondary starting turn order; and
- primary and secondary final score.

Derived analytical values will be calculated from the raw observations, including:

- score differential;
- head-to-head outcome;
- direct-following status; and
- player spacing.

Derived research values will not be persisted to the database.

Dataset selection and dataset preparation are separate responsibilities.

## 6. Hypothesis Analysis

The prepared research dataset will be evaluated against the three predefined hypotheses:

1. Starting Position
2. Direct Following
3. Player Spacing

Each hypothesis will have an independent analysis responsibility and will consume prepared research observations rather than query Django models directly.

Each hypothesis will evaluate the performance measures defined by the research methodology.

The exact statistical tests, statistical libraries, internal data structures, and module layout are implementation decisions and are not fixed by this specification.

## 7. Research Orchestration

A research orchestration layer will coordinate the complete analysis.

Its responsibilities are to:

1. select qualifying games;
2. prepare the research dataset;
3. run the applicable hypothesis analyses; and
4. assemble the complete research result for presentation.

The Django view should primarily handle request validation, invoke the research service, and pass the resulting data to the template.

## 8. Analytical Transparency

The Research feature is an analytical tool rather than a statistical black box.

Research results must retain and expose enough information for a knowledgeable reviewer to inspect how the reported statistics were produced. This should include, where applicable:

- the prepared research observations;
- group sizes and descriptive statistics;
- observed differences or effect estimates;
- statistical test outputs;
- uncertainty measures;
- relevant assumptions or diagnostics; and
- intermediate calculation details when they materially aid verification or understanding.

The exact statistics and calculation details displayed are not fixed by this specification. They should be selected according to the methodology, the analysis being performed, and their usefulness for understanding or auditing the result.

The interface may explain statistical terms, formulas, and what reported values represent. It will not generate research conclusions or decide whether a hypothesis is supported. Interpretation of the statistical evidence remains the responsibility of the researcher.

## 9. Presentation

A dedicated Research template will present:

- the selected research population and date range;
- dataset size and relevant dataset information;
- results for each of the three hypotheses; and
- the analytical evidence and supporting details produced by the research services.

The presentation should make it practical to trace reported statistical results back through the prepared observations and calculations that produced them.

## 10. Known Constraint

The current data model records the two human results and their turn order but does not independently record or verify the number of computer players.

For the initial study, qualifying games are therefore analyzed under the methodology's existing assumption that the competitive configuration contained the two selected humans and three computer players.

This limitation must remain explicit and should be revisited before using the feature for broader population-level research.

## 11. Scope Boundaries

The initial feature is limited to implementing the existing Turn Order Research Methodology.

It will not:

- introduce additional research hypotheses;
- model individual turns or round-by-round turn-order changes;
- attempt to determine causal mechanisms;
- generate automated research conclusions or hypothesis verdicts;
- calculate Feathered Foe night winners or overall winners;
- persist derived research observations or statistical results;
- generalize findings to the broader Wingspan population; or
- expose the research interface to non-staff users.

Future research capabilities should be specified separately rather than added implicitly during implementation.