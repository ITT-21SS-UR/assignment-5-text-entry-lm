#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import QCompleter
import nltk


# spacy nltk word completion dictionaries

class CompleterTextEdit(QtWidgets.QTextEdit):

    def __init__(self):
        super(CompleterTextEdit, self).__init__()
        self.corpus = nltk.corpus.ConllCorpusReader('.', 'tiger_release_aug07.corrected.16012013.conll09',
                                                    ['ignore', 'words', 'ignore', 'ignore', 'pos'], encoding='utf-8')
        print(self.corpus.words())
        self.terms = list(dict.fromkeys(self.corpus.words()))
        self.completer = QCompleter(self.terms, self)
        self.completer.setWidget(self)
        self.completer_model = BasicCompleterModel(terms=self.terms, parent=self)
        #self.completer.setModel(self.completer_model)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setFilterMode(QtCore.Qt.MatchStartsWith)
        self.popup_entry_count = 3
        self.completer.setMaxVisibleItems(self.popup_entry_count)
        self.current_popup = None
        self.completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.numbers = []
        self.template_doc = ""
        self.prev_content = ""
        self.initUI()
        self.completer.activated.connect(self.insertCompletion)

    # https://www.qtcentre.org/threads/23518-How-to-change-completion-rule-of-QCompleter?highlight=qcompleter
    def insertCompletion(self, completion):
        tc = self.textCursor()
        tc.movePosition(QtGui.QTextCursor.EndOfWord)
        tc.select(QtGui.QTextCursor.WordUnderCursor)
        tc.insertText(completion)
        self.setTextCursor(tc)

    def textUnderCursor(self):
        tc = self.textCursor()
        tc.select(QtGui.QTextCursor.WordUnderCursor)
        return tc.selectedText()

    def keyPressEvent(self, event):  
        print(self.completer.currentRow())
        if self.current_popup is not None:
            if event.text() == "1":
                self.completer.setCurrentRow(0)
                self.insertCompletion(self.completer.currentCompletion())
                self.current_popup.hide()
                return
            if event.text() == "2":
                self.completer.setCurrentRow(1)
                self.insertCompletion(self.completer.currentCompletion())
                self.current_popup.hide()
                return
            if event.text() == "3":
                self.completer.setCurrentRow(2)
                self.insertCompletion(self.completer.currentCompletion())
                self.current_popup.hide()
                return
            if event.key() == QtCore.Qt.Key_Space:
                print("space")
                self.current_popup.hide()

        super().keyPressEvent(event)
        print("keypress")
        completion_prefix = self.textUnderCursor()
        print(completion_prefix)
        if len(completion_prefix) > 2:
            if completion_prefix != self.completer.completionPrefix():
                self.completer.setCompletionPrefix(completion_prefix)
                self.current_popup = self.completer.popup()
                self.current_popup.setCurrentIndex(
                    self.completer.completionModel().index(0, 0))
            cr = self.cursorRect()
            #if self.current_popup.currentIndex().row() > self.popup_entry_count:
              #  self.current_popup.setCurrentIndex(self.popup_entry_count-1)
            self.current_popup.setBatchSize(3)
            self.current_popup.setStyleSheet("QScrollBar:vertical {width: 0px;margin: 45px 0 45px 0;}")
            cr.setWidth(self.completer.popup().sizeHintForColumn(0)
                        + self.completer.popup().verticalScrollBar().sizeHint().width())
            self.completer.complete(cr)

    def initUI(self):
        self.setGeometry(0, 0, 400, 400)
        self.setWindowTitle('SuperText')
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setMouseTracking(True)
        self.show()


class BasicCompleterModel(QtCore.QAbstractListModel):
    def __init__(self, terms=None, parent=None):
        super(BasicCompleterModel, self).__init__(parent)
        self.terms = terms
        self.num_terms = len(terms)
        self.line_edit = parent

    def rowCount(self, something):
        return self.num_terms

    def data(self, index=None, role=None):
        if role in [QtCore.Qt.DisplayRole, QtCore.Qt.EditRole]:
            return self.terms[index.row()]
        return None



def main():
    app = QtWidgets.QApplication(sys.argv)
    super_text = CompleterTextEdit()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
