---
title: "MOQT Streaming Format"
category: info

docname: draft-ietf-moq-msf-latest
submissiontype: IETF  # also: "independent", "IAB", or "IRTF"
number:
date:
consensus: true
v: 3
area: "Applications and Real-Time"
workgroup: "Media Over QUIC"
keyword:
 - MoQ
 - MoQTransport
 - MSF
venue:
  group: "Media Over QUIC"
  type: "Working Group"
  mail: "moq@ietf.org"
  arch: "https://mailarchive.ietf.org/arch/browse/moq/"
  github: "moq-wg/msf"
  latest: "https://moq-wg.github.io/msf/
           draft-ietf-moq-msf.html"

author:
 -
    fullname: Will Law
    organization: Akamai
    email: wilaw@akamai.com

normative:
  MoQTransport: I-D.draft-ietf-moq-transport-11
  LOC: I-D.draft-mzanaty-moq-loc-05
  PrivacyPassAuth: I-D.draft-ietf-moq-privacy-pass-auth
  CATAuth: I-D.draft-ietf-moq-c4m
  BASE64: RFC4648
  JSON: RFC8259
  LANG: RFC5646
  MIME: RFC6838
  RFC9000: RFC9000
  RFC4180: RFC4180
  GZIP: RFC1952
  WEBCODECS-CODEC-REGISTRY:
    title: "WebCodecs Codec Registry"
    date: September 2024
    target: https://www.w3.org/TR/webcodecs-codec-registry/
  WEBVTT:
    title: "World Wide Web Consortium (W3C), WebVTT: The Web Video Text Tracks Format"
    date: April 2019
    target: https://www.w3.org/TR/webvtt1/
  IMSC1:
    title: "W3C, TTML Profiles for Internet Media Subtitles and Captions 1.0 (IMSC1)"
    date: April 2016
    target: https://www.w3.org/TR/ttml-imsc1/

informative:


--- abstract

This document specifies the MOQT Streaming Format, designed to operate on Media Over QUIC Transport.


--- middle

# Introduction

MOQT Streaming Format (MSF) is a media format designed to deliver LOC {{LOC}}
compliant media content over Media Over QUIC Transport (MOQT) {{MoQTransport}}.
MSF works by fragmenting the bitstream into objects that can be independently
transmitted. MSF leverages a catalog format to describe the output of the
original publisher. MSF specifies how content should be packaged and signaled,
defines how the catalog communicates the content, specifies prioritization
strategies for real-time and workflows for beginning and terminating broadcasts.
MSF also details how end-subscribers may perform adaptive bitrate switching.
MSF is targeted at real-time and interactive levels of live latency, as well as
VOD content.

This document describes version 1 of the streaming format.

# Conventions and Definitions

{::boilerplate bcp14-tagged}

This document uses the conventions detailed in Section 1.3 of {{RFC9000}} when
describing the binary encoding.

# Scope

The purpose of MSF is to provide an interoperable media streaming format
operating over {{MoQTransport}}. Interoperability implies that:

* An original publisher can package incoming media content into tracks, prepare
  a catalog and announce the availability of the content to an MOQT relay. Media
  content refers to audio and video data, as well as ancillary data such as
  captions, subtitles, accessibility and other timed-text data.
* An MOQT relay can process the announcement as well as cache and propagate the
  tracks, both to other relays or to the final subscriber.
* A final subscriber can parse the catalog, request tracks, decode and render
  the received media data.

MSF is intended to provide a format for delivering commercial media content. To
that end, the following features are within scope:

* Video codecs - all codecs supported by {{LOC}}
* Audio codecs  - all audio codecs supported by {{LOC}}
* Catalog track - describes the availability and characteristics of content
  produced by the original publisher.
* Timeline track - describes the relationship between MOQT Group and Object IDs
  to media time.
* Token-based authorization and access control
* Captions + Subtitles - support for {{WEBVTT}} and {{IMSC1}} transmission
* Latency support across multiple regimes (thresholds are informative only and
  describe the delay between the original publisher placing the content on the
  wire and the final subscriber rendering it)
 * Real-time - less than 500ms
 * Interactive - between 500ms and 2500ms
 * Standard  - above 2500ms
 * VOD latency - content that was previously produced, is no longer live and is
   available indefinitely.
* Content encryption
* ABR between time-synced tracks - subscribers may switch between tracks
  at different quality levels in order to maximize visual or audio quality under
  conditions of throughput variability.
* Capable of delivering interstitial advertising.
* Logs and analytics management - support for the reporting of client-side QoE
   and relay delivery actions.

Initial versions of MSF will prioritize basic features necessary to exercise
interoperability across delivery systems. Later versions will add commercially
necessary features.

# Media packaging {#mediapackaging}
MSF delivers LOC {{LOC}} packaged media bitstreams.

## LOC packaging
This specification references Low Overhead Container (LOC) {{LOC}} to define how
audio and video content is packaged. With this packaging mode, each
EncodedAudioChunk or EncodedVideoChunk sample is placed in a separate MOQT
Object. Samples that belong to the same Group of Pictures (GOP) MUST be placed
within the same MOQT Group.

When LOC packaging is used for a track, the catalog packaging attribute
({{packaging}}) MUST be present and it MUST be populated with a value of "loc".

## Time-alignment {#timealignment}
MSF Tracks MAY be time-aligned. Those that are, are subject to the following
requirements:

* Tracks advertised in the catalog as belonging to a common render group MUST
  be time-aligned.
* The render duration of the first media object of each equally numbered MOQT
  Group, after decoding, MUST have overlapping presentation time.

A consequence of this restriction is that an MSF receiver SHOULD be able to
cleanly switch between time-aligned media tracks at group boundaries.

## Content protection and encryption {#contentprotection}

ToDo - content protection for LOC-packaged content.

