""" 
Application: Maitenotas
Made by Taksan Tong
https://github.com/maitelab/maitenotas

Main launcher of the application """
import wx
from storage import createDatabase, verifyDatabasePassword, createBook, createJournal, getBookName
from storage import getJournalText, updateJournalText, updateJournalName, deleteJournal, getTreeLeafs

from crypto import generateUserKey

import os.path
from os import path

wxPythonIdCounter = 1000
newDatabase = False
userKey = b''
selectedJournalId=-1

def getNextWxPythonId():
    global wxPythonIdCounter
    wxPythonIdCounter = wxPythonIdCounter +1
    return wxPythonIdCounter

class MyTree(wx.TreeCtrl):
    
    def __init__(self, parent, id, pos, size, style):
        wx.TreeCtrl.__init__(self, parent, id, pos, size, style)
        
class TreePanel(wx.Panel):
    
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        
        # use global userKey generated during application startup
        global userKey
        
        # create tree
        self.tree = MyTree(self, getNextWxPythonId(), wx.DefaultPosition, wx.DefaultSize,
                           wx.TR_HAS_BUTTONS  | wx.TR_EDIT_LABELS)    
        
        # get book name, it will become the name of the tree in the user interface
        # for this first version, the bookId is always 2 (because bookId 1 is reserved)
        rootItem = self.tree.AddRoot(getBookName(userKey,2))
        leafDict = {}
        
        # read journal data, each journal entry will become a leaf in the user interface
        leafList = getTreeLeafs(userKey)
        for leaf in leafList:
            parentId = leaf[0]
            leafId = leaf[1]
            leafLabel = leaf[2]
            if parentId == 0:
                # parent is rootItem
                parentLeaf = rootItem
            else:
                # get parent leaf from dictionary
                parentLeaf = leafDict.get(parentId)
            # add new leaf to tree
            xItem = self.tree.AppendItem(parentLeaf, leafLabel)
            self.tree.SetItemData(xItem, leafId)
            # add new leaf to dictionary
            leafDict[leafId] = xItem

        # show tree
        self.tree.Expand(rootItem)
        
        sizer = wx.BoxSizer()
        sizer.Add(self.tree, 1, wx.EXPAND)
        
        self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_EVT_TREE_SEL_CHANGED)
        self.tree.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.on_EVT_TREE_END_LABEL_EDIT)
        
        
        self.SetSizerAndFit(sizer)

    def setTextControl(self, textControl):
        self.textControl = textControl
        
    def on_EVT_TREE_SEL_CHANGED(self, event):
        # before we continue... update the previously selected item
        # save current text before exit application
        global selectedJournalId
        global userKey
        if selectedJournalId>=1:
            textInScreen = self.textControl.GetValue()
            updateJournalText(userKey, selectedJournalId, textInScreen)
        
        # now continue changing the selected item
        item = event.GetItem()
        if item.IsOk():
            self.selectedItem = item
            itemData = self.tree.GetItemData(item)
            if itemData:
                print (itemData)
                # get journal text from leaf data (which is also the journal id in the database)
                journalText = getJournalText(userKey, itemData)
                self.textControl.SetValue(journalText)
                
                # set global journal id for future reference
                selectedJournalId = itemData
        event.Skip()
        
    def on_EVT_TREE_END_LABEL_EDIT(self, event):
        item = event.GetItem()
        if item.IsOk():
            newLabel = event.GetLabel()
            # print (self.tree.GetItemText(item))
            print (newLabel)
            # update label in database
            updateJournalName(userKey, self.tree.GetItemData(item), newLabel)
        event.Skip()
        
    def addLeaf(self):
        if self.selectedItem:
            # print (self.tree.GetItemData(self.selectedItem))
            
            # first add leaf in database because we need the new generated id
            # remember that in this version bookId is always 2
            parentLeafId = self.tree.GetItemData(self.selectedItem)
            newLeafId = createJournal(userKey, 2, parentLeafId, "hoja nueva", "")
            newLeaf = self.tree.AppendItem(self.selectedItem, "hoja nueva")
            self.tree.SetItemData(newLeaf, newLeafId)
            self.tree.Refresh()
            
    def removeLeaf(self):
        if self.selectedItem:
            leafId = self.tree.GetItemData(self.selectedItem)
            self.tree.Delete(self.selectedItem)
            # now also delete that leaf in database
            deleteJournal(leafId)
            self.tree.Refresh()
 
    def renameLeaf(self):
        if self.selectedItem:
            self.tree.EditLabel(self.selectedItem)
        
