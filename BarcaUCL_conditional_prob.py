import scipy.stats as stats
import numpy as np

# reading the injury types, average return data, and likelihood of the injuries csv file
def info_injury():
    injury_type = []
    probability = []
    expected_return = []
    with open("injury.csv", "r") as f:
        f.readline()
        # 13 - 17 Days
        for line in f:
            injury, prob, xreturn = line.strip().split(",")
            injury_type.append(injury.strip())
            prob = prob.strip().split("%")
            probability.append(float(prob[0])/100)
            date_1,date_2 = xreturn.strip().split("-")
            date_2 = date_2.split(maxsplit=1)[0].strip()
            expected_return.append((float(date_1.strip()) + float(date_2)/2))
    return injury_type, probability, expected_return

possible_injuries, probability, expected_return_date = info_injury()

# read elo of the teams

def read_teams():
    team_elo = dict()
    with open("teams.csv", "r") as f:
        f.readline()
        for line in f:
            team, elo, class_value = line.strip().split(",")
            if team not in team_elo:
                team_elo[team] = [int(elo.strip()), int(class_value.strip())]
    return team_elo

team_elo = read_teams()

# read ratings of barca's players

def read_rating():
    player_rating_forward = dict()
    player_rating_midfielder= dict()
    player_rating_defender = dict()
    player_rating_goalkeeper = dict()
    with open("Sofascore rating until march 9.csv", "r") as f:
        f.readline()
        for line in f:
            position, player, rating = line.strip().split(",")
            if position.strip() == "Attackers":
                player_rating_forward[player] = float(rating.strip()) - 6
            elif position.strip() == "Defenders":
                player_rating_defender[player] = float(rating.strip()) -6
            elif position.strip() == "Goalkeepers":
                player_rating_goalkeeper[player] = float(rating.strip()) - 6
            else:
                player_rating_midfielder[player] = float(rating.strip()) - 6
    return player_rating_forward, player_rating_midfielder, player_rating_defender, player_rating_goalkeeper



class Player:
    def __init__(self, name, importance_weight):
        self.name = name
        self.w = importance_weight
        self.injured = False
        self.out_for = 0
        self.possible_injuries = possible_injuries
        self.prob = probability
        self.injury_x_return = expected_return_date
        self. injury_name = ""

    def call(self, is_matchday = True):
        """this is the function that the coach will use to call the player
            now this function will first check if there is an injury, by sampling a bernouli(p) where p is the probability that a player gets injured
            and then if there is an injury it will sample a multinomial injury type, and finally sample a return date from weilboul"""
        if self.injured:
            self.out_for -= 1
            if self.out_for == 0:
                self.injured = False
                self.injury_name = ""
            return False

        # now lets check the if the player is injured in the last match or in the training. I know it feels counter intuitive to check player's chance of injury during the match, after the match. But it still gets the job done, its a matter of perspective
        injury_p = 0.054 if is_matchday else 0.007
        u = np.random.uniform(0,1)
        if u <= injury_p:
            self.injured = True
            self.out_for = self.assign_injury()
            return False
        return True

    def assign_injury(self):
        """This function will first sample the injury type, which is distributed as Multinomial(1, p_vector), and then
        it will sample a weibull distribution for expected return date"""
        multinomial_cdf = np.cumsum(self.prob)
        u = np.random.uniform(0,1)
        region = 0
        for r in range(multinomial_cdf.size):
            if u <= multinomial_cdf[r]:
                region = r
                break
        self.injury_name = self.possible_injuries[region]

        # now lets sample a weibull distribution
        # c=1.5 gives a realistic 'right-skewed' tail for recovery
        shape_c = 1.5
        xreturn = self.injury_x_return[region]
        adjusted_xreturn = xreturn / (np.log(2)**(1/shape_c))
        return max(1,int(stats.weibull_min.rvs(c=1.5, scale=adjusted_xreturn)))   # applies uniform sampling automatically


def create_players(player_rating):
    players = []
    for name, rating in player_rating.items():
        players.append(Player(name, rating))
    return players

