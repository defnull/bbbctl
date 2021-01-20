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

You can geht detailed help with `./bbbctl.py -h` or `./bbbctl.py <command> -h`.

  * `record` Work with recordings
    * `list` List all recordings
    * `info <recordID>` Show info about a recording
    * `publishs <recordID>` Publish an unpublished recording
    * `unpublish <recordID>` Unpublish (hide) recording)
    * `delete <recordID>` Delete a recording
  * `meeting` List, inspect or end meetings
    * `list` List all meetings
    * `info <meetingID>` Show info about a meeting
    * `end <meetingID>` Forcefully end a meeting
    * `join <meetingID> <name>` Generate a join link for a running meeting


