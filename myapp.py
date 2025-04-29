from flask import Flask
from flask import request, jsonify, make_response
from flask_cors import CORS
import requests
import time
from functools import wraps
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)
application = app

# Cache setup
cache = {}
CACHE_EXPIRY = 12 * 60 * 60 # 12 hours in seconds

picks_url = "https://fantasy.premierleague.com/api/entry/{team_id}/event/{gameweek}/picks/"
transfer_url = "https://fantasy.premierleague.com/api/entry/{team_id}/transfers/"
info_url = "https://fantasy.premierleague.com/api/entry/{team_id}/"

cup_status_url = "https://fantasy.premierleague.com/api/league/{league_id}/cup-status/"
cup_results_url = "https://fantasy.premierleague.com/api/leagues-h2h-matches/league/{cup_id}/?page=1&event={gw}"


def cached_request(url, expiry=CACHE_EXPIRY):
    """Make a cached request to the given URL"""
    now = time.time()
    
    if url in cache and cache[url]['expires'] > now:
        print(f"Cache hit for {url}")
        return cache[url]['data']
    
    print(f"Cache miss for {url}, fetching from API")
    response = requests.get(url)
    
    if response.status_code == 200:
        result = response.json()
        cache[url] = {
            'data': result,
            'expires': now + expiry
        }
        return result
    
    return response


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/fpl_data")
def fetch_fpl_data():
    fpl_id = request.args.get('id', '')
    if fpl_id == '':
        return "Missing ID", 404
    max_gw = int(request.args.get('gw', 38))
    cache_key = f"fpl_data_{fpl_id}_{max_gw}"
    
    # Check if we have this data cached
    now = time.time()
    if cache_key in cache and cache[cache_key]['expires'] > now:
        return make_response(jsonify(cache[cache_key]['data']), 200)

    player_data = {'info': {}, 'picks': {}, 'trs': []}

    for gw in range(1,max_gw+1):
        picks = requests.get(picks_url.format(team_id=fpl_id, gameweek=gw))
        if picks.status_code == 200:
            picks = picks.json()
        player_data['picks']['GW'+str(gw)] = picks

    # r = requests.get(info_url.format(team_id=fpl_id))
    # player_data['info'] = r.json()
    player_data['info'] = cached_request(info_url.format(team_id=fpl_id))

    # r = requests.get(transfer_url.format(team_id=fpl_id))
    # player_data['trs'] = r.json()
    player_data['trs'] = cached_request(transfer_url.format(team_id=fpl_id))
    
    # Cache the complete response
    cache[cache_key] = {
        'data': player_data,
        'expires': now + CACHE_EXPIRY
    }

    return make_response(jsonify(player_data), 200)


@app.route("/general_info")
def general_info():
    fpl_id = request.args.get('id', '')
    if fpl_id == '':
        return "Missing ID", 404
    # r = requests.get(info_url.format(team_id=fpl_id))
    # player_info = r.json()
    
    url = info_url.format(team_id=fpl_id)
    player_info = cached_request(url)
    
    return make_response(jsonify(player_info), 200)


@app.route("/cup_info")
def cup_info():
    league_id = request.args.get('league_id', '')
    cup_id = request.args.get('cup_id', '')

    if league_id == '' or cup_id == '':
        return "Missing ID", 404

    cache_key = f"cup_info_{league_id}_{cup_id}"
    # Check if we have this data cached
    now = time.time()
    if cache_key in cache and cache[cache_key]['expires'] > now:
        return make_response(jsonify(cache[cache_key]['data']), 200)

    start_gw = 33

    # r = requests.get(cup_status_url.format(league_id=league_id))
    # cup_status = r.json()
    cup_status = cached_request(cup_status_url.format(league_id=league_id))

    results = {}

    for gw in range(start_gw, 39):
        # r = requests.get(cup_results_url.format(cup_id=cup_id, gw=gw))
        url = cup_results_url.format(cup_id=cup_id, gw=gw)
        # results[gw] = r.json()
        results[gw] = cached_request(url)

    data = {'status': cup_status, 'results': results}
    
    # Cache the complete response
    cache[cache_key] = {
        'data': data,
        'expires': now + CACHE_EXPIRY
    }

    return make_response(jsonify(data), 200)


# Add a cache clear endpoint (optional, for admin use)
@app.route("/clear_cache")
def clear_cache():
    global cache
    cache = {}
    return "Cache cleared", 200



if __name__ == "__main__":
    # app.config['DEBUG']=True
    # from app import app
    # app.run(host='0.0.0.0', port=9000, debug=True)
    app.run()
