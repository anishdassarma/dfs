def formatted_for_length(word, length, for_display=True):
    if for_display:
        return word + ((length - len(word)) / 8) * '\t'
    return word


def print_all_players(player_list, SEP='\t'):

    max_player_length = max(len(player.name) for player in player_list)

    header = True
    for player in player_list:
        if header:
            print SEP.join([
                formatted_for_length('#Name', max_player_length),
                'team',
                'salary',
                'pos',
                'floor',
                'ceiling',
                'avg',
                'value (proj/sal)',
                'lineup_order'
            ])
            header = False
        try:
            value = player.projected_points / player.salary
        except:
            value = None
        print SEP.join(map(str, [
            formatted_for_length(player.name, max_player_length),
            player.team.name,
            player.salary,
            player.position,
            player.projected_points,
            player.projected_points,
            player.projected_points,
            value,
            player.lineup_order
        ]))
