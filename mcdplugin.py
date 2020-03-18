﻿# -*- coding: utf-8 -*-
#this file includes basic plugin features

import os
import sys
import traceback
from imp import load_source
from mcdlog import *

class mcdplugin(object):
  def __init__(self):
    self.initPlugins()
    
  def initPlugins(self): #find plugins and init
    self.pluginList = []
    self.plugins = []
    self.startupPlugins = []
    self.onPlayerJoinPlugins = []
    self.onPlayerLeavePlugins = []
    path = 'plugins'
    filelist = os.listdir(path)
    for singleFile in filelist:
      filepath = path + '/' + singleFile
      if os.path.isfile(filepath):
        if singleFile.endswith('.py'):
          tryto = False
          try:
            self.pluginList.append(singleFile[:-3])
            tryto = True
            singlePlugin = load_source(singleFile[:-3], filepath)
          except (ImportError) as e:
            errlog(str(e))
            if tryto:
              self.pluginList.pop(-1)
          if hasattr(singlePlugin, 'onServerInfo'):
            self.plugins.append(singlePlugin)
          if hasattr(singlePlugin, 'onServerStartup'):
            self.startupPlugins.append(singlePlugin)
          if hasattr(singlePlugin, 'onPlayerJoin'):
            self.onPlayerJoinPlugins.append(singlePlugin)
          if hasattr(singlePlugin, 'onPlayerLeave'):
            self.onPlayerLeavePlugins.append(singlePlugin)

