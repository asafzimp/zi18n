__author__ = 'Asaf Peleg'
# encoding=utf8

# Import declarations
import xlwt
import xlrd
from xml.dom import minidom
import os
import argparse
import json
import sys

# Constants
START_ROW = 1
KEY_COL = 0
EXPL_COL = 1
ENG_COL = 2
LANG_COL = 3

reload(sys)
sys.setdefaultencoding('utf8')


# Functions
def generate_translation_excel(input_file_name):
    """
    :param input_file_name: the input file to be used - should be an XML string table or a JSON String table.
    :return: the output file name (Excel file)
    Example of input XML:
    <?xml version="1.0" encoding="utf8.0"?>
    <resources>
        <string name="string_key">String Value</string>
    </resources>
    Example of input JSON:
    {
    "globals": {
        "DEVICEID": "Device ID",
        "NODATAFOUND": "No data found",
        }
    }
    """

    # First check the extension of the input file - if it's JSON, treat it one way, if it's an XML, then another.
    file_name, file_extension = os.path.splitext(input_file_name)
    print "Reading file: " + file_name

    # Create a dictionary of key value pairs.
    string_dict = {}

    if file_extension == ".xml":
        # XML
        xmldoc = minidom.parse(input_file_name)
        string_list = xmldoc.getElementsByTagName('string')
        for s in string_list:
            if s.firstChild is not None:
                string_dict[s.attributes['name'].value] = s.firstChild.nodeValue
    elif file_extension == ".json":
        with open(input_file_name, 'r') as content_file:
            json_file_contents = content_file.read()
            json_data = json.loads(json_file_contents)

            # The JSON File is built in a way that we have the "screen" name (or "globals") and inside it, we have the
            # actual keys. So, to make our lives easier - the key in the string table would be a combination of the
            # "master" key and the actual key.
            for master_key, screen_values in json_data.iteritems():
                master_key_str = str(master_key)
                for item_key, item_value in screen_values.iteritems():
                    if isinstance(item_value, dict):
                        # The item value is another dict. So, we need to go one level deeper. (Hack - since if we add
                        # more levels to this - it means we'll have to do a recourse... bad bad bad).
                        for sub_item_key, sub_item_value in item_value.iteritems():
                            actual_key = master_key_str + "." + item_key + "." + sub_item_key
                            if isinstance(sub_item_value, list):
                                # The value is a list. I'll save this with a specific delimiter - so I'll know to build
                                # this back as a list later.
                                item_list_string = ""
                                for the_item in sub_item_value:
                                    if item_list_string == "":
                                        item_list_string = the_item
                                    else:
                                        item_list_string += "**" + the_item
                                string_dict[actual_key] = item_list_string
                            else:
                                string_dict[
                                    actual_key] = sub_item_value  # Please note - the value might be an array/list
                                                                  # I'm OK with dumping a list as a value.
                    else:
                        actual_key = master_key_str + "." + item_key
                        string_dict[actual_key] = item_value
    else:
        raise "Invalid extension - has to be either XML or JSON."

    wb = xlwt.Workbook()
    ws = wb.add_sheet('Translations')

    # Write the header row.
    row_idx = START_ROW
    ws.write(START_ROW, KEY_COL, 'String Key')
    ws.write(START_ROW, EXPL_COL, 'Description/Instruction')
    ws.write(START_ROW, ENG_COL, 'Text')
    ws.write(START_ROW, LANG_COL, 'Translated Text')

    row_idx += 1

    # Create a row per item.
    for key, val in string_dict.iteritems():
        ws.write(row_idx, KEY_COL, key)
        ws.write(row_idx, EXPL_COL, '')
        ws.write(row_idx, ENG_COL, val)
        ws.write(row_idx, LANG_COL, '')
        row_idx += 1

    # Output file is the same name as the input file, but with a different extension
    _output_file_name = os.path.splitext(input_file_name)[0] + ".xls"

    wb.save(_output_file_name)

    return _output_file_name


def generate_string_dict_from_excel(input_file_name):
    """
    Generates a string dictionary from an excel file. Basically, goes over all of the items in the excel
    and return a dictionary with key/value pairs.
    :param input_file_name: The input excel file.
    :return: string dictionary.
    """
    file_name, file_extension = os.path.splitext(input_file_name)
    if file_extension != ".xls":
        raise "File name" + file_name + " is not with the correct extension. Has to be .xls only!"

    string_dict = {}

    # Loop over the excel, get the key and the translated value.
    wb = xlrd.open_workbook(input_file_name)
    sheet = wb.sheet_by_index(0)
    for row_idx in range(2, sheet.nrows):  # Start from the second line (don't get the titles...)
        # We need the key col and the lang (translated) col
        key = sheet.cell_value(row_idx, KEY_COL)
        translated = sheet.cell_value(row_idx, LANG_COL)
        original_english = sheet.cell_value(row_idx, ENG_COL)

        the_value = ""  # initialize with nothing.
        if translated != "":
            the_value = translated
        else:
            the_value = original_english

        string_dict[key] = the_value

    return string_dict


def generate_string_file(input_file_name):
    """
    Generates a string table file for Android translations. Basically goes over the string dictionary, and creates
    the corresponding XML record per key/value pair.
    :param input_file_name: Name of the input file.
    :return: Name of the output file - basically, same as the input file, but with .xml for the extension.
    """
    string_dict = generate_string_dict_from_excel(input_file_name)

    # Now create the XML file.
    # <string name="nmap_command">Choose scan parameters</string>
    _output_file_name = os.path.splitext(input_file_name)[0] + ".xml"
    o = open(_output_file_name, 'wb')
    header_string = '<?xml version="1.0" encoding="utf-8"?>'
    resources_open = '<resources>'
    resources_close = '</resources>'
    o.writelines(header_string.encode("utf-8"))
    o.writelines(resources_open.encode("utf-8"))
    for key, val in string_dict.iteritems():
        encoded_str = val.encode("utf-8")
        o.writelines('<string name="' + key + '">' + encoded_str + '</string>')
    o.writelines(resources_close.encode("utf-8"))

    return _output_file_name


