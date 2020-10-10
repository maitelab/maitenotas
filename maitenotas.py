"""
Application: Maitenotas
Made by Taksan Tong
https://github.com/maitelab/maitenotas

Main launcher of the application
"""
from os import path

import wx

from storage import update_journal_text, update_journal_name, delete_journal, get_book_name,\
    get_journal_text, get_tree_leafs, create_book, create_database, verify_database_password,\
    create_journal
from crypto import generate_user_key
import text_labels

class ApplicationData:
    """Class to hold values needed at the application level"""
    def __init__(self):
        self.wx_id_counter = 1000
        self.new_database = False
        self.user_key = b''
        self.selected_journal_id = -1

    def get_next_wx_python_id(self) -> int:
        """get next wx id for GUI elements"""
        self.wx_id_counter = self.wx_id_counter +1
        return self.wx_id_counter

    def get_new_database(self) -> bool:
        """get flag for new database"""
        return self.new_database

    def set_new_database(self, new_value: bool) -> None:
        """set flag for new database"""
        self.new_database = new_value

    def get_user_key(self) -> bytes:
        """get user key"""
        return self.user_key

    def set_user_key(self, new_value: bytes) -> None:
        """set user key"""
        self.user_key = new_value

    def get_selected_journal_id(self) -> int:
        """get selected journal id"""
        return self.selected_journal_id

    def set_selected_journal_id(self, new_value: int) -> None:
        """set selected journal id"""
        self.selected_journal_id = new_value

app_data = ApplicationData()

class MyTree(wx.TreeCtrl):
    """tree class"""
    def __init__(self, parent, tid, pos, size, style):
        wx.TreeCtrl.__init__(self, parent, tid, pos, size, style)

class TreePanel(wx.Panel):
    """tree panel class"""
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        # create tree
        self.tree = MyTree(self, app_data.get_next_wx_python_id(), wx.DefaultPosition,
                           wx.DefaultSize,
                           wx.TR_HAS_BUTTONS  | wx.TR_EDIT_LABELS)

        # get book name, it will become the name of the tree in the user interface
        # for this first version, the bookId is always 2 (because bookId 1 is reserved)
        root_item = self.tree.AddRoot(get_book_name(app_data.get_user_key(),2))
        leaf_dict = {}

        # read journal data, each journal entry will become a leaf in the user interface
        leaf_list = get_tree_leafs(app_data.get_user_key())
        for leaf in leaf_list:
            parent_id = leaf[0]
            leaf_id = leaf[1]
            leaf_label = leaf[2]
            if parent_id == 0:
                # parent is rootItem
                parent_leaf = root_item
            else:
                # get parent leaf from dictionary
                parent_leaf = leaf_dict.get(parent_id)
            # add new leaf to tree
            x_item = self.tree.AppendItem(parent_leaf, leaf_label)
            self.tree.SetItemData(x_item, leaf_id)
            # add new leaf to dictionary
            leaf_dict[leaf_id] = x_item

        # show tree
        self.tree.Expand(root_item)

        sizer = wx.BoxSizer()
        sizer.Add(self.tree, 1, wx.EXPAND)

        self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_evt_tree_sel_changed)
        self.tree.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.on_evt_tree_end_label_edit)
        self.SetSizerAndFit(sizer)
        self.text_control = None
        self.selected_item = -1

    def set_text_control(self, text_control):
        """set text control"""
        self.text_control = text_control

    def on_evt_tree_sel_changed(self, event):
        """event when a tree selection changes"""
        # before we continue... update the previously selected item
        # save current text before exit application
        if app_data.get_selected_journal_id()>=1:
            text_in_screen = self.text_control.GetValue()
            update_journal_text(app_data.get_user_key(), app_data.get_selected_journal_id(),
                                text_in_screen)
        # now continue changing the selected item
        item = event.GetItem()
        if item.IsOk():
            self.selected_item = item
            item_data = self.tree.GetItemData(item)
            if item_data:
                print (item_data)
                # get journal text from leaf data (which is also the journal id in the database)
                journal_text = get_journal_text(app_data.get_user_key(), item_data)
                self.text_control.SetValue(journal_text)
                # set global journal id for future reference
                app_data.set_selected_journal_id(item_data)
        event.Skip()

    def on_evt_tree_end_label_edit(self, event):
        """event when a tree edit occurs"""
        item = event.GetItem()
        if item.IsOk():
            new_label = event.GetLabel()
            # print (self.tree.GetItemText(item))
            print (new_label)
            # update label in database
            update_journal_name(app_data.get_user_key(), self.tree.GetItemData(item), new_label)
        event.Skip()

    def add_leaf(self):
        """add leaf to tree"""
        if self.selected_item:
            # first add leaf in database because we need the new generated id
            # remember that in this version bookId is always 2
            parent_leaf_id = self.tree.GetItemData(self.selected_item)
            new_leaf_id = create_journal(app_data.get_user_key(), 2, parent_leaf_id,
                                         text_labels.NEW_LEAF, "")
            new_leaf = self.tree.AppendItem(self.selected_item, text_labels.NEW_LEAF)
            self.tree.SetItemData(new_leaf, new_leaf_id)
            self.tree.Refresh()

    def remove_leaf(self):
        """remove leaf from tree"""
        if self.selected_item:
            leaf_id = self.tree.GetItemData(self.selected_item)
            self.tree.Delete(self.selected_item)
            # now also delete that leaf in database
            delete_journal(leaf_id)
            self.tree.Refresh()

    def rename_leaf(self):
        """rename leaf"""
        if self.selected_item:
            self.tree.EditLabel(self.selected_item)

