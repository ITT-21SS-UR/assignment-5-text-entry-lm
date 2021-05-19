#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
The text input technique was completely implemented by Johannes Lorper.
"""

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
        self.terms = list(dict.fromkeys(self.corpus.words()))
        self.completer = QCompleter(self.terms, self)
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setFilterMode(QtCore.Qt.MatchStartsWith)
        self.popup_entry_count = 3
        self.completer.setMaxVisibleItems(self.popup_entry_count)
        self.current_popup = None
        self.completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.numbers = []
        self.template_doc = ""
        self.prev_content = ""
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
        if self.current_popup is not None:
            # the three words shown in the popup can be selected by pressing 1, 2 or 3 on the keyboard.
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
                self.current_popup.hide()

        # we block the "enter" keys so people cant choose a completion with it (and its not necessary for the task)
        if event.key() != QtCore.Qt.Key_Return and event.key() != QtCore.Qt.Key_Enter:
            super().keyPressEvent(event)

        completion_prefix = self.textUnderCursor()
        if len(completion_prefix) > 2:
            if completion_prefix != self.completer.completionPrefix():
                self.completer.setCompletionPrefix(completion_prefix)
                self.current_popup = self.completer.popup()
                self.current_popup.setCurrentIndex(
                    self.completer.completionModel().index(0, 0))
            cr = self.cursorRect()

            # setting stylesheet so you cant see scrollbar and highlighting in the popup
            self.current_popup.setStyleSheet("QAbstractItemView{color:white; selection-color: white;"
                                             " selection-background-color: transparent; background-color: transparent} "
                                             "QScrollBar:vertical {width: 0px;margin: 45px 0 45px 0;}")
            cr.setWidth(self.completer.popup().sizeHintForColumn(0)
                        + self.completer.popup().verticalScrollBar().sizeHint().width())
            self.completer.complete(cr)


def main():
    app = QtWidgets.QApplication(sys.argv)
    autocomplete_text_edit = CompleterTextEdit()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
