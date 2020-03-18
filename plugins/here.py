# -*- coding: utf-8 -*-
# append from TIS Trinity Union's repositories
# use for test
import re
import time
import os

here_user = 0

def onServerInfo(server, info):
    global here_user
    WAYPOINT_SUPPORT = False
    HIGHLIGHT_ENABLE = False
    dimension_convert = {"0": "主世界", "-1": "地狱", "1": "末地"}
    if (info.isPlayer == 0):
        if ("following entity data" in info.content):
            if here_user > 0:
                name = info.content.split(" ")[0]
                dimension = re.search("(?<=Dimension: )-?\d", info.content).group()
                position_str = re.search("(?<=Pos: )\[.*?\]", info.content).group()
                position = re.findall("\[(-?\d*).*?, (-?\d*).*?, (-?\d*).*?\]", position_str)[0]
                position_show = "[x:" + str(position[0]) + ",y:" + str(position[1]) + ",z:" + str(position[2]) + "]"
                if (WAYPOINT_SUPPORT):
                    pass
                else:
                    if dimension == '0':
                        server.say("§e" + name + "§r @ §2" + dimension_convert[dimension] + position_show)
                    elif dimension == '1':
                        server.say("§e" + name + "§r @ §5" + dimension_convert[dimension] + position_show)
                    elif dimension == '-1':
                        server.say("§e" + name + "§r @ §4" + dimension_convert[dimension] + position_show)
                if (HIGHLIGHT_ENABLE):
                    server.execute("effect give " + name + " minecraft:glowing 15 1 true")
                    server.tell(name, "您将会被高亮15秒。")
                here_user -= 1
    else:
        if info.content.startswith('!!here'):
            here_user += 1
            server.execute("data get entity " + info.player)
