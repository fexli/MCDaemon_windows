# -*- coding: CP936 -*-
from subprocess import Popen, PIPE
import select
import os
import time
import sys
import traceback
import threading
import mcdplugin
from mcdlog import *
import serverinfoparser
import chardet

stop_flag = 0


def notice():
    print('thanks for using MCDaemon,it\'s open source and u can find it here:')
    print('https://github.com/kafuuchino-desu/MCDaemon')
    print('please notice that this software is still in alpha version,it may not work well')
    print('this software is maintained by chino_desu,welcome for your issues and PRs')
    print('Rebuild in Windows Version by fe_x_li')
    print('sysDefaultEncoding is %s'%sys.getdefaultencoding())


def listplugins(plugins):
    result = ''
    result = result + 'loaded plugins:\n'
    for singleplugin in plugins.plugins:
        result = result + str(singleplugin) + '\n'
    result = result + 'loaded startup plugins:\n'
    for singleplugin in plugins.startupPlugins:
        result = result + str(singleplugin) + '\n'
    result = result + 'loaded onPlayerJoin plugins:\n'
    for singleplugin in plugins.onPlayerJoinPlugins:
        result = result + str(singleplugin) + '\n'
    result = result + 'loaded onPlayerLeavePlugins plugins:\n'
    for singleplugin in plugins.onPlayerLeavePlugins:
        result = result + str(singleplugin) + '\n'
    return result


def getInput(server):
    inp = ''
    while True:
        inp = input()
        if inp != '':
            if inp == 'stop':
                server.cmdstop()
            elif inp == 'MCDReload':
                print('reloading')
                plugins.initPlugins()
                plugins_inf = listplugins(plugins)
                for singleline in plugins_inf.splitlines():
                    print(singleline)
            else:
                server.execute(inp)


