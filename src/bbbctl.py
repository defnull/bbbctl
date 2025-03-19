#!/usr/bin/env python3

import argparse
import urllib.request
import urllib.parse
import hashlib
import sys, os
import xml.etree.ElementTree as ET
import json
import datetime
import ssl

__all__ = ["BBBApiClient", "ApiError"]


class ApiError(RuntimeError):
    def __init__(self, tree):
        self.tree = tree

    def __str__(self):
        return format_human(self.tree)


class BBBApiClient:
    def __init__(self, api, secret, ssl_context=None):
        self.api = api.rstrip("/")
        self.secret = secret
        self.ssl = ssl_context or ssl.create_default_context()

    def makeurl(self, command, **query):
        query = urllib.parse.urlencode({k:v for k,v in query.items() if v is not None})
        checksum = hashlib.sha1(
            (command + query + self.secret).encode("utf8")
        ).hexdigest()
        if query:
            query += "&"
        query += "checksum=" + checksum
        return "%s/%s?%s" % (self.api, command, query)

    def call(self, command, **query):
        url = self.makeurl(command, **query)
        with urllib.request.urlopen(url, context=self.ssl) as f:
            xml = f.read().decode("utf8")
        root = ET.fromstring(xml)
        if root.find("./returncode").text != "SUCCESS":
            raise ApiError(root)
        return root

    def getJoinLink(self, **query):
        return self.makeurl("join", **query)

    def getMeetings(self, **query):
        return self.call("getMeetings", **query).findall("./meetings/meeting")

    def getRecordings(self, **query):
        return self.call("getRecordings", **query).findall("./recordings/recording")

    def getMeetingInfo(self, **query):
        return self.call("getMeetingInfo", **query)

    def createMeeting(self, **query):
        return self.call("create", **query)

    def end(self, **query):
        return self.call("end", **query)

    def publishRecordings(self, recordID, publish):
        return self.call("publishRecordings", recordID=recordID, publish=publish)

    def deleteRecordings(self, recordID):
        return self.call("deleteRecordings", recordID=recordID)

    def sendChatMessage(self, meetingID, message, userName=None):
        return self.call("sendChatMessage", meetingID=meetingID, message=message, userName=userName)


def build_parser():

    parser = argparse.ArgumentParser()
    main_sub = parser.add_subparsers(title="Commands")

    parser.add_argument(
        "--server",
        help="Server URL (default: BBBCTL_SERVER or local config)",
    )
    parser.add_argument(
        "--secret",
        help="API secretd (default: BBBCTL_SECRET or local config)",
    )
    parser.add_argument(
        "--insecure",
        help="Skip TLS verification and accept self-signed or invalid SSL certificates as if they were valid",
    )

    parser.add_argument(
        "--format",
        help="Change output format.",
        choices=["human", "compact", "xml", "json", "jsonline"],
        default="human",
    )

    rec = main_sub.add_parser(
        "record",
        help="List, show, publish, unpublish or delete recordings",
    )
    rec_sub = rec.add_subparsers(title="Commands")

    cmd = rec_sub.add_parser("list", help="List all recordings")
    cmd.add_argument("--meeting", help="Filter by external meetingID")
    cmd.set_defaults(cmd=cmd_rec_list)

    cmd = rec_sub.add_parser("info", help="Show info about a recording")
    cmd.add_argument("id", help="Recording ID")
    cmd.set_defaults(cmd=cmd_rec_show)

    cmd = rec_sub.add_parser("publish", help="Publish a recording")
    cmd.add_argument("id", help="Recording ID")
    cmd.set_defaults(cmd=cmd_rec_pub)

    cmd = rec_sub.add_parser("unpublish", help="Unpublish a recording")
    cmd.add_argument("id", help="Recording ID")
    cmd.set_defaults(cmd=cmd_rec_unpub)

    cmd = rec_sub.add_parser("delete", help="Delete a recording")
    cmd.add_argument("id", help="Recording ID")
    cmd.set_defaults(cmd=cmd_rec_del)

    meet = main_sub.add_parser(
        "meeting", help="List, inspect, create, join or end meetings"
    )
    meet_sub = meet.add_subparsers()

    cmd = meet_sub.add_parser("list", help="List meetings")
    cmd.add_argument("--sort", help="Sort by a specific key")
    cmd.add_argument("--no-user", action="store_true", help="Do not show participants")
    cmd.set_defaults(cmd=cmd_meet_list)

    cmd = meet_sub.add_parser("info", help="Show meeting details")
    cmd.add_argument("id", help="Meeting ID")
    cmd.set_defaults(cmd=cmd_meet_show)

    cmd = meet_sub.add_parser("create", help="Create meeting")
    cmd.add_argument("id", help="Meeting ID")
    cmd.add_argument("name", help="Meeting name")
    cmd.add_argument("--record", help="Allow recording?", action="store_true")
    cmd.add_argument(
        "--mod",
        help="Directly create and print a moderator join link for this username. Can be repeated.",
        action="append",
    )
    cmd.set_defaults(cmd=cmd_meet_create)

    cmd = meet_sub.add_parser("join", help="Generate a join link for a meeting")
    cmd.add_argument(
        "--mod", action="store_true", help="Join as moderator (default: attendee)"
    )
    cmd.add_argument(
        "--open",
        action="store_true",
        help="Open the link directly in a webbrowser (default: print it)",
    )
    cmd.add_argument("id", help="Meeting ID")
    cmd.add_argument("name", help="Display name")
    cmd.set_defaults(cmd=cmd_meet_join)

    cmd = meet_sub.add_parser("end", help="End meeting")
    cmd.add_argument("id", help="Meeting ID")
    cmd.set_defaults(cmd=cmd_meet_end)

    cmd = meet_sub.add_parser("chat", help="Send a chat message into a running meeting (BBB 3.0)")
    cmd.add_argument("id", help="Meeting ID. Can be 'BROADCAST' do broadcase a message to all running meetings")
    cmd.add_argument("message", help="The message to send to chat")
    cmd.add_argument("--name", help="The name that will be shown as the sender of the chat message", default="SYSTEM")
    cmd.set_defaults(cmd=cmd_meet_chat)

    cmd = meet_sub.add_parser("nuke", help="End ALL meeting")
    cmd.add_argument("--doit", help="Disable dry-run mode and actually end meetings?", action="store_true")
    cmd.add_argument("--ask", help="Ask for every meeting?", action="store_true")
    cmd.set_defaults(cmd=cmd_meet_nuke)

    return parser


