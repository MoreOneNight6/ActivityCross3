#!/usr/bin/python3
from datetime import date, timedelta
import datetime
from enum import Enum
import pprint
from sys import flags
from time import perf_counter
import typing
import wx
#import wx.dataview as wxd
import data
import functools
#import wx.adv as wxa
import wx.lib.masked as wxm
import wx.lib.combotreebox as wxc
import wx.lib.colourutils as wxu
import wx.lib.mixins.listctrl as wxlistmix
from wx.lib import sized_controls
import wx.adv as wxa
from math import trunc
from wx import xrc
import calendar



#class _EventTreeModel(wxd.PyDataViewModel):
#
#	def __init__(self):
#		self.Mapper = {}
#		super().__init__()
#
#	def ItemToObject(self, item):
#		return self.Mapper[int(item.GetID())]
#
#	def ObjectToItem(self, obj: data.Categories.CategoryRef):
#		self.Mapper[obj.CatID] = obj
#		return wxd.DataViewItem(obj.CatID)
#
#	def GetColumnCount(self):
#		return 3
#
#	def HasContainerColumns(self, item):
#		return True
#
#	@functools.cache
#	def GetChildren(self, item, children):
#		with data.Database() as Db:
#			EvObj = data.Events(Db)
#			if item.IsOk():
#				wx.LogWarning("Application tried to get child of event object")
#				#ChildrenList = list(CatObj.GetChildren(self.ItemToObject(item)))
#				#for i in ChildrenList:
#				#	children.append(self.ObjectToItem(i))
#				#return len(ChildrenList)
#			else:
#				Ret = EvObj.GetRootNode()
#				children.append(self.ObjectToItem(Ret))
#				return 1
	
	

def UnPrettyTimeDate(input:datetime.datetime):
    return input.strftime("%H:%M:%S.%f")[:-4]
def PrettyTimeDate(input:datetime.datetime):
    return input.strftime("%c")

