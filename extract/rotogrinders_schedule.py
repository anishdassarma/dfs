from bs4 import BeautifulSoup
import data.team
from selenium import webdriver

URL = 'https://rotogrinders.com/schedules/{game}'


def load_teams(game, args):
    if "--display" not in args:
        return None
    driver = webdriver.Chrome('/Users/ben/Downloads/chromedriver')
    link = URL.format(game=game)
    driver.get(link)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()
    header = []
    for th in soup.find_all(name='thead')[0].findChildren(name='th'):
        header.append(th.text)

    assert header == [u'Time', u'Team', u'Opponent', u'Line', u'Moneyline',
                      u'Over/Under', u'Projected Points',
                      u'Projected Points Change']

    d = {}

    for tr in soup.find_all(name='tr'):
        if 'id' in tr.attrs:
            continue
        row = []
        for td in tr.findChildren(name='td'):
            row.append(td.text)
        if row:
            d[row[1]] = data.team.Team(row[1], row[0], *row[2:])
    print 'Found ', d.keys()
    return d