def error(text):
    print(text, file=sys.stderr)
    sys.exit(1)


config_paths = [
    "/etc/bigbluebutton/bbb-web.properties",
    "/usr/share/bbb-web/WEB-INF/classes/bigbluebutton.properties",
    "/var/lib/tomcat7/webapps/bigbluebutton/WEB-INF/classes/bigbluebutton.properties",
    "./bbbctl.conf",
]


def find_bbb_property(name):
    for fname in config_paths:
        if not os.path.isfile(fname):
            continue
        if not os.access(fname, os.R_OK):
            error("Permission denied. Unable to read: {!r}".format(fname))
        with open(fname, "r") as fp:
            for line in fp:
                key, _, value = line.partition("=")
                if _ and key.strip() == name:
                    return value.strip()
        error("Value for {!r} not found in {}".format(name, fname))


def main():
    parser = build_parser()
    args = parser.parse_args()
    if not hasattr(args, "cmd"):
        parser.parse_args(sys.argv[1:] + ["-h"])

    server = (
        args.server
        or os.environ.get("BBBCTL_SERVER")
        or find_bbb_property("bigbluebutton.web.serverURL")
        or error("No server specified")
    )
    secret = (
        args.secret
        or os.environ.get("BBBCTL_SECRET")
        or find_bbb_property("securitySalt")
        or error("No secret specified")
    )

    server = server.rstrip("/")
    if "://" not in server:
        server = "https://" + server
    if not server.endswith("/bigbluebutton/api"):
        server += "/bigbluebutton/api"

    ctx = ssl.create_default_context()
    if args.insecure:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

    client = BBBApiClient(server, secret, ssl_context=ctx)

    try:
        args.cmd(client, args)
    except ApiError as e:
        error(e)


def format(element, args):
    if args.format == "compact":
        return format_compact(element)
    if args.format == "xml":
        return format_xml(element)
    if args.format == "json":
        return format_json(element, indent=2)
    if args.format == "jsonline":
        return format_json(element)
    return format_human(element)


def safe_str(s):
    if any(c in s for c in "\n ,\"'="):
        return json.dumps(s)
    return s


def format_human(e, indent=""):
    value = e.text and e.text.strip()
    result = indent + e.tag + ":"
    if e.tag.lower() in ("starttime", "endtime"):
        value = "%s (%s)" % (
            datetime.datetime.fromtimestamp(float(value) / 1000, datetime.timezone.utc),
            value,
        )
    if value:
        result += " " + safe_str(value)
    for child in e:
        result += "\n" + format_human(child, indent + "  ")
    return result


