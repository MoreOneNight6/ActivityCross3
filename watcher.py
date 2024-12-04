#!/usr/bin/env python3
import threading
import time
#import logging
import platform
import multiprocessing
from typing import Set
import data
import datetime
import sqlite3

#############
### UTILS ###
#############
 

            # TODO: fix this hackiness later, make setinterval generic again
            #with data.Database(data.DB_FILE) as Db:
            #    AFKObj = data.AFK(Db)
            #    AFKObj.UnsetAFK()

#class LockableSqliteConnection(object):
#    def __init__(self, dburi):
#        self.lock = threading.Lock()
#        self.connection = sqlite3.connect(dburi, uri=True, check_same_thread=False)
#        self.cursor = None
#    def __enter__(self):
#        self.lock.acquire()
#        self.cursor = self.connection.cursor()
#        return self
#    def __exit__(self, type, value, traceback):
#        self.lock.release()
#        self.connection.commit()
#        if self.cursor is not None:
#            self.cursor.close()
#            self.cursor = None

################
### BUISNESS ###
################

# Launches sniffer event loop

    #def _WriteAFK():
    #    with data.Database(data.DB_FILE) as Db:
    #        AFKObj = data.AFK(Db)
    #        if not AFKObj.IsAFK():
    #            print("SETTING AFK")
    #            AFKObj.SetAFK()

    #def _WriteWindow(Class, Title, *args):
    #    ProposedEv = data.Events.Event(datetime.datetime.now(), Class, Title)
    #    if not hasattr(_WriteWindow, "LastEvent"):
    #        _WriteWindow.LastEvent = None
    #    if _WriteWindow.LastEvent == None or (_WriteWindow.LastEvent.Class != ProposedEv.Class or _WriteWindow.LastEvent.Name != ProposedEv.Name):
    #        with data.Database(data.DB_FILE) as Db:
    #            EventObj = data.Events(Db)

    #            print("WIND", Class, Title )
    #            LastWindow = (Class, Title)
    #            EventObj.AddRecord(ProposedEv)
    #            AFKObj = data.AFK(Db)
    #            LastEvent = ProposedEv
    #            _WriteWindow.LastEvent = ProposedEv


    ##with data.Database(data.DB_FILE) as Db:
    ##    with data.DBSettings2(Db) as Setts:
    ##        Timer = SetInterval(Setts.AFKTime, _WriteAFK)
    #Interval = 1500
    #with data.Database(data.DB_FILE) as Db:
    #    SetObj = data.DBSettings2(Db)
    #    Interval = SetObj.AFKTime
    #Timer = SetInterval(Interval, _WriteAFK)
    #Sniffy = Sniffer()

    #Sniffy.key_hook = Timer.Pause
    #Sniffy.mouse_button_hook = Timer.Pause
    #Sniffy.mouse_move_hook = Timer.Pause
    #Sniffy.screen_hook = _WriteWindow
    #while True:
    #    try:
    #        Sniffy.run()
    #    except Exception as e:
    #        print(e)

# https://stackoverflow.com/questions/2697039/python-equivalent-of-setinterval
# Used in _DaemonFunc to schedule when to set AFK
class SetInterval():
    def __init__(self,interval,action, offaction) :
        self.interval=interval
        self.action=action
        self.offaction = offaction
        self.stopEvent=threading.Event()
        self.hasrunEvent = threading.Event()
        self.killEvent=threading.Event()
        thread=threading.Thread(target=self.__setInterval, daemon=True)
        thread.start()

    def __setInterval(self) :
        while not self.killEvent.is_set():
            time.sleep(self.interval)
            if not self.stopEvent.is_set():
                if not self.hasrunEvent.is_set():
                    self.hasrunEvent.set()
                    self.action()
            self.stopEvent.clear()
            #self.stopEvent.wait()

            #if self.stopEvent.is_set():
            #    #print("SKIP")
            #    self.stopEvent.clear()
            #else:
            #    #print("SETI")
            #    if self.action != None:
            #        self.action()
        #else:
        #    print("ESE")
        #    self.stopEvent.clear()
        #print(self.stopEvent.is_set())
        #if not self.stopEvent.is_set():
        #if self.stopEvent.is_set():
        #    self.stopEvent.set()
        #    if self.offaction != None:
        #        self.offaction()

    def Pause(self, *args) :
        if not self.stopEvent.is_set():
            if self.hasrunEvent.is_set():
                self.offaction()
        self.stopEvent.set()
        self.hasrunEvent.clear()


