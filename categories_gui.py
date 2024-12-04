#!/usr/bin/python3
import datetime
import functools
from pprint import pp
import wx
import wx.dataview as wxd
from wx.lib import colourutils
import data
from time import perf_counter,sleep

##############
### MODELS ###
##############

#class _ChoiceRenderer(wxd.DataViewCustomRenderer):
#    def __init__(self, parent, listctrl:wxd.DataViewCtrl, choices, *args, **kw):
#        wxd.DataViewCustomRenderer.__init__(self, *args, **kw)
#        self.listctrl = listctrl
#        self.parent = parent
#        self.Choices = choices
#        self.ControlNameList = []
#
#    def SetValue(self, value):
#        self.value = int(value)
#        return True
#    def GetValue(self):
#        print(self.CurElm)
#        return str(self.value)
#    def GetSize(self):
#        return wx.Size(200, 30)
#    def Render(self, cell:wx.Rect, dc:wx.DC, state):
#        self.CellHeight = cell.height
#        if not hasattr(self,str(cell.y)):
#            TmpR = wx.Choice(self.parent, choices=self.Choices)
#            TmpR.__setattr__("Row", cell.Position.y // self.CellHeight)
#            TmpR.Bind(wx.EVT_CHOICE, self.OnChoice)
#            self.__setattr__(str(cell.y), TmpR)
#            self.ControlNameList.append(str(cell.y))
#        self.CurElm:wx.Choice = self.__getattribute__(str(cell.y))
#        self.CurElm.Show()
#        self.CurElm.SetSelection(self.value)
#        self.CurElm.Position = wx.Point(cell.Position.x+1, cell.Position.y+self.listctrl.Position.y+cell.height-3)
#        self.CurElm.SetSize(cell.width, cell.height)
#        return True
#
#    def OnChoice(self,evt):
#       print("ONCHOICE", evt.GetEventObject().Row)
#    def UnRender(self):
#        for e in self.ControlNameList:
#            self.__getattribute__(e).Hide()
#    def HasEditorCtrl(self):
#        return False
#
#self.Bind(wxd.EVT_DATAVIEW_ITEM_COLLAPSED, self.OnCollapsed)
#def OnCollapsed(self, evt):


class _ChoiceRenderer(wxd.DataViewCustomRenderer):
    def __init__(self, parent, choices, *args, **kw):
        wxd.DataViewCustomRenderer.__init__(self, *args, **kw)
        self.value = None
        self.parent = parent
        self.Choices = choices
        self.SelectedIndex = 0
        #print(self.GetView())

    def SetValue(self, value):
        self.value = int(value)
        return True
    def GetValue(self):
        return str(self.value)
    def GetSize(self):
        return self.GetTextExtent(max(self.Choices, key=len))
    def Render(self, cell:wx.Rect, dc:wx.DC, state):
        self.RenderText(self.Choices[self.value],
                        0,
                        cell,
                        dc,
                        state)
        return True

    def HasEditorCtrl(self):
        return True

    def CreateEditorCtrl(self, parent, labelRect, value):
        #print(labelRect)
        Return=wx.Choice(parent,
                              choices=self.Choices,
                              #pos=wx.Point(labelRect.Position.x, labelRect.Position.y + labelRect.Size.y + 5),
                              pos=labelRect.Position,
                              size=labelRect.Size)
        Return.SetSelection(self.SelectedIndex)
        return Return

    def GetValueFromEditorCtrl(self, editor:wx.Choice):
        self.SelectedIndex = editor.GetCurrentSelection()
        #print(self.SelectedIndex)
        return str(self.SelectedIndex)