# Catalog {#catalog}
A Catalog is an MOQT Track that provides information about the other tracks being
produced by a MSF publisher. A Catalog is used by MSF publishers for
advertising their output and for subscribers in consuming that output. The
payload of the Catalog object is opaque to Relays and can be end-to-end
encrypted. The Catalog provides the names and namespaces of the tracks being
produced, along with the relationship between tracks, properties of the tracks
that consumers may use for selection and any relevant initialization data.

The catalog track MUST have a case-sensitive Track Name of "catalog".

A catalog object MAY be independent of other catalog objects or it MAY represent
a delta update of a prior catalog object. The first catalog object published
within a new group MUST be independent.  A catalog object SHOULD be
published only when the availability of tracks changes.

Each catalog update MUST be mapped to an MOQT Object.


## Catalog Fields

A catalog is a JSON {{JSON}} document, comprised of a series of mandatory and
optional fields. At a minimum, a catalog MUST provide all mandatory fields. A
producer MAY add additional fields to the ones described in this draft. Custom
field names MUST NOT collide with field names described in this draft. The order
of field names within the JSON document is not important.

A parser MUST ignore fields it does not understand.

Table 1 provides an overview of all fields defined by this document.

| Field                   |  Name                  |           Definition      |
|:========================|:=======================|:==========================|
| MSF version             | version                | {{msfversion}}            |
| Delta update            | deltaUpdate            | {{deltaupdate}}           |
| Add tracks              | addTracks              | {{addtracks}}             |
| Remove tracks           | removeTracks           | {{removetracks}}          |
| Clone tracks            | cloneTracks            | {{clonetracks}}           |
| Generated at            | generatedAt            | {{generatedat}}           |
| Is Complete             | isComplete             | {{iscomplete}}            |
| Tracks                  | tracks                 | {{tracks}}                |
| Track namespace         | namespace              | {{tracknamespace}}        |
| Track name              | name                   | {{trackname}}             |
| Packaging               | packaging              | {{packaging}}             |
| Event timeline type     | eventType              | {{eventtype}}             |
| Is Live                 | isLive                 | {{islive}}                |
| Target latency          | targetLatency          | {{targetlatency}}         |
| Track role              | role                   | {{trackrole}}             |
| Track label             | label                  | {{tracklabel}}            |
| Render group            | renderGroup            | {{rendergroup}}           |
| Alternate group         | altGroup               | {{altgroup}}              |
| Initialization data     | initData               | {{initdata}}              |
| Dependencies            | depends                | {{dependencies}}          |
| Temporal ID             | temporalId             | {{temporalid}}            |
| Spatial ID              | spatialId              | {{spatialid}}             |
| Codec                   | codec                  | {{codec}}                 |
| Mime type               | mimeType               | {{mimetype}}              |
| Framerate               | framerate              | {{framerate}}             |
| Timescale               | timescale              | {{timescale}}             |
| Bitrate                 | bitrate                | {{bitrate}}               |
| Width                   | width                  | {{width}}                 |
| Height                  | height                 | {{height}}                |
| Audio sample rate       | samplerate             | {{audiosamplerate}}       |
| Channel configuration   | channelConfig          | {{channelconfiguration}}  |
| Display width           | displayWidth           | {{displaywidth}}          |
| Display height          | displayHeight          | {{displayheight}}         |
| Language                | lang                   | {{language}}              |
| Parent name             | parentName             | {{parentname}}            |
| Track duration          | trackDuration          | {{trackduration}}         |
| Authorization Info      | authInfo               | {{authinfo}}              |

Table 2 defines the allowed locations for these fields within the document

| Location |                Allowed locations for the field                |
|:=========|:==============================================================|
| R        | The Root of the JSON object                                   |
| T        | Track object                                                  |

### MSF version {#msfversion}
Location: R    Required: Yes    JSON Type: Number

Specifies the version of MSF referenced by this catalog. There is no guarantee
that future catalog versions are backwards compatible and field definitions and
interpretation may change between versions. A subscriber MUST NOT attempt to
parse a catalog version which it does not understand.

### Delta update {#deltaupdate}
Location: R    Required: Optional    JSON Type: Boolean

A Boolean that if true indicates that this catalog object represents a delta
(or partial) update. A delta update has a restricted set of fields and special
processing rules - see {{deltaupdates}}. This value SHOULD NOT be added to a
catalog if it is false.

### Add tracks {#addtracks}
Location: R    Required: Optional    JSON Type: Array

Indicates a delta processing instruction to add new tracks. The value of this
field is an Array of track objects {{trackobject}}.

### Remove tracks {#removetracks}
Location: R    Required: Optional    JSON Type: Array

Indicates a delta processing instruction to remove new tracks. The value of this
field is an Array of track objects {{trackobject}}. Each track object MUST include
a Track Name {{trackname}} field, MAY include a Track Namespace {{tracknamespace}}
field and MUST NOT hold any other fields.

### Clone tracks {#clonetracks}
Location: R    Required: Optional    JSON Type: Array

Indicates a delta processing instruction to clone new tracks from previously declared
tracks. The value of this field is an Array of track objects {{trackobject}}. Each
track object MUST include a Parent Name {{parentname}} field.

### Generated at {#generatedat}
Location: R    Required: Optional    JSON Type: Number

The wallclock time at which this catalog instance was generated, expressed as the
number of milliseconds that have elapsed since January 1, 1970 (midnight UTC/GMT).
This field SHOULD NOT be included if the isLive field is false.

### Is Complete {#iscomplete}
Location: R    Required: Optional    JSON Type: Boolean

Issued once a previously live broadcast is complete. This is a commitment that all
tracks are complete, no new tracks will be added and no new content will be
published. This field MUST NOT be included if it is FALSE. This field MUST NOT be
removed from a catalog once it has been added.

