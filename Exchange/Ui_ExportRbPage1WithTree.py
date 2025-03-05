# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:/proj/client_test/Exchange/ExportRbPage1WithTree.ui'
#
# Created: Thu Jun  6 18:55:42 2024
#      by: PyQt4 UI code generator 4.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_ExportRbPage1WithTree(object):
    def setupUi(self, ExportRbPage1WithTree):
        ExportRbPage1WithTree.setObjectName(_fromUtf8("ExportRbPage1WithTree"))
        ExportRbPage1WithTree.setWindowModality(QtCore.Qt.NonModal)
        ExportRbPage1WithTree.resize(593, 450)
        self.gridlayout = QtGui.QGridLayout(ExportRbPage1WithTree)
        self.gridlayout.setSpacing(4)
        self.gridlayout.setMargin(4)
        self.gridlayout.setObjectName(_fromUtf8("gridlayout"))
        self.splitterTree = QtGui.QSplitter(ExportRbPage1WithTree)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.splitterTree.sizePolicy().hasHeightForWidth())
        self.splitterTree.setSizePolicy(sizePolicy)
        self.splitterTree.setOrientation(QtCore.Qt.Horizontal)
        self.splitterTree.setObjectName(_fromUtf8("splitterTree"))
        self.treeItems = CTreeView(self.splitterTree)
        self.treeItems.setObjectName(_fromUtf8("treeItems"))
        self.tblItems = CTableView(self.splitterTree)
        self.tblItems.setTabKeyNavigation(False)
        self.tblItems.setAlternatingRowColors(True)
        self.tblItems.setObjectName(_fromUtf8("tblItems"))
        self.gridlayout.addWidget(self.splitterTree, 2, 0, 1, 1)
        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setMargin(0)
        self.hboxlayout.setObjectName(_fromUtf8("hboxlayout"))
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.hboxlayout.addItem(spacerItem)
        self.btnSelectAll = QtGui.QPushButton(ExportRbPage1WithTree)
        self.btnSelectAll.setObjectName(_fromUtf8("btnSelectAll"))
        self.hboxlayout.addWidget(self.btnSelectAll)
        self.btnClearSelection = QtGui.QPushButton(ExportRbPage1WithTree)
        self.btnClearSelection.setObjectName(_fromUtf8("btnClearSelection"))
        self.hboxlayout.addWidget(self.btnClearSelection)
        self.gridlayout.addLayout(self.hboxlayout, 3, 0, 1, 1)
        self.statusBar = QtGui.QStatusBar(ExportRbPage1WithTree)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.statusBar.sizePolicy().hasHeightForWidth())
        self.statusBar.setSizePolicy(sizePolicy)
        self.statusBar.setSizeGripEnabled(False)
        self.statusBar.setObjectName(_fromUtf8("statusBar"))
        self.gridlayout.addWidget(self.statusBar, 4, 0, 1, 1)
        self.hboxlayout1 = QtGui.QHBoxLayout()
        self.hboxlayout1.setObjectName(_fromUtf8("hboxlayout1"))
        self.chkExportAll = QtGui.QCheckBox(ExportRbPage1WithTree)
        self.chkExportAll.setObjectName(_fromUtf8("chkExportAll"))
        self.hboxlayout1.addWidget(self.chkExportAll)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.hboxlayout1.addItem(spacerItem1)
        self.chkRecursiveSelection = QtGui.QCheckBox(ExportRbPage1WithTree)
        self.chkRecursiveSelection.setObjectName(_fromUtf8("chkRecursiveSelection"))
        self.hboxlayout1.addWidget(self.chkRecursiveSelection)
        self.gridlayout.addLayout(self.hboxlayout1, 0, 0, 1, 1)

        self.retranslateUi(ExportRbPage1WithTree)
        QtCore.QMetaObject.connectSlotsByName(ExportRbPage1WithTree)
        ExportRbPage1WithTree.setTabOrder(self.treeItems, self.tblItems)

    def retranslateUi(self, ExportRbPage1WithTree):
        ExportRbPage1WithTree.setWindowTitle(_translate("ExportRbPage1WithTree", "Список записей", None))
        self.tblItems.setWhatsThis(_translate("ExportRbPage1WithTree", "список записей", "ура!"))
        self.btnSelectAll.setText(_translate("ExportRbPage1WithTree", "Выбрать все", None))
        self.btnClearSelection.setText(_translate("ExportRbPage1WithTree", "Очистить", None))
        self.statusBar.setToolTip(_translate("ExportRbPage1WithTree", "A status bar", None))
        self.statusBar.setWhatsThis(_translate("ExportRbPage1WithTree", "A status bar.", None))
        self.chkExportAll.setText(_translate("ExportRbPage1WithTree", "Выгружать всё", None))
        self.chkRecursiveSelection.setText(_translate("ExportRbPage1WithTree", "Выделять все дочерние элементы", None))

from library.TreeView import CTreeView
from library.TableView import CTableView

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    ExportRbPage1WithTree = QtGui.QDialog()
    ui = Ui_ExportRbPage1WithTree()
    ui.setupUi(ExportRbPage1WithTree)
    ExportRbPage1WithTree.show()
    sys.exit(app.exec_())