class _ColorRenderer(wxd.DataViewCustomRenderer):
    def __init__(self, parent, *args, **kw):
        wxd.DataViewCustomRenderer.__init__(self, *args, **kw)
        self.value = None
        self.parent = parent

    @staticmethod
    def _GetStrValue(val:wx.Colour):
        Ret = ",".join([str(val.GetRed()), str(val.GetGreen()), str(val.GetBlue())])
        #print(Ret)
        return Ret
    @staticmethod
    def _GetColorValue(val: str) -> wx.Colour:
        TupleValue = val.split(",") if val else None
        if TupleValue != None:
            return wx.Colour(int(TupleValue[0]), int(TupleValue[1]), int(TupleValue[2]))
        return wx.Colour(100,100,100)


    def SetValue(self, value):
        self.value = _ColorRenderer._GetColorValue(value)
        return True

    def GetValue(self):
        return _ColorRenderer._GetStrValue(self.value)


    def GetSize(self):
        # Return the size needed to display the value.  The renderer
        # has a helper function we can use for measuring text that is
        # aware of any custom attributes that may have been set for
        # this item.
        size = self.GetTextExtent(self._GetStrValue(self.value))
        return size

    def Render(self, cell:wx.Rect, dc:wx.DC, state):
        if self.value != None:
            Col = wx.Colour(self.value[0], self.value[1], self.value[2])
            dc.SetTextForeground(Col)
        dc.SetFont(wx.Font(wx.FontInfo().Bold()))
        dc.DrawText(self._GetStrValue(self.value), cell.x, cell.y)
        return True

    # The HasEditorCtrl, CreateEditorCtrl and GetValueFromEditorCtrl
    # methods need to be implemented if this renderer is going to
    # support in-place editing of the cell value, otherwise they can
    # be omitted.
    def HasEditorCtrl(self):
        return True

    def CreateEditorCtrl(self, parent, labelRect, value):
        #print(labelRect)
        DiagColor = wx.WHITE
        if self.value != None:
            DiagColor = wx.Colour(self.value[0], self.value[1], self.value[2])

        self.ctrl = wx.ColourPickerCtrl(parent, 
                                   colour=DiagColor,
                                   pos=labelRect.Position,
                                   size=labelRect.Size)
        Pickme = self.ctrl.GetPickerCtrl()
        #evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId, self.ctrl.GetId())
        #wx.PostEvent(self.ctrl, evt)
        return self.ctrl

    def GetValueFromEditorCtrl(self, editor:wx.ColourPickerCtrl):
        self.value = editor.GetColour()
        return (int(self.value.GetRed()), int(self.value.GetGreen()), int(self.value.GetBlue()))

