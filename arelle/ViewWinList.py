'''
Created on Feb 6, 2011

@author: Mark V Systems Limited
(c) Copyright 2011 Mark V Systems Limited, All rights reserved.
'''
import io
from tkinter import *
from tkinter.ttk import *
from arelle.CntlrWinTooltip import ToolTip
from arelle import XmlUtil

class ViewList():
    def __init__(self, modelXbrl, tabWin, tabTitle, hasToolTip=False):
        self.tabWin = tabWin
        self.viewFrame = Frame(tabWin)
        self.viewFrame.grid(row=0, column=0, sticky=(N, S, E, W))
        tabWin.add(self.viewFrame,text=tabTitle)
        xmlScrollbar = Scrollbar(self.viewFrame, orient=VERTICAL)
        self.listBox = Listbox(self.viewFrame, yscrollcommand=xmlScrollbar.set)
        self.listBox.grid(row=0, column=0, sticky=(N, S, E, W))
        #self.listBox.focus_set()
        self.listBox.bind("<Motion>", self.listBoxMotion, '+')
        self.listBox.bind("<Leave>", self.listBoxLeave, '+')
        xmlScrollbar["command"] = self.listBox.yview
        xmlScrollbar.grid(row=0, column=1, sticky=(N,S))
        self.viewFrame.columnconfigure(0, weight=1)
        self.viewFrame.rowconfigure(0, weight=1)
        self.listBoxToolTipText = StringVar()
        if hasToolTip:
            self.listBoxToolTip = ToolTip(self.listBox, textvariable=self.listBoxToolTipText, wraplength=480, follow_mouse=True, state="disabled")
            self.listBoxRow = -9999999
        self.modelXbrl = modelXbrl
        if modelXbrl:
            modelXbrl.views.append(self)
    
    def close(self):
        self.tabWin.forget(self.viewFrame)
        self.modelXbrl.views.remove(self)
        self.modelXbrl = None
        
    def select(self):
        self.tabWin.select(self.viewFrame)
        
    def append(self, line):
        self.listBox.insert(END, line)

    def clear(self):
        self.listBox.delete(0,END)
        
    def listBoxLeave(self, *args):
        self.listBoxRow = -9999999

    def saveToFile(self, filename):
        with open(filename, "w") as fh:
            fh.writelines([logEntry + '\n' for logEntry in self.listBox.get(0,END)])
            
    def copyToClipboard(self, cntlr=None, *ignore):
        if cntlr is None: cntlr = self.modelXbrl.modelManager.cntlr
        cntlr.clipboardData(text='\n'.join(self.listBox.get(0,END)))
            
    def listBoxMotion(self, *args):
        lbRow = self.listBox.nearest(args[0].y)
        if lbRow != self.listBoxRow:
            self.listBoxRow = lbRow
            text = self.listBox.get(lbRow)
            self.listBoxToolTip._hide()
            if text and len(text) > 0:
                if len(text) * 8 > 200:
                    self.listBoxToolTipText.set(text)
                    self.listBoxToolTip.configure(state="normal")
                    self.listBoxToolTip._schedule()
                else:
                    self.listBoxToolTipText.set("")
                    self.listBoxToolTip.configure(state="disabled")
            else:
                self.listBoxToolTipText.set("")
                self.listBoxToolTip.configure(state="disabled")
    
    def contextMenu(self,contextMenuClick=None):
        try:
            return self.menu
        except AttributeError:
            if contextMenuClick is None: contextMenuClick = self.modelXbrl.modelManager.cntlr.contextMenuClick
            self.menu = Menu( self.viewFrame, tearoff = 0 )
            self.listBox.bind( contextMenuClick, self.popUpMenu )
            return self.menu
    
    def popUpMenu(self, event):
        self.menu.post( event.x_root, event.y_root )

    def menuAddSaveClipboard(self):
        self.menu.add_command(label=_("Save to file"), underline=0, command=self.modelXbrl.modelManager.cntlr.fileSave)
        if self.modelXbrl.modelManager.cntlr.hasClipboard:
            self.menu.add_command(label=_("Copy to clipboard"), underline=0, command=self.copyToClipboard)
        
