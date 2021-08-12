# BigBlueButton REST API command-line client

This is a small but useful command-line client for controlling meetings and recordings on a [BigBlueButton](https://docs.bigbluebutton.org/) server or cluster directly via the [REST API](https://docs.bigbluebutton.org/dev/api.html). It allows administrators to bypass front-end applications ([greenlight](https://github.com/bigbluebutton/greenlight), [moodle](https://moodle.com/certified-integrations/bigbluebutton/) or alternatives) and directly access the backing BBB servers for administative tasks, monitoring or testing.

The module can also be imported as a python library, but please note that this project is not yet considered stable in any way. A stable and more usable API for python skripting might follow.

## Install

```sh
# Install via pip
sudo pip install -U bbbctl
# or manually:
sudo curl -L https://raw.githubusercontent.com/defnull/bbbctl/master/src/bbbctl.py -o /usr/local/bin/bbbctl
sudo chmos +x /usr/local/bin/bbbctl
```

## Usage

```sh
export BBBCTL_SERVER="https://bbb.example.com/"
export BBBCTL_SECRET="..."
bbbctl meeting list    # Test your secret by listing current meetings
bbbctl -h              # Print help for a list of commands

# or, if run directly on a BBB server
bbbctl --local meeting list
```

## Command overview

You can get detailed help and a list of all parameters with `bbbctl -h` or `bbbctl <command> -h`.

- `meeting` Create, list, join, inspect or end meetings
  - `list` List all meetings
  - `info <meetingID>` Show info about a meeting
  - `create <meetingID> <title>` Create a new meeting
  - `join <meetingID> <displayName>` Generate join links
  - `end <meetingID>` Forcefully end a meeting
  - `nuke` Forcefully end ALL meetings (be careful)
- `record` Work with recordings
  - `list` List all recordings
  - `info <recordID>` Show info about a recording
  - `publish <recordID>` Publish an unpublished recording
  - `unpublish <recordID>` Unpublish (hide) recording)
  - `delete <recordID>` Delete a recording

## Output format

The default output format is currently a human readable plain text format. You can switch to a more compact version with `--format=compact`. Other formats (e.g. `json`, `yaml` or `xml`) may be supported in the future.

# License

Copyright (c) 2020-2021, Marcel Hellkamp.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