class _CategoryModel(wxd.PyDataViewModel):

    def __init__(self):
        self.Mapper = {}
        super().__init__()

    def ItemToObject(self, item):
        return self.Mapper[int(item.GetID())]

    def ObjectToItem(self, obj: data.Categories.CategoryRef):
        self.Mapper[obj.CatID] = obj
        return wxd.DataViewItem(obj.CatID)

    def GetColumnCount(self):
        return 7
    def HasContainerColumns(self, item):
        return True

    # How we do Performance™ to stop the gui from raping our disk
    # TODO: Find better way, apparently causes memory leaks but its handed over
    # to wxwidget memory management so too scared to touch
    # Why does wxpython have to call these functions hundreds of times anyways
    @functools.cache
    def GetChildren(self, item, children):
        with data.Database() as Db:
            CatObj = data.Categories(Db)
            if item.IsOk():
                ChildrenList = list(CatObj.GetChildren(self.ItemToObject(item)))
                for i in ChildrenList:
                    children.append(self.ObjectToItem(i))
                return len(ChildrenList)
            else:
                Ret = CatObj.GetRootNode()
                children.append(self.ObjectToItem(Ret))
                return 1

    @functools.cache
    def IsContainer(self, item):
        #print("ISCOTAINER")
        #return True
        if not item.IsOk():
            return True
        with data.Database() as Db:
            CatObj = data.Categories(Db)
            for i in CatObj.GetChildren(self.ItemToObject(item)):
                return True
            return False

    @functools.cache
    def GetParent(self, item):
        #print("GETPARENT")
        Node = self.ItemToObject(item)
        with data.Database() as Db:
            CatObj = data.Categories(Db)
            PNode = CatObj.GetParent(Node)
            if PNode == None:
                return wxd.DataViewItem(None)
            return self.ObjectToItem(PNode)

    @functools.cache
    def GetValue(self, item, col):
        #print("GETVALUE")
        with data.Database() as Db:
            CatObj = data.Categories(Db)
            NuCategoryRef = self.ItemToObject(item)
            if NuCategoryRef == None:
                wx.LogWarning(f"CatID {item.GetID()} found in CategoryModelTable not in database")
                return "ERR"
            else:
                NuCategory: data.Categories.Category = NuCategoryRef.Category
                Mapper = {
                    0: lambda: str(NuCategory.Name),
                    1: lambda: str(NuCategory.Pattern),
                    2: lambda: str(NuCategory.MatchingMode.value),
                    3: lambda: str(NuCategory.MatchingTarget.value),
                    # Serialize color into a string for deserilization in custom renderer
                    # Wxpython wont allow me to change the expected type of my renderers
                    # for some reason
                    4: lambda: ",".join([str(i) for i in NuCategory._Color]),
                    5: lambda: NuCategory._Lowercase == 1,
                    6: lambda: NuCategory._Cascade == 1,
                    7: lambda: str(NuCategoryRef.CatID)
                }

                # TODO: Get rid of this ugly hack
                if col == 2 and type(NuCategory.MatchingMode) == int:
                    #return str(NuCategory.MatchingMode)
                    Mapper[2] = lambda: str(NuCategory.MatchingMode)
                if col == 3 and type(NuCategory.MatchingTarget) == int:
                    #return str(NuCategory.MatchingTarget)
                    Mapper[3] = lambda: str(NuCategory.MatchingTarget)
                #print(Mapper[col]())
                return Mapper[col]()

    def GetAttr(self, item, col, attr):
        if (not item.IsOk() or int(item.GetID()) == 1) and (col == 1 or col == 2 or col == 3 or col == 7):
            attr.SetColour(wx.Colour(100,100,100))
            attr.SetBold(False)
            attr.SetItalic(True)
            return True
        return False

    #@functools.cache
    def SetValue(self, value, item, col):
        # We're not allowing edits in column zero (see below) so we just need
        # to deal with Song objects and cols 1 - 5
        #print("UWWWAAAA", value)
        Node = self.ItemToObject(item)
        if Node.CatID == 1 and col != 4 and col != 5 and col != 6:
            return False

        with data.Database() as Db:
            CatObj = data.Categories(Db)
            if col == 0:
                CatObj.CategoryRefSetItem(Node, "Name", value)
            elif col == 1:
                #print("UWUW")
                CatObj.CategoryRefSetItem(Node, "Pattern", value)
            elif col == 2:
                CatObj.CategoryRefSetItem(Node, "MatchingMode", data.EMatchingMode(int(value)).value)
            elif col == 3:
                CatObj.CategoryRefSetItem(Node, "MatchingTarget", data.EMatchingTarget(int(value)).value)
            elif col == 4:
                CatObj.CategoryRefSetItem(Node, "_Color", value)
            elif col == 5:
                print(col, value)
                CatObj.CategoryRefSetItem(Node, "_Lowercase", value)
            elif col == 6:
                CatObj.CategoryRefSetItem(Node, "_Cascade", value)
            self.GetValue.cache_clear()
            return True

#################
### BUISENESS ###
#################