### Tracks {#tracks}
Location: R    Required: Yes    JSON Type: Array

An array of track objects {{trackobject}}.

### Tracks object {#trackobject}

A track object is JSON Object containing a collection of fields whose location
is specified 'T' in Table 2.

### Track namespace {#tracknamespace}
Location: T    Required: Optional    JSON Type: String

The name space under which the track name is defined. See section 2.3 of
{{MoQTransport}}. The track namespace is optional. If it is not declared within
a track, then each track MUST inherit the namespace of the catalog track. A
namespace declared in a track object overrides any inherited name space.

### Track name {#trackname}
Location: T    Required: Yes   JSON Type: String

A string defining the name of the track. See section 2.3 of {{MoQTransport}}.
Within the catalog, track names MUST be unique per namespace.

### Packaging {#packaging}
Location: T    Required: Yes   JSON Type: String

A string defining the type of payload encapsulation. Allowed values are strings
as defined in Table 3.

Table 3: Allowed packaging values

| Name            |   Value        |      Reference             |
|:================|:===============|:===========================|
| LOC             | loc            | See RFC XXXX               |
| Media Timeline  | mediatimeline  | See {{mediatimelinetrack}} |
| Event Timeline  | eventtimeline  | See {{eventtimelinetrack}} |


### Event timeline type {#eventtype}
Location: T    Required: Optional   JSON Type: String

A String defining the type & structure of the data contained within the data
field of the Event timeline track. Types are defined by the application provider
and are not centrally registered. Implementers are encouraged to use a unique
naming scheme, such as Reverse Domain Name Notation, to avoid naming collisions.
This field is required if the {{packaging}} value is "eventtimeline".
This field MUST NOT be used if the packaging value is not "eventtimeline".

### Track role {#trackrole}
Location: T    Required: Optional   JSON Type: String

A string defining the role of content carried by the track. Specified roles
are described in Table 4. These role values are case-sensitive.

This role field MAY be used in conjunction with the Mimetype {{mimetype}} to
fully describe the content of the track.

Table 4: Reserved track roles

| Role             |   Description                                              |
|:=================|:===========================================================|
| audiodescription | An audio description for visually impaired users           |
| video            | Visual content                                             |
| audio            | Audio content                                              |
| mediatimeline    | An MSF media timeline {{mediatimelinetrack}}               |
| eventtimeline    | An MSF event timeline {{eventtimelinetrack}}               |
| caption          | A textual representation of the audio track                |
| subtitle         | A transcription of the spoken dialogue                     |
| signlanguage     | A visual track for hearing impaired users.                 |
|------------------|------------------------------------------------------------|

Custom roles MAY be used as long as they do not collide with the specified roles.

### Is Live {#islive}
Location: T    Required: Yes  JSON Type: Boolean

True if new Objects will be added to the track.
False if no new Objects will be added to the track. A False value is sent under two
possible conditions:
* the publisher of a previously live track has ended the track.
* the track is Video-On-Demand (VOD) and was never live.
A True value MUST never follow a False value.

### Target latency {#targetlatency}
Location: T    Required: Optional  JSON Type: Number

The target latency in milliseconds. Target latency is defined as the offset in
wallclock time between when content was encoded and when it is displayed to the
end user. For example, if a frame of video is encoded at 10:08:32.638 UTC and the
target latency is 5000, then that frame should be rendered to the end-user at
10:08:37.638 UTC. This field MUST NOT be included if isLive is FALSE. All tracks
belonging to the same render group MUST have identical target latencies. All tracks
belonging to the same alternate group MUST have identical target latencies. If this
field is absent from the track definition, then the player MAY choose the latency
with which it renders the content.

### Track label {#tracklabel}
Location: T    Required: Optional   JSON Type: String

A string defining a human-readable label for the track. Examples might be
"Overhead camera view" or "Deutscher Kommentar". Note that the {{JSON}} spec
requires UTF-8 support by decoders.

### Render group {#rendergroup}
Location: T    Required: Optional   JSON Type: Number

An integer specifying a group of tracks which are designed to be rendered
together. Tracks with the same group number SHOULD be rendered simultaneously,
are time-aligned and are designed to accompany one another. A common
example would be tying together audio and video tracks.

### Alternate group {#altgroup}
Location: T    Required: Optional   JSON Type: Number

An integer specifying a group of tracks which are alternate versions of
one-another. Alternate tracks represent the same media content, but differ in
their selection properties. Alternate tracks MUST have matching media time
sequences. A subscriber typically subscribes to one track from a set of
tracks specifying the same alternate group number. A common example would be
a set video tracks of the same content offered in alternate bitrates.

### Initialization data {#initdata}
Location: T    Required: Optional   JSON Type: String

A string holding Base64 {{BASE64}} encoded initialization data for the track.

### Dependencies {#dependencies}
Location: T    Required: Optional   JSON Type: Array

Certain tracks may depend on other tracks for decoding. Dependencies holds an
array of track names {{trackname}} on which the current track is dependent.
Since only the track name is signaled, the namespace of the dependencies is
assumed to match that of the track declaring the dependencies.

### Temporal ID {#temporalid}
Location: T    Required: Optional   JSON Type: Number

A number identifying the temporal layer/sub-layer encoding of the track,
starting with 0 for the base layer, and increasing by 1 for the next higher
temporal fidelity.

### Spatial ID {#spatialid}
Location: T    Required: Optional   JSON Type: Number

A number identifying the spatial layer encoding of the track, starting with 0
for the base layer, and increasing by 1 for the next higher fidelity.

### Codec {#codec}
Location: T    Required: Optional   JSON Type: String

A string defining the codec used to encode the track.
For LOC packaged content, the string codec registrations are defined in Sect 3
and Section 4 of {{WEBCODECS-CODEC-REGISTRY}}.

