#!/usr/bin/env python3

import argparse
import urllib.request
import urllib.parse
import hashlib
import sys
import os
import xml.etree.ElementTree as ET
import json
import datetime
import ssl

__all__ = ["BBBApiClient", "ApiError"]


CREATE_PARAMS = {
    #'name': (str, 'A name for the meeting. Added in 2.4: This parameter is now required.'),
    #'meetingID': (str, 'A meeting ID that can be used to identify this meeting by the 3rd-party application. This must be unique to the server that you are calling: different active meetings can not have the same meeting ID. If you supply a non-unique meeting ID (a meeting is already in progress with the same meeting ID), then if the other parameters in the create call are identical, the create call will succeed (but will receive a warning message in the response). The create call is idempotent: calling multiple times does not have any side effect. This enables a 3rd-party applications to avoid checking if the meeting is running and always call create before joining each user. Meeting IDs should only contain upper/lower ASCII letters, numbers, dashes, or underscores. A good choice for the meeting ID is to generate a GUID value as this all but guarantees that different meetings will not have the same meetingID.'),
    #'attendeePW': (str, 'The password that the join URL can later provide as its password parameter to indicate the user will join as a viewer. If no attendeePW is provided, the create call will return a randomly generated attendeePW password for the meeting. Deprecated: If the role parameter is used on the join URL, the attendeePW is unused.'),
    #'moderatorPW': (str, 'The password that will join URL can later provide as its password parameter to indicate the user will as a moderator. if no moderatorPW is provided, create will return a randomly generated moderatorPW password for the meeting. Deprecated: If the role parameter is used on the join URL, the moderatorPW is unused.'),
    "welcome": (
        str,
        "A welcome message that gets displayed in the Session Details area when the participant joins (check the value of `showSessionDetailsOnJoin` in bbb-html5 settings.yml to control the state of the pop-up on join). You can include keywords ( %%CONFNAME%% , %%DIALNUM%% , %%CONFNUM%% ) which will be substituted automatically. This parameter overrides the default defaultWelcomeMessage in bigbluebutton.properties . The welcome message has limited support for HTML formatting. Be careful about copy/pasted HTML from e.g. MS Word, as it can easily exceed the maximum supported URL length when used on a GET request.",
    ),
    "dialNumber": (
        str,
        "The dial access number that participants can call in using regular phone. You can set a default dial number via defaultDialAccessNumber in bigbluebutton.properties",
    ),
    "voiceBridge": (
        str,
        "Voice conference number for the FreeSWITCH voice conference associated with this meeting. This must be a 5-digit number in the range 10000 to 99999. If you add a phone number to your BigBlueButton server, This parameter sets the personal identification number (PIN) that FreeSWITCH will prompt for a phone-only user to enter. If you want to change this range, edit FreeSWITCH dialplan and defaultNumDigitsForTelVoice of bigbluebutton.properties . The voiceBridge number must be different for every meeting. This parameter is optional. If you do not specify a voiceBridge number, then BigBlueButton will assign a random unused number for the meeting. If do you pass a voiceBridge number, then you must ensure that each meeting has a unique voiceBridge number; otherwise, reusing same voiceBridge number for two different meetings will cause users from one meeting to appear as phone users in the other, which will be very confusing to users in both meetings.",
    ),
    "maxParticipants": (
        int,
        "Set the maximum number of users allowed to joined the conference at the same time.",
    ),
    "loginURL": (
        str,
        "Enables third-party applications to provide a URL that users can access during a meeting to join the session directly.",
    ),
    "logoutURL": (
        str,
        "The URL that the BigBlueButton client will go to after users click the OK button on the ‘You have been logged out message’. This overrides the value for bigbluebutton.web.logoutURL in bigbluebutton.properties .",
    ),
    "record": (
        False,
        "Setting ‘record=true’ instructs the BigBlueButton server to record the media and events in the session for later playback. The default is false. In order for a playback file to be generated, a moderator must click the Start/Stop Recording button at least once during the session; otherwise, in the absence of any recording marks, the record and playback scripts will not generate a playback file. See also the autoStartRecording and allowStartStopRecording parameters in bigbluebutton.properties .",
    ),
    "duration": (
        int,
        "The maximum length (in minutes) for the meeting. Normally, the BigBlueButton server will end the meeting when either (a) the last person leaves (it takes a minute or two for the server to clear the meeting from memory) or when the server receives an end API request with the associated meetingID (everyone is kicked and the meeting is immediately cleared from memory). BigBlueButton begins tracking the length of a meeting when it is created. If duration contains a non-zero value, then when the length of the meeting exceeds the duration value the server will immediately end the meeting (equivalent to receiving an end API request at that moment).",
    ),
    #'isBreakout': (bool, 'Must be set to true to create a breakout room.'),
    #'parentMeetingID': (str, 'The ID of the main room where the breakout was initiated. Must be provided when creating a breakout room, the parent room must be running.'),
    #'sequence': (int, 'The sequence number of the breakout room. Must be provided when creating a breakout room, the parent room must be running.'),
    #'freeJoin': (bool, 'If set to true, the client will give the user the choice to choose the breakout rooms they want to join. Must be provided when creating a breakout room, the parent room must be running.'),
    "breakoutRoomsPrivateChatEnabled": (
        True,
        "If set to false, the private chat will be disabled in breakout rooms.",
    ),
    "breakoutRoomsRecord": (
        False,
        "If set to false, breakout rooms will not be recorded.",
    ),
    #'meta': (str, 'This is a special parameter type (there is no parameter named just meta ). You can pass one or more metadata values when creating a meeting. These will be stored by BigBlueButton can be retrieved later via the getMeetingInfo and getRecordings calls. Examples of the use of the meta parameters are meta_Presenter=Jane%20Doe , meta_category=FINANCE , and meta_TERM=Fall2016 .'),
    #'meta_bbb-disable-recording-formats': (str, 'Comma-separated list of recording format names to skip for this meeting, such as video,presentation or [video,presentation] . Format names are case-insensitive and match the format part of recording steps such as process:video . Disabled formats are not processed or published.'),
    #'meta_bbb-anonymize-chat': (False, 'Whether to anonymize the sender of chat messages in the processed recordings if the sender is viewer. Overrides the default config in bigbluebutton.yml'),
    #'meta_bbb-anonymize-chat-moderators': (False, 'Whether to anonymize the sender of chat messages in the processed recordings if the sender is moderator. Overrides the default config in bigbluebutton.yml'),
    "moderatorOnlyMessage": (
        str,
        "Display a message to all moderators in the public chat. The value is interpreted in the same way as the welcome parameter.",
    ),
    "autoStartRecording": (
        False,
        "Whether to automatically start recording when first user joins (default false ). When this parameter is true , the recording UI in BigBlueButton will be initially active. Moderators in the session can still pause and restart recording using the UI control. NOTE: Don’t pass autoStartRecording=false and allowStartStopRecording=false - the moderator won’t be able to start recording!",
    ),
    "allowStartStopRecording": (
        True,
        "Allow the user to start/stop recording. (default true) If you set both allowStartStopRecording=false and autoStartRecording=true , then the entire length of the session will be recorded, and the moderators in the session will not be able to pause/resume the recording.",
    ),
    "webcamsOnlyForModerator": (
        False,
        "Setting webcamsOnlyForModerator=true will cause all webcams shared by viewers during this meeting to only appear for moderators (added 1.1)",
    ),
    "multiUserWhiteboardEnabled": (
        False,
        "Setting multiUserWhiteboardEnabled=true automatically grants whiteboard drawing access to all users when they join (added 3.0)",
    ),
    "bannerText": (str, "Will set the banner text in the client. (added 2.0)"),
    "bannerColor": (
        str,
        "Will set the banner background color in the client. The required format is color hex #FFFFFF. (added 2.0)",
    ),
    "muteOnStart": (
        False,
        "Setting true will mute all users when the meeting starts. (added 2.0)",
    ),
    "allowModsToUnmuteUsers": (
        False,
        "Setting to true will allow moderators to unmute other users in the meeting. (added 2.2)",
    ),
    "lockSettingsDisableCam": (
        False,
        "Setting true will prevent users from sharing their camera in the meeting. (added 2.2)",
    ),
    "lockSettingsDisableMic": (
        False,
        "Setting to true will only allow user to join listen only. (added 2.2)",
    ),
    "lockSettingsDisablePrivateChat": (
        False,
        "Setting to true will disable private chats in the meeting. (added 2.2)",
    ),
    "lockSettingsDisablePublicChat": (
        False,
        "Setting to true will disable public chat in the meeting. (added 2.2)",
    ),
    "lockSettingsDisableNotes": (
        False,
        "Setting to true will disable notes in the meeting. (added 2.2)",
    ),
    "lockSettingsHideUserList": (
        False,
        "Setting to true will prevent viewers from seeing other viewers in the user list. (added 2.2)",
    ),
    "lockSettingsLockOnJoin": (
        True,
        "Setting to false will not apply lock setting to users when they join. (added 2.2)",
    ),
    "lockSettingsLockOnJoinConfigurable": (
        False,
        "Setting to true will allow applying of lockSettingsLockOnJoin .",
    ),
    "lockSettingsHideViewersCursor": (
        False,
        "Setting to true will prevent viewers to see other viewers cursor when multi-user whiteboard is on. (added 2.5)",
    ),
    "lockSettingsHideViewersAnnotation": (
        False,
        "Setting to true will prevent viewers from seeing other viewers' annotations when multi-user whiteboard is on. (added 2.7)",
    ),
    "guestPolicy": (
        ["ALWAYS_ACCEPT", "ALWAYS_DENY", "ASK_MODERATOR"],
        "Will set the guest policy for the meeting. The guest policy determines whether or not users who send a join request with guest=true will be allowed to join the meeting. Possible values are ALWAYS_ACCEPT, ALWAYS_DENY, and ASK_MODERATOR.",
    ),
    "meetingKeepEvents": (
        False,
        "Defaults to the value of defaultKeepEvents . If meetingKeepEvents is true BigBlueButton saves meeting events even if the meeting is not recorded (added in 2.3)",
    ),
    "endWhenNoModerator": (
        False,
        "Default endWhenNoModerator=false . If endWhenNoModerator is true the meeting will end automatically after a delay - see endWhenNoModeratorDelayInMinutes (added in 2.3)",
    ),
    "endWhenNoModeratorDelayInMinutes": (
        int,
        "Defaults to the value of endWhenNoModeratorDelayInMinutes=1 . If endWhenNoModerator is true, the meeting will be automatically ended after this many minutes (added in 2.2)",
    ),
    "meetingLayout": (
        [
            "CUSTOM_LAYOUT",
            "SMART_LAYOUT",
            "PRESENTATION_FOCUS",
            "VIDEO_FOCUS",
            "CAMERAS_ONLY",
            "PRESENTATION_ONLY",
            "PARTICIPANTS_AND_CHAT_ONLY",
            "MEDIA_ONLY",
        ],
        "Will set the default layout for the meeting. Possible values are: CUSTOM_LAYOUT, SMART_LAYOUT, PRESENTATION_FOCUS, VIDEO_FOCUS. (added 2.4) In version 3.0 a few more possible options were added: CAMERAS_ONLY, PRESENTATION_ONLY, PARTICIPANTS_AND_CHAT_ONLY, MEDIA_ONLY",
    ),
    "learningDashboardCleanupDelayInMinutes": (
        int,
        "Default learningDashboardCleanupDelayInMinutes=2 . This option set the delay (in minutes) before the Learning Dashboard become unavailable after the end of the meeting. If this value is zero, the Learning Dashboard will keep available permanently. (added 2.4)",
    ),
    "allowModsToEjectCameras": (
        False,
        "Setting to true will allow moderators to close other users cameras in the meeting. (added 2.4)",
    ),
    "allowRequestsWithoutSession": (
        False,
        "Setting to true will allow users to join meetings without session cookie's validation. (added 2.4.3)",
    ),
    "userCameraCap": (
        int,
        "Setting to 0 will disable this threshold. Defines the max number of webcams a single user can share simultaneously. (added 2.4.5)",
    ),
    "meetingCameraCap": (
        int,
        "Setting to 0 will disable this threshold. Defines the max number of webcams a meeting can have simultaneously. (added 2.5.0)",
    ),
    "meetingExpireIfNoUserJoinedInMinutes": (
        int,
        "Automatically end meeting if no user joined within a period of time after meeting created. (added 2.5)",
    ),
    "meetingExpireWhenLastUserLeftInMinutes": (
        int,
        "Number of minutes to automatically end meeting after last user left. (added 2.5) Setting to 0 will disable this function.",
    ),
    "groups": (
        str,
        "Pre-defined groups to automatically assign the students to a given breakout room. (added 2.5) Expected value: Json with Array of groups. Group properties: id - String with group unique id. name - String with name of the group (optional) . roster - Array with IDs of the users. E.g: [ \\\"id\\\":'1',name:'GroupA',roster:['1235'] , \\\"id\\\":'2',name:'GroupB',roster:['2333','2335'] , \\\"id\\\":'3',roster:[] ]",
    ),
    "logo": (
        str,
        "Pass a URL to an image which will then be visible in the area above the participants list if displayBrandingArea is set to true in bbb-html5's configuration",
    ),
    "sharedNotesEditor": (
        ["blockNote", "etherpad"],
        "Editor to be rendered in the shared-notes area: `blockNote` or `etherpad`",
    ),
    "sharedNotesInitialContentJsonUrl": (
        str,
        "Url from which the shared-notes will fetch the initial content (Only applicable for when `sharedNotesEditor=blockNote`, ignored otherwise)",
    ),
    #'disabledFeatures': (str, 'List (comma-separated) of features to disable in a particular meeting. Available options to disable: Chat chat - Chat (Public and Private) privateChat - Private Chat deleteChatMessage - Delete a Chat Message (moderators or author) editChatMessage - Edit a Chat Message (only author) replyChatMessage - Reply to a Chat Message chatMessageReactions - Send Reactions to a chat message chatEmojiPicker - Chat emoji picker (added in BigBlueButton 3.0) Presentation & Whiteboard presentation - Presentation downloadPresentationWithAnnotations - Annotated presentation download downloadPresentationConvertedToPdf - Converted presentation download (if BigBlueButton had to convert to PDF) downloadPresentationOriginalFile - Original presentation download snapshotOfCurrentSlide - Snapshot of the current slide infiniteWhiteboard - Infinite Whiteboard (added in BigBlueButton 3.0) Breakout Rooms breakoutRooms - Breakout Rooms importPresentationWithAnnotationsFromBreakoutRooms - Capture breakout presentation importSharedNotesFromBreakoutRooms - Capture breakout shared notes Video & Audio screenshare - Screen Sharing cameraAsContent - Camera as Content virtualBackgrounds - Virtual Backgrounds customVirtualBackgrounds - Virtual Backgrounds Upload liveTranscription - Live Transcription captions - Closed Captions User Engagement polls - Polls quizzes - Quizzes (added in BigBlueButton 3.0) raiseHand - Raise Hand (added in BigBlueButton 3.0) userReactions - User Reactions button in actions bar (added in BigBlueButton 3.0) externalVideos - Share an External Video timer - Timer Shared Notes sharedNotes - Shared Notes Learning Analytics learningDashboard - Learning Analytics Dashboard learningDashboardDownloadSessionData - Learning Analytics Dashboard Download Session Data (prevents the option to download) Layouts layouts - Layouts (allow only default layout) Plugins plugins - Plugins (added in BigBlueButton 3.0)'),
    #'disabledFeaturesExclude': (str, 'List (comma-separated) of features to no longer disable in a particular meeting. This is particularly useful if you disabled a list of features on a per-server basis but want to allow one of two of these features for a specific meeting. (added 2.6.9) The available options to exclude are exactly the same as for disabledFeatures'),
    "preUploadedPresentationOverrideDefault": (
        True,
        "If it is true, the default.pdf document is not sent along with the other presentations in the /create endpoint, on the other hand, if that's false, the default.pdf is sent with the other documents. By default it is true.",
    ),
    "notifyRecordingIsOn": (
        False,
        "If it is true, a modal will be displayed to collect recording consent from users when meeting recording starts (only if notifyRecordingIsOn=true ). By default it is false. (added 2.6)",
    ),
    "presentationUploadExternalUrl": (
        str,
        "Pass a URL to a specific page in external application to select files for inserting documents into a live presentation. Only works if presentationUploadExternalDescription is also set. (added 2.6)",
    ),
    "presentationUploadExternalDescription": (
        str,
        "Message to be displayed in presentation uploader modal describing how to use an external application to upload presentation files. Only works if presentationUploadExternalUrl is also set. (added 2.6)",
    ),
    "presentationConversionCacheEnabled": (
        False,
        "Parameter to decide whether to use the caching system in a S3-based storage system for presentation assets per meeting. If this parameter is true, the other settings related to the caching feature must be configured properly (see section Configure S3-based cache for presentation assets ).",
    ),
    "recordFullDurationMedia": (
        False,
        "Controls whether media (audio, cameras and screen sharing) should be captured on their full duration if the meeting's recorded property is true ( recorded=true ). Default is false: only captures media while recording is running in the meeting. (added 2.6.9)",
    ),
    "preUploadedPresentation": (
        str,
        "If passed with a valid presentation file url, this presentation will override the default presentation. To only upload but not set as default, also pass preUploadedPresentationOverrideDefault=false (added 2.7.2)",
    ),
    "preUploadedPresentationName": (
        str,
        "If passed it will use this string as the name of the presentation uploaded via preUploadedPresentation (added 2.7.2)",
    ),
    "allowOverrideClientSettingsOnCreateCall": (
        False,
        "Whether to allow clientSettingsOverride to be included in the body of a POST request. Because the body of the post request is not signed by the checksum , this parameter is set to false by default. If you set this to true , you must make sure that the signed parameters of the create API request are not visible to users. Added: 3.0.0-alpha.1",
    ),
    "clientSettingsOverride": (
        str,
        "A data structure containing settings which override values from the HTML5 client's settings.yml file. This data can also be provided in the body of a POST request, see clientSettingsOverride for details. Added: 3.0.0-alpha.5",
    ),
    "clientSettingsOverrideJsonUrl": (
        str,
        "A URL pointing to a JSON file whose content overrides values from the HTML5 client's settings.yml file. The JSON structure is identical to clientSettingsOverride but is provided as a direct JSON file (no XML wrapper). This parameter takes precedence over clientSettingsOverride when both are present. Unlike clientSettingsOverride , it does not require allowOverrideClientSettingsOnCreateCall to be enabled. Added: 3.0.25",
    ),
    "allowPromoteGuestToModerator": (
        False,
        "If passed as true, we allow moderators to promote guests to moderators even if the authenticatedGuest config is enabled. The defaultAllowPromoteGuestToModerator configuration sets this behaviour globally for all meetings if no api parameter is passed (added in BBB 2.7.9)",
    ),
    "pluginManifests": (
        str,
        'A list of the BigBlueButton client plugins you want included for the specific session (merged with the list in /etc/bigbluebutton/bbb-web.properties and duplicates dropped) . It is possible to add a placeholder in the URL for the plugin-sdk version being used in the server. For more information see section of placeholders in Plugins . pluginManifests=[ "url":"https://someserver.com/plugins/bbb-plugin-pick-random-user/manifest.json", "checksum": "abc123" ]',
    ),
    "pluginManifestsFetchUrl": (
        str,
        "URL that points to a JSON file containing an array of multiple plugin manifest URLs (optionally including file checksums). This is mainly used to simplify and minimize the size of the create request. The expected content is a json array with the exact same structure as the parameter pluginManifests , see example in the parameter above. It is possible to add a placeholder in the URL for the plugin-sdk version being used in the server. For more information see section of placeholders in Plugins .",
    ),
    "maxNumPages": (
        int,
        "Maximum number of pages allowed for an uploaded presentation.",
    ),
}

