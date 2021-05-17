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
from PyQt5.QtWidgets import QMainWindow
import re
import os
import pandas as pd
import time
import json
from textedit import SuperText  # TODO @Johannes


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

        # self.StudyStates = Enum('StudyStates', 'StartScreen Trial Pause Questionnaire Done')

        self.__logger = TextEntryLogger()
        self.ui = uic.loadUi("text_entry_speed_test.ui", self)
        self._setup_introduction()

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

    def _start_study(self):
        self.ui.task_text_label.setText(self.__task_text)
        # TODO init and add SuperText - Widget from textedit.py to ui here!

        # TODO do the measuring and regex stuff when first key pressed while focusing the text plain input field!
        # self.ui.task_input_field.textChanged().connect()

        # TODO only go to questionnaire after the second trial!!
        self.ui.task_finished_btn.clicked.connect(lambda: self._go_to_page(3))

    def _start_measuring_text_entry(self):
        print("Starting to measure text entry...")

    def keyPressEvent(self, event):
        # TODO text input field seems to have focus so this isn't triggered atm
        print("Pressed key: ", event.key())
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()

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