class CategoryTreeEdit(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        Start = perf_counter()

        #self.SetDoubleBuffered(False)

        #################
        ### DATA VIEW ###
        #################
        self.DataViewControl = wxd.DataViewCtrl(self,
                                   style=wx.BORDER_THEME
                                   #| wxd.DV_ROW_LINES # nice alternating bg colors
                                   | wxd.DV_HORIZ_RULES
                                   | wxd.DV_VERT_RULES
                                   )
        self.DataViewControl.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.DataViewControl.Bind(wx.EVT_LEFT_DOWN, self.LeftHandler)
        self.parent = parent

        ##with data.Database() as Db:
        ##    CatObj = data.Categories(Db)
        ##    self.NewCat = data.Categories.Category("Test12", data.EMatchingMode.ALWAYS, data.EMatchingTarget.CLASS, "UWU")
        ##    self.RootNode = CatObj.GetRootNode()
        ##    self.NewCat = CatObj.AddCategory(self.RootNode, self.NewCat)
        ##    CatObj.AddCategory(self.NewCat, data.Categories.Category("Test13", data.EMatchingMode.ALWAYS, data.EMatchingTarget.CLASS, "UWU"))

        self.Model:_CategoryModel = _CategoryModel()
        self.DataViewControl.AssociateModel(self.Model)

        C0 = self.DataViewControl.AppendTextColumn("Name", 0, mode=wxd.DATAVIEW_CELL_EDITABLE, width=125)
        C7 = self.DataViewControl.AppendTextColumn("ID", 7, align=wx.ALIGN_CENTER)
        C1 = self.DataViewControl.AppendTextColumn("Pattern", 1, mode=wxd.DATAVIEW_CELL_EDITABLE, width=150)

        #self.C3Renderer = _ChoiceRenderer(self, self.DataViewControl,["ALWAYS","PREFIX", "EXACT", "REGEX", "SUBSTR", "SUFFIX"] , mode=wxd.DATAVIEW_CELL_EDITABLE)
        self.C3Renderer = _ChoiceRenderer(self, ["ALWAYS","PREFIX", "EXACT", "REGEX", "SUBSTR", "SUFFIX"] , mode=wxd.DATAVIEW_CELL_EDITABLE)
        C3 = wxd.DataViewColumn("Mode", self.C3Renderer, 2, width=75)
        self.DataViewControl.AppendColumn(C3)
        #self.C2Renderer = _ChoiceRenderer(self, self.DataViewControl,["CLASS", "TITLE", "CLASS+TITLE"],mode=wxd.DATAVIEW_CELL_EDITABLE)
        self.C2Renderer = _ChoiceRenderer(self, ["CLASS", "TITLE", "CLASS+TITLE"],mode=wxd.DATAVIEW_CELL_EDITABLE)
        C2 = wxd.DataViewColumn("Target", self.C2Renderer, 3, width=100)
        self.DataViewControl.AppendColumn(C2)

        

        C4Renderer = _ColorRenderer(self, mode=wxd.DATAVIEW_CELL_EDITABLE)
        C4 = wxd.DataViewColumn("Color", C4Renderer, 4)
        self.DataViewControl.AppendColumn(C4)
        C5 = self.DataViewControl.AppendToggleColumn("Lowercase", 5, width=85, mode=wxd.DATAVIEW_CELL_ACTIVATABLE, flags=0)
        C6 = self.DataViewControl.AppendToggleColumn("Cascade", 6, width=85, mode=wxd.DATAVIEW_CELL_ACTIVATABLE, flags=0)

        #self.DataViewControl.ExpandChildren(wxd.DataViewItem(0))

        ###############
        #### TESTER ###
        ###############
        self.TesterSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.ClassInput = wx.TextCtrl(self)
        self.TitleInput = wx.TextCtrl(self)
        SubmitBut = wx.Button(self, wx.ID_FIND)
        SubmitBut.Bind(wx.EVT_BUTTON, self.TesterSubmit)
        SubmitBut.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_FIND))
        #SubmitBut.SetBackgroundColour(wx.NamedColour("steel blue"))
        


        #self.TesterSizer.Add(wx.Button(self, -1, "E"), 0,0,0)
        self.TesterSizer.Add(wx.StaticText(self, label="Title:"), 1, border=8, flag=wx.ALIGN_CENTER_VERTICAL|wx.LEFT)
        self.TesterSizer.Add(self.TitleInput, 6)
        self.TesterSizer.Add(wx.StaticText(self, label="Class:"), 1, border=8, flag=wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT)
        self.TesterSizer.Add(self.ClassInput, 6)
        self.TesterSizer.AddSpacer(wx.LEFT)
        self.TesterSizer.Add(SubmitBut, 1, border=8, flag=wx.RIGHT)
        self.DataViewControl.SetFocus()

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.TesterSizer, 0, border=4, flag=wx.BOTTOM|wx.TOP)
        self.Sizer.Add(self.DataViewControl, 1, wx.EXPAND)

        with data.Database() as DB:
            #LastEvent = data.Events(DB).GetLastEvent()
            #if LastEvent != None:
            Res = DB.execute("SELECT * FROM Events WHERE Name != 'ActivityCross' ORDER BY Timestamp DESC LIMIT 1;")
            ResL = Res.fetchone()
            if ResL != None:
                ResEvent = data.Events.Event.FromSQL(ResL)
                self.TitleInput.SetHint(ResEvent.Name)
                self.ClassInput.SetHint(ResEvent.Class)
            #Res = self.con.execute("SELECT * FROM Events")
            #print(ResL)
        #wx.CallAfter(self.TestSleep)
        #print(wx.GetApp().HasPendingEvents(), wx.GetApp().Yield())

        #wx.CallAfter(SubmitBut.SetBitmap)


        #if wx.GetApp().HasPendingEvents():
        #    print("PROCESSING PENDING CEVENTS")
        #    wx.GetApp().ProcessPendingEvents()
        #sleep(1)
        #wx.GetApp().Yield(onlyIfNeeded=True)

        #wx.CallAfter(self.DataViewControl.ExpandChildren, wxd.DataViewItem(1))
        self.DataViewControl.ExpandChildren(wxd.DataViewItem(1))

        #print("UWU")

        #print("PENDING", wx.GetApp().HasPendingEvents())
        #i = 0
        #while wx.GetApp().HasPendingEvents():
        #    print("PRC", i)
        #    wx.Yield()
        #    i+=1
        #print(wx.GetApp().HasPendingEvents())


        #wx.CallAfter(lambda: self.DataViewControl.ExpandChildren(wxd.DataViewItem(1)))

        # Note to self, GetBitmap is REALLY fuckin slow in the grand scheme of things
        #wx.Yield()
        #self.Show()
        #wx.CallAfter(self.TestSleep)
        #self.DataViewControl.Bind(wx.EVT_IDLE, self.TestSleep)
        #wx.FutureCall(10, self.TestSleep)
        #print("TEST")

        print(perf_counter() - Start)

            
        #wx.Yield()
        #for i in range(10):
        #    print(i)
        #    wx.Yield()
        #    sleep(0.1)
            
        #pass
        #print(args)


    def TesterSubmit(self, event):
        CIVal = self.ClassInput.GetValue()
        TiVal = self.TitleInput.GetValue()

        if CIVal == "" and TiVal == "":
            self.ClassInput.SetValue(self.ClassInput.GetHint())
            self.TitleInput.SetValue(self.TitleInput.GetHint())
        with data.Database() as DB:
            CatObj = data.Categories(DB)
            #EvObj = data.Events(DB)
            Res = data.PyCategorize(data.Events.Event(datetime.datetime.now(), 
                                                      self.ClassInput.GetValue(), 
                                                      self.TitleInput.GetValue()), 
                                                      CatObj.RenderTree(CatObj.GetRootNode()))
            #self.LastCat = None
            self.DataViewControl.UnselectAll()
            for i in Res:
                Cat = i[0]
                self.DataViewControl.Select(wxd.DataViewItem(Cat.CatID))
                #pp(i[1])


    ###########################
    ### CONTEXT MENU STUFFS ###
    ###########################

    def OnContextMenu(self, event):

        #print()
        
        # TODO: Fix this hackiness, why does it keep giving results that are one row off?
        # me thinks something to do with the header bar
        Pos:wx.Point = event.GetPosition()
        RowHeight = self.DataViewControl.GetItemRect(wxd.DataViewItem(1)).Height
        ClientPos = self.ScreenToClient(Pos.x, Pos.y)
        ClientPos = (ClientPos[0], ClientPos[1] + RowHeight)
        Item = self.DataViewControl.GetSelection()
        if not Item:
            HitTestRes = self.DataViewControl.HitTest(ClientPos)
            if HitTestRes[0].IsOk():
                Item = self.Model.ItemToObject(HitTestRes[0])
            else:
                Item = self.Model.ItemToObject(self.DataViewControl.GetTopItem())
        else:
            Item = self.Model.ItemToObject(Item)
        #print(Item)
        Menu = wx.Menu()
        #Menu.Append(wx.ID_ANY, Item.Category.Name)
        self.Bind(wx.EVT_MENU, lambda event: self.AddCat(event, Item), 
                  Menu.Append(wx.ID_ADD, "Add Category (Below)"))
        DeleteItem:wx.MenuItem= Menu.Append(wx.ID_DELETE, "Delete Category")
        if Item.CatID == 1:
            Menu.Enable(DeleteItem.Id, False)
        self.Bind(wx.EVT_MENU, lambda event: self.RemCat(event, Item), DeleteItem)

        self.Bind(wx.EVT_MENU, self.ExpandAll, Menu.Append(wx.ID_ANY, "Expand All"))
        self.Bind(wx.EVT_MENU, self.CollapseAll, Menu.Append(wx.ID_ANY, "Collapse All"))
        self.Bind(wx.EVT_MENU, lambda a: self.DataViewControl.UnselectAll(), Menu.Append(wx.ID_CLEAR, "Unselect All"))
        self.Bind(wx.EVT_MENU, self.Reload, Menu.Append(wx.ID_REFRESH, "Reload"))
        #Menu.Append(wx.ID_DELETE, "Remove Category")
        self.PopupMenu(Menu)
        #print(Item, ClientPos)
        del Menu
        #print(Pos, , self.DataViewControl.HitTest(Pos), event.GetEventObject())
        #print(self.Model.ItemToObject(self.DataViewControl.HitTest(ClientPos)[0]))

    # Deselect if cliecked on empty area
    def LeftHandler(self, event):
        ClientPos:wx.Point = event.GetPosition()
        RowHeight = self.DataViewControl.GetItemRect(wxd.DataViewItem(1)).Height
        ClientPos = wx.Point(ClientPos.x, ClientPos.y + RowHeight)
        #ClientPos = self.ScreenToClient(Pos.x, Pos.y)
        #ClientPos = (ClientPos[0], ClientPos[1] + RowHeight)
        #print(ClientPos)
        HitTestRes = self.DataViewControl.HitTest(ClientPos)
        if not HitTestRes[0].IsOk():
            self.DataViewControl.UnselectAll()

    # Add a new cateogry callback
    def AddCat(self,event, Item):
        #print()
        #print(Item)
        #myCursor= 
        #self.SetCursor(wx.StockCursor(wx.CURSOR_WAIT))
        with data.Database() as DB:
            CatObj = data.Categories(DB)
            Ret = CatObj.AddCategory(Item, data.Categories.DefaultCategory)
            self.Model.GetChildren.cache_clear()
            self.Model.GetParent.cache_clear()
            self.Model.IsContainer.cache_clear()
            self.Model.Cleared()
            self.DataViewControl.ExpandChildren(wxd.DataViewItem(1))
            self.DataViewControl.EnsureVisible(wxd.DataViewItem(Ret.CatID))
            #self.DataViewControl.Select(wxd.DataViewItem(Ret.CatID))
            #self.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
            #self.Model.ItemAdded(HitItem, self.Model.ObjectToItem(Ret))
            #self.DataViewControl.ExpandAncestors(wxd.DataViewItem(Ret.CatID))

    # Remove a cateogry callback
    def RemCat(self,event, Item):
        with data.Database() as DB:
            CatObj = data.Categories(DB)
            ParentItem = CatObj.GetParent(Item)
            if any(True for _ in CatObj.GetChildren(Item)):
                if wx.MessageDialog(self, 
                                    "This item has one or more children, are you sure you want to delete?", 
                                    style=wx.YES_NO).ShowModal() == wx.ID_NO:
                    return
            CatObj.DeleteSubtree(Item, True)
            self.Model.GetChildren.cache_clear()
            self.Model.GetParent.cache_clear()
            self.Model.IsContainer.cache_clear()
            self.Model.Cleared()
            self.DataViewControl.ExpandChildren(wxd.DataViewItem(1))
            if ParentItem != None:
                #self.DataViewControl.EnsureVisible(wxd.DataViewItem(ParentItem.CatID))
                for i in CatObj.GetChildren(ParentItem):
                    NextChild=wxd.DataViewItem(i.CatID)
                    #self.DataViewControl.EnsureVisible(NextChild)
                    self.DataViewControl.Select(NextChild)
                    break
            pass

    def ExpandAll(self, event):
        self.DataViewControl.ExpandChildren(wxd.DataViewItem(1))
    def CollapseAll(self, event):
        self.DataViewControl.Collapse(wxd.DataViewItem(1))
    def Reload(self, event):
        self.Model.GetChildren.cache_clear()
        self.Model.GetParent.cache_clear()
        self.Model.IsContainer.cache_clear()
        self.Model.Cleared()
        self.DataViewControl.ExpandChildren(wxd.DataViewItem(1))