### Mimetype {#mimetype}
Location: T    Required: Optional   JSON Type: String

A string defining the mime type {{MIME}} of the track.

### Framerate {#framerate}
Location: T    Required: Optional   JSON Type: Number

A number defining the video framerate of the track, expressed as frames per
second. This property SHOULD only accompany video codecs.

### Timescale {#timescale}
Location: T    Required: Optional   JSON Type: Number

The number of time units that pass per second.

### Bitrate {#bitrate}
Location: T    Required: Optional   JSON Type: Number

A number defining the bitrate of track, expressed in bits per second.

### Width {#width}
Location: T    Required: Optional   JSON Type: Number

A number expressing the encoded width of the video frames in pixels.

### Height {#height}
Location: T    Required: Optional   JSON Type: Number

A number expressing the encoded height of the video frames in pixels.

### Audio sample rate {#audiosamplerate}
Location: T    Required: Optional   JSON Type: Number

The number of audio frame samples per second. This property SHOULD only
accompany audio codecs.

### Channel configuration {#channelconfiguration}
Location: T    Required: Optional   JSON Type: String

A string specifying the audio channel configuration. This property SHOULD only
accompany audio codecs. A string is used in order to provide the flexibility to
describe complex channel configurations for multi-channel and Next Generation
Audio schemas.


### Display width {#displaywidth}
Location: T    Required: Optional   JSON Type: Number

A number expressing the intended display width of the track content in pixels.

### Display height {#displayheight}
Location: T    Required: Optional   JSON Type: Number

A number expressing the intended display height of the track content in pixels.

### Language {#language}
Location: T    Required: Optional   JSON Type: String

A string defining the dominant language of the track. The string MUST be one of
the standard Tags for Identifying Languages as defined by {{LANG}}.

### Parent name {#parentname}
Location: T    Required: Optional   JSON Type: String

A string defining the parent track name {{trackname}} to be cloned. This field
MUST only be included inside a Clone tracks {{clonetracks}} object.

### Track duration {#trackduration}
Location: T    Required: Optional   JSON Type: Number

The duration of the track expressed in integer milliseconds. This field MUST NOT
be included if the isLive {{islive}} field value is true.

### Authorization Info {#authinfo}
Location: T    Required: Optional    JSON Type: Object

An object indicating that authorization is required to access this track.
The presence of this field signals to subscribers that they must obtain
and present valid authorization tokens when subscribing to this track.

The keys of this object are authorization scheme identifiers. Registered
schemes are defined in Table 5. The values are scheme-specific configuration
objects defined by the referenced specifications.

Table 5: Registered Authorization Schemes

| Scheme           | Value          | Reference                              |
|:================|:===============|:======================================|
| Privacy Pass     | privacy-pass   | {{PrivacyPassAuth}}                    |
| CAT              | cat            | {{CATAuth}}                            |

Custom authorization schemes MAY be used. Custom scheme names MUST use a
unique naming convention, such as Reverse Domain Name Notation
(e.g., "com.example.custom-auth"), to avoid naming collisions.

Subscribers inspect the authInfo field to determine which authorization
scheme to use and then obtain tokens through out-of-band mechanisms.
The specific token format, acquisition process, and presentation method
are defined by the authorization scheme specification.

TODO: Consider adding a mechanism to indicate which token should be applied
during connection establishment vs. per-track operations. Revisit once MOQT
variable parameters support is finalized.

## Delta updates {#deltaupdates}
A catalog update might contain incremental changes. This is a useful property if
many tracks may be initially declared but then there are small changes to a
subset of tracks. The producer can issue a delta update to describe these changes.
Changes are described incrementally, meaning that a delta update can itself modify
a prior delta update.

A restricted set of operations are allowed with each delta update:
* Add a new track that has not previously been declared.
* Add a new track by cloning a previously declared track.
* Remove a track that has been previously declared.

The following rules are to be followed in constructing and processing delta updates:

* A delta update MUST include the Delta Update {{deltaupdate}} field set to true.
* A delta update catalog MUST contain at least one instance of Add tracks
  {{addtracks}}, Remove tracks {{removetracks}} or Clone Tracks {{clonetracks}}
  fields and MAY contain more. It MUST NOT contain an instance of a Tracks
  {{tracks}} field or an MSF version {{msfversion}} field.
* The Add, Delete and Clone operations are applied sequentially in the order they
  are declared in the document. Each operation in the sequence is applied to the
  target document; the resulting document becomes the target of the next operation.
  Evaluation continues until all operations are successfully applied.
* A Cloned track inherits all the attributes of the track defined by the Parent Name
  {{parentname}}, except the Track Name which MUST be new. Attributes redefined
  in the cloning Object override inherited values.
* The tuple of Track Namespace and Track Name defines a fixed set of Track attributes
  which MUST NOT be modified after being declared. To modify any attribute, a new
  track with a different Namespace|Name tuple is created by Adding or Cloning and then
  the old track is removed.


## Catalog Examples

The following section provides non-normative JSON examples of various catalogs
compliant with this draft.


### Time-aligned Audio/Video Tracks with single quality

This example shows a catalog for a media producer capable of sending LOC
packaged, time-aligned audio and video tracks.

~~~json
{
  "version": 1,
  "generatedAt": 1746104606044,
  "tracks": [
    {
      "name": "1080p-video",
      "namespace": "conference.example.com/conference123/alice",
      "packaging": "loc",
      "isLive": true,
      "targetLatency": 2000,
      "role": "video",
      "renderGroup": 1,
      "codec":"av01.0.08M.10.0.110.09",
      "width":1920,
      "height":1080,
      "framerate":30,
      "bitrate":1500000
    },
    {
      "name": "audio",
      "namespace": "conference.example.com/conference123/alice",
      "packaging": "loc",
      "isLive": true,
      "targetLatency": 2000,
      "role": "audio",
      "renderGroup": 1,
      "codec":"opus",
      "samplerate":48000,
      "channelConfig":"2",
      "bitrate":32000
    }
   ]
}

