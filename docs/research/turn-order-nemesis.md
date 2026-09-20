# Wingspan Turn Order Research Methodology

**Version:** 0.3
**Status:** Draft

## 1. Purpose

This study investigates whether turn order is associated with player performance in competitive Wingspan games.

The analysis focuses on two selected human players:

* **Primary player:** the player from whose perspective the analysis is performed.
* **Secondary player:** the human opponent used for comparison.

Performance is evaluated both as the primary player's individual scoring performance and as their performance relative to the secondary player.

The study evaluates three turn-order hypotheses:

1. Starting Position
2. Direct Following
3. Player Spacing

## 2. Scope and Assumptions

Only competitive games containing results for both selected players are eligible.

For purposes of this study, each competitive game is assumed to contain exactly five players:

* the primary human player;
* the secondary human player; and
* three computer players.

This configuration is an analytical assumption where it cannot be verified from the recorded data. Games that did not actually use this configuration may produce incorrectly classified turn-order relationships.

Each qualifying game is treated as one observation from the primary player's perspective.

A date range may be used to restrict the study population.

## 3. Simplified Turn-Order Model

Wingspan turn order changes between rounds. A player's starting position therefore does not represent their ordinal position throughout the entire game.

This study intentionally does not model individual turns or round-by-round changes. Instead, it uses starting turn order and the circular relationship between the two human players as simplified representations of turn order.

The analysis does not attempt to model computer-player decisions, resource availability, individual bird selections, or other within-game interactions.

Results should therefore be interpreted as associations between turn-order characteristics and performance, not as a complete causal model of turn order.

## 4. Recorded Variables

The following raw values are required for each qualifying game:

* Game identifier
* Game date
* Primary player
* Secondary player
* Primary starting position
* Secondary starting position
* Primary final score
* Secondary final score

Derived variables may include:

* Primary score differential
* Primary head-to-head outcome
* Direct-following status
* Number of computer players between the secondary and primary player in the direction of play

Raw starting positions must be retained so derived turn-order variables can be independently reproduced.

## 5. Performance Measures

Each hypothesis may be evaluated using three measures of performance.

### 5.1 Final Score

The primary player's final score measures individual scoring performance.

This allows the primary player's results under different turn-order conditions to be compared with their general scoring results within the selected dataset.

### 5.2 Score Differential

Score differential measures performance relative to the secondary player:

**Primary Score − Secondary Score**

Positive values indicate that the primary player outscored the secondary player. Negative values indicate the opposite.

### 5.3 Head-to-Head Outcome

A win occurs when the primary player's final score is greater than the secondary player's final score.

A loss occurs when it is lower.

Tied scores will be reported separately and excluded from binary win/loss analysis.

## 6. Research Hypotheses

Each hypothesis will be evaluated against final score, score differential, and head-to-head outcome where statistically appropriate.

### 6.1 Starting Position

**Question:** Is the primary player's starting position associated with performance?

The primary player's starting position is classified from 1 through 5.

**Null hypothesis:** Performance does not differ according to starting position.

**Alternative hypothesis:** Performance differs according to starting position.

Starting position will initially be treated as categorical. No assumption is made that its effect is linear from positions 1 through 5.

### 6.2 Direct Following

**Question:** Does the primary player perform differently when directly following the secondary player in the circular turn order?

Games are classified as either:

* directly following the secondary player; or
* not directly following the secondary player.

Circular wraparound is recognized. Starting position 1 therefore directly follows starting position 5.

**Null hypothesis:** Performance does not differ between the two conditions.

**Alternative hypothesis:** Performance differs when the primary player directly follows the secondary player.

### 6.3 Player Spacing

**Question:** Is primary-player performance associated with the number of computer players between the secondary and primary player in the direction of play?

Spacing is classified as:

* 0 computer players
* 1 computer player
* 2 computer players
* 3 computer players

**Null hypothesis:** Performance does not differ according to player spacing.

**Alternative hypothesis:** Performance differs according to player spacing.

Spacing will initially be treated as categorical. A linear relationship between spacing and performance will not be assumed.

## 7. Analysis

Each hypothesis should first be evaluated descriptively.

Where applicable, descriptive statistics should include:

* number of games;
* mean and median final score;
* standard deviation of final score;
* mean and median score differential;
* standard deviation of score differential;
* wins, losses, and ties; and
* win percentage.

Inferential tests will then be selected based on the hypothesis, outcome type, sample size, distribution of observations, and assumptions of the statistical test.

The statistical test used, its assumptions, significance threshold, effect size where appropriate, and confidence interval should be reported with the result.

## 8. Interpretation

The three performance measures answer related but distinct questions.

**Final score** evaluates the primary player's performance against their own general scoring results.

**Score differential** evaluates the magnitude of the primary player's performance relative to the secondary player.

**Head-to-head outcome** evaluates whether the primary player defeated the secondary player.

Evidence found for one outcome should not automatically be treated as evidence for the others.

Statistical significance indicates evidence against the specified null hypothesis under the assumptions of the test. It does not establish that turn order caused the observed difference.

A non-significant result does not establish that no effect exists. It indicates that the available data did not provide sufficient evidence to reject the null hypothesis.

Observed effect size, sample size, uncertainty, and descriptive statistics should be considered alongside statistical significance.

## 9. Limitations

The study uses historical observational data and a simplified model of Wingspan turn order.

Important limitations include:

* the assumption of exactly two human and three computer players;
* turn-order rotation between rounds;
* unmeasured computer-player behavior;
* unmeasured card, food, objective, and resource availability;
* differences in player strategy and skill;
* changes in player skill over time;
* possible changes in game rules or configuration; and
* limited sample sizes within individual turn-order categories.

The study can identify statistical relationships in the recorded games but cannot independently establish the mechanisms responsible for those relationships.

## 10. Reproducibility

The methodology is independent of the software used to perform the analysis.

Given the same source game records, primary and secondary player selection, date range, inclusion criteria, and methodology, another implementation should produce the same research dataset and statistical results.

## 11. Exploratory Scope and Future Generalization

This research is an exploratory observational study of a specific sample of competitive games between two human players. Its purpose is to identify and quantify potential relationships between turn order and player performance within this sample.

Results from this study should not be assumed to represent Wingspan players generally. Any relationships identified apply directly only to the games and players included in the study.

The hypotheses and methodology developed through this exploratory study may later provide the basis for a separate population-level study if Wingspan Portal accumulates sufficient data from a larger and more diverse group of players.

Such a study should use new player data to evaluate whether the relationships identified here also appear across the broader population. This would allow the original hypotheses to be tested for generalizability rather than assuming that patterns observed between two players apply universally.

The exploratory study and any future population-level study should therefore be treated as distinct phases of research, with their respective datasets, methods, results, and conclusions reported separately.