class MainPanel(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        
class TextPanel(wx.Panel):
    
        
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        
        self.textControl = wx.TextCtrl(self, -1,
                              "Bienvenido(a) a Maitenotas. En esta ventana aparecerán las notas de la hoja que elijas del árbol de la izquierda",
                              style=wx.TE_MULTILINE|wx.TE_PROCESS_ENTER)
        
        bsizer = wx.BoxSizer()
        bsizer.Add(self.textControl, 1, wx.EXPAND)
        self.SetSizerAndFit(bsizer)
        
    def getTextControl(self):
        return self.textControl
    
class MainFrame(wx.Frame):

    def __init__(self):
        wx.Frame.__init__(self, None, title="Maitenotas")

        # ask for user password
        userPassword = ""
        global userKey
        global newDatabase
        if newDatabase:
            # create db and set new password
            dlgPass1 = wx.TextEntryDialog(self, 'Defina una contraseña a usar','Nuevo diario') 
            
            if dlgPass1.ShowModal() == wx.ID_OK: 
                password1=dlgPass1.GetValue()
                dlgPass1.Destroy()
                
                # ask password confirmation
                dlg = wx.TextEntryDialog(self, 'Confirme contraseña a usar','Nuevo diario')
                if dlg.ShowModal() == wx.ID_OK:
                    password2=dlg.GetValue()
                    dlg.Destroy()
                    if password1 == password2:
                        userPassword = password1
                    else:
                        wx.MessageBox("Contraseñas no coinciden", "Error" ,wx.OK | wx.ICON_ERROR) 
                        self.Close()
                else:
                    dlg.Destroy()
                    self.Close() 
            else:
                dlgPass1.Destroy()
                self.Close() 
                
            # get name of first book
            dlgFirstBookName = wx.TextEntryDialog(self, 'Defina un nombre para el diario','Nombre inicial') 
            nameOfFirstBook=""
            if dlgFirstBookName.ShowModal() == wx.ID_OK: 
                nameOfFirstBook=dlgFirstBookName.GetValue()
                dlgFirstBookName.Destroy()
            else:
                dlgFirstBookName.Destroy()
                self.Close() 
                            
        else:
            # ask for password for existing database
            dlgPass = wx.TextEntryDialog(self, 'Ingrese contraseña','Abriendo diario') 
            
            if dlgPass.ShowModal() == wx.ID_OK: 
                userPassword=dlgPass.GetValue()
                dlgPass.Destroy()
            else:
                dlgPass.Destroy()
                self.Close()
                
        # verify database connection
        userKey = generateUserKey(userPassword)
        if newDatabase:
            databaseAccess = createDatabase(userKey, userPassword)
            if databaseAccess == False:
                wx.MessageBox("Error leyendo datos", "Error" ,wx.OK | wx.ICON_ERROR)
                self.Close()
            # create first book
            bookId = createBook(userKey, nameOfFirstBook)      
            # create example data to start, since the book is new the parentId leaf is ZERO
            journalName = "hoja 1 de " + nameOfFirstBook
            journalText = "texto ejemplo de hoja 1 de " + nameOfFirstBook
            createJournal(userKey, bookId, 0, journalName, journalText)
            journalName = "hoja 2 de " + nameOfFirstBook
            journalText = "texto ejemplo de hoja 2 de " + nameOfFirstBook
            createJournal(userKey, bookId, 0, journalName, journalText)
        else:
            databaseAccess = verifyDatabasePassword(userKey, userPassword)
            if databaseAccess == False:
                wx.MessageBox("Contraseña inválida", "Error" ,wx.OK | wx.ICON_ERROR)
                self.Close() 
        
        # create GUI Main panel and sub panels
        panel = MainPanel(self)
        boxSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.treePanel = TreePanel(panel)
        boxSizer.Add(self.treePanel, 1, wx.EXPAND | wx.ALL, 1)

        textPanel = TextPanel(panel)
        boxSizer.Add(textPanel, 2, wx.EXPAND | wx.ALL, 1)
        panel.SetSizer(boxSizer)
        
        # keep a reference to the text control inside the tree panel 
        # and inside the main panel also to access it later
        self.textControl = textPanel.getTextControl()
        self.treePanel.setTextControl(self.textControl)  
        
        # Show main panel
        self.Show()
        self.Maximize(True)
        
        # menus
        menubar = wx.MenuBar()
        
        # application menu
        applicationMenu = wx.Menu()
        wxPythonIDExit=getNextWxPythonId()
        wxIdAbout=getNextWxPythonId()
        
        menuItemAbout = wx.MenuItem(applicationMenu, wxIdAbout, '&Acerca de')
        applicationMenu.Append(menuItemAbout)
        self.Bind(wx.EVT_MENU, self.showAboutScreen, id=wxIdAbout)
        menuItemExit = wx.MenuItem(applicationMenu, wxPythonIDExit, '&Salir\tCtrl+Q')
        applicationMenu.Append(menuItemExit)
        self.Bind(wx.EVT_MENU, self.quitApplication, id=wxPythonIDExit)
        
        # tree menu
        treeMenu = wx.Menu()
        wxPythonID1=getNextWxPythonId()
        wxPythonID2=getNextWxPythonId()
        wxPythonID3=getNextWxPythonId()
        menuItemAddLeaf = wx.MenuItem(treeMenu, wxPythonID1, '&Agregar hoja\tCtrl+A')
        menuItemRemoveLeaf = wx.MenuItem(treeMenu, wxPythonID2, '&Remover hoja\tCtrl+D')
        menuItemRenameLeaf = wx.MenuItem(treeMenu, wxPythonID3, '&Renombrar hoja\tCtrl+R')
        treeMenu.Append(menuItemAddLeaf)
        treeMenu.Append(menuItemRemoveLeaf)
        treeMenu.Append(menuItemRenameLeaf)
        
        self.Bind(wx.EVT_MENU, self.addLeaf, id=wxPythonID1)
        self.Bind(wx.EVT_MENU, self.removeLeaf, id=wxPythonID2)
        self.Bind(wx.EVT_MENU, self.renameLeaf, id=wxPythonID3)

        menubar.Append(applicationMenu, '&Aplicación')
        menubar.Append(treeMenu, '&Arbol')
        self.SetMenuBar(menubar)
        
        # window close event
        self.Bind(wx.EVT_CLOSE, self.closeWindow)
        
    def quitApplication(self, e):
        self.Close()
        
    def closeWindow(self, e):
        # save current text before exit application
        global selectedJournalId
        global userKey
        if selectedJournalId>=1:
            textInScreen = self.textControl.GetValue()
            updateJournalText(userKey, selectedJournalId, textInScreen)
        print("goodbye!")
        self.Destroy()
            
    def addLeaf(self, e):
        self.treePanel.addLeaf()

    def removeLeaf(self, e):
        self.treePanel.removeLeaf()
        
    def renameLeaf(self, e):
        self.treePanel.renameLeaf()
        
    def showAboutScreen(self, e):
        wx.MessageBox("Maitenotas versión 1\nProgramada por Taksan Tong\nPara uso libre y personal. Prohibido su venta o uso comercial\nCódigo fuente disponible\ntaksantong@gmail.com", "Acerca de" ,wx.OK | wx.ICON_INFORMATION)
           
if __name__ == "__main__":
    """ application main entry point function """
    
    # check if database exists
    if path.exists("maitenotas.data") == False:
        newDatabase = True
    
    app = wx.App(False)
    frame = MainFrame()
    app.MainLoop()