~~~



### Simulcast video tracks - 3 alternate qualities along with audio

This example shows a catalog for a media producer capable of sending 3
time-aligned video tracks for high definition, low definition and medium
definition video qualities, along with an audio track. In this example the
namespace is absent, which infers that each track must inherit the namespace
of the catalog.

~~~json
{
  "version": 1,
  "generatedAt": 1746104606044,
  "tracks":[
    {
      "name": "hd",
      "renderGroup": 1,
      "packaging": "loc",
      "isLive": true,
      "targetLatency": 1500,
      "role": "video",
      "codec":"av01",
      "width":1920,
      "height":1080,
      "bitrate":5000000,
      "framerate":30,
      "altGroup":1
    },
    {
      "name": "md",
      "renderGroup": 1,
      "packaging": "loc",
      "isLive": true,
      "targetLatency": 1500,
      "role": "video",
      "codec":"av01",
      "width":720,
      "height":640,
      "bitrate":3000000,
      "framerate":30,
      "altGroup":1
    },
    {
      "name": "sd",
      "renderGroup": 1,
      "packaging": "loc",
      "isLive": true,
      "targetLatency": 1500,
      "role": "video",
      "codec":"av01",
      "width":192,
      "height":144,
      "bitrate":500000,
      "framerate":30,
      "altGroup":1
    },
    {
      "name": "audio",
      "renderGroup": 1,
      "packaging": "loc",
      "isLive": true,
      "targetLatency": 1500,
      "role": "audio",
      "codec":"opus",
      "samplerate":48000,
      "channelConfig":"2",
      "bitrate":32000
    }
   ]
}
~~~


### SVC video tracks with 2 spatial and 2 temporal qualities


This example shows a catalog for a media producer capable
of sending scalable video codec with 2 spatial and 2 temporal
layers with a dependency relation as shown below:

~~~ascii-figure

                  +----------+
     +----------->|  S1T1    |
     |            | 1080p30  |
     |            +----------+
     |                  ^
     |                  |
+----------+            |
|  S1TO    |            |
| 1080p15  |            |
+----------+      +-----+----+
      ^           |  SOT1    |
      |           | 480p30   |
      |           +----------+
      |               ^
+----------+          |
|  SOTO     |         |
| 480p15    |---------+
+----------+
~~~



The corresponding catalog uses "depends" attribute to
express the track relationships.

~~~json
{
  "version": 1,
  "generatedAt": 1746104606044,
  "tracks":[
    {
      "name": "480p15",
      "namespace": "conference.example.com/conference123/alice",
      "renderGroup": 1,
      "packaging": "loc",
      "isLive": true,
      "role": "video",
      "codec":"av01.0.01M.10.0.110.09",
      "width":640,
      "height":480,
      "bitrate":3000000,
      "framerate":15
    },
    {
      "name": "480p30",
      "namespace": "conference.example.com/conference123/alice",
      "renderGroup": 1,
      "packaging": "loc",
      "isLive": true,
      "role": "video",
      "codec":"av01.0.04M.10.0.110.09",
      "width":640,
      "height":480,
      "bitrate":3000000,
      "framerate":30,
      "depends": ["480p15"]
    },
    {
      "name": "1080p15",
      "namespace": "conference.example.com/conference123/alice",
      "renderGroup": 1,
      "packaging": "loc",
      "isLive": true,
      "role": "video",
      "codec":"av01.0.05M.10.0.110.09",
      "width":1920,
      "height":1080,
      "bitrate":3000000,
      "framerate":15,
      "depends":["480p15"]
    },

    {
      "name": "1080p30",
      "namespace": "conference.example.com/conference123/alice",
      "renderGroup": 1,
      "packaging": "loc",
      "isLive": true,
      "role": "video",
      "codec":"av01.0.08M.10.0.110.09",
      "width":1920,
      "height":1080,
      "bitrate":5000000,
      "framerate":30,
      "depends": ["480p30", "1080p15"]
    },
    {
      "name": "audio",
      "namespace": "conference.example.com/conference123/alice",
      "renderGroup": 1,
      "packaging": "loc",
      "isLive": true,
      "role": "audio",
      "codec":"opus",
      "samplerate":48000,
      "channelConfig":"2",
      "bitrate":32000
    }
   ]
}
~~~

### Delta update  - adding two tracks

This example shows the catalog delta update for a media producer adding
two tracks to an established video conference. One track is newly declared,
the other is cloned from a previous track.

~~~json
{
  "deltaUpdate": true,
  "generatedAt": 1746104606044,
  "addTracks": [
      {
        "name": "slides",
        "isLive": true,
        "role": "video",
        "codec": "av01.0.08M.10.0.110.09",
        "width": 1920,
        "height": 1080,
        "framerate": 15,
        "bitrate": 750000,
        "renderGroup": 1
      }
   ],
   "cloneTracks": [
      {
        "parentName": "video-1080",
        "name": "video-720",
        "width":1280,
        "height":720,
        "bitrate":600000
      }
   ]
}
~~~

### Delta update removing tracks

This example shows a delta update for a media producer removing two tracks
from an established video conference.

~~~json
{
  "deltaUpdate": true,
  "generatedAt": 1746104606044,
  "removeTracks": [{"name": "video"},{"name": "slides"}]
}
~~~


### Time-aligned Audio/Video Tracks with custom field values

This example shows a catalog for a media producer capable of sending LOC packaged,
time-aligned audio and video tracks along with custom fields in each track
description.

