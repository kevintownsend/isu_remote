#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright 2014 Kevin Townsend
# Copyright 2011 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from html.parser import *
from urllib.request import *
from subprocess import *
from sys import *
from os.path import *

home = expanduser("~")
user_info = "user_config.py"


def _PrepareFileData(file_lines):
    # For each line, remove comments and trim all spaces at beginning and the end.
    for i in range(len(file_lines)):
        comment_index = file_lines[i].find('#')
        if comment_index != -1:
            file_lines[i] = file_lines[i][:comment_index]
        file_lines[i] = file_lines[i].strip()

    # Join all lines into a single string, being careful to remove empty lines.
    return '\n'.join(line for line in file_lines if line)

def _ReadDataImpl(filename):
    """Read the persistent data from the specified file, which should be
    formatted as a python dict.

    Args:
        filename: Name of the file with the data to load.

    Returns:
        A python dictionary with the file contents.

    Raises:
        error.InternalError: If there is any error while reading the data from the
            file.
    """
    try:
        # Open the configuration file and read all lines from it.
        file = open(filename, 'rt')
        file_lines = file.readlines()
        file.close()

        # Prepare the file data to prevent mistakes and evaluate it as if it were a
        # python dictionary.
        file_data = _PrepareFileData(file_lines)
        return eval(file_data, {}, {})
    except IOError as e:
        raise IOError('IO error happened while reading data from file '
                              '"{0}" : {1}.\n'.format(filename, e))

try:
    userInfo = _ReadDataImpl(user_info)
except IOError:
    print("""no user_config.py file
Create a file called user_config.py with contents:
{
'username'  : '',
'password'  : ''
}
""")
username = userInfo['username']
password = userInfo['password']
if(username == ""):
    username = input("Enter username:")

lowestLoadServer = "none"
serverLoadPairs = []
class MyHTMLParser(HTMLParser):
    encounteredContent = False
    readingServerName = False
    readingServerLoad = False
    readingTable = False
    currentServerName = ""
    column = 0
    lowestLoad = 100
    subPreference = 0
    inTd = False
    global lowestLoadServer
    def handle_starttag(self,tag,attrs):
        if(tag == "td"):
            if(len(attrs) == 0):
                self.readingServerName = True
            if(len(attrs) == 2):
                self.readingServerLoad = True
            self.inTd = True
        elif(tag == "tr"):
            self.column = 0
            self.subPreference = 0
        elif(tag == "table"):
            if(len(attrs) == 1):
                if(attrs[0][0] == "class" and attrs[0][1] == "remote"):
                    self.readingTable = True
    def handle_data(self, data):
        if(self.readingServerName):
            self.currentServerName = data
        if(self.readingServerLoad):
            load = 4
            if(data == "Low"):
                load = 1
            elif(data == "Medium"):
                load = 2
            elif(data == "High"):
                load = 3
            load = load - self.subPreference
            serverLoadPairs.append((load,self.currentServerName))
        if(self.column == 1 and self.readingTable and self.inTd):
            memory = data.split()[0]
            self.subPreference = self.subPreference + int(memory) / 100.0 / 100.0
        if(self.column == 2 and self.readingTable and self.inTd):
            cpu = data.split()[0]
            self.subPreference = self.subPreference + int(cpu) / 100.0

    def handle_endtag(self,tag):
        if(tag == "td"):
            self.readingServerName = False
            self.readingServerLoad = False
            self.column = self.column + 1
            self.inTd = False
        elif(tag == "table"):
            self.readingTable = False

try:
    f = urlopen("http://it.engineering.iastate.edu/ece-remote-servers")
except URLError:
    print("Unable to open it.engineering.iastate.edu. Try connecting to the internet.")

feed = ""
for line in f:
    try:
        data = str(line)
    except EOFError:
        break
    feed = feed + data

loginToBestServer = True

if(len(argv) == 2):
    if(argv[1] == "last"):
        loginToBestServer = False
        infoFile = open(home + "/.isu_remote_info", "r")
        line = infoFile.readline()
        server = line.split(':')[1].strip()
        login = username + "@" + server
        print("attempting to attach to " + login)
        if(password == ""):
            call(["ssh", "-X", login])
        else:
            ret = call(["sshpass", "-p", password, "ssh", "-X", login])
            if(ret == 6):
                call(["ssh", "-X", login])
            elif(ret == 5):
                print("Incorrect password")



if(loginToBestServer):

    parser = MyHTMLParser()
    parser.feed(feed)
    serverLoadPairs.sort()
    i = 0

    if(len(serverLoadPairs)==0):
        print("No servers listed, they might be down.")
        pass

    choosenServer = ""
    for pair in serverLoadPairs:
        choosenServer = pair[1]
        if(i == 3):
            break
        login = username + "@" + pair[1]
        print("attempting to attach to " + login)
        i = i + 1
        try:
            if(password == ""):
                call(["ssh", "-X", login])
            else:
                ret = call(["sshpass", "-p", password, "ssh", "-X", login])
                if(ret == 6):
                    call(["ssh", "-X", login])
                elif(ret == 5):
                    print("Incorrect password")

            break
        except KeyboardInterrupt:
            print("Trying next server")

infoFile = open(home + "/.isu_remote_info", "w")
infoFile.write("lastServer : " + choosenServer + "\n")
infoFile.close()

#NOTICE:
# The software from Google contains significant changes. I am not a lawyer and am not sure of
# the correct way to attribute the first two functions to the Google open source project 
# "Google Code Jam Commandline".
