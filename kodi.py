#!/usr/bin/env python

"""
The MIT License (MIT)

Copyright (c) 2015 Maker Musings

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

# For a complete discussion, see http://www.makermusings.com

import datetime
import json
import requests
import time
import urllib


# Change this to the IP address of your Kodi server or always pass in an address

KODI = '192.168.5.31'
PORT = 8080


# These two methods construct the JSON-RPC message and send it to the Kodi player

def SendCommand(address, port, command):
    url = "http://%s:%d/jsonrpc" % (address, port)
    try:
        r = requests.post(url, data=command)
    except:
        return {}
    return json.loads(r.text)

def RPCString(method, params=None):
    j = {"jsonrpc":"2.0", "method":method, "id":1}
    if params:
        j["params"] = params
    return json.dumps(j)


# This is a little weak because if there are multiple active players,
# it only returns the first one and assumes it's the one you want.
# In practice, this works OK in common cases.

def GetPlayerID(address, port):
    info = SendCommand(address, port, RPCString("Player.GetActivePlayers"))
    result = info.get("result", [])
    if len(result) > 0:
        return result[0].get("playerid")
    else:
        return None


# Tell Kodi to update its video or music libraries

def UpdateVideo(address=KODI, port=PORT):
    return SendCommand(address, port, RPCString("VideoLibrary.Scan"))

def UpdateMusic(address=KODI, port=PORT):
    return SendCommand(address, port, RPCString("AudioLibrary.Scan"))



# Perform UI actions that match the normal remote control buttons

def PageUp(address=KODI, port=PORT):
    return SendCommand(address, port, RPCString("Input.ExecuteAction", {"action":"pageup"}))

def PageDown(address=KODI, port=PORT):
    return SendCommand(address, port, RPCString("Input.ExecuteAction", {"action":"pagedown"}))

def ToggleWatched(address=KODI, port=PORT):
    return SendCommand(address, port, RPCString("Input.ExecuteAction", {"action":"togglewatched"}))

def Info(address=KODI, port=PORT):
    return SendCommand(address, port, RPCString("Input.Info"))

def Menu(address=KODI, port=PORT):
    return SendCommand(address, port, RPCString("Input.ContextMenu"))

def Home(address=KODI, port=PORT):
    return SendCommand(address, port, RPCString("Input.Home"))

def Select(address=KODI, port=PORT):
    return SendCommand(address, port, RPCString("Input.Select"))

def Up(address=KODI, port=PORT):
    return SendCommand(address, port, RPCString("Input.Up"))

def Down(address=KODI, port=PORT):
    return SendCommand(address, port, RPCString("Input.Down"))

def Left(address=KODI, port=PORT):
    return SendCommand(address, port, RPCString("Input.Left"))

def Right(address=KODI, port=PORT):
    return SendCommand(address, port, RPCString("Input.Right"))

def Back(address=KODI, port=PORT):
    return SendCommand(address, port, RPCString("Input.Back"))

def PlayPause(address=KODI, port=PORT):
    playerid = GetPlayerID(address, port)
    if playerid:
        return SendCommand(address, port, RPCString("Player.PlayPause", {"playerid":playerid}))

def Stop(address=KODI, port=PORT):
    playerid = GetPlayerID(address, port)
    if playerid:
        return SendCommand(address, port, RPCString("Player.Stop", {"playerid":playerid}))

def Replay(address=KODI, port=PORT):
    playerid = GetPlayerID(address, port)
    if playerid:
        return SendCommand(address, port, RPCString("Player.Seek", {"playerid":playerid, "value":"smallbackward"}))


# Returns a list of dictionaries with information about episodes that have been watched. 
# May take a long time if you have lots of shows and you set max to a big number

def GetWatchedEpisodes(address=KODI, port=PORT, max=90):
    data = SendCommand(address, port, RPCString("VideoLibrary.GetEpisodes", {"limits":{"end":max}, "filter":{"field":"playcount", "operator":"greaterthan", "value":"0"}, "properties":["playcount", "showtitle", "season", "episode", "lastplayed" ]}))
    return data['result']['episodes']


# Returns a list of dictionaries with information about unwatched episodes. Useful for
# telling/showing users what's ready to be watched. Setting max to very high values
# can take a long time.

def GetUnwatchedEpisodes(address=KODI, port=PORT, max=90):
    data = SendCommand(address, port, RPCString("VideoLibrary.GetEpisodes", {"limits":{"end":max}, "filter":{"field":"playcount", "operator":"lessthan", "value":"1"}, "sort":{"method":"dateadded", "order":"descending"}, "properties":["title", "playcount", "showtitle", "tvshowid", "dateadded" ]}))
    answer = []
    shows = set([d['tvshowid'] for d in data['result']['episodes']])
    show_info = {}
    for show in shows:
        show_info[show] = GetShowDetails(show=show)
    for d in data['result']['episodes']:
        showinfo = show_info[d['tvshowid']]
        banner = ''
        if 'banner' in showinfo['art']:
            banner = "http://%s:%s/image/%s" % (address, port, urllib.quote(showinfo['art']['banner']))
        answer.append({'title':d['title'], 'episodeid':d['episodeid'], 'show':d['showtitle'], 'label':d['label'], 'banner':banner, 'dateadded':datetime.datetime.strptime(d['dateadded'], "%Y-%m-%d %H:%M:%S")})
    return answer


# Grabs the artwork for the specified show. Could be modified to return other interesting data.

def GetShowDetails(address=KODI, port=PORT, show=0):
    data = SendCommand(address, port, RPCString("VideoLibrary.GetTVShowDetails", {'tvshowid':show, 'properties':['art']}))
    return data['result']['tvshowdetails']


# Information about the video that's currently playing

def GetVideoPlayItem(address=KODI, port=PORT):
    playerid = GetPlayerID(address, port)
    if playerid:
        data = SendCommand(address, port, RPCString("Player.GetItem", {"playerid":playerid, "properties":["episode","showtitle", "tvshowid", "season", "description"]}))
        return data["result"]["item"]


# Returns information useful for building a progress bar to show a video's play time

def GetVideoPlayStatus(address=KODI, port=PORT):
    playerid = GetPlayerID(address, port)
    if playerid:
        data = SendCommand(address, port, RPCString("Player.GetProperties", {"playerid":playerid, "properties":["percentage","speed","time","totaltime"]}))
        if 'result' in data:
            hours = data['result']['totaltime']['hours']
            speed = data['result']['speed']
            if hours > 0:
                total = '%d:%02d:%02d' % (hours, data['result']['totaltime']['minutes'], data['result']['totaltime']['seconds'])
                cur = '%d:%02d:%02d' % (data['result']['time']['hours'], data['result']['time']['minutes'], data['result']['time']['seconds'])
            else:
                total = '%02d:%02d' % (data['result']['totaltime']['minutes'], data['result']['totaltime']['seconds'])
                cur = '%02d:%02d' % (data['result']['time']['minutes'], data['result']['time']['seconds'])
            return {'state':'play' if speed > 0 else 'pause', 'time':cur, 'total':total, 'pct':data['result']['percentage']}
    return {'state':'stop'}


