#!/usr/bin/python
# -*- coding: utf-8 -*-

import spacy
import re
import nltk.data
import nltk.tokenize

# some sentences that should test quite a few things to work correctly when splitting
doc1 = "As the most quoted English writer Shakespeare has more than his share of famous quotes.  Some Shakespare famous quotes are known for their beauty, some for their everyday truths and some for their wisdom. We often talk about Shakespeare’s quotes as things the wise Bard is saying to us but, we should remember that some of his wisest words are spoken by his biggest fools. For example, both ‘neither a borrower nor a lender be,’ and ‘to thine own self be true’ are from the foolish, garrulous and quite disreputable Polonius in Hamlet."

doc2 = "Mr. John Johnson Jr. was born in the U.S.A but earned his Ph.D. in Israel before joining Nike Inc. as an engineer. He also worked at craigslist.org as a business analyst."

doc3 = "Mr. Schmidt lief um, sagen wir, 13:00 Uhr nach Hause; er wollte sich schnell einen Krabbenburger (uvm.) machen. \"Hallo\", sagter er zu Joseph S., seinem Bruder."


def compare_sentence_split_options(nlp):
    for doc in [doc1, doc2, doc3]:
        # print("\nStart new doc:")
        # print("########### NLTK ############")
        # res = nltk.tokenize.sent_tokenize(doc, 'english')
        # print(f"Len: {len(res)}")
        # print('\n-----\n'.join(res))

        # print("\n\n######### Spacy ##############")
        # text = nlp(doc)
        # res = [sent for sent in text.sents]
        # print('\n-----\n'.join(res))
        # res = [sent.string.strip() for sent in text.sents]
        # print('\n-----\n'.join(res))

        # print("\n\n#######################")
        # res = re.split(r"\.(?![\w,;()])|\?|!|:(?!\w)|;", doc)  # own creation
        # print('\n-----\n'.join(res))

        # works best:
        print("\n\n#######################")
        res = re.split(r"(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s", doc)  # see https://stackoverflow.com/a/25736082
        print('\n-----\n'.join(res))

    print("\nFinished!")


def split_into_words():
    sentences = re.split(r"(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s", doc2)
    word_split_regex = r"\w+"
    for sent in sentences:
        words = re.findall(word_split_regex, sent)
        print(words)

    print("\n\n#######################")

    for sent in sentences:
        print(sent.split())  # split wins


def main():
    nlp = spacy.load('en_core_web_sm')  # install with ```python3 -m spacy download en_core_web_sm```
    # tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')  # import nltk; nltk.download('punkt')
    compare_sentence_split_options(nlp)
    split_into_words()


if __name__ == '__main__':
    main()