class MainPanel(wx.Panel):
    """main panel class"""
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

class TextPanel(wx.Panel):
    """tree panel"""
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self.text_control = wx.TextCtrl(self, -1,
                              text_labels.WELCOME,
                              style=wx.TE_MULTILINE|wx.TE_PROCESS_ENTER)

        bsizer = wx.BoxSizer()
        bsizer.Add(self.text_control, 1, wx.EXPAND)
        self.SetSizerAndFit(bsizer)

    def get_text_control(self):
        """get text control"""
        return self.text_control

class MainFrame(wx.Frame):
    """main frame"""
    def __init__(self):
        wx.Frame.__init__(self, None, title="Maitenotas")
        # ask for user password
        user_password = ""
        if app_data.get_new_database():
            # create db and set new password
            dlg_pass1 = wx.TextEntryDialog(self, text_labels.DEFINE_PASSWORD,
                                           text_labels.NEW_DIARY)
            if dlg_pass1.ShowModal() == wx.ID_OK:
                password1=dlg_pass1.GetValue()
                dlg_pass1.Destroy()

                # ask password confirmation
                dlg = wx.TextEntryDialog(self, text_labels.CONFIRM_PASSWORD,text_labels.NEW_DIARY)
                if dlg.ShowModal() == wx.ID_OK:
                    password2=dlg.GetValue()
                    dlg.Destroy()
                    if password1 == password2:
                        user_password = password1
                    else:
                        wx.MessageBox(text_labels.PASSWORDS_DO_NOT_MATCH, "Error" ,
                                      wx.OK | wx.ICON_ERROR)
                        self.Close()
                else:
                    dlg.Destroy()
                    self.Close()
            else:
                dlg_pass1.Destroy()
                self.Close()

            # get name of first book
            dlg_first_book_name = wx.TextEntryDialog(self, text_labels.DIARY_NAME,
                                                  text_labels.INITIAL_NAME)
            name_of_first_book=""
            if dlg_first_book_name.ShowModal() == wx.ID_OK:
                name_of_first_book=dlg_first_book_name.GetValue()
                dlg_first_book_name.Destroy()
            else:
                dlg_first_book_name.Destroy()
                self.Close()

        else:
            # ask for password for existing database
            dlg_pass = wx.TextEntryDialog(self, text_labels.ENTER_PASSWORD, text_labels.OPENING_DIARY)

            if dlg_pass.ShowModal() == wx.ID_OK:
                user_password=dlg_pass.GetValue()
                dlg_pass.Destroy()
            else:
                dlg_pass.Destroy()
                self.Close()

        # verify database connection
        app_data.set_user_key(generate_user_key(user_password))
        if app_data.get_new_database():
            database_access = create_database(app_data.get_user_key(), user_password)
            if database_access is False:
                wx.MessageBox(text_labels.ERROR_READING_DATA, "Error" ,wx.OK | wx.ICON_ERROR)
                self.Close()
            # create first book
            book_id = create_book(app_data.get_user_key(), name_of_first_book)
            # create example data to start, since the book is new the parentId leaf is ZERO
            journal_name = text_labels.LEAF_ONE_OF + name_of_first_book
            journal_text = text_labels.SAMPLE_TEXT_1 + name_of_first_book
            create_journal(app_data.get_user_key(), book_id, 0, journal_name, journal_text)
            journal_name = text_labels.LEAF_TWO_OF + name_of_first_book
            journal_text = text_labels.SAMPLE_TEXT_2 + name_of_first_book
            create_journal(app_data.get_user_key(), book_id, 0, journal_name, journal_text)
        else:
            database_access = verify_database_password(app_data.get_user_key(), user_password)
            if database_access is False:
                wx.MessageBox(text_labels.INVALID_PASSWORD, "Error" ,wx.OK | wx.ICON_ERROR)
                self.Close()

        # create GUI Main panel and sub panels
        panel = MainPanel(self)
        box_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.tree_panel = TreePanel(panel)
        box_sizer.Add(self.tree_panel, 1, wx.EXPAND | wx.ALL, 1)
        text_panel = TextPanel(panel)
        box_sizer.Add(text_panel, 2, wx.EXPAND | wx.ALL, 1)
        panel.SetSizer(box_sizer)

        # keep a reference to the text control inside the tree panel
        # and inside the main panel also to access it later
        self.text_control = text_panel.get_text_control()
        self.tree_panel.set_text_control(self.text_control)

        # Show main panel
        self.Show()
        self.Maximize(True)

        # menus
        menubar = wx.MenuBar()

        # application menu
        application_menu = wx.Menu()
        wx_pythonid_exit=app_data.get_next_wx_python_id()
        wx_id_about=app_data.get_next_wx_python_id()

        menu_item_about = wx.MenuItem(application_menu, wx_id_about, text_labels.TEXT_ABOUT)
        application_menu.Append(menu_item_about)
        self.Bind(wx.EVT_MENU, show_about_screen, id=wx_id_about)
        menu_item_exit = wx.MenuItem(application_menu, wx_pythonid_exit, text_labels.TEXT_QUIT)
        application_menu.Append(menu_item_exit)
        self.Bind(wx.EVT_MENU, self.quit_application, id=wx_pythonid_exit)

        # tree menu
        tree_menu = wx.Menu()
        wx_python_d1=app_data.get_next_wx_python_id()
        wx_python_d2=app_data.get_next_wx_python_id()
        wx_python_d3=app_data.get_next_wx_python_id()
        menu_item_add_leaf = wx.MenuItem(tree_menu, wx_python_d1, text_labels.TEXT_ADD_LEAF)
        menu_item_remove_leaf = wx.MenuItem(tree_menu, wx_python_d2, text_labels.TEXT_REMOVE_LEAF)
        menu_item_rename_leaf = wx.MenuItem(tree_menu, wx_python_d3, text_labels.TEXT_RENAME_LEAF)
        tree_menu.Append(menu_item_add_leaf)
        tree_menu.Append(menu_item_remove_leaf)
        tree_menu.Append(menu_item_rename_leaf)

        self.Bind(wx.EVT_MENU, self.add_leaf, id=wx_python_d1)
        self.Bind(wx.EVT_MENU, self.remove_leaf, id=wx_python_d2)
        self.Bind(wx.EVT_MENU, self.rename_leaf, id=wx_python_d3)

        menubar.Append(application_menu, text_labels.TEXT_APPLICATION)
        menubar.Append(tree_menu, text_labels.TEXT_TREE)
        self.SetMenuBar(menubar)

        # window close event
        self.Bind(wx.EVT_CLOSE, self.close_window)

    def quit_application(self, _event):
        """quit application"""
        self.Close()

    def close_window(self, _event):
        """close window"""
        # save current text before exit application
        if app_data.get_selected_journal_id()>=1:
            text_in_screen = self.text_control.GetValue()
            update_journal_text(app_data.get_user_key(), app_data.get_selected_journal_id(),
                                text_in_screen)
        print("goodbye!")
        self.Destroy()

    def add_leaf(self, _event):
        """add leaf"""
        self.tree_panel.add_leaf()

    def remove_leaf(self, _event):
        """remove leaf"""
        self.tree_panel.remove_leaf()

    def rename_leaf(self, _event):
        """rename leaf"""
        self.tree_panel.rename_leaf()

def show_about_screen(_event):
    """show about window"""
    wx.MessageBox(text_labels.MESSAGE_BOX, text_labels.TEXT_ABOUT ,wx.OK | wx.ICON_INFORMATION)

if __name__ == "__main__":
    # check if database exists
    if path.exists("maitenotas.data") is False:
        app_data.set_new_database(True)

    app = wx.App(False)
    frame = MainFrame()
    app.MainLoop()
