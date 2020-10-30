#!/usr/bin/env python3

import argparse
import urllib.request
import urllib.parse
import hashlib
import sys, os
import xml.etree.ElementTree as ET
from xml.dom import minidom
import json
import datetime

class ApiError(RuntimeError):
  def __init__(self, tree):
    self.tree = tree

  def __str__(self):
    return format_human(self.tree)

class BBBApiClient:
  def __init__(self, api, secret):
    self.api = api.rstrip('/')
    self.secret = secret

  def call(self, command, **query):
    query = urllib.parse.urlencode(query)
    checksum = hashlib.sha1((command+query+self.secret).encode('utf8')).hexdigest()
    if query:
      query += "&"
    query += "checksum=" + checksum
    url = '%s/%s?%s' % (self.api, command, query)
    with urllib.request.urlopen(url) as f:
      xml = f.read().decode('utf8')
    root = ET.fromstring(xml)
    if root.find('./returncode').text != "SUCCESS":
      raise ApiError(root)
    return root

  def getMeetings(self, **query):
    return self.call('getMeetings', **query).findall('./meetings/meeting')

  def getRecordings(self, **query):
    return self.call('getRecordings', **query).findall('./recordings/recording')

  def getMeetingInfo(self, **query):
    return self.call('getMeetingInfo', **query)

  def end(self, **query):
    return self.call('end', **query)

  def publishRecordings(self, recordID, publish):
    return self.call('publishRecordings', recordID=recordID, publish=publish)

  def deleteRecordings(self, recordID):
    return self.call('deleteRecordings', recordID=recordID)


def build_parser():

  def add_format_args(p):
    grp = p.add_mutually_exclusive_group()
    grp.add_argument("--compact", action="store_true", help="Print result in compact form (one per line)")
    #grp.add_argument("--json", action="store_true", help="Print result as json")
    #grp.add_argument("--csv", help="Print named fields as CSV")

  parser = argparse.ArgumentParser()
  main_sub = parser.add_subparsers(title="Commands")
  add_format_args(parser)

  rec = main_sub.add_parser('record', help='List, show, publish, unpublish or delete recordings')
  rec_sub = rec.add_subparsers(title="Commands")

  rec_list = rec_sub.add_parser('list', help='List all recordings')
  rec_list.add_argument('--meeting', help='Filter by external meetingID')
  rec_list.set_defaults(cmd=cmd_rec_list)

  rec_show = rec_sub.add_parser('info', help='Show info about a recording')
  rec_show.add_argument('id', help='Recording ID')
  rec_show.set_defaults(cmd=cmd_rec_show)

  rec_pub = rec_sub.add_parser('publish', help='Publish a recording')
  rec_pub.add_argument('id', help='Recording ID')
  rec_pub.set_defaults(cmd=cmd_rec_pub)

  rec_unpub = rec_sub.add_parser('unpublish', help='Unpublish a recording')
  rec_unpub.add_argument('id', help='Recording ID')
  rec_unpub.set_defaults(cmd=cmd_rec_unpub)

  rec_del = rec_sub.add_parser('delete', help='Delete a recording')
  rec_del.add_argument('id', help='Recording ID')
  rec_del.set_defaults(cmd=cmd_rec_del)

  meet = main_sub.add_parser('meeting', help='List, inspect, end or change meetings')
  meet_sub = meet.add_subparsers()

  meet_list = meet_sub.add_parser('list', help='List meetings')
  meet_list.add_argument('--sort', help='Sort by a specific key')
  meet_list.add_argument('--no-user', action="store_true", help='Do not show participatns')
  meet_list.set_defaults(cmd=cmd_meet_list)

  meet_show = meet_sub.add_parser('info', help='Show meeting')
  meet_show.add_argument('id', help='Meeting ID')
  meet_show.set_defaults(cmd=cmd_meet_show)

  meet_end = meet_sub.add_parser('end', help='End meeting')
  meet_end.add_argument('id', help='Meeting ID')
  meet_end.set_defaults(cmd=cmd_meet_end)

  return parser

def error(text):
  print(text, file=sys.stderr)
  sys.exit(1)

def main():
  parser = build_parser()
  args = parser.parse_args()
  if not hasattr(args, 'cmd'):
    parser.parse_args(sys.argv[1:] + ["-h"])

  try:
    apiurl = os.environ["BBBCTL_SERVER"].rstrip("/")
    if not apiurl.endswith('/bigbluebutton/api'):
      apiurl += '/bigbluebutton/api'
    secret = os.environ["BBBCTL_SECRET"]
  except KeyError:
    error("Please set BBBCTL_SERVER and BBBCTL_SECRET environment variables.")

  client = BBBApiClient(apiurl, secret)

  try:
    args.cmd(client, args)
  except ApiError as e:
    error(e)

def format(element, args):
  if args.compact:
    return format_compact(element)
  return format_human(element)

def save_str(s):
  if any(c in s for c in '\n ,"\'='):
    return json.dumps(s)
  return s

def format_human(e, indent=""):
  value = e.text and e.text.strip()
  result = indent + e.tag + ":"
  if e.tag.lower() in ('starttime', 'endtime'):
    value = '%s (%s)' % (datetime.datetime.utcfromtimestamp(float(value)/1000), value)
  if value:
    result += " " + save_str(value)
  for child in e:
    result += "\n" + format_human(child, indent+"  ")
  return result

def format_compact(e):
  tag = e.tag
  value = e.text and e.text.strip()
  if value:
    tag += "=" + save_str(value)
  if len(e):
    tag += "(" + ", ".join(format_compact(child) for child in e) + ")"
  return tag;

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

def cmd_meet_end(api, args):
  pwd = api.getMeetingInfo(meetingID=args.id).find("moderatorPW").text
  api.end(meetingID=args.id, password=pwd)

if __name__ == '__main__':
  main()