def format_compact(e):
    tag = e.tag
    value = e.text and e.text.strip()
    if value:
        tag += "=" + safe_str(value)
    if len(e):
        tag += "(" + ", ".join(format_compact(child) for child in e) + ")"
    return tag


def format_xml(e):
    return ET.tostring(e, encoding="unicode")


def format_json(e, *a, **ka):
    return json.dumps(_unpack_xml(e), *a, **ka)


_should_be_list = ["attendees"]
_should_be_number = [
    "createTime",
    "duration",
    "startTime",
    "endTime",
    "participantCount",
    "listenerCount",
    "voiceParticipantCount",
    "videoCount",
    "maxUsers",
    "moderatorCount",
]


def _unpack_xml(e):
    if e.tag in _should_be_list:
        return [_unpack_xml(c) for c in e if e.tag]
    if len(e):
        return {c.tag: _unpack_xml(c) for c in e if c.tag}
    value = e.text and e.text.strip()
    if e.tag in _should_be_number:
        return int(value)
    if not value:
        return None
    if value in ("true", "false"):
        return value == "true"
    return value


def cmd_rec_list(api, args):
    opts = {}
    if args.meeting:
        opts["meetingID"] = args.meeting
    for recording in api.getRecordings(**opts):
        print(format(recording, args))


def cmd_rec_show(api, args):
    print(format(api.getRecordings(recordID=args.id)[0], args))


def cmd_rec_pub(api, args):
    print(format(api.publishRecordings(recordID=args.id, publish="true"), args))


def cmd_rec_unpub(api, args):
    print(format(api.publishRecordings(recordID=args.id, publish="false"), args))


def cmd_rec_del(api, args):
    print(format(api.deleteRecordings(recordID=args.id), args))


def sortkey(elem, key):
    v = elem.find(key)
    return int(v.text.strip())


def cmd_meet_list(api, args):
    meetings = list(api.getMeetings())
    if args.sort:
        meetings = sorted(meetings, key=lambda m: sortkey(m, args.sort))
    if args.no_user:
        for m in meetings:
            m.remove(m.find("attendees"))
    for meeting in meetings:
        print(format(meeting, args))


def cmd_meet_show(api, args):
    print(format(api.getMeetingInfo(meetingID=args.id), args))


def cmd_meet_create(api, args):
    created = api.createMeeting(
        meetingID=args.id, name=args.name, record=args.record and "true" or "false"
    )
    print(format(created, args))

    if args.mod:
        print()
        for name in args.mod:
            link = api.getJoinLink(
                meetingID=args.id,
                fullName=name,
                createTime=created.find("createTime").text,
                role="MODERATOR",
            )
        print(name + ":", link)


def cmd_meet_join(api, args):
    meeting = api.getMeetingInfo(meetingID=args.id)
    query = {"meetingID": args.id, "fullName": args.name}
    query["createTime"] = meeting.find("createTime").text
    query["role"] = "MODERATOR" if args.mod else "VIEWER"
    link = api.getJoinLink(**query)

    if args.open:
        import webbrowser

        webbrowser.open_new_tab(link)
    else:
        print(link)


def cmd_meet_end(api, args):
    pwd = api.getMeetingInfo(meetingID=args.id).find("moderatorPW").text
    api.end(meetingID=args.id, password=pwd)


def cmd_meet_chat(api, args):
    if args.id == "BROADCAST":
        meetings = [m.find("meetingID").text for m in api.getMeetings()]
    else:
        meetings = [args.id]

    for meeting in meetings:
        api.sendChatMessage(meeting, args.message, userName=args.name)


def cmd_meet_nuke(api, args):
    meetings = list(api.getMeetings())
    for meeting in meetings:
        print(
            "{dryrun}id={id} user={users} name={name!r}".format(
                dryrun="" if args.doit else "(dry run) ",
                id=meeting.find("meetingID").text,
                users=meeting.find("participantCount").text,
                name=meeting.find("meetingName").text,
            )
        )
        if args.doit:
            if args.ask:
                answer = input("End this meeting? [Yna] ").strip().lower()
                if answer == "a":
                    args.ask = False
                elif answer in ("", "y"):
                    pass
                else:
                    continue
            api.end(meetingID=meeting.find("meetingID").text)


if __name__ == "__main__":
    main()