CREATE_FEATURES = [
    "breakoutRooms",
    "captions",
    "chat",
    "privateChat",
    "deleteChatMessage",
    "editChatMessage",
    "replyChatMessage",
    "chatMessageReactions",
    "downloadPresentationWithAnnotations",
    "downloadPresentationConvertedToPdf",
    "downloadPresentationOriginalFile",
    "snapshotOfCurrentSlide",
    "externalVideos",
    "importPresentationWithAnnotationsFromBreakoutRooms",
    "importSharedNotesFromBreakoutRooms",
    "layouts",
    "learningDashboard",
    "learningDashboardDownloadSessionData",
    "polls",
    "screenshare",
    "sharedNotes",
    "virtualBackgrounds",
    "customVirtualBackgrounds",
    "liveTranscription",
    "presentation",
    "cameraAsContent",
    "timer",
    "infiniteWhiteboard",
    "raiseHand",
]

CREATE_LOCKS = {
    "cam": "lockSettingsDisableCam",
    "mic": "lockSettingsDisableMic",
    "chat": "lockSettingsDisablePublicChat",
    "pm": "lockSettingDisablePrivateChat",
    "notes": "lockSettingDisableNotes",
    "userlist": "lockSettingsHideUserList",
    "cursor": "lockSettingsHideViewersCursor",
}


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

    def csv_type(value):
        return value.split(",")

    def kv_type(value):
        k, _, v = value.partition("=")
        if not (k.strip() and _ and v.strip()):
            raise argparse.ArgumentTypeError("Not a KEY=VALUE pair")
        return (k, v)

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
        help="Skip TLS verification and accept self-signed or expired SSL certificates",
        action="store_true",
    )


    formats = ["human", "compact", "xml", "json", "jsonline"]
    parser.add_argument(
        "--format",
        help="Change output format.",
        choices=formats,
        default=formats[0],
    )

    rec = main_sub.add_parser(
        "record",
        help="List, show, publish, unpublish or delete recordings",
    )
    rec_sub = rec.add_subparsers(title="Manage recordings")

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
    cmd.add_argument(
        "params",
        nargs="*",
        type=kv_type,
        help="Raw additional key=value create parameters.",
    )

    cmd.add_argument(
        "--join",
        "--mod",
        metavar="NAME",
        help="Print a moderator join link for this username. Can be repeated.",
        action="append",
    )

    cmd.add_argument(
        "--lock",
        help="Shortcuts for --lockSettingsDisable... parameters.",
        choices=list(CREATE_LOCKS.keys()),
        type=csv_type,
    )

    cmd.add_argument(
        "--meta",
        metavar="KEY=VALUE",
        action="append",
        type=kv_type,
        help="Attach metadata to this meeting. Parameter can be repeated.",
    )

    cmd.add_argument(
        "--disabledFeatures",
        help="Disable features for this meeting. Set multiple values as comma-separated list.",
        choices=CREATE_FEATURES,
        type=csv_type,
    )

    cmd.add_argument(
        "--disabledFeaturesExclude",
        help="Remove featres from the --disabledFeatures list. Set multiple values as comma-separated list.",
        choices=CREATE_FEATURES,
        type=csv_type,
    )

    for name, (type_, help) in CREATE_PARAMS.items():
        help = help or "See BBB API docs"
        if type_ is str:
            cmd.add_argument(f"--{name}", help=help)
        elif isinstance(type_, list):
            cmd.add_argument(f"--{name}", help=help, choices=type_)
        elif type_ is bool or type_ in (True, False):
            cmd.add_argument(
                f"--{name}", help=help, action=argparse.BooleanOptionalAction
            )
        elif type_ is int:
            cmd.add_argument(f"--{name}", help=help, metavar="NUMBER", type=int)
        else:
            raise RuntimeError(f"Unsupported parameter type: {type_}")

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

    sign = main_sub.add_parser(
        "sign",
        help="Sign URLs with a secret",
    )

    sign.add_argument("action")
    sign.add_argument("parameters", nargs="*", help="Any number of KEY=VALUE parameters.")
    sign.set_defaults(cmd=cmd_sign)

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
    params = {"meetingID": args.id, "name": args.name}

    # Process --lock first so it can be overridden by explicit --no-lockSettingsBlaBla
    for k, v in CREATE_LOCKS:
        if k in args.lock:
            params[v] = "true"

    # Apply all CREATE_PARAMS
    for name, (type_, help) in CREATE_PARAMS.items():
        if (value := getattr(args, name, None)) is None:
            continue
        if isinstance(value, bool):
            if value == type_:
                continue  # This is the default anyway
            value = str(value).lower()
        params[name] = str(value)

    # Apply --meta key=value
    for k, v in args.meta:
        if v:
            params[f"meta_{k}"] = str(v)

    # Apply --disable feature,feature
    disabled = set()
    enabled = set()
    for feature in args.disable or []:
        if feature in CREATE_FEATURES:
            disabled.add(feature)
    for feature in args.enabled or []:
        if feature in CREATE_FEATURES:
            enabled.add(feature)
            disabled.remove(feature)
    if disabled:
        params["disabledFeatures"] = ",".join(sorted(disabled))
    if disabled:
        params["disabledFeaturesExclude"] = ",".join(sorted(enabled))

    created = api.createMeeting(**params)

    if args.join:
        print()
        for name in args.join:
            link = api.getJoinLink(
                meetingID=args.id,
                fullName=name,
                createTime=created.find("createTime").text,
                role="MODERATOR",
            )
            print(f"{name}: {link}")


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


def cmd_sign(api, args):
    action = args.action
    query = {}
    for param in args.parameters:
        name, sep, value = param.partition("=")
        if sep:
            query[name] = value
        else:
            query[name] = ""
    print(api.makeurl(action, **query))


if __name__ == "__main__":
    main()