class Server(object):
    default_sleep = 0.1
    recv_wait = 1
    def __init__(self):
        self.tempbuffer = ''
        self.fstdout = open('./stdout.out', 'w')
        self.fstdout_toread = open('./stdout.out', 'rb')
        self.start()
    def start(self):
        if sys.argv[-1] != 'fabric':
            self.process = Popen('start.bat', stdin=PIPE, stdout=self.fstdout, stderr=PIPE,universal_newlines=True,
                                 encoding='UTF-8')
        else:
            print('[MCDeamon]start server by Fabric')
            self.process = Popen('start-fabric.bat', stdin=PIPE, stdout=self.fstdout, stderr=PIPE, universal_newlines=True,
                                 encoding='UTF-8')
        # flags = fcntl.fcntl(self.process.stdout, fcntl.F_GETFL)
        # fcntl.fcntl(self.process.stdout, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        log('Server Running at PID:' + str(self.process.pid))

    def tick(self):
        try:
            global stop_flag
            receive = self.recv()
            # print('recv done')
            if receive != '':
                print(receive)
                for line in receive.splitlines():
                    if line[11:].startswith('[Server Shutdown Thread/INFO]: Stopping server') or line[11:].startswith(
                            '[Server thread/INFO]: Stopping server'):  # sometimes this two message will only show one of them
                        if stop_flag > 0:
                            log('Plugin called a reboot')
                        else:
                            log('Server stopped by itself.Exiting...')
                            sys.exit(0)
                        stop_flag -= 1
                    if line[11:].startswith('[Server Watchdog/FATAL]: A single server tick'):
                        exitlog('single tick took too long for server and watchdog forced the server off', 1)
                        sys.exit(0)
                    result = serverinfoparser.parse(line)
                    if (result.isPlayer == 1) and (result.content == '!!MCDReload'):
                        try:
                            self.say('[MCDaemon] :Reloading plugins')
                            plugins.initPlugins()
                            plugins_inf = listplugins(plugins)
                            for singleline in plugins_inf.splitlines():
                                server.say(singleline)
                        except:
                            server.say('error initalizing plugins,check console for detailed information')
                            errlog('error initalizing plugins,printing traceback.', traceback.format_exc())
                    elif (result.isPlayer == 0) and (result.content.endswith('joined the game')):
                        player = result.content.split(' ')[0]
                        for singleplugin in plugins.onPlayerJoinPlugins:
                            try:
                                t = threading.Thread(target=singleplugin.onPlayerJoin, args=(server, player))
                                t.setDaemon(True)
                                t.start()
                            except:
                                errlog('error processing plugin: ' + str(singleplugin), traceback.format_exc())
                    elif (result.isPlayer == 0) and (result.content.endswith('left the game')):
                        player = result.content.split(' ')[0]
                        for singleplugin in plugins.onPlayerLeavePlugins:
                            try:
                                t = threading.Thread(target=singleplugin.onPlayerLeave, args=(server, player))
                                t.setDaemon(True)
                                t.start()
                            except:
                                errlog('error processing plugin: ' + str(singleplugin), traceback.format_exc())
                    for singleplugin in plugins.plugins:
                        t = threading.Thread(target=self.callplugin, args=(result, singleplugin))
                        t.setDaemon(True)
                        t.start()
                # time.sleep(0.01)
        except (KeyboardInterrupt, SystemExit):
            self.stop()
            sys.exit(0)

    def send(self, data):  # send a string to STDIN
        try:
            self.process.stdin.write(data)
            self.process.stdin.flush()
        except Exception as e:
            errlog(str(e))
            errlog('UTF-8 Encoding data is %s'%data.encode('UTF-8'))
        # try:
        #     # self.process.stdin.write(data.encode('UTF-8').decode('gbk'))
        #     self.process.stdin.write(data.encode('UTF-8').decode('gbk'))
        #     self.process.stdin.flush()
        # except UnicodeDecodeError:
        #     self.process.stdin.write(data)
        #     self.process.stdin.flush()
        #     errlog('The Program Does not support Chinese!')
        # except Exception as e:
        #     errlog(str(e))
    def execute(self, data, tail='\n'):  # puts a command in STDIN with \n to execute
        self.send(data + tail)

    def recv(self, t=0.1):  # returns latest STDOUT
        r = ''
        try:
            # r = self.process.stdout.readline()
            if self.recv_wait:
                time.sleep(self.default_sleep)
                # pass
            r = self.fstdout_toread.readline().decode('GB2312')
            if not r:
                self.recv_wait = 1
            # print('[debug]recv len=%s -1==/r:%s -1==/n:%s'%(len(r),r[-1]=='\r',r[-1]=='\n'))
            if r[-1] != '\n': # 结尾非换行符(\n)
                self.tempbuffer += r # 将内容存储到buffer中
                self.recv_wait = 0
                return '' # 不返回任何值
            else: # 结尾是换行符,一行输出内容结束
                self.tempbuffer += r # 将内容存储到buffer中
                ret = self.tempbuffer # 将buffer中内容提取出来
                self.tempbuffer = '' # 清空buffer 等待下次调用
                self.recv_wait = 0
                return ret.rstrip() # 返回完整行
        except:
            # print(str(e))
            return ''
    # def recv(self, t=0.1):  # returns latest STDOUT
    #     r = ''
    #     pr = self.process.stdout
    #     while True:
    #         if not select.select([pr], [], [], 0.1)[0]:
    #             time.sleep(t)
    #             continue
    #         r = pr.read()
    #         return r.rstrip()


    def cmdstop(self):  # stop the server using command
        self.send('stop\n')

    def forcestop(self):  # stop the server using pclose, donnt use it until necessary
        try:
            self.process.kill()
        except:
            raise RuntimeError

    def stop(self):
        global stop_flag
        stop_flag = 2
        self.cmdstop()
        # try:
            # self.forcestop()
            # log('forced server to stop because it has closed[stopflag=%s]'%stop_flag)
        # except:
        #     pass

    def say(self, data):
        self.execute('tellraw @a {"text":"' + str(data) + '"}')

    def tell(self, player, data):
        self.execute('tellraw ' + player + ' {"text":"' + str(data) + '"}')
    # def tell_command(self,player,text,command,hoverEvent):
    #     # "open_url" "run_command"
    #     self.execute('tellraw' + player + '{"text":"'+str(text) + '"},"clickEvent":{"action":}')
    def callplugin(self, result, plugin):
        try:
            plugin.onServerInfo(self, result)
        except:
            errlog('error processing plugin: ' + str(plugin), traceback.format_exc())


if __name__ == "__main__":
    notice()
    log('initalizing plugins')
    try:
        import mcdplugin

        plugins = mcdplugin.mcdplugin()
        plugins_inf = listplugins(plugins)
        print(plugins_inf)
    except:
        errlog('error initalizing plugins,printing traceback.', traceback.format_exc())
        sys.exit(0)
    try:
        server = Server()
    except:
        exitlog('failed to initalize the server.', 1, traceback.format_exc())
        sys.exit(0)
    for singleplugin in plugins.startupPlugins:
        try:
            t = threading.Thread(target=singleplugin.onServerStartup, args=(server,))
            t.setDaemon(True)
            t.start()
        except:
            errlog('error initalizing startup plugins,printing traceback.', traceback.format_exc())
    cmd = threading.Thread(target=getInput, args=(server,))
    cmd.setDaemon(True)
    cmd.start()
    while True:
        try:
            server.tick()
        except (SystemExit, IOError) as e:
            print(e)
            log('server stopped')
            sys.exit(0)
        except:
            errlog('error ticking MCD')
            print(traceback.format_exc())
            server.stop()
            sys.exit(0)