def StartWatcherLoop(Sniffer, DBFilePath, AFKTime=-1):
    print("Sniffer  :", Sniffer)
    print("Filepath :", DBFilePath)
    if AFKTime < 0:
        with data.Database(DBFilePath) as DB:
            AFKTime = data.DBSettings2(DB).AFKTime
    print("AFKTime  :", AFKTime)

    def OnSetAFK():
        print("AFK Set")
        with data.Database(DBFilePath) as Db:
            AFKObj = data.AFK(Db)
            AFKObj.SetAFK()

    def OnStopAFK():
        print("AFK Unset")
        with data.Database(DBFilePath) as Db:
            AFKObj = data.AFK(Db)
            AFKObj.UnsetAFK()

    def WriteWindow(Class, Title, *args):
        # TODO: Refactor this ugliness
        if "LastEvent" not in WriteWindow.__dict__: 
            WriteWindow.LastEvent = None
        ProposedEv = (Class, Title)
        if WriteWindow.LastEvent != ProposedEv:
            Timer.Pause()
            WriteWindow.LastEvent = ProposedEv
            print("WIN", ProposedEv)
            with data.Database(data.DB_FILE) as Db:
                EventObj = data.Events(Db)
                EventObj.AddRecord(data.Events.Event(datetime.datetime.now(), ProposedEv[0], ProposedEv[1]))

    Timer = SetInterval(AFKTime, OnSetAFK, OnStopAFK)
    Sniffy = Sniffer()
    Sniffy.key_hook = Timer.Pause
    Sniffy.mouse_button_hook = Timer.Pause
    Sniffy.mouse_move_hook = Timer.Pause
    Sniffy.screen_hook = WriteWindow
    #while True:
        #try:
    Sniffy.run()
        #except Exception as e:
        #    print(e)

def GetSniffer():
    Sniffer = None
    if platform.system() == "Linux":
        from sniff.sniff_x import Sniffer
    else:
        return None
        #print("Running on incompatible platform %s", platform.system())
    return Sniffer


def StartIcon(P, PFunc):
    import wx
    from wx.adv import TaskBarIcon
    import wx.adv
    class TbIcon(TaskBarIcon):
        def __init__(self, parent):
            self.parent = parent
            super(TaskBarIcon, self).__init__()

            self.P = P
            self.SetOIcon()
            self.Bind(wx.EVT_MENU, self.OnStopWatching, id=1)
            self.Bind(wx.EVT_MENU, self.OnStartWatching, id=2)
            self.Bind(wx.EVT_MENU, self.OnQuit, id=wx.ID_EXIT)
            self.Bind(wx.adv.EVT_TASKBAR_RIGHT_DOWN, self.ShowMenu)

        def SetOIcon(self):
            #if 
            #self.SetIcon(wx.Icon("icon.png", wx.BITMAP_TYPE_PNG), f"activitycross {data.app_ver} {'(watching@pid ' + str(self.p.pid) + ')' if self.p.is_alive() else ''} ")
            if self.P.is_alive():
                self.SetIcon(wx.Icon("media/icon_watching.png", 
                                     wx.BITMAP_TYPE_PNG),
                                     f"ActivityCross {data.APP_VER} (Watching@PID {self.P.pid})")
            else:
                self.SetIcon(wx.Icon("media/icon.png", 
                                     wx.BITMAP_TYPE_PNG),
                                     f"ActivityCross {data.APP_VER}")

        def ShowMenu(self, event):
            menu = wx.Menu()
            #menu.Append(
            menu.AppendSeparator()
            menu.Append(2, 'Start Watching')
            menu.Append(1, 'Stop Watching')
            menu.AppendSeparator()
            menu.Append(wx.ID_EXIT, 'Close')
            self.PopupMenu(menu)
            menu.Destroy()

        def OnStopWatching(self, e):
            print("Watcher stopped via systray icon")
            self.P.join(0.5)
            self.P.terminate()
            self.P.join(0.5)
            print("ChildLft :", multiprocessing.active_children())
            self.SetOIcon()
        def OnStartWatching(self, e):
            print("Watcher started via systray icon")
            #print(self.P.is_alive())
            if not self.P.is_alive():
                del self.P
                self.P = PFunc()
                self.P.start()
                time.sleep(0.5)
                self.SetOIcon()
            else:
                wx.Bell()
        def OnQuit(self, e):
            print("Abrupt stop by systray icon")
            self.OnStopWatching(None)
            wx.Exit()

    class TaskBarApp(wx.Frame):
        def __init__(self, parent, id, title):
            wx.Frame.__init__(self, parent, -1, title, size = (1, 1),
                style=wx.FRAME_NO_TASKBAR|wx.NO_FULL_REPAINT_ON_RESIZE)

            self.tbicon = TbIcon(self)
            self.Show(True)

        def OnClose(self, event):
            self.Close()
            
    class MyApp(wx.App):
        def OnInit(self):
            frame = TaskBarApp(None, -1, ' ')
            frame.Center(wx.BOTH)
            frame.Show(False)
            return True
    Wxapp = MyApp()
    Wxapp.MainLoop()

#def StartNewProcess():
#    P = multiprocessing.Process(target=_StartWatcher)
#    P.start()
import argparse
if __name__ == "__main__":
    Parser = argparse.ArgumentParser()
    Parser.add_argument("-g", "--nogui", 
                        action="store_false",
                        help="dont show the system tray icon, removes program dependency on wxpython")
    Parser.add_argument("-f", "--file", 
                        type=str, 
                        default=data.DB_FILE,
                        help="the %s database file to use" % data.APP_NAME)
    Parser.add_argument("-k", "--afk", 
                        type=int, 
                        default=-1,
                        help="time in seconds it takes to register the computer as AFK")
    Args = Parser.parse_args()
    Sniffer = GetSniffer()
    if Sniffer != None:
        WatcherFunc = lambda: multiprocessing.Process(target=StartWatcherLoop, args=(Sniffer,Args.file, Args.afk), daemon=True)
        Watcher = WatcherFunc()
        Watcher.start()
        if Args.nogui:
            StartIcon(Watcher, WatcherFunc)
        Watcher.join()
    else:
        print("Program running on unsupported platform %s" % platform.system())
#    P.join()
