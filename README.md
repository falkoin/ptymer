![unit tests passing](https://github.com/falkoin/ptymer/actions/workflows/main.yml/badge.svg?event=push)

# ptymer
A simple CLI work timer written in Python.

This started as a pet project to get familiar with developing cli applications. My intention was to create something
that I would use myself and not just a random prototype. As it turned out, I use this work timer on a daily basis (on work
days). It is very simple. It doesn't support projects, since I am only working in one project. So, it is merely to track
my daily work time. It also doesn't alert you, when your work time is over or anything similar. It is just a tool to
create timestamps when you started or stopped/paused and tracks your overall work time.

Some features that are intended to be developed in the future are listed below. Additional features might occur on this 
list, when I have the need for them.

## Commands
    app.py <command>
           start # starts the session
           stop # stops or pauses the session
           show # shows your current progress 
           week # shows worktime per day for the current week
           start/stop --delta INTEGER # sets timestamp x minutes earlier
           timestamps "YYYY-MM-DD" # lists timestamps for date, default is today
           delete INTEGER # deletes timestamp by id
           add "YYYY-MM-DD HH:MM:SS" <event> ("start"/"stop") # adds timestamp
    app.py --help

## Installation and Usage
- Use `pipenv install`
- `pipenv shell`
- `python app.py start`

## TODO
- [x] Migrate to SQLite
- [x] Gain 100 % test-coverage
- [x] Show statistics
- [x] Make output more graphical
- [x] Implement as "real" terminal commands
- [x] Add editing feature to entries
- [x] Add more information to output
- [ ] Create specific exceptions
- [ ] Switch to better datetime handling