def generate_json_file(input_file_name):
    """
    Generates a JSON file for the web app translations. Basically goes over each item in the key/value pairs, and
    recreates the JSON file needed by the web application.
    :param input_file_name: Name of the input file.
    :return: Name of the output file - basically, same as the input file, but with .json for the extension.
    """
    string_dict = generate_string_dict_from_excel(input_file_name)

    # Now we need to create the JSON. Please note - the JSON is hierarchical - which means that we need to read the key
    # and for each of the keys, we need to write it into the appropriate object.
    master_list = {}

    for key, val in string_dict.iteritems():

        screen_items = {}

        # Split the key into two, using a delimiter.
        items = key.split(".")

        master_key = items[0]
        deeper_hierarchy = False
        if len(items) > 2:
            deeper_hierarchy = True

        if len(items) > 1:
            item_key = items[1]

            # I actually need to create a dictionary (for the master key) that contains a dictionary of the actual
            # key/value pairs for that master key (screen).
            if master_list.has_key(master_key):
                screen_items = master_list[master_key]

            # If the item key has more than one level (i.e. datePicker.rangePicker.daysMin), we need to split that into
            # two levels.
            if not deeper_hierarchy:
                # Two levels only - use item_key as-is.
                if not screen_items.has_key(item_key):
                    screen_items[item_key] = val#.encode("utf-8")

                master_list[master_key] = screen_items
            else:
                # More than two levels... we need to create a new sub-key here, and then use the value based on what
                # it was originally.
                # So, screen_items is basically just like the master_list, it's a dictionary. So, I need to handle it
                # the same way.
                # First, I need to generate the original item_key to see if I already have something for it.
                upd_screen_items = {}
                if screen_items.has_key(item_key):
                    upd_screen_items = screen_items[item_key]

                if not upd_screen_items.has_key(items[2]):
                    if "**" in val:
                        # This is a list, split and use that as the value
                        arr = val.split("**")
                        upd_screen_items[items[2]] = arr
                    else:
                        upd_screen_items[items[2]] = val#.encode("utf-8")

                screen_items[item_key] = upd_screen_items

    _output_file_name = os.path.splitext(input_file_name)[0] + ".json"
    o = open(_output_file_name, 'w')
    o.write(json.dumps(master_list, indent=1, ensure_ascii=False))
    o.close()

    return _output_file_name


def generate_translation_files(base_file, base_folder):

    # Build a dictionary of keys, and then build a dictionary of the keys in each sub-file and do a comparison
    string_dict = {}
    xmldoc = minidom.parse(base_file)
    string_list = xmldoc.getElementsByTagName('string')
    for s in string_list:
        if s.firstChild is not None:
            string_dict[s.attributes['name'].value] = s.firstChild.nodeValue

    # Now I have the base string list, I need to compare all others against.
    for dirName, subdirList, fileList in os.walk(base_folder):
        for file_name in fileList:
            if file_name.find(".xml") >= 0 and not (dirName + "/" + file_name == base_file):
                localized_xml_doc = minidom.parse(dirName + "/" + file_name)
                localized_string_dict = {}
                new_strings_dict = {}
                localized_string_list = localized_xml_doc.getElementsByTagName('string')
                for s in localized_string_list:
                    if s.firstChild is not None:
                        localized_string_dict[s.attributes['name'].value] = s.firstChild.nodeValue

                # Now compare against the base string dict, and add anything that's there and not here to this list
                for key, value in string_dict.iteritems():
                    if key not in localized_string_dict:
                        new_strings_dict[key] = value

                _output_file_name = dirName + "/" + os.path.splitext(file_name)[0] + "_upd.xml"
                o = open(_output_file_name, 'wt')
                header_string = '<?xml version="1.0" encoding="utf-8" standalone="no"?>\n'
                resources_open = '<resources>\n'
                resources_close = '</resources>\n'
                o.writelines(header_string.encode("utf-8"))
                o.writelines(resources_open.encode("utf-8"))
                for key, val in new_strings_dict.iteritems():
                    encoded_str = val.encode("utf-8")
                    o.writelines('<string name="' + key + '">' + encoded_str + '</string>\n')
                o.writelines(resources_close.encode("utf-8"))


parser = argparse.ArgumentParser(description='Generate String Table/String Excel File')
parser.add_argument('--file', help='The file name to use')
parser.add_argument('--op', help='What operation to do: excel - generate excel, table - generate string table')
parser.add_argument('--base_folder', help='Base folder when compiling differences')

args = parser.parse_args()
out_file_name = ""

if args.op == "excel":
    print "Generating Excel File..."
    out_file_name = generate_translation_excel(args.file)
    print "Done. Output file: " + out_file_name
elif args.op == "table":
    print "Generating String Table File..."
    out_file_name = generate_string_file(args.file)
    print "Done. Output file: " + out_file_name
elif args.op == "json":
    print "Generating JSON Key File..."
    out_file_name = generate_json_file(args.file)
    print "Done. Output file: " + out_file_name
elif args.op == "compile_android":
    print "Compiling missing translations..."
    generate_translation_files(args.file, args.base_folder)
else:
    parser.print_help()