~~~json
{
  "version": 1,
  "generatedAt": 1746104606044,
  "tracks": [
    {
      "name": "1080p-video",
      "namespace": "conference.example.com/conference123/alice",
      "packaging": "loc",
      "isLive": true,
      "role": "video",
      "renderGroup": 1,
      "codec":"av01.0.08M.10.0.110.09",
      "width":1920,
      "height":1080,
      "framerate":30,
      "bitrate":1500000,
      "com.example-billing-code": 3201,
      "com.example-tier": "premium",
      "com.example-debug": "h349835bfkjfg82394d945034jsdfn349fns"
    },
    {
      "name": "audio",
      "namespace": "conference.example.com/conference123/alice",
      "packaging": "loc",
      "isLive": true,
      "role": "audio",
      "renderGroup": 1,
      "codec":"opus",
      "samplerate":48000,
      "channelConfig":"2",
      "bitrate":32000
    }
   ]
}

~~~


### Time-aligned VOD Audio/Video Tracks

This example shows a catalog for a media producer offering VOD (video on-demand)
non-live content. The content is LOC packaged, and includes time-aligned audio
and video tracks.


~~~json
{
  "version": 1,
  "tracks": [
    {
      "name": "video",
      "namespace": "movies.example.com/assets/boy-meets-girl-season3/episode5",
      "packaging": "loc",
      "isLive": false,
      "trackDuration": 8072340,
      "renderGroup": 1,
      "codec":"av01.0.08M.10.0.110.09",
      "width":1920,
      "height":1080,
      "framerate":30,
      "bitrate":1500000
    },
    {
      "name": "audio",
      "namespace": "movies.example.com/assets/boy-meets-girl-season3/episode5",
      "packaging": "loc",
      "isLive": false,
      "trackDuration": 8072340,
      "renderGroup": 1,
      "codec":"opus",
      "samplerate":48000,
      "channelConfig":"2",
      "bitrate":32000
    }
   ]
}

~~~

### Media timeline and Event timeline

This example shows a catalog for a media producer capable of sending LOC
packaged, time-aligned audio and video tracks, along with a Media Timeline
which describes the history of those tracks and an Event Timeline providing
synchronized data.

~~~json
{
  "version": 1,
  "generatedAt": 1746104606044,
  "tracks": [
    {
      "name": "history",
      "namespace": "conference.example.com/conference123/alice",
      "packaging": "mediatimeline",
      "mimetype": "application/json",
      "depends": ["1080p-video","audio"]
    },
    {
      "name": "identified-objects",
      "namespace": "another-provider/time-synchronized-data",
      "packaging": "eventtimeline",
      "eventType": "com.ai-extraction/appID/v3",
      "mimetype": "application/json",
      "depends": ["1080p-video"]
    },
    {
      "name": "1080p-video",
      "namespace": "conference.example.com/conference123/alice",
      "packaging": "loc",
      "isLive": true,
      "targetLatency": 2000,
      "role": "video",
      "renderGroup": 1,
      "codec":"av01.0.08M.10.0.110.09",
      "width":1920,
      "height":1080,
      "framerate":30,
      "bitrate":1500000
    },
    {
      "name": "audio",
      "namespace": "conference.example.com/conference123/alice",
      "packaging": "loc",
      "isLive": true,
      "targetLatency": 2000,
      "role": "audio",
      "renderGroup": 1,
      "codec":"opus",
      "samplerate":48000,
      "channelConfig":"2",
      "bitrate":32000
    }
   ]
}

~~~

### Terminating a live broadcast

This example shows a catalog for a media producer terminating a previously
live broadcast containing a video and an audio track.

~~~json
{
  "version": 1,
  "generatedAt": 1746104606044,
  "isComplete": true,
  "tracks": []
}

~~~

### Time-aligned Audio/Video Tracks with Authorization

This example shows a catalog for a media producer requiring authorization
for premium content.

~~~json
{
  "version": 1,
  "generatedAt": 1746104606044,
  "tracks": [
    {
      "name": "premium-4k-video",
      "namespace": "streaming.example.com/live/sports",
      "packaging": "loc",
      "isLive": true,
      "targetLatency": 2000,
      "role": "video",
      "renderGroup": 1,
      "codec": "av01.0.12M.10.0.110.09",
      "width": 3840,
      "height": 2160,
      "framerate": 60,
      "bitrate": 15000000,
      "authInfo": {
        "cat": {}
      }
    },
    {
      "name": "standard-720p-video",
      "namespace": "streaming.example.com/live/sports",
      "packaging": "loc",
      "isLive": true,
      "targetLatency": 2000,
      "role": "video",
      "renderGroup": 2,
      "codec": "av01.0.05M.10.0.110.09",
      "width": 1280,
      "height": 720,
      "framerate": 30,
      "bitrate": 2500000,
      "authInfo": {
        "privacy-pass": {}
      }
    },
    {
      "name": "audio",
      "namespace": "streaming.example.com/live/sports",
      "packaging": "loc",
      "isLive": true,
      "targetLatency": 2000,
      "role": "audio",
      "renderGroup": 1,
      "codec": "opus",
      "samplerate": 48000,
      "channelConfig": "2",
      "bitrate": 128000
    }
  ]
}
~~~


# Media transmission
The MOQT Groups and MOQT Objects need to be mapped to MOQT Streams. Irrespective
of the {{mediapackaging}} in place, each MOQT Object MUST be mapped to a new
MOQT Stream.

## Group numbering
The Group ID of the first Group published in a track at application startup MUST be
a unique integer that will not repeat in the future. One approach to achieve this
is to set the initial Group ID to the creation time of the first Object in the
group, represented as the number of milliseconds since the Unix epoch, rounded to
the nearest millisecond. This ensures that republishing the same track in the
future, such as after a loss of connectivity or an encoder restart, will not result
in smaller or duplicate Group IDs for the same track name. Note that this method
does not prevent duplication if more than 1000 Groups are published per second.