def PrettyTimeDelta(diff:timedelta, ActionWord="ago"):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    """
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 1:
            return "<1 second " + ActionWord
        if second_diff < 60:
            return str(second_diff) + " seconds "+ActionWord
        if second_diff < 120:
            return "a minute " + ActionWord
        if second_diff < 3600:
            return str(second_diff // 60) + " minutes "+ActionWord
        if second_diff < 7200:
            return "an hour " + ActionWord
        if second_diff < 86400:
            Hours, SecondsMod = divmod(second_diff, 3600)
            if SecondsMod//60 > 0:
                return str(second_diff // 3600) + " hours, " + str(SecondsMod // 60) + " min "+ActionWord
            else:
                return str(second_diff // 3600) + " hours "+ActionWord
    # Hardcode this value cuz too lazy
    if ActionWord == "ago":
        if day_diff == 1:
            return "Yesterday"
    else:
        if day_diff == 1:
            return "1 day" + ActionWord
    if day_diff < 7:
        return str(day_diff) + " days "+ActionWord
    if day_diff < 31:
        return str(day_diff // 7) + " weeks "+ActionWord
    if day_diff < 365:
        return str(day_diff // 30) + " months "+ActionWord
    return str(day_diff // 365) + " years "+ActionWord

#def strfdelta(tdelta, fmt):
#    d = {"days": tdelta.days}
#    d["hours"], rem = divmod(tdelta.seconds, 3600)
#    d["minutes"], d["seconds"] = divmod(rem, 60)
#    return fmt.format(**d)

def UnPrettyTimeDelta(Input:datetime.timedelta):
    return str(Input)[:-4]
    #Hours, MinutesMod = divmod(Input.seconds, 3600)
    #Minutes = 60 - MinutesMod
    #Seconds, MicroMod = divmod(Input.total_seconds(), 1)
    #print(Seconds, MicroMod, Input)
    #Minutes, SecondsMod = divmod(Input.seconds, 60)
    ##print(Input.seconds)
    #Seconds = 60 - SecondsMod
    #Hours, _ = divmod(Minutes, 60)
    #print(Seconds, FracSeconds, TotalSeconds)
    #_, FracSeconds = divmod(Input.total_seconds(), 1)
    #SmolFracSeconds = trunc(FracSeconds * 100)

    #print(Hours, Minutes, Seconds)
    #return ""

    #MicroRem = Input.total_seconds() % 1
    #Micro = trunc(MicroRem * 100)
    #Hours, Rem = divmod(Input.seconds, 3600)
    #Minutes, Seconds = divmod(Rem,60)
    #return "{0:02d}:{1:02d}:{2:02d}.{3:02d}".format(Hours, Minutes, Seconds, Micro)


def WxDateToDateTime(Val:wx.DateTime):
    f = Val.Format('%d/%m/%y %H:%M:%S')
    x = datetime.datetime.strptime(f,'%d/%m/%y %H:%M:%S')
    return x
def DateTimeToWxDate(Val:datetime.datetime):
    return wx.DateTime.FromDMY(Val.day, Val.month, Val.year, Val.hour, Val.minute, Val.second)

class TSDisplayType(Enum):
    MOMENT = 0
    AGO = 1
    TIMEIN = 2


#import time

class CalenderDiag(wx.Dialog):
    def __init__(self, parent, Time:datetime.datetime | None=None, *args, **kw):
        super().__init__(parent, *args, **kw)
        #self.SetTitle("Choose date")
        Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Calender = wxa.CalendarCtrl(self)
        if Time!=None:
            self.Calender.SetDate(wx.DateTimeFromDMY(Time.day, Time.month, Time.year))
        #self.SetSize(self.Calender.GetSize())
        #OkBut = wx.Button(self, wx.ID_OK)
        #OkBut.Bind(wx.EVT_BUTTON, self.OnOK)

        Sizer.Add(self.Calender)
        Sizer.Add(self.CreateStdDialogButtonSizer(wx.OK|wx.CANCEL))
        self.SetSizer(Sizer)
        self.Fit()
    #def OnOK(self, e):
    #    self.Destroy()


class EventJustNowInput(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        self.parent = parent
        #text = wx.TextCtrl(self, style = wx.TE_MULTILINE) 
        #but = wx.Button(self, label="UWU")
        #box = wx.StaticBox(self, wx.ID_ANY, "StaticBox")
        #text = wx.StaticText(self, wx.ID_ANY, "This window is a child of the staticbox")
        #text2 = wx.StaticText(self, wx.ID_ANY, "This window is a child of the staticbox2")
        self.Num = wx.SpinCtrl(self, min=0, max=10000, initial=data.DBSettings2.EventsJustNowLimit)

        self.TesterSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.TesterSizer.Add(wx.StaticText(self, label="Records to store:"), 1, border=8, flag=wx.ALIGN_CENTER_VERTICAL|wx.RIGHT)
        self.TesterSizer.Add(self.Num)
        #self.TesterSizer.Add(text2)
        self.SetSizer(self.TesterSizer)
        with data.Database() as DB:
            SetObj = data.DBSettings2(DB)
            self.Num.SetValue(SetObj.EventsJustNowLimit)
        self.Num.Bind(wx.EVT_SPINCTRL, self.OnSpinCtrl)


    def OnSpinCtrl(self, *args):
        with data.Database() as DB:
            SetObj = data.DBSettings2(DB)
            SetObj.EventsJustNowLimit = self.Num.GetValue()

class DateTimeMaskedInput():
    def TextValToDateTime(self, Val:str):
        try:
            return datetime.datetime.strptime(Val, "%d-%m-%y %H:%M:%S")
        except ValueError as e:
            wx.LogError("Incorrectly formatted input " + str(e))
            raise e
    def DateTimeToTextVal(self, Val:datetime.datetime):
        return datetime.datetime.strftime(Val, "%d-%m-%y %H:%M:%S")

    def __init__(self, parent, NotBefore=None, NotAfter=None) -> None:
        # TODO: Make this respond to locales
        self.NotBefore = NotBefore
        self.NotAfter = NotAfter
        self.parent = parent
        UsedFixed = data.DBSettings2.UseMonospace
        with data.Database() as DB:
            UsedFixed = data.DBSettings2.UseMonospace
        self.Ctrl = wx.BoxSizer(wx.HORIZONTAL)
        self.TextCtrl = wxm.TextCtrl(parent, -1, 
                     self.DateTimeToTextVal(datetime.datetime.now()), 
                     mask=       "##-##-## ##:##:##", 
                     formatcodes="0T",
                     fields={
                         5: wxm.maskededit.Field(validRange=(0,59), validRequired=True),
                         4: wxm.maskededit.Field(validRange=(0,59), validRequired=True),
                         3: wxm.maskededit.Field(validRange=(0,23), validRequired=True),
                         0: wxm.maskededit.Field(validRange=(0,31), validRequired=True),
                         1: wxm.maskededit.Field(validRange=(1,12), validRequired=True),
                         2: wxm.maskededit.Field(validRange=(0,99), validRequired=True),
                     },
                     useFixedWidthFont=False)
        DropdownBut = wx.Button(parent, style=wx.BU_EXACTFIT)
        DropdownBut.SetBitmapLabel(wx.ArtProvider.GetBitmap(wx.ART_GO_DOWN, wx.ART_MENU))
        DropdownBut.Bind(wx.EVT_BUTTON, self.DropdownShowDiag) 
        self.Ctrl.Add(self.TextCtrl)
        self.Ctrl.Add(DropdownBut, border=4, flag=wx.LEFT)
        #self.Ctrl = wxm.TimeCtrl(parent)
        #print(self.Ctrl.SetFont(wx.Font(wx.FontInfo(10))))
        self.TextCtrl.SetMinSize(wx.Size(140, -1))
        #self.SetTime(initial)

    def DropdownShowDiag(self,e):
        #print(e, self.parent)
        #wxc.CalenDlg(self.parent)
        CurrInput = self.GetTime()
        Diag = CalenderDiag(self.parent, CurrInput)
        NotBeforeObj = self.NotBefore() if self.NotBefore != None else None
        NotAfterObj= self.NotAfter() if self.NotAfter!= None else None
        print("BObj", NotBeforeObj, "AObj", NotAfterObj, "B", self.NotBefore)
        Diag.Calender.SetDateRange(
                DateTimeToWxDate(NotBeforeObj) if NotBeforeObj != None else wx.DefaultDateTime,
                DateTimeToWxDate(NotAfterObj) if NotAfterObj != None else wx.DefaultDateTime)
        if Diag.ShowModal() == wx.ID_OK:
            #print(Diag.Calender)
            WxDate:wx.DateTime = Diag.Calender.GetDate()
            Return = WxDateToDateTime(WxDate)
            if CurrInput != None:
                Return = datetime.datetime(WxDate.year, WxDate.month, WxDate.day, CurrInput.hour, CurrInput.minute, CurrInput.second)
            self.SetTime(Return)
        Diag.Destroy()

    def SetTime(self, Input:datetime.datetime):
        #pass
        self.TextCtrl.SetValue(self.DateTimeToTextVal(Input))
    def GetTime(self):
        #pass
        #try:
        return self.TextValToDateTime(self.TextCtrl.GetValue())
        #except ValueError as e:
        #    print(e)
        #    return None


class EventRangeInput(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        self.parent = parent
        self.TimeCtrlStart = DateTimeMaskedInput(self)
        self.TimeCtrlStart.SetTime(datetime.datetime.now() - datetime.timedelta(days=1))
        self.TimeCtrlEnd = DateTimeMaskedInput(self)
        self.TimeCtrlEnd.NotAfter = lambda: datetime.datetime.now()
        self.TimeCtrlEnd.NotBefore = self.TimeCtrlStart.GetTime

        self.TimeCtrlStart.NotAfter = self.TimeCtrlEnd.GetTime
        self.TimeCtrlEnd.SetTime(datetime.datetime.now())

        self.UpdateButtonW = wx.Button(self, label="Go!")
        self.UpdateButtonW.SetMaxSize(wx.Size(40,-1))
        self.UpdateButtonW.BackgroundColour= wx.NamedColour("green")
        self.TesterSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.TesterSizer.Add(wx.StaticText(self, label="Start: "), 0, border=4, flag=wx.ALIGN_CENTER_VERTICAL|wx.LEFT)
        self.TesterSizer.Add(self.TimeCtrlStart.Ctrl, 1, border=4, flag=wx.RIGHT)
        self.TesterSizer.Add(wx.StaticText(self, label="End: "), 0, border=4, flag=wx.ALIGN_CENTER_VERTICAL|wx.LEFT)
        self.TesterSizer.Add(self.TimeCtrlEnd.Ctrl, 1, border=4, flag=wx.LEFT)
        self.TesterSizer.Add(self.UpdateButtonW, 0, border=4, flag=wx.LEFT)
        self.SetSizer(self.TesterSizer)

    @property
    def StartTime(self):
        return self.TimeCtrlStart.GetTime()
    @StartTime.setter
    def StartTime(self, val):
        self.TimeCtrlStart.SetTime(val)
    @property
    def EndTime(self):
        return self.TimeCtrlEnd.GetTime()
    @EndTime.setter
    def EndTime(self, val):
        self.TimeCtrlEnd.SetTime(val)

class EventRangeInputFancy(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        self.parent = parent
        self.QuickChoice = wx.Choice(self, choices=["Today",
                                                    "Yesterday",
                                                    "This Week",
                                                    "Last Week",
                                                    "This Month",
                                                    "Custom"])
        self.QuickChoice.Select(0)
        self.UnitChoice = wx.Choice(self, choices=["Minutes(s)",
                                                   "Hours(s)",
                                                   "Day(s)",
                                                   "Week(s)",
                                                   "Month(s)"])
        self.UnitChoice.Select(0)
        self.UnitChoice.Disable()
        self.Magnitude = wx.SpinCtrl(self,initial=1, min=1, max=1000)
        self.Magnitude.Disable()
        self.Magnitude.Bind(wx.EVT_SPINCTRL, self.OnMagnitude)
        self.UnitChoice.Bind(wx.EVT_CHOICE, self.OnMagnitude)
        self.UpdateButtonW = wx.Button(self, label="Go!")
        self.UpdateButtonW.SetMaxSize(wx.Size(40,-1))
        self.UpdateButtonW.BackgroundColour= wx.NamedColour("green")

        self.TesterSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.TesterSizer.Add(self.QuickChoice, 1, border=16, flag=wx.RIGHT)
        self.TesterSizer.Add(wx.StaticText(self, label="Last"), border=6, flag=wx.ALIGN_CENTER_VERTICAL|wx.RIGHT)
        self.TesterSizer.Add(self.Magnitude, 0, border=6, flag=wx.RIGHT)
        self.TesterSizer.Add(self.UnitChoice, 0)
        self.TesterSizer.Add(self.UpdateButtonW, 0, border=4, flag=wx.LEFT)
        self.SetSizer(self.TesterSizer)
        self.StartDate = None
        self.EndDate = None
        self.OnQuickChoice(self)
        self.QuickChoice.Bind(wx.EVT_CHOICE, self.OnQuickChoice)

    # Do not call this outside of OnQuickChoice when StartDate is defined
    # TODO: Generalize this
    def _AccountForStartWeek(self):
        with data.Database() as DB:
            if data.DBSettings2(DB).StartWeekOnSunday:
                self.StartDate -= datetime.timedelta(days=1)
                self.EndDate -= datetime.timedelta(days=1)

    def OnQuickChoice(self, evt):
        if self.QuickChoice.GetStringSelection() == "Custom":
            self.StartDate = None
            self.EndDate = None
            self.Magnitude.Enable()
            self.UnitChoice.Enable()
            self.OnMagnitude(None)
        else:
            self.Magnitude.Disable()
            self.UnitChoice.Disable()
            CustomTZ = data.CustomTZ()
            with data.Database() as DB:
                SetObj = data.DBSettings2(DB)
                if SetObj.EventsInputCustomMidnight:
                    CustomTZ = data.CustomTZ(SetObj.CustomMidnight)
            if self.QuickChoice.GetStringSelection() == "Today":
                self.StartDate= CustomTZ.OffsetNaive(
                        datetime.datetime.combine(datetime.datetime.now(), datetime.time.min))
                self.EndDate = CustomTZ.OffsetNaive(
                        datetime.datetime.combine(datetime.datetime.now(), datetime.time.max))
            elif self.QuickChoice.GetStringSelection() == "Yesterday":
                self.StartDate= CustomTZ.OffsetNaive(
                        datetime.datetime.combine(datetime.datetime.now() - datetime.timedelta(days=1), datetime.time.min))
                self.EndDate = CustomTZ.OffsetNaive(
                        datetime.datetime.combine(datetime.datetime.now() - datetime.timedelta(days=1), datetime.time.max))
            elif self.QuickChoice.GetStringSelection() == "This Week":
                today = date.today()
                self.StartDate = today - timedelta(days=today.weekday())
                self.EndDate = self.StartDate + timedelta(days=6)
                self._AccountForStartWeek()
                self.StartDate = datetime.datetime.combine(self.StartDate, datetime.datetime.min.time())
                self.EndDate = datetime.datetime.combine(self.EndDate, datetime.datetime.min.time())
            elif self.QuickChoice.GetStringSelection() == "Last Week":
                today = date.today()
                self.StartDate = today - timedelta(days=today.weekday() + 7)
                self.EndDate = self.StartDate + timedelta(days=6)
                self._AccountForStartWeek()
                self.StartDate = datetime.datetime.combine(self.StartDate, datetime.datetime.min.time())
                self.EndDate = datetime.datetime.combine(self.EndDate, datetime.datetime.min.time())
                #with data.Database() as DB:
                #    if data.DBSettings2(DB).StartWeekOnSunday:
                #        self.StartDate -= datetime.timedelta(days=1)
                #        self.EndDate -= datetime.timedelta(days=1)
            elif self.QuickChoice.GetStringSelection() == "This Month":
                self.StartDate = datetime.datetime.today().replace(day=1)
                self.EndDate = datetime.datetime.today().replace(
                            day=calendar.monthrange(self.StartDate.year,self.StartDate.month)[1]
                )
        print(self.StartDate, self.EndDate)

    def OnMagnitude(self, evt):
        Val = self.Magnitude.GetValue()
        Unit = self.UnitChoice.GetSelection()

        CustomTZ = data.CustomTZ()
        with data.Database() as DB:
            SetObj = data.DBSettings2(DB)
            if SetObj.EventsInputCustomMidnight:
                CustomTZ = data.CustomTZ(SetObj.CustomMidnight)

        self.EndDate = datetime.datetime.now()
        self.StartDate = self.EndDate
        if Unit == 0:
            self.StartDate = self.EndDate - datetime.timedelta(minutes=Val)
        elif Unit == 1:
            self.StartDate = self.EndDate - datetime.timedelta(hours=Val)
        elif Unit == 2:
            self.StartDate = self.EndDate -CustomTZ.OffsetNaiveTimeDelta(datetime.timedelta(days=Val))
        elif Unit == 3:                                         
            #self.StartDate = self.EndDate -CustomTZ.OffsetNaiveTimeDelta(datetime.timedelta(weeks=Val))
            today = date.today()
            self.StartDate = today - timedelta(days=today.weekday() + (7*(Val-1)))
            self.EndDate = self.StartDate + timedelta(days=6*Val)
            self._AccountForStartWeek()
            self.StartDate = datetime.datetime.combine(self.StartDate, datetime.datetime.min.time())
            self.EndDate = datetime.datetime.combine(self.EndDate, datetime.datetime.min.time())
        elif Unit == 4:
            # I dont really know how months work
            # TODO: Understand months
            self.StartDate = CustomTZ.OffsetNaive(self.EndDate - datetime.timedelta(days=Val*30))

            #self.StartDate = today - timedelt
            #self._AccountForStartWeek()
            #self.StartDate = datetime.datetime.combine(self.StartDate, datetime.datetime.min.time())
        print(self.StartDate, self.EndDate)

class NewCatDiag(wx.Dialog):
    def __init__(self, parent, Time:datetime.datetime | None=None, *args, **kw):
        super().__init__(parent, *args, **kw)
        #self.SetTitle("Choose date")
        Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Calender = wxa.CalendarCtrl(self)
        if Time!=None:
            self.Calender.SetDate(wx.DateTimeFromDMY(Time.day, Time.month, Time.year))
        #self.SetSize(self.Calender.GetSize())
        #OkBut = wx.Button(self, wx.ID_OK)
        #OkBut.Bind(wx.EVT_BUTTON, self.OnOK)

        Sizer.Add(self.Calender)
        Sizer.Add(self.CreateStdDialogButtonSizer(wx.OK|wx.CANCEL))
        self.SetSizer(Sizer)
        self.Fit()

#def GetCategoryFromUser(Parent):
class CatDiag():
    def __init__(self, Parent) -> None:
        self.Parent = Parent

    def GetCategory(self):
        if not hasattr(self, "Diag"):
            self.Diag = xrc.XmlResource("xrc/CatDiag.xml").LoadDialog(self.Parent, "CatDiag")
        if self.Diag.ShowModal() == wx.ID_OK:
            Colour:wx.Colour= xrc.XRCCTRL(self.Diag, "ColourInput").GetColour()
            return data.Categories.Category(xrc.XRCCTRL(self.Diag, "TitleInput").GetValue(),
                                            data.EMatchingMode(xrc.XRCCTRL(self.Diag, "MatchInput").GetSelection()),
                                            data.EMatchingTarget(xrc.XRCCTRL(self.Diag, "TargetInput").GetSelection()),
                                            xrc.XRCCTRL(self.Diag, "PatternInput").GetValue(),
                                            (Colour.Red(), Colour.Green(), Colour.Blue()),
                                            xrc.XRCCTRL(self.Diag, "Lower").GetValue(),
                                            0,
                                            xrc.XRCCTRL(self.Diag, "Cascade").GetValue())
        else:
            return None


class CatAddDiag(sized_controls.SizedDialog):

    def __init__(self, Parent, StartDate:datetime.datetime | None =None, EndDate:datetime.datetime | None =None) -> None:
        sized_controls.SizedDialog.__init__(self, None, title="SizedDialog Demo")
                                

        panel = self.GetContentsPane()
        panel.SetSizerType("form")  

        if StartDate:
            wx.StaticText(panel,-1,"Start")
            StartPane = sized_controls.SizedPanel(panel, -1)
            StartPane.SetSizerType("horizontal")

            StartDate = wxa.DatePickerCtrl(StartPane, dt=wx.DateTimeFromDMY(StartDate.day, StartDate.month, StartDate.year))
            StartTime = wxa.TimePickerCtrl(StartPane, dt=wx.DateTimeFromHMS(StartDate.hour, StartDate.minute, StartDate.second))

        wx.StaticText(panel, -1, "Current")
        CurrPane = sized_controls.SizedPanel(panel, -1)
        CurrPane.SetSizerType("form")

        CurrDate = wxa.DatePickerCtrl(CurrPane)
        CurrTime = wxa.TimePickerCtrl(CurrPane)

        if EndDate:
            wx.StaticText(panel, -1, "End")
            EndPane = sized_controls.SizedPanel(panel, -1)
            EndPane.SetSizerType("horizontal")

            EndDate = wxa.DatePickerCtrl(EndPane, dt=wx.DateTimeFromDMY(StartDate.day, StartDate.month, StartDate.year))
            EndTime = wxa.TimePickerCtrl(EndPane, dt=wx.DateTimeFromHMS(StartDate.hour, StartDate.minute, StartDate.second))




        #if not hasattr(self, "DiagRec"):
        #    self.DiagRec = xrc.XmlResource("xrc/CatDiagAdd.xml")
        ##print(self.DiagRec.GetXRCID("YourPicker"))
        #Diag = self.DiagRec.LoadDialog(self.Parent, "CatAddDiag")
        #print(self.DiagRec.Ge
        #if Diag.ShowModal() == wx.ID_OK:
        #    YourTime = datetime.time(*xrc.XRCCTRL(Diag, "YourPicker").GetTime())
        #    YourDateWx:wx.DateTime = xrc.XRCCTRL(Diag, "YourDate").GetValue()
        #    YourDate = datetime.datetime.combine(datetime.datetime(YourDateWx.year, YourDateWx.month, YourDateWx.day),  
        #                                         YourTime)
        #    print(YourDate)
        #    return YourDate
        #    #YourDate = datetime.datetime(
        #    
        #    #Colour:wx.Colour= xrc.XRCCTRL(self.Diag, "ColourInput").GetColour()
        #    #return data.Categories.Category(xrc.XRCCTRL(self.Diag, "TitleInput").GetValue(),
        #    #                                data.EMatchingMode(xrc.XRCCTRL(self.Diag, "MatchInput").GetSelection()),
        #    #                                data.EMatchingTarget(xrc.XRCCTRL(self.Diag, "TargetInput").GetSelection()),
        #    #                                xrc.XRCCTRL(self.Diag, "PatternInput").GetValue(),
        #    #                                (Colour.Red(), Colour.Green(), Colour.Blue()),
        #    #                                xrc.XRCCTRL(self.Diag, "Lower").GetValue(),
        #    #                                0,
        #    #                                xrc.XRCCTRL(self.Diag, "Cascade").GetValue())
        #else:
        #    return None



    
    


#class CatInputDiag(wx.Dialog):
#    def __init__(self, *args, **kw):
#        super().__init__(*args, **kw)
#        print(self.Res)
#    
#    @property
#    def Category(self):

class EventCatInputMode(Enum):
    ALL = 0
    NONE = 1
    TREE = 2
    CUSTOM = 3

class EventCatInput(wx.Panel):

    def _AddComboboxTree(self, Curr, Parent):
        RCurr = Curr["Name"].Category
        #if Parent != None:
        #    Parent = Parent["Name"].Category.Name
        Parent = self.QuickChoice.Append(RCurr.Name, clientData=Curr["Name"].Category, parent=Parent)
        #if Curr["Name"].CatID == 1:
        #    self.AllItem = Parent
        for i in Curr["Children"]:
            self._AddComboboxTree(i, Parent)
        #self.QuickChoice.Append(self, Node.Name, parent=Parent.Name if Parent != None else None)
        #print(Node.Name)
        #if Node. != None:
            #for i in Par

    def OnComboBox(self,evt):
        if self.QuickChoice.GetSelection() == self.CustomId:
        #    self.EditButton.Enable()
        #    #if self.Custom == None:
        #        #if not hasattr(self, "CatDiag"):
            GetCustom = self.CatDiag.GetCategory()
            if GetCustom == None:
                self.QuickChoice.SetSelection(self.AllItem)
            else:
                self.Custom = GetCustom

            #print(self.Custom)
            if self.Custom != None:
                self.QuickChoice.SetString(self.CustomId, "[CUSTOM] " +self.Custom.Name)
                if self.Custom.Name == "":
                    self.QuickChoice.SetString(self.CustomId, "[CUSTOM] " +self.Custom.Pattern)
                self.QuickChoice.SetSelection(self.CustomId)
        #        #print(self.Custom)
        #        #R = CatInputDiag(self)
        #        #if R.ShowModal() == wx.ID_OK:
        #            #self.Custom = R.Category
        #        #self.Custom = 
        else:
            self.Custom = None
        #    self.EditButton.Disable()

    #def OnEditCustom(self,evt):
    #    self.Custom = self.CatDiag.GetCategory()
    #    self.QuickChoice.SetString(self.CustomId, "[CUSTOM] " +self.Custom.Name)
    #    if self.Custom.Name == "":
    #        self.QuickChoice.SetString(self.CustomId, "[CUSTOM] " +self.Custom.Pattern)
    #    self.QuickChoice.SetSelection(self.CustomId)



    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        self.parent = parent
        self.Custom = None
        self.CatDiag = CatDiag(self)

        self.QuickChoice:wx.ComboBox = wxc.ComboTreeBox(self)
        with data.Database() as DB:
            CatObj = data.Categories(DB)
            self._AddComboboxTree(CatObj.RenderTree(), None)
            
            #for i in CatObj.GetSubtree(Root):
            #    if i != None:
        self.AllItem = self.QuickChoice.Append("[ALL]")
        self.QuickChoice.Select(self.AllItem)
        #self.HighlightID = self.QuickChoice.Append("[HIGHLIGHTED]")
        self.CustomId = self.QuickChoice.Append("[CUSTOM]")
        self.QuickChoice.Bind(wx.EVT_COMBOBOX, self.OnComboBox)
        

        #self.IsFilter = wx.CheckBox(self, label="Filter")
        #self.EditButton = wx.Button(self, wx.ID_EDIT, label="Edit Custom")
        #self.EditButton.Bind(wx.EVT_BUTTON, self.OnEditCustom)
        self.FindButton = wx.Button(self, wx.ID_FIND)
        self.PrevBtn = wx.Button(self, wx.ID_BACKWARD)
        self.PrevBtn.Disable()
        self.NextBtn = wx.Button(self, wx.ID_FORWARD)
        self.NextBtn.Disable()
        #self.EditButton.Disable()

        self.TesterSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.TesterSizer.Add(self.QuickChoice, 1, border=6, flag=wx.RIGHT)
        self.TesterSizer.Add(self.PrevBtn, 0, border=4, flag=wx.RIGHT)
        self.TesterSizer.Add(self.NextBtn, 0, border=0, flag=wx.RIGHT)
        #self.TesterSizer.Add(self.IsFilter, 0, flag=wx.ALIGN_CENTER_VERTICAL|wx.LEFT)
        self.TesterSizer.Add(self.FindButton, 0, border=4, flag=wx.LEFT)
        self.SetSizer(self.TesterSizer)
        #self.QuickChoice = wx.Choice(self, choices=["Today",
                                                    #"Yesterday",
                                                    #"Custom"])
        #self.QuickChoice.Select(0)

    #@property

    def SetMode(self, NewMode:EventCatInputMode):
        if NewMode == EventCatInputMode.ALL:
            self.QuickChoice.SetSelection(self.AllItem)
        elif NewMode == EventCatInputMode.CUSTOM:
            self.QuickChoice.SetSelection(self.CustomId)
        else:
            raise NotImplementedError("Only ALL or CUSTOM modes are supported in SetMode")
        self.OnComboBox(None)

    def GetMode(self):
        if self.QuickChoice.GetSelection() == self.AllItem:
            return EventCatInputMode.ALL
        elif self.QuickChoice.GetSelection() == self.CustomId:
            return EventCatInputMode.CUSTOM
        else:
            return EventCatInputMode.TREE

    def GetCategory(self):
        if self.Custom != None:
            return self.Custom
        return self.QuickChoice.GetClientData(self.QuickChoice.GetSelection())


class EventTreeCtrl(wx.ListCtrl, wxlistmix.TextEditMixin):

    def __init__(self, *args, **kw):
        wx.ListCtrl.__init__(self, style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_SINGLE_SEL, *args, **kw)
        wxlistmix.TextEditMixin.__init__(self)
        self.Len = 0
        #self.TimeStamps = []
        self.AppendColumn("Num", wx.LIST_FORMAT_RIGHT, 50)
        self.AppendColumn("Timestamp", 0, 160)
        self.AppendColumn("Title", 0, 410)
        self.AppendColumn("Class", 0, 120)
        self.Range = []
        self.Highlight = None
        self.TimestampDisplayMode = (TSDisplayType(data.DBSettings2.EventsDisplayType), data.DBSettings2.EventsDisplayIsFancy)

    def _GetItemIndex(self, item):
        return -item-1

    def OnGetItemText(self, item, column):
        #print(item, len(self.Range))
        CurItem = self.Range[self._GetItemIndex(item)]
        if item > len(self.Range):
            return "NO DATA"
        else:
            if column == 0:
                return str(item)
            if column == 1:
                Return = ""
                if (self.TimestampDisplayMode[0] == TSDisplayType.MOMENT):
                    if not self.TimestampDisplayMode[1]:
                        Return = UnPrettyTimeDate(CurItem.Timestamp)
                    else:
                        Return = PrettyTimeDate(CurItem.Timestamp)
                elif (self.TimestampDisplayMode[0] == TSDisplayType.AGO):
                    diff = datetime.datetime.now() - CurItem.Timestamp
                    if not self.TimestampDisplayMode[1]:
                        Return = UnPrettyTimeDelta(diff)
                    else:
                        Return = PrettyTimeDelta(diff)
                elif (self.TimestampDisplayMode[0] == TSDisplayType.TIMEIN):
                    #if not hasattr(self, "LastTime") or self.LastTime == None:
                    #TimeSpent:datetime.timedelta = self.LastTime - CurItem.Timestamp
                    #print(TimeSpent, "\t", self.LastTime, "\t", CurItem.Timestamp)
                    TimeSpent:datetime.timedelta = datetime.timedelta()
                    try:
                        TimeSpent = CurItem.Timestamp - self.Range[-item-2].Timestamp
                    except:
                        TimeSpent = self.LastTime - CurItem.Timestamp
                    if not self.TimestampDisplayMode[1]:
                        Return = UnPrettyTimeDelta(TimeSpent)
                    else:
                        Return = PrettyTimeDelta(TimeSpent, "spent")
                    self.LastTime = CurItem.Timestamp
                else:
                    #wx.LogError("Unknown display type %i" % self.TimestampDisplayMode[0])
                    return "UNKNOWN DISPLAY TYPE"
                return Return
            elif column == 2:
                return CurItem.Name
            elif column == 3:
                return CurItem.Class

    def OnGetItemAttr(self, item):
        Curr = self.Range[self._GetItemIndex(item)] 
        ColorTuple = None
        if type(self.Highlight) == data.Categories.Category:
          if data.Events.MatchAgainstCategory(Curr, self.Highlight):
                ColorTuple = self.Highlight._Color
        elif self.Highlight == True:
            with data.Database() as DB:
                CattRef:data.Categories.CategoryRef = data.PyCategorize(Curr,data.Categories(DB).RenderTree())[-1][0]
                if CattRef.CatID != 1:
                    ColorTuple = CattRef.Category._Color
                
        if self.Highlight != None:
            if ColorTuple != None:
                WxColor = wx.Colour(ColorTuple[0], ColorTuple[1], ColorTuple[2])
                PropStr = "_HighlightColour"+str(datetime.datetime.now().timestamp())
                self.__setattr__(PropStr, wx.ItemAttr(wxu.BestLabelColour(WxColor), WxColor, wx.Font()))
                return self.__getattribute__(PropStr)

    def SetVirtualData(self, Row, Col, Data):
        print("COL", Col, "ROW", Row, Data)
        if Col > 1:
            CurrEvent = self.Range[self._GetItemIndex(Row)]
            CurrClass = Data if Col == 3 else CurrEvent.Class 
            CurrName = Data if Col == 2 else CurrEvent.Name
            if CurrClass == CurrEvent.Class and CurrName == CurrEvent.Name:
                return
            print(CurrEvent, CurrName, CurrClass)
            with data.Database() as DB:
                data.Events(DB).SetRecordWithTimestamp(CurrEvent.Timestamp, CurrName, CurrClass)
            self.Range[self._GetItemIndex(Row)] = data.Events.Event(CurrEvent.Timestamp, CurrClass, CurrName)
            #self.SetItemCount(len(self.Range))
            self.Update()
            return Data
            #print(CurrEvent)

    def ClearHighlight(self, *args):
        if self.Highlight == None:
            Sels = self.GetFirstSelected()
            if Sels != -1:
                self.Select(Sels,0)

        #print(Sels)
        self.Highlight = None
        self.SetItemCount(len(self.Range))

    def AddCat(self, *args):
        #CatAddDiag(self).GetCategory()
        CatAddDiag(self).ShowModal()

    def DeleteEvent(self, Row):
        CurrEvent = self.Range[self._GetItemIndex(Row)]
        with data.Database() as DB:
            data.Events(DB).RemoveRecord(CurrEvent)
        del self.Range[self._GetItemIndex(Row)]
        self.SetItemCount(len(self.Range))

    def SelectNextEvent(self, Cat:data.Categories.Category):
        CurrSelInd = self.GetFirstSelected()+1
        print(self._GetItemIndex(CurrSelInd) + len(self.Range), len(self.Range))

        for i in range(CurrSelInd, len(self.Range)):
            Curr = self.Range[self._GetItemIndex(i)]
            if data.Events.MatchAgainstCategory(Curr, Cat):
                self.Select(i)
                self.EnsureVisible(i)
                return

    def SelectPrevEvent(self, Cat:data.Categories.Category):
        CurrSelInd = self.GetFirstSelected()-1
        print("PREV", CurrSelInd)

        for i in range(CurrSelInd, -CurrSelInd-3,-1):
            print(i)
            Curr = self.Range[self._GetItemIndex(i)]
            if data.Events.MatchAgainstCategory(Curr, Cat):
                if i < 0:
                    i = len(self.Range) + i
                print("EEE", i)
                self.Select(i)
                self.EnsureVisible(i)
                return

    def ShowRange(self, Begin:datetime.datetime, End:datetime.datetime):
        wx.BeginBusyCursor()
        with data.Database() as DB:
            #wx.BeginBusyCursor()
            EvObj = data.Events(DB)
            self.Range = EvObj.GetRange(Begin, End)
            self.LastTime = End
            #print(Begin.timestamp(), End.timestamp(), len(Range))
            if len(self.Range) == 0:
                wx.LogError("No records found")

            self.SetItemCount(len(self.Range))
        wx.EndBusyCursor()
        

    def ChangeTimestampDisplay(self, Mode: TSDisplayType, Fancy:bool):
        #wx.BeginBusyCursor()
        self.TimestampDisplayMode = (Mode, Fancy)
        self.SetItemCount(len(self.Range))
        #wx.EndBusyCursor()
            #SetObj.EventsDisplayType = self.TimestampDisplayMode[0]


class EventTreeEdit(wx.Panel):
    def OnTimeModeChange(self,*args):
        #frame.TreeEdit.ChangeTimestampDisplay(TSDisplayType.TIMEIN, False)
        TimeSel = self.TimestampModeW.GetSelection()
        if TimeSel < 0 or TimeSel > 2:
            wx.LogError("Invalid timestamp mode, no changes applied")
            return
        wx.Yield()
        with data.Database() as DB:
            SetObj = data.DBSettings2(DB)
            SetObj.EventsDisplayIsFancy = self.FancyModeW.GetValue()
            SetObj.EventsDisplayType = TimeSel
        self.ListCtrl.ChangeTimestampDisplay(TSDisplayType(TimeSel), self.FancyModeW.GetValue())

    def OnInputRange(self, evt):
        self.ListCtrl.ShowRange(self.EVRange.StartTime, self.EVRange.EndTime)

    def OnInputRangeFancy(self, evt):
        print(self.EVRangeFancy.StartDate, self.EVRangeFancy.EndDate)
        self.ListCtrl.ShowRange(self.EVRangeFancy.StartDate, self.EVRangeFancy.EndDate)
        pass

    def OnInputCatInput(self, evt):
        Mode = self.EVCatInput.GetMode()
        if Mode == EventCatInputMode.CUSTOM or Mode == EventCatInputMode.TREE:
            Cat = self.EVCatInput.GetCategory()
            self.ListCtrl.Highlight = Cat
            self.EVCatInput.NextBtn.Enable()
            self.EVCatInput.PrevBtn.Enable()
            self.EVCatInput.NextBtn.Bind(wx.EVT_BUTTON, lambda evt: self.ListCtrl.SelectNextEvent(Cat))
            self.EVCatInput.PrevBtn.Bind(wx.EVT_BUTTON, lambda evt: self.ListCtrl.SelectPrevEvent(Cat))
            self.ListCtrl.SelectNextEvent(Cat)
        elif Mode == EventCatInputMode.ALL:
            self.ListCtrl.Highlight = True
            self.EVCatInput.NextBtn.Disable()
            self.EVCatInput.PrevBtn.Disable()
        else:
            wx.LogError("Unknown CatInputMode %s".format(Mode))
        self.ListCtrl.SetItemCount(len(self.ListCtrl.Range))

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        self.parent = parent

        self.ListCtrl:EventTreeCtrl= EventTreeCtrl(self)
        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        # Date mode selectoir
        self.TesterSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.TimestampModeW = wx.Choice(self, choices=["DATE", "AGO", "SPENT"])
        self.TimestampModeW.SetSelection(0)
        self.TimestampModeW.Bind(wx.EVT_CHOICE, self.OnTimeModeChange)
        self.FancyModeW = wx.CheckBox(self, label="Fancy")
        self.FancyModeW.Bind(wx.EVT_CHECKBOX, self.OnTimeModeChange)
        #self.UpdateButtonW.Bind(wx.EVT_BUTTON, self.OnGo)

        self.Book = wx.Choicebook(self, style=wx.CHB_RIGHT)

        self.EVRange = EventRangeInput(self.Book)
        self.EVRange.UpdateButtonW.Bind(wx.EVT_BUTTON, self.OnInputRange)
        self.EVNow = EventJustNowInput(self.Book)
        self.EVRangeFancy = EventRangeInputFancy(self.Book)
        self.EVRangeFancy.UpdateButtonW.Bind(wx.EVT_BUTTON, self.OnInputRangeFancy)
        self.EVCatInput = EventCatInput(self.Book)
        self.EVCatInput.FindButton.Bind(wx.EVT_BUTTON, self.OnInputCatInput)

        self.Book.AddPage(self.EVNow, "Just Now", True)
        self.Book.AddPage(self.EVRangeFancy, "Range Fancy", False)
        self.Book.AddPage(self.EVRange, "Range", False)
        self.Book.AddPage(self.EVCatInput, "Find", False)
        #self.Book.Bind(wx.EVT_CHOICEBOOK_PAGE_CHANGED, self.OnBookChanging)

        self.TesterSizer.Add(self.TimestampModeW, 1, border=4, flag=wx.ALIGN_CENTER_VERTICAL|wx.LEFT)

        #self.FancyModeW = wx.CheckBox(self, label="Fancy")
        self.TesterSizer.Add(self.FancyModeW, 1, flag=wx.ALIGN_CENTER_VERTICAL|wx.LEFT)
        self.TesterSizer.AddStretchSpacer(2)
        self.TesterSizer.Add(self.Book, 1, border=4, flag=wx.EXPAND|wx.RIGHT)
        #self.TesterSizer.Add(self.UpdateButtonW, border=4, flag=wx.RIGHT|wx.EXPAND )

        self.Sizer.Add(self.TesterSizer, 0, border=4, flag=wx.BOTTOM|wx.TOP)
        self.Sizer.Add(self.ListCtrl, 1, wx.EXPAND)
        self.SetSizer(self.Sizer)

        with data.Database() as DB:
            SetObj = data.DBSettings2(DB)
            self.ListCtrl.TimestampDisplayMode= (TSDisplayType(SetObj.EventsDisplayType), SetObj.EventsDisplayIsFancy)
            self.TimestampModeW.SetSelection(SetObj.EventsDisplayType)
            self.FancyModeW.SetValue(SetObj.EventsDisplayIsFancy)


                  
class EventEditDialog(wx.Frame):	

    def __init__(self):
        super().__init__(parent=None, title="ActivityCross", size=wx.Size(755, 400))
        self.TreeEdit = EventTreeEdit(self)
        Toolbar:wx.ToolBar = self.CreateToolBar(style=wx.TB_BOTTOM)
        AddTool = Toolbar.AddTool(wx.ID_ANY, "New", wx.ArtProvider.GetBitmap(wx.ART_NEW, wx.ART_TOOLBAR))
        RemoveTool = Toolbar.AddTool(wx.ID_ANY, "Delete", wx.ArtProvider.GetBitmap(wx.ART_DELETE, wx.ART_TOOLBAR))
        DeselectTool = Toolbar.AddTool(wx.ID_ANY, "Deselect", wx.ArtProvider.GetBitmap(wx.ART_CROSS_MARK, wx.ART_TOOLBAR))
        self.Bind(wx.EVT_TOOL, self.TreeEdit.ListCtrl.AddCat, AddTool)
        self.Bind(wx.EVT_TOOL, lambda event: self.TreeEdit.ListCtrl.DeleteEvent(
            self.TreeEdit.ListCtrl.GetFirstSelected()
        ), RemoveTool)
        self.Bind(wx.EVT_TOOL, self._ClearEvent, DeselectTool)

        Toolbar.Realize()
        self.Show()

        
    def _ClearEvent(self, *args):
        self.TreeEdit.ListCtrl.ClearHighlight()
        if self.TreeEdit.EVCatInput.GetMode() == EventCatInputMode.TREE:
            self.TreeEdit.EVCatInput.SetMode(EventCatInputMode.ALL)


		#Sel = self.TreeEdit.DataViewControl.GetSelection()
		#if Sel.IsOk():
		#	Func(Event, self.TreeEdit.Model.ItemToObject(Sel))
		#elif AssumeRoot:
		#	Func(Event, self.TreeEdit.Model.ItemToObject(wxd.DataViewItem(1)))
			

##################
### STANDALONE ###
##################
	
if __name__ == '__main__':
    app = wx.App()
    frame = EventEditDialog()
    #wx.BeginBusyCursor()
    frame.TreeEdit.ListCtrl.ShowRange(datetime.datetime.now() - datetime.timedelta(days=100), datetime.datetime.now())
    #wx.EndBusyCursor()
    #frame.TreeEdit.ChangeTimestampDisplay(TSDisplayType.TIMEIN, False)
    #import wx.lib.inspection
    #wx.lib.inspection.InspectionTool().Show()

    app.MainLoop()
