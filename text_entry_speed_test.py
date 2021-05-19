#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
The text used for the task in this study has been taken from https://www.blindtextgenerator.de/ (Werther) and is a
short extract of "Die Leiden des jungen Werther" from Johann Wolfgang von Goethe. It was chosen because it is a
meaningful text unlike other blind texts like 'Lorem Ipsum' but on the other hand shouldn't be too easy.
Both parts of the text (task text 1 and 2) consist of 58 words.

The example texts were taken from the same page but from other blind texts to prevent too many similarities with the
real experiment text. The first one was taken from "Er hörte leise" and the second example text was taken from
"Kafka". Both consist of 19 words.


The speed test experiment logic and logging, the ui and the automatic setup (setup_experiment.py) have been implemented
by Michael Meckl. The integration of the custom input technique has been done by Johannes Lorper.
"""

import sys
from PyQt5 import QtCore, QtWidgets, uic
from PyQt5.QtCore import QEvent, QElapsedTimer
from PyQt5.QtWidgets import QMainWindow
import re
import math
import os
import pandas as pd
import time
import json
from enum import Enum
from text_input_technique import CompleterTextEdit


class EventTypes(Enum):
    KEY_PRESSED = "key_pressed"
    WORD_TYPED = "word_typed"
    SENTENCE_TYPED = "sentence_typed"
    TEST_FINISHED = "test_finished"


# def _test_timers():
#     # simple test to compare timing functions:
#     timer = QElapsedTimer()
#     timer.start()
#     time_start = time.time()
#     t1 = time.perf_counter()
#
#     # do some calculations (actually this calculates the fibonacci number, see https://stackoverflow.com/a/4936086)
#     n = 127
#     fib_n = int(((1 + math.sqrt(5)) / 2) ** n / math.sqrt(5) + 0.5)
#     time.sleep(2)
#
#     time_end = time.time()
#     t2 = time.perf_counter()
#     print("Duration with time module: ", time_end - time_start)
#     print("Duration with perfcounter module: ", t2 - t1)
#     print("Duration with QElapsedTimer: ", timer.elapsed())


def get_current_time() -> float:
    return time.time()


def parse_setup_file(file_name: str) -> dict:
    # check if the file exists
    if os.path.isfile(file_name):
        with open(file_name) as setup_file:
            content = json.load(setup_file)
            # load the json condition object as a python dictionary
            conditions: dict = content['conditions']
            return conditions
    else:
        sys.stderr.write("Given setup file does not exist!")
        exit(1)


def split_text(text: str) -> dict[str, list[str]]:
    text_content_dict = dict()
    # regex to split text into sentences taken from https://stackoverflow.com/a/25736082
    sentences = re.split(r"(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s", text)

    for sent in sentences:
        # for every sentence, save the corresponding words as a list
        words = sent.split()
        words = [word.rstrip(',;!?.') for word in words]  # strip trailing commas, semicolons and point characters
        text_content_dict[sent] = words

    return text_content_dict


def get_balanced_condition_list(condition_list, participant_id):
    condition_count = len(condition_list)

    # First we need to create a balanced latin square according to our number of conditions:
    # see https://medium.com/@graycoding/balanced-latin-squares-in-python-2c3aa6ec95b9
    balanced_order = [[((j // 2 + 1 if j % 2 else condition_count - j // 2) + i) % condition_count + 1 for j in
                       range(condition_count)] for i in range(condition_count)]
    if condition_count % 2:  # Repeat reversed for odd n
        balanced_order += [seq[::-1] for seq in balanced_order]

    order_for_participant = balanced_order[participant_id % condition_count]  # get trial order for current participant

    # Now we will reorder our conditions-list with the balanced-latin-square order we created above
    # see https://stackoverflow.com/questions/2177590/how-can-i-reorder-a-list/2177607
    for i in range(len(order_for_participant)):
        order_for_participant[i] -= 1  # we have to subtract 1 before to prevent an IndexOutOfRange-Error
    return [condition_list[i] for i in order_for_participant]


class TextEntryExperiment(QMainWindow):
    __TASK_DESCRIPTION_AUTOCOMPLETE = "Beim Eingeben der Texte werden mögliche Autovervollständigungen angezeigt! " \
                                      "Du kannst diese NUR mit den Tasten 1, 2 oder 3 auswählen. Eine Bestätigung " \
                                      "mit der Entertaste wie in anderen Programmen ist nicht möglich!"
    __TASK_DESCRIPTION_NO_AUTOCOMPLETE = "Beim Eingeben der Texte gibt es KEINE Hilfestellungen, wie z.B. " \
                                         "Autokorrektur oder Autovervollständigung!"

    def __init__(self, participant_id, setup_file, debug=False):
        super(TextEntryExperiment, self).__init__()
        self.__debug = debug
        self.__participant_id = participant_id
        self.__condition_dict = parse_setup_file(setup_file)
        conditions = list(self.__condition_dict.keys())
        self.__balanced_condition_list = get_balanced_condition_list(conditions, self.__participant_id)
        if self.__debug:
            print("Balanced conditions: ", self.__balanced_condition_list)

        self.__curr_trial_index = 0
        self._init_trial_data()

        self.__logger = TextEntryLogger()
        self.ui = uic.loadUi("text_entry_speed_test.ui", self)
        self._setup_introduction()
        self.current_text_input_field = None
        self.ui.start_actual_study_btn.clicked.connect(lambda: self._go_to_page(2))
        self.ui.task_finished_btn.clicked.connect(self._decide_next_task_page)

        self.completer_text_widget = CompleterTextEdit()  # the text field widget with our custom input technique

    def _init_trial_data(self):
        self.__current_condition = self.__balanced_condition_list[self.__curr_trial_index]
        self.__current_example_text = self.__condition_dict[self.__current_condition]['example_text']
        self.__current_task_text = self.__condition_dict[self.__current_condition]['task_text']
        self.__autocompletion_active = self.__condition_dict[self.__current_condition]['autocompletion']

        if self.__debug:
            print("Current Condition: ", self.__current_condition)

        self.__task_started = False
        self.__text_dict = split_text(self.__current_task_text)

        self.__curr_sentence_index = 0
        self.__curr_word_index = 0
        self.__current_sentence = self._get_current_sentence()
        self.__current_word = self._get_current_word()
        self.__last_char = None

    def _was_last_trial(self):
        return True if self.__curr_trial_index >= len(self.__balanced_condition_list) else False

    def _get_current_sentence(self):
        return self._get_sentence(self.__curr_sentence_index)

    def _get_sentence(self, index):
        sentences = list(self.__text_dict.keys())
        sent_count = len(sentences)
        if self.__debug:
            print(f"\n--------- get sentence: sentence_count:{sent_count}; sentenced index: {index} ---------\n")

        if index >= sent_count:
            if self.__debug:
                sys.stderr.write(f"Attempted to get sentence at position {index}; Max. sentences: {sent_count}")
            return None

        # get the key at the specified position; works because since Python 3.7 the order in dictionaries won't change
        return sentences[index]

    def _get_current_word(self):
        current_sentence = self.__current_sentence
        if current_sentence is not None:
            return self._get_word(current_sentence, self.__curr_word_index)

    def _get_word(self, sentence, index):
        words = self.__text_dict.get(sentence)
        word_count = len(words)
        if self.__debug:
            print(f"\n------------ get word: word_count:{word_count}; word index: {index} --------------\n")

        if index >= word_count:
            if self.__debug:
                sys.stderr.write(f"Attempted to get word at position {index}; Max. words: {word_count}\n")
            return None

        return words[index]

    def _setup_introduction(self):
        self._get_sub_pages()
        self.ui.stackedWidget.setCurrentIndex(0)

        self.ui.start_study_btn.setFocusPolicy(QtCore.Qt.NoFocus)  # prevent auto-focus of the start button
        self.ui.start_study_btn.clicked.connect(lambda: self._go_to_page(1))

    def _get_sub_pages(self):
        # save all sub-pages for the stacked widget as member variables
        self.firstPage = self.ui.introduction
        self.secondPage = self.ui.example_trial
        self.thirdPage = self.ui.text_entry_task
        self.fourthPage = self.ui.post_questionnaire
        self.fifthPage = self.ui.finish_page

    def _go_to_page(self, index=None):
        if self.__debug:
            print(f"go to page with index: {index}")

        if index is None:
            # if no index is given, simply move to the next page
            index = self.ui.stackedWidget.currentIndex() + 1

        # switch widget index to the element in the stack at the given index (i.e. move to this page)
        self.ui.stackedWidget.setCurrentIndex(index)

        current_widget = self.ui.stackedWidget.currentWidget()
        if current_widget is self.secondPage:
            self._show_example()
        elif current_widget is self.thirdPage:
            self._start_study()
        elif current_widget is self.fourthPage:
            self._setup_questionnaire()
        elif current_widget is self.fifthPage:
            self._setup_finish_page()

    def new_text_box_widget(self, autocomplete):
        if autocomplete:
            widget = self.completer_text_widget
            widget.clear()
        else:
            widget = QtWidgets.QTextEdit(self)
        return widget

    def _show_example(self):
        # change task text based on condition!
        if self.__autocompletion_active:
            self.ui.example_task_description.setText(TextEntryExperiment.__TASK_DESCRIPTION_AUTOCOMPLETE)
        else:
            self.ui.example_task_description.setText(TextEntryExperiment.__TASK_DESCRIPTION_NO_AUTOCOMPLETE)

        container_layout = self.ui.example_text_box_container.layout()

        for i in reversed(range(container_layout.count())):
            # insert custom widget at correct position in the layout
            container_layout.itemAt(i).widget().setParent(None)

        text_box = self.new_text_box_widget(self.__autocompletion_active)
        self.current_text_input_field = text_box
        self.ui.example_text_box_container.layout().addWidget(text_box)

        self.ui.example_text.setText(self.__current_example_text)
        # clear the text field to prevent leftovers from the last trial
        # input_field.clear()

        # focus the text field automatically so user doesn't have to click it first!
        text_box.setFocus()

    def _start_study(self):
        self.ui.task_text_label.setText(self.__current_task_text)
        container_layout = self.ui.task_text_box_container.layout()
        for i in reversed(range(container_layout.count())):
            container_layout.itemAt(i).widget().setParent(None)

        text_box = self.new_text_box_widget(self.__autocompletion_active)
        self.current_text_input_field = text_box
        container_layout.addWidget(text_box)

        # input_field.clear()
        text_box.setFocus()

        # install event filter to only listen to keypress events on this text edit field,
        # see https://stackoverflow.com/questions/46505769/pyqt-keypress-event-in-lineedit
        text_box.installEventFilter(self)
        # self.ui.task_input_field.textChanged.connect(self._text_content_changed)

        # self.ui.task_finished_btn.setEnabled(False)  # disable 'next'-button at first!

    def _start_measuring_text_entry_speed(self):
        if self.__debug:
            print("Starting to measure text entry...")
        current_time = get_current_time()
        self.__start_time_task = current_time
        self.__start_time_word = current_time
        self.__start_time_sentence = current_time

    # def _text_content_changed(self):
    #     self.__current_input = self.ui.task_input_field.toPlainText()
    #     # print("Current Input Field Content: ", self.__current_input)

    def eventFilter(self, source, event):
        if event.type() == QEvent.KeyPress and source is self.current_text_input_field:
            if not self.__task_started:
                self.__task_started = True
                self._start_measuring_text_entry_speed()

            if self.__debug:
                print('key press:', (event.key(), event.text()))
            pressed_key = event.text()

            self.__logger.log_event(EventTypes.KEY_PRESSED, get_current_time(), self.__participant_id,
                                    self.__current_condition, self.__autocompletion_active, pressed_key, time.time(),
                                    time.time(), 0)

            # check if the pressed key was one of the defined ending characters;
            # if yes, either a word or a word and a sentence have been finished! (naive implementation)
            if pressed_key in [' ', ',', ';', ':', '.', '!', '?']:  # '\n', '\r',
                # TODO right now word time includes the typing of the whitespace character afterwards !!
                self._handle_word_finished(pressed_key)

            # elif re.match(r"\b(\w)", pressed_key):  # use \b (word boundaries) ?
            elif re.match(r"\w", pressed_key):
                # if a word character has been entered and the character before wasn't one too (or a digit), we
                # probably started a new word

                if self.__debug:
                    print(f"char entered; last char was: {self.__last_char}")

                if self.__last_char is not None and not self.__last_char.isalnum():
                    # new word has started, restart timer
                    if self.__debug:
                        print("new word started")
                    self.__start_time_word = get_current_time()

            self.__last_char = pressed_key  # save the entered char

        return super(TextEntryExperiment, self).eventFilter(source, event)

    def _handle_word_finished(self, entered_char):
        if entered_char == ' ' and self.__last_char in [',', ';', ':', '.', '!', '?']:
            # this is just a whitespace after one of the other ending chars; ignore it
            return

        # word has been finished
        if self.__debug:
            print("word finished")

        current_time = get_current_time()
        end_time_word = current_time
        word_duration = end_time_word - self.__start_time_word
        self.__logger.log_event(EventTypes.WORD_TYPED, get_current_time(), self.__participant_id,
                                self.__current_condition, self.__autocompletion_active, self.__current_word,
                                end_time_word, self.__start_time_word, word_duration)

        self.__curr_word_index += 1
        self.__current_word = self._get_current_word()
        if self.__debug:
            print(f"\n###########################\nCurrent word is now: {self.__current_word}\n")

        if entered_char in ['.', '!', '?']:
            # sentence has been finished
            self._handle_sentence_finished()

    def _handle_sentence_finished(self):
        if self.__debug:
            print("sentence finished")

        end_time_sentence = get_current_time()
        sentence_duration = end_time_sentence - self.__start_time_sentence
        self.__logger.log_event(EventTypes.SENTENCE_TYPED, get_current_time(), self.__participant_id,
                                self.__current_condition, self.__autocompletion_active, self.__current_sentence,
                                end_time_sentence, self.__start_time_sentence, sentence_duration)

        self.__curr_word_index = 0  # reset word index to start with the first word of the new sentence again

        self.__curr_sentence_index += 1
        self.__current_sentence = self._get_current_sentence()
        if self.__debug:
            print(f"\n###########################\nCurrent sentence is now: {self.__current_sentence}\n")

        if self.__current_sentence is not None:
            # it would only be None if this was the last sentence, so start timer for the next sentence
            self.__start_time_sentence = get_current_time()
        else:
            if self.__debug:
                print("\n###############################\nFinished entering text!")
            # TODO check for number of errors and discard this participant if too many errors were made??

            # text has been completely entered
            end_time = get_current_time()
            task_duration = end_time - self.__start_time_task
            self.__logger.log_event(EventTypes.TEST_FINISHED, get_current_time(), self.__participant_id,
                                    self.__current_condition, self.__autocompletion_active, self.__current_task_text,
                                    end_time, self.__start_time_task, task_duration)

            # now enable the button at the bottom
            # self.ui.task_finished_btn.setEnabled(True)

    def _decide_next_task_page(self):
        self.__curr_trial_index += 1
        if self._was_last_trial():
            # go to next page when finished with the last trial
            self._go_to_page(3)
        else:
            # start next trial
            self._init_trial_data()
            self._go_to_page(1)

    def _setup_questionnaire(self):
        self.ui.send_questionnaire_btn.clicked.connect(self._save_questionnaire_answers)

    def _save_questionnaire_answers(self):
        age = str(self.ui.age_selection.value())
        gender = str(self.ui.gender_selection.currentText())
        occupation = str(self.ui.occupation_input.text())
        keyboard_affinity = str(self.ui.keyboard_affinity_slider.value())
        entry_speed = str(self.ui.speed_estimation_slider.value())
        self.__logger.log_questionnaire(self.__participant_id, age, gender, occupation, keyboard_affinity, entry_speed)

        self._go_to_page()  # if no index is specified, simply go to the next page

    def _setup_finish_page(self):
        self.ui.exit_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.ui.exit_btn.clicked.connect(lambda: sys.exit(1))  # send error code so the setup program will finish
        self.ui.next_trial_btn.clicked.connect(lambda: sys.exit(0))  # exit normally to start with the next participant


class TextEntryLogger:

    def __init__(self):
        self.__log_file_name = "text_entry_log.csv"
        self.__questionnaire_log_file_name = "questionnaire_log.csv"
        self._init_logger()

    def _init_logger(self) -> None:
        if os.stat(self.__log_file_name).st_size == 0:
            # log file is empty, add the csv headers
            print('event_type', 'timestamp', 'participant_id', 'condition', 'with_autocompletion', 'entered_content',
                  'start_time_in_s', 'end_time_in_s', 'duration_in_s')

        if os.path.isfile(self.__questionnaire_log_file_name):
            self.__questionnaire_data = pd.read_csv(self.__questionnaire_log_file_name)
        else:
            self.__questionnaire_data = pd.DataFrame(
                columns=['participant_id', 'age', 'gender', 'occupation', 'keyboard_usage', 'entry_speed'])

    def log_event(self, event: EventTypes, timestamp: float, participant_id: int, condition: str, autocompletion: bool,
                  entered_content: str, start_time_in_s: float, end_time_in_s: float, duration_in_s: float) -> None:

        print(f"{event},{timestamp},{participant_id},{condition},{autocompletion},{entered_content},{start_time_in_s},"
              f"{end_time_in_s},{duration_in_s}")

    def log_questionnaire(self, participant_id: int, age: str, gender: str, occupation: str, keyboard_usage: str,
                          entry_speed: str) -> None:

        # log questionnaire answers to a csv file to keep log data separated
        self.__questionnaire_data = self.__questionnaire_data.append({'participant_id': participant_id,
                                                                      'age': age,
                                                                      'gender': gender,
                                                                      'occupation': occupation,
                                                                      'keyboard_usage': keyboard_usage,
                                                                      'entry_speed': entry_speed
                                                                      }, ignore_index=True)
        self.__questionnaire_data.to_csv(self.__questionnaire_log_file_name, index=False)


def main():
    if len(sys.argv) < 2:
        sys.stderr.write("Missing command line arguments: participant_id and setup_file!"
                         "\nUsage: text_entry_speed_test.py participant_id setup_file >> output_file.csv")
        exit(1)
    else:
        # get the passed command line arguments
        participant_id = int(sys.argv[1])
        setup_file = sys.argv[2]

        app = QtWidgets.QApplication(sys.argv)
        text_entry_experiment = TextEntryExperiment(participant_id, setup_file, debug=False)
        text_entry_experiment.show()
        sys.exit(app.exec_())


if __name__ == '__main__':
    main()