def extract_points(s):
    team_form = {"L":0,"D":0, "W":0}
    for char in s:
        if char == "W":
            team_form["W"] += 1
        elif char == "L":
            team_form["L"] += 1
        else:
            team_form["D"] += 1

    return team_form
forward, midfielder, defender, goalkeeper = read_rating()
points_as_of_march_14 = {"Barcelona": 67, "Real Madrid": 63, "Atletico Madrid": 54}
form_as_of_march_14 = {"Barcelona" : "WLWWW", "Real Madrid": "WWLLW", "Atletico Madrid" : "LLWWW"}
class Team:
    def __init__(self, name, is_barca = False, is_madrid = False, is_atletico = False):
        if name not in team_elo:
            raise ValueError("Team name not found in the dataset")
        self.name = name
        self.elo = team_elo[name][0]
        self.is_barca = is_barca
        self.class_ = team_elo[name][1]
        if is_barca:
            self.attackers = create_players(forward)
            self.midfielders = create_players(midfielder)
            self.defenders = create_players(defender)
            self.goalkeepers = create_players(goalkeeper)
            self.ideal_line_up_rating = 13.86
        if is_barca or is_madrid or is_atletico:
            self.form = form_as_of_march_14[name]  # past 5 games of laliga teams
            self.form_numerical = extract_points(self.form)
            self.point = points_as_of_march_14[name]
    def assemble(self, is_big_matchday = False):
        if self.is_barca:
            match_day_elo = self.sample_lineup(is_big_matchday)
            return match_day_elo
        return self.elo
    def sample_lineup(self, is_big_matchday):
        """
        This function will sample each category of the team: attacker, midfielder, defender, goalkeeper. To do so it will model each category of the team as multinomial(n, p_vector)
        where p_vector is the importance weight of each player. and n is the number of attackers, midfielder, defender, and goalkeeper to be sampled which respectively are 3,3,4,1
        :return: this function will compare the match day starting eleven, compare it with the ideal starting eleven, and then return adjusted elo
        """
        # first we call healthy memebers

        healthy_attackers = [p for p in self.attackers if p.call()]
        healthy_midfielders = [p for p in self.midfielders if p.call()]
        healthy_defenders = [p for p in self.defenders if p.call()]
        healthy_goalkeeper = [p for p in self.goalkeepers if p.call()]

        # then we sample a lineup
        k = 4 if is_big_matchday else 2    # this is to ensure that the best players gets chosen in a big match.
        sampled_lineup = (self.multinomial_without_replacement(healthy_attackers,3, k) + self.multinomial_without_replacement(healthy_midfielders,3, k)
                          + self.multinomial_without_replacement(healthy_defenders,4,k) + self.multinomial_without_replacement(healthy_goalkeeper,1,k))
        total_rating = sum([p.w for p in sampled_lineup])
        return (total_rating/self.ideal_line_up_rating)*self.elo


    def multinomial_without_replacement(self, healthy_pool, n, k = 1):
        """
        Weighted sampling without replacement (Successive Sampling).
        This handles the 'Tactical Rotation' logic.
        """
        selected_squad = []
        current_pool = list(healthy_pool)
        actual_n = min(len(current_pool), n)

        for _ in range(actual_n):
            # 1. Get the current weights of everyone left in the pool
            weights = np.array([p.w ** k for p in current_pool])

            # 2. Renormalize: Turn weights into a probability vector that sums to 1
            probs = weights / weights.sum()

            # 3. Inverse Transform (CDF) Region Check
            u = np.random.uniform(0, 1)
            cum_probs = np.cumsum(probs)

            for i, threshold in enumerate(cum_probs):
                if u <= threshold:
                    # 4. Remove the sampled player so they can't be picked again
                    # This is the 'without replacement' part
                    chosen_player = current_pool.pop(i)
                    selected_squad.append(chosen_player)
                    break
        return selected_squad

    def update_points(self, result):
        res_points = {"D":1, "L":0, "W":3}
        self.form = (self.form+result)[1:]
        self.form_numerical = extract_points(self.form)
        self.point = self.point + res_points[result]