class CategoryEditDialog(wx.Frame):    
    def __init__(self):
        super().__init__(parent=None, title="ActivityCross", size=wx.Size(735, 400))
        self.TreeEdit:CategoryTreeEdit = CategoryTreeEdit(self)
        Toolbar:wx.ToolBar = self.CreateToolBar(style=wx.TB_BOTTOM)
        AddTool = Toolbar.AddTool(wx.ID_ANY, "New", wx.ArtProvider.GetBitmap(wx.ART_NEW, wx.ART_TOOLBAR))
        RemoveTool = Toolbar.AddTool(wx.ID_ANY, "Delete", wx.ArtProvider.GetBitmap(wx.ART_DELETE, wx.ART_TOOLBAR))
        DeselectTool = Toolbar.AddTool(wx.ID_CLEAR, "Deselect", wx.ArtProvider.GetBitmap(wx.ART_CROSS_MARK, wx.ART_TOOLBAR))
        self.Bind(wx.EVT_TOOL, lambda event: self._GetItem(event, self.TreeEdit.AddCat, True), AddTool)
        self.Bind(wx.EVT_TOOL, lambda event: self._GetItem(event, self.TreeEdit.RemCat), RemoveTool)
        self.Bind(wx.EVT_TOOL, lambda event: self.TreeEdit.DataViewControl.UnselectAll(), DeselectTool)
        
        Toolbar.Realize()
        self.Show()


    def _GetItem(self, Event, Func, AssumeRoot=False):
        Sel = self.TreeEdit.DataViewControl.GetSelection()
        if Sel.IsOk():
            Func(Event, self.TreeEdit.Model.ItemToObject(Sel))
        elif AssumeRoot:
            Func(Event, self.TreeEdit.Model.ItemToObject(wxd.DataViewItem(1)))
            
        

##################
### STANDALONE ###
##################

if __name__ == '__main__':
    app = wx.App()
    frame = CategoryEditDialog()
    #import wx.lib.inspection
    #wx.lib.inspection.InspectionTool().Show()

    app.MainLoop()
