#!/usr/bin/python
# -*- coding: utf-8 -*-

# TODO längere Texte nehmen und dafür keine wiederholungen?

"""
The text used for the task in this study has been taken from https://www.blindtextgenerator.de/ (Werther) and is a
short extract of "Die Leiden des jungen Werther" from Johann Wolfgang von Goethe. It was chosen because it is a
meaningful text unlike other blind texts like 'Lorem Ipsum' but on the other hand shouldn't be too easy.
The text consists of 58 words.

The example texts were taken from the same page but from other blind texts to prevent too many similarities with the
real experiment text. The first one was taken from "Er hörte leise" and the second example text was taken from
"Kafka". Both consist of 19 words.
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


def parse_setup_file(file_name: str) -> tuple[int, str, dict]:
    # check if the file exists
    if os.path.isfile(file_name):
        with open(file_name) as setup_file:
            content = json.load(setup_file)  # load the json file content as dictionary

            number_of_trials: int = content['number_of_trials']
            task_text: str = content['task_text']
            conditions: dict = content['conditions']

            return number_of_trials, task_text, conditions
    else:
        print("Given setup file does not exist!")
        exit(1)


def _test_timers():
    # simple test to compare timing functions:
    timer = QElapsedTimer()
    timer.start()
    time_start = time.time()
    t1 = time.perf_counter()

    # do some calculations (actually this calculates the fibonacci number, see https://stackoverflow.com/a/4936086)
    n = 127
    fib_n = int(((1 + math.sqrt(5)) / 2) ** n / math.sqrt(5) + 0.5)
    time.sleep(2)

    time_end = time.time()
    t2 = time.perf_counter()
    print("Duration with time module: ", time_end - time_start)
    print("Duration with perfcounter module: ", t2 - t1)
    print("Duration with QElapsedTimer: ", timer.elapsed())


def split_text(text: str) -> dict[str, list[str]]:
    text_content_dict = dict()
    # regex to split text into sentences taken from https://stackoverflow.com/a/25736082
    sentences = re.split(r"(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s", text)

    for sent in sentences:
        # for every sentence, save the corresponding words as a list
        words = sent.split()
        # print("normal words: ", words)
        words = [word.rstrip(',;!?.') for word in words]  # strip trailing commas, semicolons and point characters
        # print("stripped words: ", words)
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

    def __init__(self, participant_id, setup_file):
        super(TextEntryExperiment, self).__init__()
        self.__participant_id = participant_id
        self.__num_trials, self.__task_text, self.__condition_dict = parse_setup_file(setup_file)

        conditions = list(self.__condition_dict.keys())
        self.__balanced_condition_list = get_balanced_condition_list(conditions, self.__participant_id)

        self.__current_condition = self.__balanced_condition_list[0]
        print("Current Condition: ", self.__current_condition)
        self.__current_example_text = self.__condition_dict[self.__current_condition]['example_text']
        self.__current_task_description = self.__condition_dict[self.__current_condition]['task_description']

        self.__task_started = False
        self.__text_dict = split_text(self.__task_text)
        self.__curr_sentence_index = 0
        self.__curr_word_index = 0
        self.__current_sentence = self._get_current_sentence()
        self.__current_word = self._get_current_word()
        self.__last_char = None

        print("Current Sentence: ", self.__current_sentence)
        print("Current Word: ", self.__current_word)

        self.__logger = TextEntryLogger()
        self.ui = uic.loadUi("text_entry_speed_test.ui", self)
        self._setup_introduction()

    def _get_current_sentence(self):
        return self._get_sentence(self.__curr_sentence_index)

    def _get_sentence(self, index):
        sentences = list(self.__text_dict.keys())
        sent_count = len(sentences)
        if index > sent_count:
            sys.stderr.write(f"Attempted to get sentence at position {index} even though there are only {sent_count}")
            return None

        # get the key at the specified position; works because since Python 3.7 the order in dictionaries won't change
        return sentences[index]

    def _get_current_word(self):
        current_sentence = self.__current_sentence  # if self.__current_sentence is not None else self._get_current_sentence()
        if current_sentence is not None:
            return self._get_word(current_sentence, self.__curr_word_index)

    # def _get_last_word_of_sentence(self):
    #     current_sentence = self.__current_sentence
    #     if current_sentence is not None:
    #         last_sentence_idx = len(self.__text_dict.get(current_sentence))
    #         return self._get_word(current_sentence, last_sentence_idx)

    def _get_word(self, sentence, index):
        words = self.__text_dict.get(sentence)
        word_count = len(words)
        if index > word_count:
            sys.stderr.write(f"Attempted to get word at position {index} even though there are only {word_count}")
            return None

        return words[index]

    def _setup_introduction(self):
        self._get_sub_pages()
        self.ui.stackedWidget.setCurrentIndex(0)
        self.ui.trial_number_label.setText(str(self.__num_trials))

        # change task text based on condition!
        self.ui.task_description_label.setText(self.__current_task_description)

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

    def _show_example(self):
        self.ui.example_task_description.setText(self.__current_task_description)
        self.ui.example_text.setText(self.__current_example_text)
        self.ui.start_actual_study_btn.clicked.connect(lambda: self._go_to_page(2))

        # TODO only for testing here: (should only be called in start_study below)
        self.ui.example_input_field.installEventFilter(self)
        self.ui.example_input_field.textChanged.connect(self._text_content_changed)

    def _start_study(self):
        self.ui.task_text_label.setText(self.__task_text)

        # TODO focus the text field automatically so user doesn't have to click it first!

        # install event filter to only listen to keypress events on this text edit field,
        # see https://stackoverflow.com/questions/46505769/pyqt-keypress-event-in-lineedit
        self.ui.task_input_field.installEventFilter(self)
        self.ui.task_input_field.textChanged.connect(self._text_content_changed)

        # TODO only go to questionnaire after the second trial!!
        self.ui.task_finished_btn.clicked.connect(lambda: self._go_to_page(3))

    def _start_measuring_text_entry_speed(self):
        print("Starting to measure text entry...")
        current_time = time.time()
        self.__start_time_word = current_time
        self.__start_time_sentence = current_time

    def _text_content_changed(self):
        self.__current_input = self.ui.example_input_field.toPlainText()  # self.ui.task_input_field
        # print("Current Input Field Content: ", self.__current_input)

    def eventFilter(self, source, event):
        if event.type() == QEvent.KeyPress and source is self.ui.example_input_field:  # self.ui.task_input_field
            if not self.__task_started:
                self.__task_started = True
                self._start_measuring_text_entry_speed()

            print('key press:', (event.key(), event.text()))
            pressed_key = event.text()
            if pressed_key in [' ', ',', ';', ':', '\n', '\r', '.', '!', '?']:
                self._handle_word_sentence_finished(pressed_key)

            # elif re.match(r"\b(\w)", pressed_key):
            elif re.match(r"\w", pressed_key):
                if self.__last_char is not None and self.__last_char.isspace():
                    # TODO this isn't always called on new word; investigate this issue!
                    # new word has started, restart timer
                    print("new word started")
                    self.__start_time_word = time.time()

            self.__last_char = pressed_key  # save the entered char

        return super(TextEntryExperiment, self).eventFilter(source, event)

    def _handle_word_sentence_finished(self, entered_char):
        if entered_char == ' ' and self.__last_char in [',', ';', ':', '.', '!', '?']:
            # this is just a whitespace after one of the other ending chars; ignore it
            return

        # word has been finished
        print("word finished")
        current_time = time.time()
        end_time_word = current_time
        print(f"Took {end_time_word - self.__start_time_word} seconds to enter this word.")
        # TODO log
        # reset timer
        # self.__start_time_word = None  # TODO resetting causes crash sometimes, this shouldn't happen !!! (maybe because of the TODO above)

        self.__curr_word_index += 1
        print(f"\n###########################\nCurrent word is now: {self.__current_word}\n")

        if entered_char in ['.', '!', '?']:
            # sentence has been finished
            print("sentence finished")
            end_time_sentence = current_time
            print(f"Took {end_time_sentence - self.__start_time_sentence} seconds to enter this sentence.")
            # TODO log
            # reset timer
            # self.__start_time_sentence = None  # TODO perf_counter() instead of time?

            self.__curr_sentence_index += 1
            self.__current_sentence = self._get_current_sentence()
            print(f"\n###########################\nCurrent sentence is now: {self.__current_sentence}\n")

            if self.__current_sentence is not None:  # it would only be None if this was the last sentence
                self.__start_time_sentence = time.time()
            else:
                # text has been completely entered # TODO log this!
                print("\n###############################\nFinished entering text!")

    def _setup_questionnaire(self):
        self.ui.send_questionnaire_btn.clicked.connect(self._save_answers)

    def _save_answers(self):
        participant_age = str(self.ui.age_selection.value())
        participant_gender = str(self.ui.gender_selection.currentText())
        participant_occupation = str(self.ui.occupation_input.text())
        keyboard_affinity = str(self.ui.keyboard_affinity_slider.value())
        entry_speed = str(self.ui.speed_estimation_slider.value())

        # TODO this part should be extracted to the logger below!
        # self.__questionnaire_data = self.__questionnaire_data.append({'timestampInMs': time.time(),
        #                                                               'participantID': self._participant_id,
        #                                                               'age': participant_age,
        #                                                               'gender': participant_gender,
        #                                                               'occupation': participant_occupation,
        #                                                               'keyboardUsage': keyboard_affinity,
        #                                                               'entrySpeed': entry_speed
        #                                                               }, ignore_index=True)
        # self.__questionnaire_data.to_csv(self.__QUESTIONNAIRE_DATA_CSV_NAME, index=False)

        self._go_to_page()  # go to the next page

    def _setup_finish_page(self):
        self.ui.exit_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.ui.exit_btn.clicked.connect(lambda: sys.exit(1))  # send error code so the setup program will finish
        self.ui.next_trial_btn.clicked.connect(lambda: sys.exit(0))  # exit normally to start with the next participant


class TextEntryLogger:

    def __init__(self):
        self.__log_file_name = "text_entry_log.csv"
        # self.__study_data = self._init_study_log()  # TODO implement logging

    def _init_study_log(self):
        # check if the file already exists
        if os.path.isfile(self.__log_file_name):
            study_data = pd.read_csv(self.__log_file_name)
        else:
            study_data = pd.DataFrame(
                columns=['timestamp', 'participantID', 'condition', 'pointerPositionsPerTarget', 'timesPerTargetInS',
                         'startTimeAsUnix', 'endTimeAsUnix', 'timeTillFinishedInS', 'missedClickCount',
                         'bubblePointingTechnique'])
        return study_data

    def _log_data(self):
        print(f"'id', 'trial', 'time'")
        print(f"{0}, {2}, {589749594}")
        # TODO mit os aus der setup python file das hier ausführen? oder lieber direkt über cmd?
        #  python3 testsetup.py >> log.csv

    def _log_keypress(self):
        pass

    def _log_word_finished(self):
        pass

    def _log_sentence_finished(self):
        pass

    def _log_task_finished(self):
        pass

    def add_new_log_data(self, participant_id, condition, pointer_position_list, time_per_target_list, start_time,
                         end_time, missed_clicks, bubble_pointing_active):

        self.__study_data = self.__study_data.append({'timestampInMs': time.time(), 'participantID': participant_id,
                                                      'condition': condition,
                                                      'pointerPositionsPerTarget': pointer_position_list,
                                                      'timesPerTargetInS':
                                                          time_per_target_list, 'startTimeAsUnix':
                                                          start_time, 'endTimeAsUnix': end_time, 'timeTillFinishedInS':
                                                          end_time - start_time, 'missedClickCount': missed_clicks,
                                                      'bubblePointingTechnique': bubble_pointing_active},
                                                     ignore_index=True)
        self.__study_data.to_csv(self.__log_file_name, index=False)
        with open(self.__log_file_name) as file:
            print(file.readlines()[-1])


def main():
    if len(sys.argv) < 2:
        print("Missing command line arguments: participant_id and setup_file!"
              "\nUsage: text_entry_speed_test.py participant_id setup_file >> output_file.csv")
        exit(1)
    else:
        # get the passed command line arguments
        participant_id = int(sys.argv[1])
        setup_file = sys.argv[2]

        app = QtWidgets.QApplication(sys.argv)
        text_entry_experiment = TextEntryExperiment(participant_id, setup_file)
        text_entry_experiment.show()
        sys.exit(app.exec_())


if __name__ == '__main__':
    main()
