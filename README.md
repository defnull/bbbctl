# Command-line tools for the BBB REST API

## Usage

```sh
export BBBCTL_SERVER=https://meet.gwdg.de/
export BBBCTL_SECRET=...
./bbbctl.py -h              # print help
./bbbctl.py meeting list    # list meetings
./bbbctl.py record list     # list recordings
...
```


## Output format

The default output format is currently a human readable plain text format. You
can switch to a more compact version with `--compact`. Other formats
(e.g. json, yaml or xml) may be supported in the future.


## Command overview

You can get detailed help with `./bbbctl.py -h` or `./bbbctl.py <command> -h`.

  * `record` Work with recordings
    * `list` List all recordings
    * `info <recordID>` Show info about a recording
    * `publishs <recordID>` Publish an unpublished recording
    * `unpublish <recordID>` Unpublish (hide) recording)
    * `delete <recordID>` Delete a recording
  * `meeting` List, inspect or end meetings
    * `list` List all meetings
    * `info <meetingID>` Show info about a meeting
    * `create <meetingID> <name>` Create a meeting and optionally print a bunch of join links
    * `join <meetingID> <name>` Generate a join link for a running meeting
    * `end <meetingID>` Forcefully end a meeting
    * `nuke` Forcefully end ALL meetings


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
