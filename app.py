from flask import Flask
from flask import request, jsonify, make_response
import requests
import time

app = Flask(__name__)

picks_url = "https://fantasy.premierleague.com/api/entry/{team_id}/event/{gameweek}/picks/"
transfer_url = "https://fantasy.premierleague.com/api/entry/{team_id}/transfers/"
info_url = "https://fantasy.premierleague.com/api/entry/{team_id}/"


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/fpl_data")
def fetch_fpl_data():
    fpl_id = request.args.get('id', '')
    if fpl_id == '':
        return "Missing ID"
    max_gw = int(request.args.get('gw', 38))

    player_data = {'info': {}, 'picks': {}, 'trs': []}

    for gw in range(1,max_gw+1):
        picks = requests.get(picks_url.format(team_id=fpl_id, gameweek=gw))
        if picks.status_code == 200:
            picks = picks.json()
        player_data['picks']['GW'+str(gw)] = picks

    r = requests.get(info_url.format(team_id=fpl_id))
    player_data['info'] = r.json()

    r = requests.get(transfer_url.format(team_id=fpl_id))
    player_data['trs'] = r.json()

    return make_response(jsonify(player_data), 200)


if __name__ == "__main__":
    app.config['DEBUG']=True
    from app import app
    app.run(host='0.0.0.0', port=8001, debug=True)
