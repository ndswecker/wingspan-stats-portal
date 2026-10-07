# Wingspan Turn Order Research Methodology

**Version:** 0.4  
**Status:** Draft

## 1. Purpose

This study investigates whether turn order is associated with player performance in competitive Wingspan games.

Each analysis is performed from the perspective of two selected human players:

* **Principal player:** the player whose performance is being analyzed.
* **Opponent:** the other human player whose score and turn-order relationship are used for comparison.

All performance measures and derived turn-order relationships are expressed from the perspective of the principal player.

The study evaluates three turn-order hypotheses:

1. Starting Position
2. Direct Preceding
3. Player Spacing

## 2. Scope and Assumptions

Only competitive games containing results for both selected players are eligible.

For purposes of this study, each competitive game is assumed to contain exactly five players:

* the principal human player;
* the opponent; and
* three computer players.

This configuration is an analytical assumption where it cannot be verified from the recorded data. Games that did not actually use this configuration may produce incorrectly classified turn-order relationships.

Each qualifying game is treated as one observation from the principal player's perspective.

A date range may be used to restrict the study population.

## 3. Simplified Turn-Order Model

Wingspan turn order changes between rounds. A player's starting position therefore does not represent their ordinal position throughout the entire game.

This study intentionally does not model individual turns or round-by-round changes. Instead, it uses starting turn order and the circular relationship between the principal player and opponent as simplified representations of turn order.

The circular relationship between players is retained as the starting player rotates between rounds. Turn-order relationships therefore recognize wraparound between starting positions 5 and 1.

The analysis does not attempt to model computer-player decisions, resource availability, individual bird selections, or other within-game interactions.

Results should therefore be interpreted as associations between turn-order characteristics and performance, not as a complete causal model of turn order.

## 4. Recorded Variables

The following raw values are required for each qualifying game:

* Game identifier
* Game date
* Principal player
* Opponent
* Principal starting position
* Opponent starting position
* Principal final score
* Opponent final score

Derived variables may include:

* Principal score differential
* Principal head-to-head outcome
* Winning player
* Direct-preceding status
* Number of computer players after the principal player and before the opponent
* Number of computer players after the opponent and before the principal player

Raw starting positions must be retained so derived turn-order variables can be independently reproduced.

## 5. Performance Measures

Each hypothesis may be evaluated using three measures of performance.

### 5.1 Final Score

The principal player's final score measures individual scoring performance.

This allows the principal player's results under different turn-order conditions to be compared with their general scoring results within the selected dataset.

### 5.2 Score Differential

Score differential measures performance relative to the opponent:

**Principal Score − Opponent Score**

Positive values indicate that the principal player outscored the opponent. Negative values indicate the opposite.

### 5.3 Head-to-Head Outcome

A win occurs when the principal player's final score is greater than the opponent's final score.

A loss occurs when it is lower.

Tied scores will be reported separately and excluded from binary win/loss analysis.

## 6. Research Hypotheses

Each hypothesis will be evaluated against final score, score differential, and head-to-head outcome where statistically appropriate.

All hypotheses are evaluated from the perspective of the principal player.

### 6.1 Starting Position

**Question:** Is the principal player's starting position associated with performance?

The principal player's starting position is classified from 1 through 5.

**Null hypothesis:** Performance does not differ according to starting position.

**Alternative hypothesis:** Performance differs according to starting position.

Starting position will initially be treated as categorical. No assumption is made that its effect is linear from positions 1 through 5.

### 6.2 Direct Preceding

**Question:** Does the principal player perform differently when directly preceding the opponent in the circular turn order?

Games are classified as either:

* directly preceding the opponent; or
* not directly preceding the opponent.

The principal player directly precedes the opponent when no computer player occurs between them in the direction of play from the principal player to the opponent.

Circular wraparound is recognized. Starting position 5 therefore directly precedes starting position 1.

This condition is independent of the principal player's absolute starting position. A principal player may directly precede the opponent from any starting position where the circular relationship satisfies this condition.

**Null hypothesis:** Performance does not differ between the two conditions.

**Alternative hypothesis:** Performance differs when the principal player directly precedes the opponent.

### 6.3 Player Spacing

**Question:** Is principal-player performance associated with the number of computer players occurring after the principal player and before the opponent in the circular turn order?

Spacing is measured in the direction of play from the principal player to the opponent and is classified as:

* 0 computer players
* 1 computer player
* 2 computer players
* 3 computer players

For example, a spacing value of 0 means that the principal player directly precedes the opponent. A spacing value of 3 means that all three computer players occur after the principal player and before the opponent.

The complementary number of computer players occurring after the opponent and before the principal player may also be retained in the research dataset to fully represent the circular relationship.

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

The analysis should retain sufficient intermediate information to allow the statistical results to be independently inspected and reproduced. Statistical outputs should be presented as evidence rather than converted into automated conclusions about whether a hypothesis is supported.

## 8. Interpretation

The three performance measures answer related but distinct questions.

**Final score** evaluates the principal player's performance against their own general scoring results.

**Score differential** evaluates the magnitude of the principal player's performance relative to the opponent.

**Head-to-head outcome** evaluates whether the principal player defeated the opponent.

Evidence found for one outcome should not automatically be treated as evidence for the others.

Statistical significance indicates evidence against the specified null hypothesis under the assumptions of the test. It does not establish that turn order caused the observed difference.

A non-significant result does not establish that no effect exists. It indicates that the available data did not provide sufficient evidence to reject the null hypothesis.

Observed effect size, sample size, uncertainty, and descriptive statistics should be considered alongside statistical significance.

Interpretation of the statistical evidence remains the responsibility of the researcher.

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

For example, an association between direct preceding or player spacing and performance would not independently demonstrate that changes to the bird tray, resource availability, computer-player actions, or any other particular game mechanism caused the observed relationship.

## 10. Reproducibility

The methodology is independent of the software used to perform the analysis.

Given the same source game records, principal player and opponent selection, date range, inclusion criteria, and methodology, another implementation should produce the same research dataset and statistical results.

Derived turn-order variables must be reproducible from the recorded starting positions and the five-player circular turn-order model.

## 11. Exploratory Scope and Future Generalization

This research is an exploratory observational study of a specific sample of competitive games between two human players. Its purpose is to identify and quantify potential relationships between turn order and principal-player performance within this sample.

Results from this study should not be assumed to represent Wingspan players generally. Any relationships identified apply directly only to the games and players included in the study.

The hypotheses and methodology developed through this exploratory study may later provide the basis for a separate population-level study if Wingspan Portal accumulates sufficient data from a larger and more diverse group of players.

Such a study should use new player data to evaluate whether the relationships identified here also appear across the broader population. This would allow the original hypotheses to be tested for generalizability rather than assuming that patterns observed between two players apply universally.

The exploratory study and any future population-level study should therefore be treated as distinct phases of research, with their respective datasets, methods, results, and conclusions reported separately.