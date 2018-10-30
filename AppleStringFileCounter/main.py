__author__ = 'Asaf Peleg'
# encoding=utf8

import argparse
import sys


# Logic:
# Run the script with the name of the .strings file as the argument. It will look at all strings that are NOT
# enclosed in /* or */ and then count the words, and output them to the screen.


reload(sys)
sys.setdefaultencoding('utf8')


def count_words_in_text(line):
    # The line is something like: "some english text" = "some other text";
    # We need to find the " = " and count only the words from the " = " until the ";"
    txtToCount = ""
    idxOfEqual = line.find("=")

    if idxOfEqual != -1:
        idxOfEOL = line.find(";", idxOfEqual + 1)
        if idxOfEOL != -1:
            txtToCount = line[idxOfEqual+1:idxOfEOL]
            words = txtToCount.split()
            return len(words)

    return 0


def count_words(fileName):
    content = None

    total_word_count = 0

    with open(fileName) as f:
        content = f.read()

    lines = content.splitlines()
    bLookAtNextLine = True

    textToAnalyze = ""

    # Algorithm for going over the lines:
    # 1. Look for an opening comment: /*
    # 2. If found, look for a closing /* in the same line.
    # 3. If not found in the same line, wait until we find it in the next line.
    # 4. Once found, I can count the words. If #1 is not found, I can count the words.
    for line in lines:
        if line.find("/*") == -1:
            # Count the words in this line, since we don't have an opening tag, unless we don't want to look at this
            # line.
            if bLookAtNextLine and line != "":
                # Now, look to see if we found an end of line mark (;). If we didn't, add this text to the total text
                # otherwise, send this text to count
                if line.find(";") == -1:
                    textToAnalyze += line
                else:
                    # In case this is a single line (i.e. the text to count doesn't extend over more than one line)
                    if textToAnalyze == "":
                        textToAnalyze = line

                    total_word_count += count_words_in_text(textToAnalyze)
                    textToAnalyze = ""
        else:
            # Found an opening /* tag, first, look for a closing tag in ths same line
            if line.find("*/") == -1:
                # Did not find a closing tag, so this means that we need to wait for the next line.
                bLookAtNextLine = False
            else:
                # Found a closing tag. So we can start the process on the next line.
                bLookAtNextLine = True

        if not bLookAtNextLine:
            if line.find("*/") <> -1:
                bLookAtNextLine = True

    return total_word_count


parser = \
    argparse.ArgumentParser(description='Count the words in an xCode strings file (ends with a .strings extension)')
parser.add_argument('--file', help='The file name to use')
args = parser.parse_args()

word_count = count_words(args.file)
print "total word count: " + str(word_count)
