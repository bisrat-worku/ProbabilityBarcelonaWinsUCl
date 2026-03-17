# ProbabilityBarcelonaWinsUCl
Applying the "Stat 110" Philosophy to Elite Football Forecasting 

🚀 README: Stochastic Season Simulator 

The Motive: "Condition on what you wish you knew" 
This project is an exploration of the probability distributions and strategies found in Professor Joe Blitzstein’s Introduction to Probability. The core architecture is driven by the Law of Total Probability (LOTP) and the fundamental Blitzstein advice: "Condition on what you wish you knew." 

To find the probability that Barcelona wins the Champions League, there are a million branches we wish we knew: Who will they draw in the Round of 8? Who survives the Semi-final? Will a domestic title clinch provide a psychological edge? Because we cannot know the future, we treat these unknowns as random variables and use Bayesian Updating to refine our predictions as the simulation progresses from March 17th to the end of May.

Given the immense "noise" in football data, this project focuses on four key "stories": 

    Player Availability: The health of the squad as the foundation of strength.
    
    The "Big Three" Momentum: Detailed form conditioning for the giants of Spanish football (FC Barcelona, Real Madrid, and Atlético Madrid).
    
    Title-Clinch Dynamics: How winning La Liga alters the probability space for the European bracket.
    
    UCL Knockout Progression: Modeling the sequential conditional probability of advancing through the Quarter-finals and Semi-finals.

🎲 The Distribution Toolkit I have implmented: 

      Bernoulli: Daily injury "failure" checks.
      
      Weibull: Realistic recovery timelines for injured players.Uniform: Randomizing draw dates and minor atmospheric variables.
      
      Multinomial: Successive sampling for matchday lineups and categorical results.
      
      Dirichlet: Modeling the "Match-Day Chaos" and volatility of the result density.
      
      Poisson: Bridging categorical wins to discrete goal counts for aggregate tie-breakers.
      
      Uniform: for sampling a given distribiton 


**🏗️ Project Pipeline**
**1. The Atomic Layer:** Player Health & Survival. The simulation begins at the individual player level.

Every player is treated as an autonomous unit with a state: [Available] or [Injured]. 
     Injury Modeling: Availability is determined via Bernoulli Sampling. On every simulated day (matchday or training), we perform a Bernoulli trial $X \sim \text{Bernoulli}(p)$.Parameters: The probability of "failure" (injury) $p$ is derived from longitudinal sports medicine data.Reference: Analysis of injury rates in professional football (UEFA Study).

     Injury selection: If a player fails the bernouli test above, an injury will be sampled from injury lists. not every injury have equal chance of happening.
     To do this we use the injury.csv file which has the likelhood of the injury happening and the average return date for the injury type. This file is               is again scraped from Analysis of injury rates in professional football (UEFA Study). To sample injuries that have different probabilities of happening, we       will use a multinomial distribution. 
     
     Recovery: Once the injury is sampled, then we use a Weibull Distribution(expected return date of the injury, c= 1.5) to sample the recovery date. 
     The reason why weibull and not exponential is because weibull has memory, meaning events happen around the expected the lambda, which in this case the            expected return date, which is what we want: players to return around the expeceted return date. 

**2. The Organizational Layer:**
   
   The "Team" is not a static Elo rating,  but a dynamic assembly based on the current health pool. 
   
   Successive Sampling: For matchday assembly, we don't just pick the best players. We use a weighted Multinomial Sampling (sampling without replacement) where each player’s weight $w$ is their SofaScore Rating.
   
   Elo Scaling: The team’s "Matchday Elo" is a scaled function of their theoretical max:$$Elo_{Matchday} = \left( \frac{\sum SofaScore_{Current}}{\sum SofaScore_{Ideal}} \right) \times Elo_{Base}$$

   This idea is only implmented for Barcelona given it requires collecting information about all the players, which can be done, but for now we will assume that 
    that every team other than barca plays with their ideal squad every single time.
   
   
   Form Tracking: The Team object maintains a rolling state of the last 5 games as a vector $F = [L, D, W]$, which acts as the "Momentum" input for the next         player.
  
**3. The Predictive Layer**: Conditioned Prior ProbabilitiesBefore a ball is kicked, we calculate the "Expectancy" of the match using a Logistic-to-Arctan pipeline.

    The Logistic Prior: Based on the Elo gap ($\Delta$), we calculate the initial probability $P(W, D, L)$ using a standard logistic curve adjusted by a Draw Gap (anchor for league parity).
    
    The Arctan Form Filter: We apply a non-linear "Momentum" shift. We use the Arctan function because it allows for diminishing returns—form can only help you        so much before it hits a ceiling:$$P_{Conditioned} = \text{softmax}(P_{Prior} + \eta \cdot \arctan(F))$$Where $\eta$ is a dampening coefficient to prevent         form from over-powering fundamental Elo.4. 
    
    The Chaos Layer: To capture "The Magic of the Cup" or "Any Given Sunday," we use a Dirichlet Distribution (the distribution that models probabilities             itself). 
    
    The Class Factor ($C$): This parameter is supposed to capture how predictible a team is. For now this value is given based on the elo rating of the team, so      high values for top teams, and low for lower teams. But this means only top teams are expected to perform at the top level, but more often than not, we can       expect bad teams to perform badly. Which is why in the future, instead of giving this value manually, I will implmnet a k means algorithm to find                 clusters of teams, analyze if the clusters are grouped into top, mid, and bottom teams, which is what we are implmenting now, or top+bottom and mid,              which will mean we can trust top and bottom teams to perform consistently. The features i will be using then will be **elo and (expected point in a season -      real point in a season). **
    
    
    
    Stochastic Density: By feeding our Conditioned_Prob into a Dirichlet  distribution as the $\alpha$ parameters (scaled by $C$), we generate a Match-Day            Probability Vector.High $C$: The vector stays close to the expectation (Predictable).  Low $C$: The distribution spreads out (Chaos/Upsets). 
   
**4. The Sampling Layer: ** Where i am currently at.  Multinomial vs. Poisson. The Dilemma: * Multinomial: Excellent for single-game "W/D/L" results, but "Goal-Blind."Poisson: Samples discrete goals ($\lambda$). Essential for UCL 2-leg aggregates where away goals (historical) or total goal-diff matters.

    The Experiment Im conducting is **A Model Equivalence Test**. I am running 1,000 Monte Carlo trials across 50 random fixtures to calculate the Covariance         between these two sampling methods. Goal: If $Cov(Res_{Mult}, Res_{Poiss})$ is high, we adopt Poisson globally. If not, we fine-tune $\lambda = 2.8$ (the         global goal average) to align its prediction with the mutlinomial one.

**To be continued**
