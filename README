BZRFlag: BZFlag with Robotic Tanks!
=======

Developed by the BYU AML Lab to support the objectives of Brigham Young
University CS 470 "Introduction to Artificial intelligence." 

Copyright 2008-2011 Brigham Young University, and distributed under the GNU GPL.

Comments and suggentions are welcome at: kseppi@byu.edu


Installation:
You may need to install the pyparsing and pygame pkgs before running the barflag
server. If you're a CS470 student you will also need to use telnet for one of
the assignments, but that shouldn't be difficlt to install if you don't already
have it.

Zip and tar source distributions are maintained at:

    http://code.google.com/p/bzrflag/

but can also be obtained by simply cloning the git reposatory. Use:

    [you@yourmachine ~]$ git clone git://aml.cs.byu.edu/bzrflag.git

For windows, use the windows equivalent, or the provided git gui.

After downloading and unziping the distribution of your choice, run:

    [you@yourmachine bzrflag]$ python setup.py install (if on linux, or)

    ???(on windows)

...(not finished... Add windows instructions and how to run tests)



Running the game:
The server can be run with the command: (assuming you are in the bzrflag dir)

    [you@yourmachine bzrflag]$ ./bin/bzrflag

To get a list of the command line options you can use, run:

    [you@yourmachine bzrflag]$ ./bin/bzrflag -h

Note that if you are on a laptop with low resolution, or in any event the window
size is too big, the option to change the size of the window is:

    --window-size=[size]x[size]

The included simple agent can now be run (from a new window) using:

    [you@yourmachine bzrflag]$ python bzagents/agent0.py localhost [port]

If you want to control the tanks manually, start up the server, then open
another terminal and run: (use one of the ports printed out by bzrflag)

    [you@yourmachine bzrflag]$ telnet localhost [port] 

The robotic tanks should introduce themselves by saying:

    bzrobots 1

Reply with:

    agent 1

You should now be connected, and may begin typing commands. For example, type
'shoot 0' to send the command to tank 0 to shoot. You can use the 'help' command
to get a list of all the commands available, or 'help [command]' to get help for
a specific command.

The game, of course, can also be run with the included simple agent using the 
example shell script provided (example batch files are also included).
   



