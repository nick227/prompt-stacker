code_report_card = [
"""
ok let's focus on just the file handling process. We need to be able to handle audio, video, images and pdfs. 

we are going to need to then retrieve those paths after uploading so our server.js needs a public folder to serve them through.

let's review the routes, review my multer implementation, review what our our server is exposing.

Currently we are running on http localhost, but in the future production will use https. We need to be smart about the urls for the exposed media. 

I also want the /public folder organized by file type and date. 

So we need an advanced file manager service.
""",
""" 
yes proceed setup the flexible file manager.
""", 
""" 
focus on the folder management let's keep it simple and robust.
""", 
""" 
great double check your work.
""", 
""" 
Let's work on adding a new post to the HOME feed. 

The HOME feed is like Tik-Tok but more conversational. It's a cross between Tik-Tok and Facebook, except all about our fake elections.

Fist I want to show the entire scope. 

Later we will go through the components, services and hooks individually and focus on them.

For now let's look at the big picture.

Create Post Feature Requirements:
    Textarea for typing text (multi-line, auto-expand).
    Attach media button → select/upload photo/video/audio from device.
    Speech to text button  → speech to textarea.
    Record audio section  → shares audio file as content.
    Allow multiple media per post; show small thumbnail strip with remove option.
    Record Video section → starts live stream setup (title + privacy) directly from composer.
    Create Poll button → open poll creator.

We need to break this functionality down into atomic React components.

We need to correlate this functionality with our available routes and data schema.

Some large separate views include: 

  - Record Video feature (probably most complex)
  - The audio recorder screen (also complex displays audio waveform)
  - The create Poll screen (very simple easy minimal)

Consider our state, hooks and props.

UI Components and new containers.

We also have to think about the Services (API layer).

So to summarize, the new post to feed widget allows the user to go live or share multiple media and content types. 

First you analyze the new feature and decide what our initial priorities should be.

Let's think about shared services or state setup before we dive into the components.

We are going to focus on the components a lot later, for now let's setup our client to server requirements.

Remember the feed is infinite scroll lazy loader.

Have a look at our current routes and prisma. 

In our app posts are feed items. 

Users can schedule posts, videos and streams can all be scheduled and followed by site members who get notifications.

users can follow scheduled releases and get notifications on release.

One thing I am considering is if we should add a posts table that can organize everything into a consistent format for retrieval.

Setup our front end state to work with existing routes and create new routes when needed. 

Let's dig deep and get our back and front end ready for these features.

""",
"""
ok proceed, 
""",
"""
yes let's continue, make sure we are reusing code and following best practices.
""",
"""
final review
""",
"""
great now let's focus on posting to the HOME screen, if the user is logged in they will see all feed items by date

and able to add a new feed item. 

Let's talk about the components and sub-components for our new add post feature.

For now we will work on the main containers that let's the user easily post text or speech to text and upload media or record audio or video.

Quick recap:

    Textarea for typing text (multi-line, auto-expand).
    Attach media button → select/upload photo/video/audio from device.
    Speech to text button  → speech to textarea.
    Record audio section  → shares audio file as content. (audio memo)
    Record Video section → starts live stream setup (title + privacy) directly from composer.
    Create Poll button → open poll creator. 

Users can schedule posts, videos and streams can all be scheduled and followed by site members who get notifications.


This is a mobile-first experience.

Break it down into individual components and begin implementing. 

Let's start with the top-level containers and work inward.

We want dumb as possible components.

We want reusable hooks and services where possible.

The components should be small and light, don't hesitate to break them down.

We have a lot of components coming up that will need easy consistent wiring.


""",
"""
great continue.


""",
"""
ok let's focus on the: 
    Textarea for typing text (multi-line, auto-expand).
component, this should be a beautiful highly-functional modern textarea. 
""",
"""
ok let's focus on the: 
    scheduling for later ui/ux
""",
"""
ok let's focus on the: 
    Attach media button → select/upload photo/video/audio from device.
    Speech to text button  → speech to textarea.
make sure they are styled, aligned, consistent and functional.
""",
"""
ok let's focus on the:
    Record audio section  → shares audio file as content. (audio memo)
    
eventually this will be a complex full-featured audio editing interface.

long term i want the ability for the user to see their waveform and use the waveform to seek to position in the recording and delete crop or re-record before submitting.

And i want all this advanced functionality client side. In fact audio recording is complex enough to be it's own module to organize our tools and libraries.

Start by creating our simple beautiful consistent ui screen that let's the user record, playback and submit the audio as a post. 

Consider we want to reuse most of this exact same ui in our video record feature!

Reuse existing components where possible and avoid overloading the new component. 

We call this "audio memo"

let's plan out the audio recording services and hooks in our post to feed widget then proceed.
""",
"""
ok double check your work.
""",
"""
great now let's focus on the: 
    Record Video section → starts live stream setup (title + privacy) directly from composer.

We should reuse most of the ui from our audio recording screen. 

However video recording is going to require unique services.

Let's plan out the hooks and services for the record video screen in our post to feed widget.

""",
"""
ok proceed
""",
"""
ok double check your work.
""",
"""
great now let's focus on the: 
'create poll' option which i want to title "ask a question"

we have a current create poll website section, but i want this ui built into the post feed option. 

we need to really keep it extra-minimal and simplified. 

users can ask a question and add answers to a poll. 

let's focus on creating the components and wiring it up. 

""",
"""
great proceed
""",
"""
great let's review the new components for redundancy or optimizations

""",
"""
let's focus on the add post implementation on the HOME page, how can we improve the user experience?
""",
"""
let's really seriously focus on the add post implementation on the HOME page, how can we dramatically improve the user experience?
""",
"""
Let's do a client-side code review for errors, problems and fixes.
""",
"""
Let's do a client-side code review for improvements, optimizations and upgrades.
""",
"""
ok proceed
""",
"""
great we just setup the add new post to feed feature. 

now review the client to server flow. 

confirm that are payloads and events are correctly synced and saved. 

We amy need to make adjustments for the various file handling.
""",
"""
ok let's focus on just the file handling process. We need to be able to handle audio, video, images and pdfs. 

we are going to need to then retrieve those paths so after uploading we will have to save the remote paths to our database associated with posts.

Now we must save the valid browseable url to the post object.
""",
""" 
great let's review the feed post end to end process for fixes and improvements.
""",
""" 
great let's review the feed post end to end process for fixes and improvements.
""",
""" 
great let's review the feed retrieval end to end process for fixes and improvements.

Remember the feed is infinite scroll lazy loader.
""",
""" 
great now let's focus on rendering the feed items on the homepage. 

users can follow scheduled releases and get notifications on release.

break down a feed item into individual components. 

let's proceed.
""",
""" 
great improve the ui/ux of the feed item.
""",
""" 
review our overall css strategy for improvements and optimizations. 

break down large files and make it more variable driven.
""",
""" 
review the front-end component library for improvements and optimizations.
""",
""" 
review the back-end services for improvements and optimizations.
""",
""" 
ok proceed.
""",
""" 
final review
""", 
""" 
where does the app still need improvement?
""",
""" 
ok proceed.
""",
""" 
final review
""", 
""" 
where does the app still need improvement?
""", 
""" 
ok let's start discussing another large feature. 

I want to add (near) live streaming to the site. 

I want to use ffmpeg over HTTP → Node.js → HLS initially.

we want streaming to give the streamers a room basically that users can join and they can see who is watching, we will have group chat, the streamer can kick or mute people. 

We are going to need a new module to contain all our video transcoding, ffmpeg, compression and video handling code.

We can reuse our file services when possible.

let's start with the fundamental back-end work new streaming module first.



    Auth & session start

        Node verifies the ingest token/secret → resolves the stream.
        Creates a stream_sessions row (starting) and picks an output folder: /tmp/hls/<sessionId>/.

    Spawn ffmpeg

        Node spawns ffmpeg, pipes the HTTP request body (req) into ffmpeg’s stdin.
        ffmpeg demuxes (e.g., WebM) → transcodes to H.264/AAC → segments into .ts files + an .m3u8 playlist in /tmp/hls/<sessionId>/.

    Flip to live

        When the first playable playlist appears, Node marks session live, sets streams.is_live=1, and emits a WS event so the UI can start the player.

    Serve HLS

        Express serves /hls/<sessionId>/index.m3u8 and segments.
        Playlists are short (e.g., last 6 segments) with delete_segments so disk usage stays bounded.

    End & cleanup

        On client disconnect or ffmpeg exit: mark session ended, set streams.is_live=0, clear presence, reap segments.

ffmpeg essentials (stdin → HLS)

ffmpeg -f webm -i pipe:0 \
  -fflags +genpts \
  -c:v libx264 -preset veryfast -tune zerolatency -pix_fmt yuv420p \
  -g 60 -keyint_min 60 -sc_threshold 0 \
  -c:a aac -ar 48000 -ac 2 \
  -f hls -hls_time 2 -hls_list_size 6 \
  -hls_flags delete_segments+program_date_time+independent_segments \
  -hls_segment_filename /tmp/hls/<sessionId>/seg_%05d.ts \
  /tmp/hls/<sessionId>/index.m3u8

    Why transcode? Browser upload is typically WebM (VP8/Opus); HLS on iOS requires H.264/AAC.

Node details that matter

    Streaming body → backpressure: req.pipe(ffmpeg.stdin) naturally pauses/resumes if ffmpeg lags; don’t buffer blobs in memory.
    Request timeouts: disable per-request timeouts for /ingest so long streams don’t close.
    Early 200 OK: respond immediately after launching ffmpeg; the real signal to the UI is “playlist exists” via WS/poll.
    Atomic writes: ffmpeg writes segments first, then updates the playlist; clients won’t see half-written files.
    Store HLS paths as relative (/hls/<id>.m3u8) in DB; never trust client-provided paths; generate playback URLs server-side.
    Use Prisma transactions for session start (create session + set streams.current_session_id + set is_live) and for session end to avoid race conditions.

Serving HLS correctly

    Headers: Content-Type: application/vnd.apple.mpegurl for .m3u8, video/mp2t for .ts.
    Cache: playlists Cache-Control: no-store; segments can use short max-age.
    Paths: store relative paths in DB (e.g., /hls/<sessionId>/index.m3u8), not absolute URLs.
    Disk: write to /tmp; with 2s × 6 segments at ~2.5 Mbps ≈ tens of MB total.

Lifecycle & health

    Stall watchdog: if index.m3u8 mtime doesn’t change for N seconds, mark session error, kill ffmpeg, notify UI.
    Graceful end: on req close, end ffmpeg.stdin; on ffmpeg close, finalize DB + broadcast ended.
    Thumbnails: run a second ffmpeg to grab a frame every 10–15s for posters.
    
Recommended single rendition (safe baseline)

    720p30, H.264/AAC, ~2.2–2.8 Mbps video + 96 kbps audio
    HLS 2s segments, GOP ≈ 60, x264 veryfast, tune=zerolatency
    Works on iOS/Android/desktop; OK CPU on a small container.

Security & abuse controls

    Short-lived JWT ingest tokens bound to a stream_id.
    Origin/CORS allowlist for /ingest.
    Rate-limit /ingest attempts and WS chat sends.
    Validate the streamer owns the stream before starting ffmpeg.

Failure modes to expect

    Codec mismatch: fix with input hints (-f webm) and -fflags +genpts.
    High CPU: lower bitrate/resolution; consider 720p@2–3 Mbps.
    Playlist not advancing: usually stale input or ffmpeg crash → watchdog restart/end.

""", 
""" 
great proceed.
""", 
""" 
double check your work.
""", 
""" 
double check the server-side streaming tools for optimization and memory improvements.
""", 
""" 
let's make sure the new video transcode flow services are optimal and complete
""", 
""" 
now let's look at the database schema for our new live streaming rooms features.

We need tables to manage streams and to manage the attached "rooms" that a stream more less is.

Site users can join the room and chat and watch the stream.

Stream owners can invite and kick and mute users. 

Users can schedule streams to start and prejoin and get notifications.

Scheduling a new stream or starting a stream are both "feed-worthy" events that should become new posts for users to join!

Map out the schema requirements.

review and update our prisma schema 
""", 
""" 
great focus on the streaming specific requirement.
""", 
""" 
double check your work.
""", 
""" 
let's focus on our notifications system, notifications are tied into scheduling (posts) and (users) following, we will need a back end cron like service to check schedules find prejoined users and notify them. 

we need to setup the notification system and the scheduling system.
""", 
""" 
let's focus on our scheduling system.
""", 
""" 
great proceed
""", 
""" 
let's focus on our notification system.
""", 
""" 
great proceed
""", 
""" 
review the notification and scheduling system - remember it is tied into posts! any type of posts including streams can be scheduled and followed.
""", 
""" 
great now let's review our routes and events for the complete streaming features.

Organize them separately and load them in server.ts
""", 
""" 
review the back-end streaming flow, walk through our use cases i.e. user starts stream, new user joins stream, new user leaves stream, original user ends stream
""", 
""" 
review the back-end streaming room flow, walk through our use cases i.e. user chats, original user mutes a user, original user boots a user
""", 
""" 
Review the new streaming features available to our client let's setup the state types and definitions for our front-end.
""", 
""" 
let's review the the streaming room features front-end requirements.

users can follow scheduled releases and get notifications on release.
""", 
""" 
create the new streaming screen and the new new schedule a stream screen and stub out the new child components. 
""", 
""" 
great let's focus on the client-side streaming tools. We can do some client-side video compression such as:

    Bitrate: MediaRecorder({ videoBitsPerSecond: 2_500_000, audioBitsPerSecond: 96_000 })
    Resolution/FPS: request getUserMedia({ video: { width: 1280, height: 720, frameRate: 30 } })
    Screen share: prefer 1080p 24–30 fps (text stays sharp), not 60 fps.
    Note: you’ll still transcode to H.264/AAC on the server for HLS/iOS compatibility.
    
create dedicate service, create dedicated config files, keep the code maintainable.
    
""", 
""" 
double check the client-side streaming tools for fixes and improvements.

we want to keep the code light and idiomatic.
""", 
""" 
double check the client-side streaming tools for optimization and memory improvements.
""", 
""" 
let's focus on improving the streaming screen child components.
""", 
""" 
let's focus on wiring up the the new streaming screen. 
""", 
""" 
focus on scheduling a stream for later. tie this into our notifications system.
""", 
""" 
focus on the unique url generated for the streaming session.
""", 
""" 
improve the streaming session user experience.
""", 
""" 
enhance the streaming session user experience.
""", 
""" 
let's focus on setting up the streaming session chat room. 
""", 
""" 
let's focus on improving the streaming session chat room ui/ux. 
""", 
""" 
clean up the streaming session overall ui/ux,
""", 
""" 
improve the streaming session overall ui/ux,
""", 
""" 
let's implemented improved services and hooks for the streaming session front end.
""", 
""" 
lets really focus on the streaming session socket events. 

we need to analyze streaming session chat and notifications events (for scheduling notifications)
""", 
""" 
let's improve the notifications ui
""", 
""" 
let's improve the notifications integration with the session scheduling
""", 
""" 
let's discuss scheduling posts, videos and streams can all be scheduled and followed by site members who will get notifications.
""", 
""" 
review our streaming front-end so far, how can we improve it?
""", 
""" 
let's focus on making the stream more aesthetic and pleasant
""", 
""" 
great let's do a final check for front-end streaming improvements and fixes.
""", 
""" 
yes proceed.
""", 
""" 
now let's do an end to end flow check for streaming video, fix our problems and errors!
""", 
""" 
ok let's review how started and scheduled streams become posts. 

Confirm that yes these are both feed posts and that we are able to display them in the feed

and the user can join or prejoin the stream.
""", 
""" 
focus on the HOME feed, we must be able to show when new posts and scheduled posts users may follow. 

let's make sure the components are organized and logical. 

check the props and types.
""", 
""" 
great now let's turn our attention to the user's profile page. The profile page and the HOME feed are very much connected.

While the HOME feed shows everyone's posts, the user profile only shows that user's posts. 

The user profile is their campaign page. Remember ths is a fake election website.

Let's focus on integrating the user's posts into their profile page.

we also need to integrate the create post form on the user profile.
""", 
""" 
let's improve the user profile ui/ux. 
""", 
""" 
great 
setup the user profile image
""", 
""" 
i want to make the user profile page A LOT more creative and aesthetic. 

it should be beautiful simple, elegant, creative and informative
""", 
""" 
great 
let's polish the user profile ui/ux. 
""", 
""" 
let's improve our site text and language to be more election oriented. 
""", 
"""
let's review the end to end user profile flow,
""",
""" 
let's start to work on a site search feature. 

the search results page can show posts or users or polls or media!

it is a talented page. 

initially let's work on the front-end first this time.

create the result screen and the distinct components.
""", 
""" 
let's improve the search ui/ux keep it minimal and modern. 

keep the code light and reuse components where possible.
""", 
""" 
okay let's wire up the back end to work with our new search feature.

first we need the route and this is a complex query.

create the route and let's add a new search module that we can improve in the future.
""", 
""" 
great wire up the the search back end as needed.
""", 
""" 
does our search front end and back end payload and response match?
""", 
""" 
how can we optimize and improve the search?
""", 
""" 
ok review the end to end search process for fixes and improvements
""", 
""" 
ok review the end to end search process for fixes and improvements

""", 
""" 
great final review
""", 
""" 
ok let's do a more comprehensive back-end code review
""", 
""" 
ok let's do a more comprehensive front-end code review

""", 
""" 
ok let's do a more comprehensive full-stack code review

""", 
""" 
let's double check our code for redundancy and over-engineering.

"""
]