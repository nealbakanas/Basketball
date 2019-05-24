from urllib.request import urlopen
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

year = 2019
print(year)

totals = "https://www.basketball-reference.com/leagues/NBA_{}_totals.html".format(year)
advanced = "https://www.basketball-reference.com/leagues/NBA_{}_advanced.html".format(year)


def getDF(url):
    # create pandas dataframe from data on basketball-refernce.com
    html = urlopen(url)

    soup = BeautifulSoup(html, features="lxml")

    # soup.findAll('tr', limit=2)

    headers = [th.getText() for th in soup.findAll('tr', limit=2)[0].findAll('th')]

    headers = headers[1:]

    rows = soup.findAll('tr')[1:]

    player_stats = [[td.getText() for td in rows[i].findAll('td')] for i in range(len(rows))]
    stats = pd.DataFrame(player_stats, columns=headers)
    stats = stats.replace(to_replace="None", value=np.nan).dropna()
    return stats


def cleanColumns(df):
    # adjust datatypes of columns to make data easier to use
    for x in df:
        # if x!='\xa0':
        if x.endswith('%') or x in ['PER', 'OWS', 'DWS', 'WS', 'WS/48', 'OBPM', 'DBPM', 'BPM', 'VORP', 'FTr', '3PAr']:
            df[x] = pd.to_numeric(df[x], errors='coerce')
        elif x in ['Player', 'Pos', 'Tm']:
            df[x] = df[x].astype(str)
        else:
            try:
                df[x] = df[x].astype(str).astype(int)
            except ValueError:
                pass
    return df


def getTmWins(team):
    # find teams total wins based on how it is stored in the individual statistic tables
    url = r'https://www.basketball-reference.com/teams/{}/{}.html'.format(team, year)
    html = urlopen(url)

    soup = BeautifulSoup(html, features="lxml")
    ps = [p.getText() for p in soup.find_all('p') if 'Record:' in p.getText()][0].split()[1].split('-')[0]
    return int(ps)


# Scrape team wins and add to dictionary
# seen = set()
# winDict = {}
# for team in stats['Tm']:
#     if team in seen or team == 'TOT':
#         pass
#     else:
#         print(team)
#         print(seen)
#         winDict[team] = getTmWins(team)
#         seen.add(team)
# print(winDict)

# hardcoded team wins to save time and page requests
winDict = {'OKC': 49, 'PHO': 19, 'ATL': 29, 'MIA': 39, 'CLE': 19, 'DEN': 54, 'SAS': 48, 'CHI': 22, 'UTA': 50, 'BRK': 42,
           'NYK': 17, 'POR': 53, 'MEM': 33, 'IND': 48, 'MIL': 60, 'DAL': 33, 'HOU': 53, 'TOR': 58, 'WAS': 32, 'ORL': 42,
           'CHO': 39, 'SAC': 39, 'LAL': 37, 'MIN': 36, 'BOS': 49, 'GSW': 57, 'NOP': 33, 'LAC': 48, 'PHI': 51, 'DET': 41}
# Scrape Advanced stats
advancedStats = getDF(advanced)
# Scrape Regular Season Totals
stats = getDF(totals)
# Convert Data Types of columns
stats = cleanColumns(stats)
advancedStats = cleanColumns(advancedStats)

# Calculate fantasy totals
stats['FantasyTotal'] = (advancedStats['TS%'] * stats['PTS'] + (1.2 * stats['TRB']) + 1.5 * stats['AST'] + 3 * stats[
    'STL'] + 3 * stats['BLK'] - \
                         stats['TOV'] - stats['PF'])

# Level of Impact = (Team Wins * Games Played/82 * Minutes/48 * Usage Rate/100)
# Quality of Impact = .4(VORP+Win Share)+ .2(Net Rating)
# MVP = LOI + QOI

# Add column for team wins
advancedStats['TW'] = advancedStats['Tm']
advancedStats['TW'] = advancedStats['TW'].map(winDict)

# Level of Impact = (Team Wins * Games Played/82 * Minutes/48 * Usage Rate/100)
# Quality of Impact = .4(VORP+Win Share)+ .2(Net Rating)
# Win Contribution = LOI * QOI
# MVP = FantasyStats + Win Contribution

advancedStats['LOI'] = advancedStats['TW'] * (advancedStats['G'] / 82) * (advancedStats['MP'] / 48) * (
        advancedStats['USG%'] / 100)
advancedStats['QOI'] = .4 * (advancedStats['VORP'] + advancedStats['WS']) + .2 * (advancedStats['BPM'])
advancedStats['WinCon'] = advancedStats['LOI'] * advancedStats['QOI']
advancedStats['MVP'] = advancedStats['WinCon'] + stats['FantasyTotal']
print(advancedStats.sort_values(by='MVP', ascending=False).head(20))