Each subsequent Group ID MUST increase by 1.

If a publisher is able to maintain state across a republish, it MUST signal the gap
in Group IDs using the MOQT Prior Group ID Gap Extension header.

# Media Timeline track {#mediatimelinetrack}
The media timeline track provides data about the previously published Groups and their
relationship to wallclock time and media time. Media timeline tracks allow players to
seek to precise points behind the live head in a live broadcast, or for random access
in a VOD asset. Media timeline tracks are optional. Multiple media timeline tracks
can exist inside a catalog.

## Media Timeline track payload {#mediatimelinepayload}
A media timeline track is a JSON {{JSON}} document. This document MAY be compressed
using GZIP {{GZIP}}. The document contains an array of records. Each record consists of
an array of three required items, whose ordinal position defines their type:

* The first item holds the media presentation timestamp, expressed as a JSON Number.
  This value MUST match the media presentation timestamp, rounded to the nearest
  millisecond, of the first media sample in the referenced Object
* The second item holds the MOQT Location of the entry, defined as a tuple of the MOQT
  Group ID and MOQT Object ID, and expressed as a JSON Array of Numbers, where the
  first number is the Group ID and the second number is the Object ID.
* The third time holds the wallclock time at which the media was encoded, defined as
  the number of milliseconds that have elapsed since January 1, 1970
  (midnight UTC/GMT) and expressed as a JSON Number. For VOD assets, or if the
  wallclock time is not known, the value SHOULD be 0.

An example media timeline is shown below:

~~~json
[
  [0, [0,0], 1759924158381],
  [2002, [1,0], 1759924160383],
  [4004, [2,0], 1759924162385],
  [6006, [3,0], 1759924164387],
  [8008, [4,0], 1759924166389]
]
~~~

## Media Timeline Catalog requirements
A media timeline track MUST carry a 'type' identifier in the Catalog with a value
of "mediatimeline". A media timeline track MUST carry a 'depends' attribute which
contains an array of all track names to which the media timeline track applies.
The mime-type of a media timeline track MUST be specified as "application/json".

## Media Timeline track updating
The publisher MUST publish an independent media timeline in the first MOQT Object
of each MOQT Group of a media timeline track. The publisher MAY publish incremental
updates in the second and subsequent Objects within each Group. Incremental updates
only contain media timeline records since the last media timeline Object.

# Event Timeline track {#eventtimelinetrack}
The event timeline track provides a mechanism to associate ad-hoc event metadata with
the broadcast. Use-case examples include live sports score data, GPS coordinates of race
cars, SAP-types for media segments or active speaker notifications in web conferences.

To allow the client to bind this event metadata with the broadcast content described by
the media timeline track, each event record MUST contain a reference to one of
Media PTS, wallclock time or MOQT Location.

Event timeline tracks are optional. Multiple event timeline tracks can exist inside a
catalog. The type & structure of the data contained within each event timeline track is
declared in the catalog, to facilitate client selection and parsing.

## Event Timeline data format {#eventtimelineformat}
An event timeline track is a JSON {{JSON}} document. This document MAY be compressed
using GZIP {{GZIP}}. The document contains an array of records. Each record consists of
a JSON Object containing the following required fields:

* An index reference, which MUST be either 't' for wallclock time, 'l' for Location or
  'm' for Media PTS. Only one of these index values may be used within each record. Event
  timelines SHOULD use the same index reference type for each record. The definitions for
  wallclock time, Location and Media PTS are identical to those defined for media timeline
  payload {{mediatimelinepayload}}. Wallclock time and media PTS values are JSON Number,
  while Location value is an Array of Numbers, where the first item represents the MOQT
  GroupID and the second item the MOQT Object ID.
* A 'data' Object, whose structure is defined by the {{eventtype}} value declared for this
  track in the Catalog.

## Event Timeline Catalog requirements
An event timeline track MUST carry:

* a {{packaging}} attribute with a value of "eventtimeline".
* a {{dependencies}} attribute which contains an array of all track names to which the event
  timeline track applies.
* a {{mimetype}} attribute with a value of "application/json".
* an {{eventtype}} attribute declaring the type & structure of data contained in the
  event timeline track.

## Event Timeline track updating
The publisher MUST publish an independent event timeline in the first MOQT Object
of each MOQT Group of an event timeline track. The publisher MAY publish incremental
updates in the second and subsequent Objects within each Group. Incremental updates
only contain event timeline records since the last event timeline Object.

## Event timeline track examples

### Event timeline track with wallclock time indexing
This example shows how sports scores and game information might be defined in a live
sports broadcast.

~~~json
[
    {
        "t": 1756885678361,
        "data": {
            "status": "in_progress",
            "period": 1,
            "clock": "12:00",
            "homeScore": 0,
            "awayScore": 0,
            "lastPlay": "Game Start"
        }
    },
    {
        "t": 1756885981542,
        "data": {
            "status": "in_progress",
            "period": 1,
            "clock": "09:25",
            "homeScore": 2,
            "awayScore": 0,
            "lastPlay": "Team A: #23 makes 2-pt jump shot"
        }
    }
]

~~~

### Event timeline track with MOQT Location indexing
This example shows drone GPS coordinates synched with the start of each Group.

~~~json
[
    {
        "l": [0,0],
        "data": [47.1812,8.4592]
    },
    {
        "l": [1,0],
        "data": [47.1662,8.5155]
    }
]

~~~

# Workflow

## Initiating a broadcast
An MSF publisher MUST publish a catalog track object before publishing any media
track objects.

## Ending a live broadcast
After publishing a catalog and defining tracks carrying live content, an original
publisher can deliver a deterministic signal to all subscribers that the broadcast
is complete by taking the following steps:

* Send a SUBSCRIBE_DONE (See MOQT Sect 8.1.2) message for all active tracks using
  status code 0x2 Track Ended.
* If the live stream is being converted instantly to a VOD asset, then publish an
  independent (non-delta) catalog update which, for each track, sets isLive {{islive}}
  to FALSE and adds a track duration {{trackduration}} field.
* If the live stream is being terminated permanently without conversion to VOD, then
  publish an independent catalog update which signals isComplete {{iscomplete}} as
  TRUE and which contains an empty Tracks {{tracks}} field.

## Authorization {#authorization}

MSF supports token-based authorization through pluggable authentication schemes.
Both original publishers and end subscribers can independently acquire authorization
tokens and present them to relays. Relays use these tokens to authorize whether
an end subscriber is permitted to receive content and whether an original publisher
is permitted to send content.

### Discovering Authorization Requirements

End subscribers discover authorization requirements by parsing the catalog.
For each track of interest, examine the `authInfo` field. If present, the
track requires authorization and the subscriber must obtain appropriate
credentials for one of the schemes listed in the field.

Original publishers and end subscribers may obtain authorization tokens from
multiple sources, including out-of-band provisioning or as a parameter in
the connection URI. These tokens can be presented either in the connection
setup message (CLIENT_SETUP) or in control messages (SUBSCRIBE, FETCH, PUBLISH,
PUBLISH_NAMESPACE) as described in {{presentingauthorization}}.

### Token Acquisition

Token acquisition is out of scope for this specification. Both original publishers
and end subscribers independently obtain tokens through mechanisms such as:

* Direct authentication with a distribution service
* OAuth 2.0 or OpenID Connect flows
* Out-of-band provisioning

The token acquisition endpoint and flow depend on the authorization scheme
and deployment configuration. Original publishers and end subscribers MAY
use the same or different authorization services depending on the deployment.

Tokens MAY also be supplied as parameters in the connection URI. When a
connection URI contains token parameters, the subscriber extracts the token
value and includes it in the appropriate MOQT message. For example:

~~~
https://relay.example.com/moqt?token=eyJhbGciOiJFZERTQSJ9...
~~~

URI parameters provide a convenient mechanism for distributing pre-authorized
playback links. The parameter name and format are deployment-specific.

### Presenting Authorization {#presentingauthorization}

Once tokens are obtained, both original publishers and end subscribers present
them to relays according to the scheme specification. Tokens MAY be presented
at two points during the connection lifecycle:

* **Connection establishment**: Tokens may be included in the SETUP message
  (CLIENT_SETUP or SERVER_SETUP) using the AUTHORIZATION TOKEN setup parameter.
  This authorizes the connection itself or pre-authorizes subsequent operations.

* **Per-operation**: Tokens may be included in individual control messages
  using the AUTHORIZATION TOKEN message parameter. For end subscribers, this
  applies to SUBSCRIBE, SUBSCRIBE_NAMESPACE, FETCH, and REQUEST_UPDATE messages. For original
  publishers, this applies to PUBLISH and PUBLISH_NAMESPACE messages. When a track's catalog entry includes an
  `authInfo` field, valid authorization credentials MUST be included in the
  control messages used to access that track.

Original publishers and end subscribers independently choose when and how to
present their tokens based on their authorization requirements.

### Authorization in SETUP Messages

Both original publishers and end subscribers MAY include authorization tokens
in their respective SETUP messages to establish session-wide authorization:

* **End subscribers** include an AUTHORIZATION TOKEN parameter in CLIENT_SETUP
  when connecting to a relay. This token MAY pre-authorize the subscriber
  for subsequent SUBSCRIBE, SUBSCRIBE_NAMESPACE, FETCH, and REQUEST_UPDATE
  operations on tracks or namespaces covered by the token's scope.

* **Original publishers** include an AUTHORIZATION TOKEN parameter in CLIENT_SETUP
  when connecting to a relay. This token MAY pre-authorize the publisher
  for subsequent PUBLISH and PUBLISH_NAMESPACE operations on namespaces
  covered by the token's scope.

The SETUP token establishes a default authorization context for the session.
When a track's catalog entry includes an `authInfo` field, valid authorization
tokens MUST be included in ALL control messages associated with that track,
regardless of whether a token was provided in SETUP. This ensures that relays
can independently verify authorization for each operation.

### Handling Authorization Failures

When a relay rejects an authorization token, subscribers SHOULD handle the
failure gracefully:

* If a SUBSCRIBE or FETCH request is rejected due to invalid or expired
  authorization, the subscriber MAY attempt to obtain a fresh token and
  retry the request.

* If a token is rejected due to insufficient scope, the subscriber SHOULD
  NOT retry with the same token.

* For interactive applications, subscribers MAY prompt users to
  re-authenticate when authorization fails.

* Subscribers SHOULD implement exponential backoff when retrying failed
  authorization attempts to avoid overwhelming the relay or token issuer.

The specific error codes and retry semantics are defined by the authorization
scheme specifications. See {{PrivacyPassAuth}} for Privacy Pass error handling
and {{CATAuth}} for CAT error handling.

# Security Considerations

ToDo

# IANA Considerations {#IANA}

This document creates a new entry in the "MoQ Streaming Format" Registry
(see {{MoQTransport}} Sect 8).  The type value is 0x001, the name is
"MOQT Streaming Format" and the RFC is XXX.

--- back

# Acknowledgments
{:numbered="false"}

- the MoQ Workgroup and mailing lists.

# Contributors
{:numbered="false"}

The following persons where the co-authors of the individual draft (draft-law-moq-warpstreamingformat) this document is based on:

* Luke Curley
* Victor Vasiliev
* Suhas Nandakumar
* Kirill Pugin
* Will Law
