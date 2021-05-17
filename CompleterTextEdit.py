#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import QCompleter
import nltk


# spacy nltk word completion dictionaries

class CompleterTextEdit(QtWidgets.QTextEdit):

    def __init__(self, example_text):
        super(CompleterTextEdit, self).__init__()
        self.corpus = nltk.corpus.ConllCorpusReader('.', 'tiger_release_aug07.corrected.16012013.conll09',
                                                    ['ignore', 'words', 'ignore', 'ignore', 'pos'], encoding='utf-8')
        print(self.corpus.words())
        self.terms = list(dict.fromkeys(self.corpus.words()))
        self.completer = QCompleter(self.terms, self)
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setFilterMode(QtCore.Qt.MatchStartsWith)
        self.numbers = []
        self.template_doc = ""
        self.setHtml(example_text)
        self.prev_content = ""
        self.initUI()
        self.completer.activated.connect(self.insertCompletion)

    def insertCompletion(self, completion):
        tc = self.textCursor()
        extra = (len(completion) -
                 len(self.completer.completionPrefix()))
        tc.movePosition(QtGui.QTextCursor.Left)
        tc.movePosition(QtGui.QTextCursor.EndOfWord)
        tc.insertText(completion[len(self.completer.completionPrefix()):])
        self.setTextCursor(tc)

    def textUnderCursor(self):
        tc = self.textCursor()
        tc.select(QtGui.QTextCursor.WordUnderCursor)
        return tc.selectedText()

    def keyPressEvent(self, event):  # TODO remove popup "1" "2" or "3"
        print(self.completer.currentRow())
        if event.text() == "1":
            self.completer.setCurrentRow(0)
            self.insertCompletion(self.completer.currentCompletion())
            return
        if event.text() == "2":
            self.completer.setCurrentRow(1)
            self.insertCompletion(self.completer.currentCompletion())
            return
        if event.text() == "3":
            self.completer.setCurrentRow(2)
            self.insertCompletion(self.completer.currentCompletion())
            return
        super().keyPressEvent(event)
        print("keypress")
        completion_prefix = self.textUnderCursor()
        print(completion_prefix)
        if len(completion_prefix) > 2:
            if completion_prefix != self.completer.completionPrefix():
                self.completer.setCompletionPrefix(completion_prefix)
                popup = self.completer.popup()
                popup.setCurrentIndex(
                    self.completer.completionModel().index(0, 0))
            cr = self.cursorRect()
            cr.setWidth(self.completer.popup().sizeHintForColumn(0)
                        + self.completer.popup().verticalScrollBar().sizeHint().width())
            self.completer.complete(cr)  # TODO should only show the 3 first completions

    def initUI(self):
        self.setGeometry(0, 0, 400, 400)
        self.setWindowTitle('SuperText')
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setMouseTracking(True)
        self.show()


def main():
    app = QtWidgets.QApplication(sys.argv)
    super_text = CompleterTextEdit("An 123 Tagen kamen 1342 Personen.")
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
