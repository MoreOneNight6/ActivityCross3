#!/usr/bin/env python3
from __future__ import annotations
import sys
from time import perf_counter
import typing
from dataclasses import dataclass
import os
import datetime
import sqlite3
from enum import Enum

from closure_table import ClosureTable
#from collections.abc import MutableMapping
import json
import unittest
from functools import cache
from threading import Lock
import pprint
import inspect
import re
import datetime

import pickle
from contextlib import contextmanager
PP = pprint.PrettyPrinter()
DATETIME_STR_FORMAT = "%Y-%B-%dT%H:%M:%S-%H:%M"
wx=None
################
### SETTINGS ###
################
APP_NAME="ActivityCross"
APP_AUTHOR="juser"
APP_VER=1.0
APP_LICENSE="""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
class WxFakeLoogger():
    @staticmethod
    def LogError(*args):
        print("ERR", *args)
    @staticmethod
    def LogWarn(*args):
        print("WRN", *args)
    @staticmethod
    def LogWarning(*args):
        WxFakeLoogger.LogWarn(args)
    @staticmethod
    def LogInfo(*args):
        print(*args)
wx = WxFakeLoogger()

try:
    import wx
except:
    wx.LogError("Failed to load wxwidgets, CLI tools should still work but your milage may vary")

try:
    import appdirs
    SETTINGS_FILE=os.path.join(appdirs.user_config_dir(APP_NAME, APP_AUTHOR), "config.json")
    DATA_DIR = appdirs.user_data_dir(APP_NAME, APP_AUTHOR)
    DB_FILE = os.path.join(appdirs.user_data_dir(APP_NAME, APP_AUTHOR), "data.db")
except ImportError:
    SETTINGS_FILE="settings.json"
    DATA_DIR = ""
    DB_FILE = "data.db"
    wx.LogWarning("Couldnt get platform native paths, likely due to appdirs module not installed")
SETTINGS_DIR = os.path.dirname(SETTINGS_FILE)
OSVER = sys.platform
class Singleton(object):
    _instance = None
    _lock = Lock()
    def __new__(class_, *args, **kwargs):
        if not isinstance(class_._instance, class_):
            with class_._lock:
                if not isinstance(class_._instance, class_):
                    class_._instance = object.__new__(class_, *args, **kwargs)
                    if "__post_init__" in class_.__dict__:
                        class_._instance.__post_init__()
        return class_._instance

#################
### UTILTITES ###
#################

# Attack list of matching categories to event tree
def PyCategorize(EventObj:Events.Event, CatTree, Depth=0, ParentCatID=None):
    Return = []
    if ParentCatID == None:
        ParentCatID = CatTree["Name"].CatID
    Matched = Events.MatchAgainstCategory(EventObj,CatTree["Name"])
    if Matched:
        Return.append((CatTree["Name"], Depth, ParentCatID))
    if CatTree["Name"].Category._Cascade and Matched:
        for Cat in CatTree["Children"]:
            Return += PyCategorize(EventObj, Cat, Depth+1, CatTree["Name"].CatID)
    elif not CatTree["Name"].Category._Cascade:
        for Cat in CatTree["Children"]:
            Return += PyCategorize(EventObj, Cat, Depth+1, CatTree["Name"].CatID)
    return Return

def DeepMerge(a: dict, b: dict, path=[]):
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                DeepMerge(a[key], b[key], path + [str(key)])
            elif a[key] != b[key]:
                raise Exception('Conflict at ' + '.'.join(path + [str(key)]))
        else:
            a[key] = b[key]
    return a


################
### DATABASE ###
################

_TableSettings="""
CREATE TABLE Settings (
    Key  TEXT PRIMARY KEY,
    Val  TEXT,
    Type TEXT
)
"""

_TableCategories = """
CREATE TABLE Categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT,
    MatchingMode INT,
    MatchingTarget INT,
    Pattern TEXT,
    ColorR INT,
    ColorG INT,
    ColorB INT,
    Lowercase BOOL,
    AlwaysActive BOOL,
    Cascade BOOL
    --FOREIGN KEY (CatID) REFERENCES data_table(id)
);
INSERT INTO Categories (id, Name, MatchingMode, MatchingTarget, Pattern, ColorR, ColorG, ColorB) 
VALUES (0, "Total", 0, 0, "", 100, 100, 100);
"""

_TableEvents = """
CREATE TABLE Events (
    Timestamp REAL NOT NULL UNIQUE,
    Class TEXT,
    Name TEXT
)"""

_TableAFK = """
CREATE TABLE AFK (
    Timestamp REAL NOT NULL,
    AFK BOOL
)"""

class Database():
    Opens = 0
    def __init__(self, DatabasePath=DB_FILE):
        self.DatabasePath = DatabasePath

    def __enter__(self):
        Database.Opens += 1
        #print("DatabaseEntered", Database.Opens)
        self.Created = os.path.exists(self.DatabasePath)
        self.con = sqlite3.connect(self.DatabasePath)
        #wx.LogDebug("Database lock tried")
        self.StartTime = perf_counter()
        if not self.Created:

            self.con.executescript(ClosureTable._Table)
            #self.con.execute(Categories.Category._Table)
            #self.con.execute(Events.Event._Table)
            #self.con.execute(AFK._Table)
            self.con.execute(_TableSettings)
            self.con.execute(_TableAFK)
            self.con.execute(_TableEvents)
            self.con.executescript(_TableCategories)
            CatObj = Categories(self.con)
        


            #wx.LogWarning("Creating new database at "+ self.DatabasePath)
        return self.con

    def __exit__(self, *args):
        #print("DatabaseClosed")
        #wx.LogMessage("Cleaning up database to "+ self.DatabasePath)
        #wx.LogDebug(f"Database lock released {round(perf_counter() - self.StartTime, 3)}")
        self.con.close()

################
### SETTINGS ###
################

@dataclass()
class DBSettings2(object):
    # Time settings
    CustomMidnight: str = "+040000"
    EventsInputCustomMidnight: bool = True
    EventsDisplayCustomMidnight: bool = False
    StartWeekOnSunday:bool = False

    # Watcher settings
    UseSysIcon:bool = True
    AFKTime: int = 60

    # GUI Settings
    EventsDisplayType: int = 0
    EventsDisplayIsFancy: bool = False
    EventsChunkSize:int = 100
    EventsJustNowLimit:int = 100
    #EventsDoubleBufferListGen:bool = OSVER != "linux" # double buffering on gtk by default kinda broken
    EventsDoubleBuffer:int = 0 # 0, use platform value, 1 force on, 2 force off
    UseMonospace: bool = OSVER != "linux" # sometimes wxwidgets cant detect monospaced font on linux

    def __init__(self, DBCon):
        self.DBCon = DBCon

    #def __setattr__(self, __name: str, __value) -> None:
    #    #wx.LogWarning("Cannot set settings values until a _DBSettingsEditable is opened using with as syntax")
    #    return

    def __enter__(self):
        #return _DBSettingsEditable(self.DBCon)
        return self

    def __exit__(self, *args):
        pass

    def __getattribute__(self, name):
        DBCon = super().__getattribute__("DBCon")
        Ret = DBCon.execute("SELECT * FROM Settings WHERE Key = ?", (name,)).fetchone()
        if (Ret != None):
            ConvertedData = DBSettings2._SqliteTypeToPython(Ret[1], Ret[2])
            return ConvertedData
        else:
            #pass
            #wx.LogWarning("Could not find property " + name + " in db settings table, assuming default")
            #return self.__dict__[name]
            return super().__getattribute__(name)

    def __setattr__(self, name, value):
        #print(self, name, value)
        if name != "DBCon":
            DBCon = super().__getattribute__("DBCon")
            SQLDataTuple = DBSettings2._PythonTypeToSqlite(value)
            if (SQLDataTuple != None):
                #QueryStr = "INSERT INTO Settings (Key, Val, Type) VALUES(?,?,?) ON DUPLICATE KEY UPDATE Key=?, Val=?, Type=?"
                QueryStr = "INSERT OR REPLACE INTO Settings (Key, Val, Type) VALUES(?,?,?)"
                if (self.DBCon != None):
                    self.DBCon.execute(QueryStr, (name, SQLDataTuple[1], SQLDataTuple[0]))
                    self.DBCon.commit()
            else:
                wx.LogError("Could not update setting value "+name)
        else:
            return super().__setattr__(name, value)


    @staticmethod
    def _PythonTypeToSqlite(Data):
        if (type(Data) is int):
            return ("INT", str(Data))
        elif (type(Data) is str):
            return ("STR", '"'+Data+'"')
        elif (type(Data) is bool):
            return ("BOOL", "TRUE" if Data == True else "FALSE")
        elif (type(Data) is float):
            return ("REAL", str(Data))
        else:
            wx.LogError("Could not get sqlite type for python data " + str(Data) + " " + str(type(Data)))
            return None                                                                                              

    @staticmethod
    def _SqliteTypeToPython(Data, Type):
        match(Type):
            case "INT":
                return int(Data)
            case "STR":
                return Data
            case "BOOL":
                return True if Data == "TRUE" else False
            case "REAL":
                return float(Data)
            case _:
                wx.LogError("Could not get python types for sqlite data " + str(Data) + " " + Type)
                return None

        
#class _DBSettingsEditable(DBSettings2):
#    DBCon = None
#
#    def __getattribute__(self, name):
#        DBCon = super().__getattribute__("DBCon")
#        Ret = DBCon.execute("SELECT * FROM Settings WHERE Key = ?", (name,)).fetchone()
#        if (Ret != None):
#            ConvertedData = DBSettings2._SqliteTypeToPython(Ret[1], Ret[2])
#            return ConvertedData
#        else:
#            #pass
#            #wx.LogWarning("Could not find property " + name + " in db settings table, assuming default")
#            #return self.__dict__[name]
#            return super().__getattribute__(name)
#
#    def __setattr__(self, name, value):
#        #print(self, name, value)
#        if name != "DBCon":
#            DBCon = super().__getattribute__("DBCon")
#            SQLDataTuple = _DBSettingsEditable._PythonTypeToSqlite(value)
#            if (SQLDataTuple != None):
#                #QueryStr = "INSERT INTO Settings (Key, Val, Type) VALUES(?,?,?) ON DUPLICATE KEY UPDATE Key=?, Val=?, Type=?"
#                QueryStr = "INSERT OR REPLACE INTO Settings (Key, Val, Type) VALUES(?,?,?)"
#                if (self.DBCon != None):
#                    self.DBCon.execute(QueryStr, (name, SQLDataTuple[1], SQLDataTuple[0]))
#                    self.DBCon.commit()
#            else:
#                wx.LogError("Could not update setting value "+name)
#        else:
#            return super().__setattr__(name, value)

#class Settings(Database):
#    def __init__(self, DatabasePath=DB_FILE):
#        super().__init__(DB_FILE)
#    def __enter__(self):
#        return _DBSettingsEditable(super().__enter__())
#    def __exit__(self, *args):
#        return super().__exit__(*args)

# If you dont use __enter__/with as syntax it will show the default values
# God I hate i created this piece of shit settings class
# TODO: Refactor this
#@dataclass
#class DBSettings(object):
#    _DataPath: str = DB_FILE
#    _Db = None
#    UseSysIcon:bool = True
#    AFKTime: int = 60
#    _Done = True
#
#    @staticmethod
#    def _PythonTypeToSqlite(Data):
#        #match(Data):
#        #    case int():
#        #        print("RaW")
#        #        return ("INT", str(Data))
#        #    case str():
#        #        return ("STR", '"'+Data+'"')
#        #    case bool():
#        #        return ("BOOL", "TRUE" if Data == True else "FALSE")
#        #    case float():
#        #        return ("REAL", str(Data))
#        #    case _:
#        #        wx.LogError("Could not get sqlite type for python data " + str(Data) + " " + str(type(Data)))
#        #        return None
#        if (type(Data) is int):
#            return ("INT", str(Data))
#        elif (type(Data) is str):
#            return ("STR", '"'+Data+'"')
#        elif (type(Data) is bool):
#            return ("BOOL", "TRUE" if Data == True else "FALSE")
#        elif (type(Data) is float):
#            return ("REAL", str(Data))
#        else:
#            wx.LogError("Could not get sqlite type for python data " + str(Data) + " " + str(type(Data)))
#            return None                                                                                              
#    @staticmethod
#    def _SqliteTypeToPython(Data, Type):
#        match(Type):
#            case "INT":
#                return int(Data)
#            case "STR":
#                return Data
#            case "BOOL":
#                return True if Data == "TRUE" else False
#            case "REAL":
#                return float(Data)
#            case _:
#                wx.LogError("Could not get python types for sqlite data " + str(Data) + " " + Type)
#                return None
#
#    def __enter__(self):
#        self._Db = Database(self._DataPath)
#        #print(self._Db)
#        self._Db.__enter__()
#        self._Ready = True
#        return self
#        #print("UWU")
#        #self.setattr = self.SetAttrReal
#        #setattr(self, "__setattr__", self.SetAttrReal)
#        #self.__getattribute__ = self._GetAttrReal
#        #self.__setattr__ = self.SetAttrReal
#                                                    
#    def __exit__(self, *args):
#        #print("EXITED")
#        if (self._Db != None):
#            self._Db.__exit__()
#        self._Db = None
#        self._Ready = False
#
#    # Before __enter__ no dynamic attributes allowed!
#    def __setattr__(self, name, value) -> None:
#        if (name[0] == "_"):
#            super().__setattr__(name, value)
#        else:
#            if inspect.getattr_static(self, "_Db") != None:
#                self._SetAttrReal(self,name,value)
#            else:
#                pass
#                #wx.LogMessage("Cannot modify values of default settings " + name + ", please open using with as syntax")
#    def __getattribute__(self, name):
#        #if (name[0] == "_" or getattr(self, "_Db").con == None):
#        #    return getattr(self, name)
#        #print("UWU")
#        if inspect.getattr_static(self, "_Db") == None or name[0] == "_":
#            return inspect.getattr_static(self, name)
#        else:
#            return inspect.getattr_static(self, "_GetAttrReal")(self, name)
#
#    def _GetAttrReal(self, name):
#        Db = inspect.getattr_static(self, "_Db")
#        if (hasattr(Db, "con") == True):
#            Ret = Db.con.execute("SELECT * FROM Settings WHERE Key = ?", (name,)).fetchone()
#            if (Ret != None):
#                ConvertedData = DBSettings._SqliteTypeToPython(Ret[1], Ret[2])
#                return ConvertedData
#            else:
#                pass
#                #wx.LogWarning("Could not find property " + name + " in db settings table, assuming default")
#                #return self.__dict__[name]
#        return inspect.getattr_static(self, name)
#
#    def _SetAttrReal(self, name, value):
#        #print(self, name, value)
#        SQLDataTuple = DBSettings._PythonTypeToSqlite(value)
#        if (SQLDataTuple != None):
#            #QueryStr = "INSERT INTO Settings (Key, Val, Type) VALUES(?,?,?) ON DUPLICATE KEY UPDATE Key=?, Val=?, Type=?"
#            QueryStr = "INSERT OR REPLACE INTO Settings (Key, Val, Type) VALUES(?,?,?)"
#            if (self._Db != None):
#                self._Db.con.execute(QueryStr, (name, SQLDataTuple[1], SQLDataTuple[0]))
#                self._Db.con.commit()
#        else:
#            wx.LogError("Could not update setting value "+name)

#import random
#DBSet = DBSettings()
#DBSet._DataPath = "UwUDB"
#print("BEFORE", DBSet.AFKTime)
#DBSet.__enter__(DBSet)
#print("BOPEN", DBSet.AFKTime)
#DBSet.AFKTime = random.random()
#print("OPEN", DBSet.AFKTime)
#DBSet.__exit__(DBSet)
#print("AFTER", DBSet.AFKTime)
#DBSet.__enter__(DBSet)
#print("AGAIN", DBSet.AFKTime)
#DBSet.__exit__(DBSet)
#DBSet.__enter__(DBSet)
#print(DBSet.AFKTime)
#DBSet.__exit__(DBSet)


#@contextmanager
#def LoadSettings(DBPath=DB_FILE, *args, **kwargs):
#    pass
#    #with Database(DBPath) as DB:
    #    if DB.Created:



#@dataclass
#class DBSettings():
#    _AppVersion:int = 1
#    Version: int = _AppVersion
#    UseSysIcon:bool = True
#    AFKTime: int = 120
#
#    def _PythonTypeToSqlite(Data):
#        match(Data):
#            case int():
#                return ("INT", str(Data))
#            case str():
#                return ("STR", '"'+Data+'"')
#            case bool():
#                return ("BOOL", "TRUE" if Data == True else "FALSE")
#            case float():
#                return ("REAL", str(Data))
#            case _:
#                wx.LogError("Could not get sqlite for data " + str(Data) + " " + str(type(Data)))
#                return ("BLOB", Data)
#
#    def _Save(self):
#        DBEnter = ""
#        for k,v in self.__dict__.items():
#            # This is gonna cause so many issues
#            if (k[0] != "_"):
#                Combi = DBSettings._PythonTypeToSqlite(v)
#                DBCreateStr += " ".join([k, Combi[0]]) + ","
#                DBEnter += " ".join(["INSERT INTO Settings (",k,")","VALUES",Combi[1]]) + ";\n"
#            #self._Db.con.executescript(
#        else:
#            Values = self._Db.con.execute("SELECT * FROM Settings")
#
#    def __enter__(self, DataPath=DB_FILE):
#        self._Db = Database(DataPath)
#        self._Db.__enter__()
#        if (self._Db.Created):
#            DBCreateStr = "CREATE TABLE Settings( "
#            DBCreateStr = DBCreateStr[:-1]+")"
#            print(DBCreateStr)
#            print(DBEnter)
#
#    def __exit__(self, *args):
#        self._Db.__exit__()
#
#with DBSettings() as Settings:
#    print("UWU")


################
### CATEGORY ###
################

# How to match an event for Category
class EMatchingMode(Enum):
    ALWAYS = 0
    PREFIX = 1
    EXACT  = 2
    REGEX  = 3
    SUBSTR = 4
    SUFFIX = 5

# What to match event on for Category
class EMatchingTarget(Enum):
    #TIMESTAMP = 0
    CLASS = 0
    TITLE = 1
    CLASS_TITLE = 2

def TextEncode(Str):
    if "&c" in Str:
        wx.LogWarning("EncodingError, cannot use &c in any text fields")
        raise Categories.Category.EncodingError(Str)
    return Str.replace("~", "&c1").replace(",", "&c2")
def TextDecode(Str):
    return Str.replace("&c1", "~").replace("&c2", ",")


# Wrapper for Category for interacting with database
# Uses closure table to represent hiearchy
class Categories(ClosureTable):
    def __init__(self, DB:sqlite3.Connection):
        ##print(conn)
        super().__init__(DB)
        self.con = DB

    # Data struct for one category
    @dataclass(eq=True, frozen=True)
    class Category():
        Name: str
        MatchingMode: EMatchingMode
        MatchingTarget: EMatchingTarget
        Pattern: str
        _Color: tuple[int,int,int] = (100,100,100)
        _Lowercase: bool = False
        _AlwaysActive: bool = False
        _Cascade: bool = True

        #_CatID: int = int(random.random() * 1000000)
        #_Depth: Optional[int] = None
        #_CatID: Optional[int] = None


        class EncodingError(Exception):
            pass

        #AHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH
        @staticmethod
        def FromTuple(SQLTuple):
            if SQLTuple == None:
                return None
            return Categories.Category(TextDecode(SQLTuple[1]),
                                       EMatchingMode(int(SQLTuple[2])),
                                       EMatchingTarget(int(SQLTuple[3])),
                                       TextDecode(SQLTuple[4]),
                                       (int(SQLTuple[5]), int(SQLTuple[6]), int(SQLTuple[7])),
                                       bool(SQLTuple[8]),
                                       bool(SQLTuple[9]),
                                       bool(SQLTuple[10]))
                                       #SQLTuple[0])

        def ToTuple(self):
            return [#self._CatID, 
                    TextEncode(self.Name), 
                    self.MatchingMode.value, 
                    self.MatchingTarget.value, 
                    TextEncode(self.Pattern), 
                    *self._Color,
                    self._Lowercase,
                    self._AlwaysActive,
                    self._Cascade]
    globals()["Category"] = Category

        #def __eq__(self, other):
        #    return self.ToTuple()[:-2] == other.ToTuple()[:-2]

        #def __hash__(self):
        #return hash(self.__key())

    # Category that contains refernce to table
    # Also updates records if properties on Category object is updated
    # Very important variable names in Category class match ones in database
    @dataclass(frozen=True)
    class CategoryRef():

        CatID: int
        Category: Categories.Category


            #elif ExpectedClass == EMatchingMode:
            #    value = object.__getattribute__(self.Category, "MatchingMode").value

        @staticmethod
        def FromTuple(SQLTuple):
            if SQLTuple == None:
                return None
            return Categories.CategoryRef(int(SQLTuple[0]), Categories.Category.FromTuple(SQLTuple))

        def ToTuple(self):
            return [self.CatID, *self.Category.ToTuple()]

        def __eq__(self, __value: object) -> bool:
            if isinstance(__value, Categories.CategoryRef):
                return self.CatID == __value.CatID
            return False

    FieldList = "Name, MatchingMode, MatchingTarget, Pattern, ColorR, ColorG, ColorB, Lowercase, AlwaysActive, Cascade"
    FieldList_ID="id,"+FieldList
    DefaultRootNode = Category("Total", 
                               EMatchingMode.ALWAYS, 
                               EMatchingTarget.CLASS_TITLE,
                               "N/A")
    DefaultRootNodeAlt = Category("Undefined", 
                               EMatchingMode.ALWAYS, 
                               EMatchingTarget.CLASS_TITLE,
                               "RAD",(200,200,200))
    DefaultCategory = Category("Undefined", 
                               EMatchingMode.ALWAYS, 
                               EMatchingTarget.CLASS_TITLE,
                               "")
    def _InsertIntoSQL(self, Child:Category, ID=None) -> CategoryRef:
        Cur = self.con.cursor()
        if ID == None:
            #print(Child.ToTuple()[1::], len(Child.ToTuple()[1::]))
            Cur.execute("""INSERT INTO Categories """ + 
                        " (" + self.FieldList + ") " +
                        """VALUES (?,?,?,?,?,?,?,?,?,?)""", Child.ToTuple())
        else:
            #print(Child.ToTuple())
            Cur.execute("""INSERT INTO Categories """ +
                        " (" +self.FieldList_ID+ ") " +
                        """VALUES (?,?,?,?,?,?,?,?,?,?,?)""", Categories.CategoryRef(ID, Child).ToTuple())
        ID = Cur.lastrowid
        Cur.close()
        return self.CategoryRef(ID, Child)
    def _InsertIntoSQLRef(self, Ref:CategoryRef):
        return self._InsertIntoSQL(Ref.Category, Ref.CatID)

    # Will update object as well as database
    def CategoryRefSetItem(self, Item: CategoryRef, key:str, value) -> None:
        object.__setattr__(Item.Category, key, value)
        key = key.replace("_","")
        #print(key)
        #ExpectedClass = Item.Category.__annotations__[key]
        #ExpectedClass = object.__getattribute__(Item.Category, "__annotations__")[key]
        #ExpectedClass = object.__getattribute__(Item.Category, "__annotations__")[key]
        #ExpectedClass = Item.Category.__annotations__[key]
        #if type(value) != ExpectedClass:
        #    raise TypeError(repr(type(value)), repr(ExpectedClass), )
        if type(value) == str:
        #if ExpectedClass == str:
            value = TextEncode(value)
        Cur = self.con.cursor()
        if key == "Color":
            #ColorTuple = object.__getattribute__(Item.Category, "_Color")
            Cur.execute("UPDATE Categories SET ColorR = ?, ColorG = ?, ColorB = ? WHERE id = ?", (value[0], 
                                                                                   value[1],
                                                                                   value[2],
                                                                                   Item.CatID))
            self.con.commit()
        else:
            #print()
            #print(key, value, Item.CatID, type(value))
            #Cur.execute("UPDATE Categories SET Pattern = 'E' WHERE id = 1")
            Cur.execute("UPDATE Categories SET "+key+" = ? WHERE id = ?", (value, Item.CatID))
            self.con.commit()

    def GetRootNode(self) -> CategoryRef:
        Root = self.select_children(0)
        if Root == []:
            ##print("CREATED")
            #RootNode._CatID = 1
            self.insert_root(0)
            self.insert_child(0, 1)
            RootNodeR = self._InsertIntoSQL(Categories.DefaultRootNode, 1)
            self.con.commit()
            return RootNodeR
        else:
            ##print("LOADED", Root)
            return Categories.CategoryRef(1, Categories.Category.FromTuple(Root[0]))
            ##print(Ret)
            #return Ret

    def AddCategory(self, Parent:CategoryRef, Child:Category) -> CategoryRef:
        Childe = self._InsertIntoSQL(Child)
        self.insert_child(Parent.CatID, Childe.CatID)
        self.con.commit()
        return Childe


    def ReplaceParent(self, Child: CategoryRef, NewParent:CategoryRef) -> None:
        self.unlink_parent(Child.CatID)
        self.link_child(NewParent.CatID, Child.CatID)

    def GetParent(self, Child:CategoryRef) -> Categories.CategoryRef | None:
        if Child.CatID == 1:
            return None

        Root = self.select_parent(Child.CatID)
        #print("ROOT", Root, Child._CatID)
        return Categories.CategoryRef.FromTuple(Root)

    def GetChildren(self, Parent:CategoryRef) -> typing.Iterable[CategoryRef]:
        #print("CATER", Parent.CatID)
        
        Root = self.select_children(Parent.CatID)
        #print("REOOT", Root)
        for i in Root:
            Tmp = Categories.CategoryRef.FromTuple(i)
            if Tmp == None:
                continue
            yield Tmp

    def RenderTree(self):
        # TODO: Fix the jank
        ModFList = " || '~' || ".join(["n."+i for i in self.FieldList_ID.split(",")])
        #print("""select GROUP_CONCAT("""+ModFList+""", ) as path""")
        #print(ModFList)
        Cur = self.con.execute("""select GROUP_CONCAT("""+ModFList+""", ',') as path
                                  from tree d
                                  join tree a on (a.child = d.child)
                                  join Categories n on (n.id = a.parent)
                                  where d.parent = ? and d.child != d.parent
                                  group by d.child
                                  order by d.child;""", (0,))
        Return = {}
        Raws = Cur.fetchall()
        SplitNode = [[Categories.CategoryRef.FromTuple(i.split("~")) for i in i[0].split(",")] for i in Raws]
        #PP.pprint(SplitNode)
        DefaultEntry = lambda a: {"Name":a, "Children":[]}
        Root = None
        #print(SplitNode)

        for Row in SplitNode:
            #PP.pprint(Return)
            Temp = Return
            if Root:
                Temp = Root
            elif len(Row) == 1:
                #print("ROW0", Row[0])
                Temp = DefaultEntry(Row[0])
                Root = Temp
            for Node in Row[1::]:
                ChildElm = next(((i,x) for i,x in enumerate(Temp["Children"]) if x["Name"] == Node), None)
                #print("CHILDELM", ChildElm)
                if ChildElm:
                    Temp = Temp["Children"][ChildElm[0]]
                else:
                    Temp["Children"].append(DefaultEntry(Node))
                    #Temp = Temp["Children"][-1]
            #pprint.pp(Temp["Name"].CatID)
            #if Temp["Name"].CatID == Parent.CatID:
            Return = Temp | Return
        return Return


    #def PyCategorize(self, Parent:CategoryRef, Events:Iterable[Events.Event]):
    #    Tree = self.RenderTree(Parent)
    #    for Event in Events:

    def GetCategoryRefFromCategoryRef(self, Ref:CategoryRef) -> CategoryRef:
        Cur = self.con.execute("SELECT * FROM Categories WHERE ID = ?", (Ref.CatID,))
        return self.CategoryRef.FromTuple(Cur.fetchone())

    def GetSubtree(self, Parent:CategoryRef) -> typing.Iterable[typing.Tuple[Categories.CategoryRef, int]]:
        Root = self.select_descendants(Parent.CatID)
        for i in Root:
            yield (Categories.CategoryRef.FromTuple(i), self.descendants_depth(i[0])-1)

    def DeleteSubtree(self, Parent:CategoryRef, DeleteSelf=False) -> None:
        assert Parent.CatID != None
        # TODO: Refactor this to use SQL native commands
        #pprint.pp(list(self.GetChildren(Parent)))
        ToBeDeleted = [i[0] for i in self.GetSubtree(Parent)]
        if DeleteSelf:
            ToBeDeleted.append(Parent)
        for k in ToBeDeleted:
            ##print("TO BE DLETED", k, k._CatID)
            #print(k)
            if k != None:
                self.con.execute("DELETE FROM Categories WHERE id = ?", (k.CatID,))
        self.delete_descendants(Parent.CatID)
        self.con.commit()

#############
### EVENT ###
#############

# Wrapper for Event table to interact with code
class Events():
    def __init__(self, DB:sqlite3.Connection):
        self.con = DB

    # Data struct for one window event
    @dataclass()
    class Event():

        Timestamp:datetime.datetime
        Class: str
        Name: str

        @staticmethod
        def FromSQL(SQLTuple):
            #print(SQLTuple)
            return Events.Event(datetime.datetime.fromtimestamp(SQLTuple[0]), SQLTuple[1], SQLTuple[2])

        def ToSQL(self):
            return [self.Timestamp.timestamp(), self.Class, self.Name]

    @staticmethod
    def MatchAgainstCategory(Self:Events.Event,Category:Categories.Category):
        if isinstance(Category, Categories.CategoryRef):
            Category = Category.Category
        Func = None
        if Category.MatchingMode == EMatchingMode.ALWAYS:
            Func = lambda a,x: True
        elif Category.MatchingMode == EMatchingMode.EXACT:
            Func = lambda Target,Pattern: Target == Pattern
        elif Category.MatchingMode == EMatchingMode.PREFIX:
            Func = lambda Target,Pattern: Target.startswith(Pattern)
        elif Category.MatchingMode == EMatchingMode.REGEX:
            Func = lambda Target,Pattern: bool(re.search(Pattern, Target))
        elif Category.MatchingMode == EMatchingMode.SUBSTR:
            Func = lambda Target,Pattern: Pattern in Target
        elif Category.MatchingMode == EMatchingMode.SUFFIX:
            Func = lambda Target,Pattern: Target.endswith(Pattern)
        else:
            raise NotImplementedError()
        #print("FUNC", Func, Category, self)
        LClass = Self.Class
        LTitle = Self.Name
        LPattern = Category.Pattern
        if Category._Lowercase:
            LClass = LClass.lower()
            LTitle = LTitle.lower()
            LPattern = LPattern.lower()
        #print(LClass, LTitle, LPattern)
        if Category.MatchingTarget == EMatchingTarget.CLASS:
            return Func(LClass, LPattern)
        if Category.MatchingTarget == EMatchingTarget.CLASS_TITLE:
            #print(self.Class+self.Name, Category.Pattern)
            return Func(LClass+LTitle, LPattern)
        #if Category.MatchingTarget == EMatchingTarget.TIMESTAMP:
        #    raise NotImplementedError()
        if Category.MatchingTarget == EMatchingTarget.TITLE:
            return Func(LTitle, LPattern)

    def GetLastEvent(self):
        con = self.con
        Res = con.execute("SELECT * FROM Events ORDER BY ROWID DESC LIMIT 1")
        Ret = Res.fetchone()
        #wx.LogMessage("Finding DB last record")
        Return = None
        if Ret != None:
            Return = Events.Event.FromSQL(Ret)
        else:
            wx.LogWarning("Could not find database last event, timeline may be empty")
        #self.FirstEvent = Ret
        ##print(Ret)
        return Return

    def GetRange(self, Begin: datetime.datetime, End:datetime.datetime=datetime.datetime.now()):
        con=self.con
        #print("RESSSLLL", Start.timestamp(), Stop.timestamp())
        Res = con.execute("SELECT * FROM Events WHERE Timestamp <= ? AND Timestamp >= ? ORDER BY Timestamp", (End.timestamp(), Begin.timestamp()))
        #Res = self.con.execute("SELECT * FROM Events")
        ResL = Res.fetchall()
        #print(ResL)
        if ResL != None:
            return [Events.Event.FromSQL(i) for i in ResL]
        return []

    def AddRecord(self,Record:Event) -> None:
        con = self.con
        #print("ADDDREEEC", Record)
        if Record.Timestamp.year <= 1970 and Record.Timestamp.month <= 1 and Record.Timestamp.day <= 1:
            wx.LogError("Cannot add date before 1/1/1970")
            return
        RawTimestamp = Record.Timestamp.timestamp()
        #print("RAWR TIMESTAMP", Record.Timestamp.timestamp(), Record.Timestamp)
        con.execute("INSERT INTO Events VALUES (?,?,?)", (RawTimestamp, Record.Class, Record.Name))
        con.commit()

    def RemoveRecord(self, Record:Event)->None:
        RawTimestamp = Record.Timestamp.timestamp()
        self.con.execute("DELETE FROM Events WHERE Timestamp = ?", (RawTimestamp,))
        self.con.commit()

    def GetRecordWithTimestamp(self, Timestamp:datetime.datetime)->Events.Event|None:
        RawTimestamp = Timestamp.timestamp()
        Res = self.con.execute("SELECT * FROM Events WHERE Timestamp = ? LIMIT 1", (RawTimestamp,))
        ResL = Res.fetchone()
        if ResL != None:
            #return [Events.Event.FromSQL(i) for i in ResL]
            return Events.Event.FromSQL(ResL)
        return None

    # TODO: Do unit testing for this func
    def SetRecordWithTimestamp(self, Timestamp:datetime.datetime, Name:str, Class:str)->None:
        RawTimestamp = Timestamp.timestamp()
        print(Timestamp, Name, Class, RawTimestamp)
        Res = self.con.execute("UPDATE Events SET Name = ?, Class = ? WHERE Timestamp = ?", 
                               (Name, Class, RawTimestamp))
        self.con.commit()
        
       # self.con.execute("INSERT INTO Events VALUES (?,?,?)", (RawTimestamp, Record.Class, Record.Name))


###########
### AFK ###
###########

# Wrapper for AFK table to interact with code
class AFK():
    def __init__(self, con:sqlite3.Connection):
        self.con = con
    def IsAFK(self):
        SQLTuple = self.con.execute("SELECT * FROM AFK ORDER BY Timestamp DESC").fetchone()
        #print(SQLTuple)
        if SQLTuple != None:
            return SQLTuple[1] == 1
        else:
            return False

    def SetAFK(self):
        #if not self.IsAFK():
            #print("SETAFK")
        self.con.execute("INSERT INTO AFK VALUES (?,TRUE)", (datetime.datetime.now().timestamp(),))
    def UnsetAFK(self):
        #if self.IsAFK():
            #print("UNSETAFK")
        self.con.execute("INSERT INTO AFK VALUES (?,FALSE)", (datetime.datetime.now().timestamp(),))

    def GetRange(self, Begin: datetime.datetime, End:datetime.datetime=datetime.datetime.now()):
        con=self.con
        Res = con.execute("SELECT * FROM AFK WHERE Timestamp < ? AND Timestamp > ? ORDER BY Timestamp DESC", (End.timestamp(), Begin.timestamp()))
        return [(datetime.datetime.fromtimestamp(i[0]), bool(i[1])) for i in Res.fetchall()]


############
### TIME ###
############

# Application allows you to set a custom midnight, create timezone with offsetted time
class CustomTZ(datetime.tzinfo):
    def __init__(self, MidnightTime="+000000"):
        print(len(MidnightTime))
        self.Positive = MidnightTime[0] != "-"
        self.MidnightTime = datetime.datetime.strptime(MidnightTime[1:7], "%H%M%S")
    def utcoffset(self, __dt: datetime.datetime | None) -> datetime.timedelta | None:

        Return = datetime.timedelta(hours=0, minutes=0, seconds=0)
        try:
            if self.Positive:
                Return = datetime.timedelta(hours=self.MidnightTime.hour, minutes=self.MidnightTime.second, seconds=self.MidnightTime.second)
            else:
                Return = -datetime.timedelta(hours=self.MidnightTime.hour, minutes=self.MidnightTime.second, seconds=self.MidnightTime.second)
        except Exception as e:
            wx.LogError("Could not pass custom midnight " + str(e))
        print(Return)
        return Return
    def dst(self, dt):
        return datetime.timedelta(0)
    def OffsetNaive(self, Date:datetime.datetime):
        return Date.astimezone(self).replace(tzinfo=None)
    def OffsetNaiveTimeDelta(self, Time:datetime.timedelta):
        return datetime.timedelta(seconds=Time.total_seconds() + self.utcoffset(None).total_seconds())
        #return Time.d self.utcoffset(None)


#class MidnightAwareTime():
#    def __init__(self, MidnightTime=DBSettings2.CustomMidnight) -> None:
#        self.MidnightTime = datetime.datetime.strptime(MidnightTime, "%H%M%S")
#    def GetToday(self):
#        Now = datetime.datetime.now()
#        CurrMid = Now + datetime.timedelta(days=1
#        if self.MidnightTime.time() > Now.time():
#            return 
        

##################
### UNIT TESTS ###
##################
# TODO: Do the rest
class _TestEvents(unittest.TestCase):
    def setUp(self) -> None:
        #print()

        self.Db = Database("testdb_events.db")
        self.EvObj = Events(self.Db.__enter__())
        self.WebEvent =             Events.Event(datetime.datetime(year=1970, month=1, day=10),  "Firefox", "Youtube - Firefox")
        self.TerminalEvent =        Events.Event(datetime.datetime(year=1980, month=1, day=2),  "Urxvt", "juser@jarch7:/home/juser/")
        self.TerminalEvent2 =       Events.Event(datetime.datetime.now(),                       "xterm", "user@jarch7:/home/user/")
        self.TerminalEvent3 =       Events.Event(datetime.datetime(year=1980, month=1, day=3),  "Urxvt", "juser@jarch7:/home/Videos/")
        self.TerminalEvent4 =       Events.Event(datetime.datetime(year=1980, month=1, day=4),  "Urxvt", "juser@jarch7:/home/Pictures/")

        self.TerminalCategory1 =    Categories.Category("Term1", EMatchingMode.EXACT, EMatchingTarget.CLASS, "Urxvt")
        self.TerminalCategory2 =    Categories.Category("Term2", EMatchingMode.PREFIX, EMatchingTarget.CLASS_TITLE, "xtermuser@jarch7")

        self.TerminalCategory3 =    Categories.Category("TermVideos", EMatchingMode.REGEX, EMatchingTarget.CLASS_TITLE, "Videos")
        self.TerminalCategory4 =    Categories.Category("TermPictures", EMatchingMode.REGEX, EMatchingTarget.CLASS_TITLE, "Pictures")

        self.ForbiddenCategory  =   Categories.Category("Forbidden", EMatchingMode.EXACT, EMatchingTarget.CLASS, "FORBIDDEN")
        self.ForbiddenCategory1 =   Categories.Category("ForbVideos", EMatchingMode.REGEX, EMatchingTarget.CLASS_TITLE, "Videos")
        self.ForbiddenCategory2 =   Categories.Category("ForbPictures", EMatchingMode.REGEX, EMatchingTarget.CLASS_TITLE, "Pictures")

        self.WebCategory =          Categories.Category("Web",   EMatchingMode.REGEX,  EMatchingTarget.CLASS_TITLE, r"\W*Y")

        self.EvObj.AddRecord(self.WebEvent)
        self.EvObj.AddRecord(self.TerminalEvent)
        self.EvObj.AddRecord(self.TerminalEvent2)
        self.EvObj.AddRecord(self.TerminalEvent3)
        self.EvObj.AddRecord(self.TerminalEvent4)
        self.CatObj = Categories(self.Db.__enter__())
        self.RootCat = self.CatObj.GetRootNode()
        TermCat1Ref = self.CatObj.AddCategory(self.RootCat, self.TerminalCategory1)
        TermCat2Ref = self.CatObj.AddCategory(self.RootCat, self.TerminalCategory2)
        self.CatObj.AddCategory(self.RootCat, self.WebCategory)
        self.CatObj.AddCategory(TermCat1Ref, self.TerminalCategory3)
        self.CatObj.AddCategory(TermCat1Ref, self.TerminalCategory4)

        ForbCat1Ref = self.CatObj.AddCategory(self.RootCat, self.ForbiddenCategory)
        self.CatObj.AddCategory(ForbCat1Ref, self.ForbiddenCategory1)
        self.CatObj.AddCategory(ForbCat1Ref, self.ForbiddenCategory2)
        
        return super().setUp()


    def test_MatchAgainstCategory(self):
        #print(self.WebEvent.MatchAgainstCategory(self.WebCategory))
        self.assertTrue(Events.MatchAgainstCategory(self.WebEvent,self.WebCategory))
        self.assertFalse(Events.MatchAgainstCategory(self.WebEvent,self.TerminalCategory1))
        self.assertFalse(Events.MatchAgainstCategory(self.WebEvent,self.TerminalCategory2))

        self.assertTrue(Events.MatchAgainstCategory(self. TerminalEvent,self.TerminalCategory1))
        self.assertFalse(Events.MatchAgainstCategory(self.TerminalEvent,self.TerminalCategory2))
        self.assertFalse(Events.MatchAgainstCategory(self.TerminalEvent,self.WebCategory))

        self.assertTrue(Events.MatchAgainstCategory(self.TerminalEvent2,self.TerminalCategory2))
        self.assertFalse(Events.MatchAgainstCategory(self.TerminalEvent2,self.TerminalCategory1))
        self.assertFalse(Events.MatchAgainstCategory(self.TerminalEvent2,self.WebCategory))

    def test_GetRangeNull(self):
        with Database("testdb_events2.db") as DB:
            EvObj = Events(DB)
            self.assertEqual(EvObj.GetRange(datetime.datetime(year=1970, month=1, day=1), datetime.datetime.now()), [])
        os.remove("testdb_events2.db")


    def test_GetRange(self):
        Res1 = self.EvObj.GetRange(datetime.datetime(year=1970, month=1, day=10), datetime.datetime(year=1980, month=1, day=20))
        #self.assertEqual(len(Res1), 2)
        #print("RES!!!", Res1)
        self.assertEqual(Res1[0], self.WebEvent)
        self.assertEqual(Res1[1], self.TerminalEvent)
        Res1 = self.EvObj.GetRange(datetime.datetime(year=1980, month=1, day=1), datetime.datetime(year=2030, month=1, day=1))
        #self.assertEqual(len(Res1), 2)
        #print("RES1", Res1)
        self.assertEqual(Res1[0], self.TerminalEvent)
        self.assertEqual(Res1[1], self.TerminalEvent3)

    # TODO: Fill out pycategorize test
    def test_PyCategorize(self):
        Res = self.EvObj.GetRange(datetime.datetime(year=1970, month=1, day=1), datetime.datetime.now())
        #print("PYCATEGORISE")
        #print(Res)
        for Obj in Res:
            pass
            #print(Obj)
            #PP.pprint(PyCategorize(Obj, self.CatObj.RenderTree(self.CatObj.GetRootNode())))

    def tearDown(self) -> None:
        self.Db.__exit__()
        os.remove("testdb_events.db")
        return super().tearDown()

class _TestEvents2(unittest.TestCase):
    def setUp(self) -> None:
        #print()
        self.Db = Database("testdb2ee.db")
        self.EvObj = Events(self.Db.__enter__())
        return super().setUp()

    def test_GetLastEventNull(self):
        Res = self.EvObj.GetLastEvent()
        self.assertEqual(Res, None)

    def test_RemoveEvent(self):
        Test1 = Events.Event(datetime.datetime.now(), "Test1", "Test1")
        Test2 = Events.Event(datetime.datetime.now(), "Test2", "Test2")
        Test3 = Events.Event(datetime.datetime.now(), "Test3", "Test3")
        self.EvObj.AddRecord(Test1)
        self.EvObj.AddRecord(Test2)
        self.EvObj.AddRecord(Test3)
        self.EvObj.RemoveRecord(Test3)
        Res = self.EvObj.GetRange(datetime.datetime(1980, 1, 1), datetime.datetime.now())
        self.assertEqual(Res, [Test1, Test2])

    def test_GetRecordWithTimestamp(self):
        Test1 = Events.Event(datetime.datetime.now(), "Test1", "Test1")
        self.EvObj.AddRecord(Test1)
        self.assertEqual(self.EvObj.GetRecordWithTimestamp(Test1.Timestamp), Test1)
        self.assertEqual(self.EvObj.GetRecordWithTimestamp(datetime.datetime(1980,1,1)), None)
        
    def tearDown(self) -> None:
        self.Db.__exit__()
        os.remove("testdb2ee.db")
        return super().tearDown()

#class _TestSettings(unittest.TestCase):
#    def setUp(self) -> None:
#        #print()
#        pass
#
#    def test_GettingDefaultValue(self):
#        self.assertEqual(Settings()["_Test"], 1) 
#    
#    def test_SettingValue(self):
#        Settings()["_Test"] = 2
#        self.assertEqual(Settings()["_Test"], 2)
#        Settings()["_Test"] = 1
#
#    def test_GettingValue(self):
#        self.assertEqual(Settings()["_Test"], 1)

class _TestCategoriesSubtree(unittest.TestCase):
    def setUp(self) -> None:
        #print()
        self.Db = Database("testdb2.db")
        self.CatObj = Categories(self.Db.__enter__())

        Ret = self.CatObj.AddCategory(self.CatObj.GetRootNode(), 
                                      Categories.Category("1", EMatchingMode.ALWAYS, EMatchingTarget.CLASS, ""))
        Ret = self.CatObj.AddCategory(Ret,
                                      Categories.Category("2", EMatchingMode.ALWAYS, EMatchingTarget.CLASS, ""))
        self.TwoRet = Ret
        _ = self.CatObj.AddCategory(Ret,
                                      Categories.Category("3", EMatchingMode.ALWAYS, EMatchingTarget.CLASS, ""))
        _ = self.CatObj.AddCategory(Ret,
                                      Categories.Category("4", EMatchingMode.ALWAYS, EMatchingTarget.CLASS, ""))

        self.FourRet = _

        return super().setUp()



    def test_GetSubtree(self):
        Proc = list(self.CatObj.GetSubtree(self.CatObj.GetRootNode()))
        self.assertEqual(len(Proc), 4)

    def test_DeleteSubtreeSelf(self):
        self.CatObj.DeleteSubtree(self.TwoRet, True)
        Proc = list(self.CatObj.GetSubtree(self.CatObj.GetRootNode()))
        #pprint.pp(Proc)
        self.assertEqual(len(Proc), 1)

    def test_DeleteSubtree(self):
        self.CatObj.DeleteSubtree(self.TwoRet)
        Proc = list(self.CatObj.GetSubtree(self.CatObj.GetRootNode()))
        self.assertEqual(len(Proc), 2)

    def test_NoSubtreeDeleteSubtree(self):
        self.CatObj.DeleteSubtree(self.FourRet)
        Proc = list(self.CatObj.GetSubtree(self.CatObj.GetRootNode()))
        self.assertEqual(len(Proc), 4)

    def test_NoSubtreeDeleteSubtreeSelf(self):
        self.CatObj.DeleteSubtree(self.FourRet, True)
        Proc = list(self.CatObj.GetSubtree(self.CatObj.GetRootNode()))
        #pprint.pp(Proc)
        self.assertEqual(len(Proc), 3)

    def test_RefToRef(self):
        self.assertEqual(self.CatObj.GetCategoryRefFromCategoryRef(Categories.CategoryRef(self.TwoRet.CatID, None)).Category, self.TwoRet.Category)
        self.assertEqual(self.CatObj.GetCategoryRefFromCategoryRef(Categories.CategoryRef(self.CatObj.GetRootNode().CatID, None)).Category, self.CatObj.GetRootNode().Category)
        self.assertEqual(self.CatObj.GetCategoryRefFromCategoryRef(Categories.CategoryRef(1, None)).Category, self.CatObj.GetRootNode().Category)

    def tearDown(self) -> None:
        self.Db.__exit__()
        os.remove("testdb2.db")
        return super().tearDown()


class _TestCategories(unittest.TestCase):

    def setUp(self) -> None:
        #print()
        self.Db = Database("testdb.db")
        self.CatObj = Categories(self.Db.__enter__())
        return super().setUp()

    def test_SettingCategoryRef(self):
        RN = self.CatObj.GetRootNode()
        self.CatObj.CategoryRefSetItem(RN, "Pattern", Categories.DefaultRootNodeAlt.Pattern)

        TestCan = Categories.DefaultRootNodeAlt
        RN2 = self.CatObj.GetRootNode()
        self.assertEqual(TestCan.Pattern, RN2.Category.Pattern)

    def test_SettingCategoryRefColor(self):
        RN = self.CatObj.GetRootNode()
        self.CatObj.CategoryRefSetItem(RN, "Color", Categories.DefaultRootNodeAlt._Color)
        TestCan = Categories.DefaultRootNodeAlt
        del RN
        RN2 = self.CatObj.GetRootNode()
        self.assertEqual(TestCan._Color, RN2.Category._Color)



    def test_GetRootNode(self):
        self.RootNode = self.CatObj.GetRootNode()
        #ExampleRootNode._CatID = 1
        self.assertEqual(self.RootNode.Category, Categories.DefaultRootNode)
                         
        return self.RootNode

    def test_AddNewCat(self):
        self.NewCat = Categories.Category("Test1", EMatchingMode.ALWAYS, EMatchingTarget.CLASS, "")
        self.RootNode = self.test_GetRootNode()
        self.NewCat = self.CatObj.AddCategory(self.RootNode, self.NewCat)
        CatChil = list(self.CatObj.GetChildren(self.RootNode))
        #print(CatChil)
        #self.assertEqual(len(CatChil), 1)
        #self.assertEqual(CatChil[0], self.NewCat.Category)
        return self.NewCat

    def test_GetParent(self):
        self.RootNode = self.test_GetRootNode()
        self.NewCat = Categories.Category("Test1", EMatchingMode.ALWAYS, EMatchingTarget.CLASS, "")
        self.NewCat = self.CatObj.AddCategory(self.RootNode, self.NewCat)

        self.assertEqual(self.CatObj.GetParent(self.NewCat), self.RootNode)
        print("ROOT NODE", self.RootNode)
        self.assertEqual(self.CatObj.GetParent(self.RootNode), None)
        #self.assertEqual(self.CatObj.GetParent(self.test_AddNewCat()), self.RootNode)
    

    def test_GetChildren(self):
        self.RootNode = self.test_GetRootNode()

        self.assertEqual(len(list(self.CatObj.GetChildren(self.RootNode))), 0)

        self.NewCat = self.test_AddNewCat()


        self.CatObj.AddCategory(self.NewCat, Categories.Category("Test2", EMatchingMode.ALWAYS, EMatchingTarget.CLASS, ""))
        self.CatObj.AddCategory(self.NewCat, Categories.Category("Test3", EMatchingMode.ALWAYS, EMatchingTarget.CLASS, ""))
        #PP.pprint(list(self.CatObj.GetChildren(self.RootNode)))
        self.assertEqual(len(list(self.CatObj.GetChildren(self.RootNode))), 1)
        self.assertEqual(len(list(self.CatObj.GetChildren(self.NewCat))), 2)

    def test_GetChildrenNull(self):
        with Database("test_getchildren2.db") as DB:
            CatObj = Categories(DB)
            RootNode = CatObj.GetRootNode()
            self.assertEqual(len(list(CatObj.GetChildren(RootNode))), 0)

    def test_RenderTree(self):
        self.RootNode = self.test_GetRootNode()
        self.test_GetChildren()
        #print("TREEEEE")
        #PP.pprint(self.CatObj.RenderTree(self.RootNode))
        #PP.pprint(self.CatObj.RenderTree(self.RootNode)["Children"][0]["Children"][0]["Name"].CatID)
        self.assertEqual(self.CatObj.RenderTree()["Children"][0]["Children"][0]["Name"].CatID, 3)
        self.assertEqual(self.CatObj.RenderTree()["Children"][0]["Children"][1]["Name"].CatID, 4)
        self.assertEqual(self.CatObj.RenderTree()["Children"][0]["Name"].CatID, 2)
        self.assertEqual(self.CatObj.RenderTree()["Name"].CatID, 1)


    def tearDown(self) -> None:
        self.Db.__exit__()
        os.remove("testdb.db")
        try:
            os.remove("test_getchildren2.db")
        except FileNotFoundError:
            pass
        return super().tearDown()


#class _TestDBSettings(unittest.TestCase):
#    def setUp(self) -> None:
#        #print()
#        self.Obj = DBSettings()
#        self.Obj._DataPath = "TestDBSettings.db"
#        return super().setUp()
#
#    def test_GetDefault(self):
#        self.assertEqual(self.Obj.AFKTime, DBSettings.AFKTime)
#        self.assertEqual(self.Obj.UseSysIcon, DBSettings.UseSysIcon)
#
#    def test_DBOpenedSet(self):
#        self.Obj.__enter__(self.Obj)
#        self.Obj.AFKTime = 90
#        self.assertEqual(self.Obj.AFKTime, 90)
#        self.Obj.__exit__(self.Obj)
#
#    def test_DBOpenedGet(self):
#        self.Obj.__enter__(self.Obj)
#        self.assertEqual(self.Obj.AFKTime, DBSettings.AFKTime)
#        self.Obj.__exit__(self.Obj)
#
#    def test_DBOpendedSetThenGet(self):
#        self.Obj.__enter__(self.Obj)
#        self.Obj.AFKTime = 45
#        self.Obj.__exit__(self.Obj)
#
#        self.assertEqual(self.Obj.AFKTime, DBSettings.AFKTime)
#
#        self.Obj.__enter__(self.Obj)
#        self.assertEqual(self.Obj.AFKTime, 45)
#        self.Obj.__exit__(self.Obj)
#
#
#    def tearDown(self) -> None:
#        try:
#            os.remove("TestDBSettings.db")
#        except FileNotFoundError:
#            pass
#        return super().tearDown()

class _TestDBSettings2(unittest.TestCase):
    def setUp(self) -> None:
        #print()
        self.DB = Database("TestDBSettings2.db")
        Con = self.DB.__enter__()
        #print("CONNNNN", Con)
        self.Obj = DBSettings2(Con)
        return super().setUp()

    def test_GetDefault(self):
        self.assertEqual(self.Obj.AFKTime, DBSettings2.AFKTime)
        self.assertEqual(self.Obj.UseSysIcon, DBSettings2.UseSysIcon)

    def test_DBOpenedSet(self):
        with self.Obj as EObj:
            EObj.AFKTime = 90
            self.assertEqual(EObj.AFKTime, 90)

    def test_DBOpenedGet(self):
        with self.Obj as EObj:
            self.assertEqual(EObj.AFKTime, DBSettings2.AFKTime)

    def test_DBOpendedSetThenGet(self):
        with self.Obj as EObj:
            self.assertEqual(EObj.AFKTime, DBSettings2.AFKTime)
        with self.Obj as EObj:
            EObj.AFKTime = 45
        with self.Obj as EObj:
            self.assertEqual(EObj.AFKTime, 45)

    def tearDown(self) -> None:
        try:
            os.remove("TestDBSettings2.db")
        except FileNotFoundError:
            pass
        return super().tearDown()

class _TestAFK(unittest.TestCase):
    def setUp(self) -> None:
        #print()
        self.Database = Database("TestDBAFK.db")
        self.Obj = AFK(self.Database.__enter__())
        return super().setUp()

    def test_IsAFK(self):
        self.assertEqual(self.Obj.IsAFK(), False)

    def test_SetAFK(self):
        self.Obj.SetAFK()
        self.assertEqual(self.Obj.IsAFK(), True)

    def test_UnsetAFK(self):
        self.Obj.UnsetAFK()
        self.assertEqual(self.Obj.IsAFK(), False)

    def test_GetRange(self):
        self.Obj.SetAFK()
        self.Obj.UnsetAFK()
        self.Obj.SetAFK()

        Res = self.Obj.GetRange(datetime.datetime.now() - datetime.timedelta(days=1), datetime.datetime.now())
        self.assertEqual(Res[0][1], True)
        self.assertEqual(Res[1][1], False)
        self.assertEqual(Res[2][1], True)

    def test_GetRangeNull(self):
        with Database("testdb_afk2.db") as DB:
            AFKObj = AFK(DB)
            Ret = AFKObj.GetRange(datetime.datetime(year=1970, month=1, day=1), datetime.datetime.now())
            self.assertListEqual(Ret, [])
        os.remove("testdb_afk2.db")

    #def tearDown(self):
    #    with Database("testdb") as DB:
    #        CatObj = Categories(DB)
    #        CatObj.AddCategory(Parent, Child)

    def tearDown(self) -> None:
        self.Database.__exit__()
        os.remove("TestDBAFK.db")
        return super().tearDown()

if 'unittest.util' in __import__('sys').modules:
    # Show full diff in self.assertEqual.
    __import__('sys').modules['unittest.util']._MAX_LENGTH = 999999999
    #pass
    #pass
if __name__ == '__main__':
    unittest.main(verbosity=4, )
