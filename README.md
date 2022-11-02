# Hopperbot
Because a hopper takes something from one place to another, and this is updateing on minecraft youtubers

# Project Design
## Language
I am using python, loads of libraries are already written for python, so there is a lot of support available.

## Design
### Data driven
As of yet very rudamentery, but in config.py you can specify the twitter handles you want to update on

### Reblogs
Work in progress:
I want to do that cool thing where ranboo-updates will reblog from tommy-updates and say "Ranboo replied to Tommy"

To do this I will need to store a list of (twitter) ids and link them to tumblr reblog id's.
I think I will also need to store the blog/person this is for, just so that I can have the correct name in the text. It would also be good to store the thread index of that tweet.

It seems sqlite is by far the easiest as there are build in python libaries for it.

## Setup
I'm using [this](https://mitelman.engineering/blog/python-best-practice/automating-python-best-practices-for-a-new-project/) setup right now. It is rather strict, but I found that works really well for me

### Setup selenium
Imports like selenium are automatically handled with poetry, however to use selenium we do need to install chromedriver and make sure chrome is intalled:


[source](https://skolo.online/documents/webscrapping/#step-1-download-chrome)
```
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt-get install -f
```

run `google-chrome --version` to get the version number
My version number didn't match up entirely. If it doesn't work, look up [here](https://chromedriver.chromium.org/downloads) what version number you should use.

```
wget https://chromedriver.storage.googleapis.com/<version-number>/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
chmod +x chromedriver
sudo mv chromedriver /usr/bin/chromedriver
sudo chown root:root /usr/bin/chromedriver
```

# Tumblr

### API
[Tumblr api](https://www.tumblr.com/oauth/apps) using [pytumblr2](https://github.com/nostalgebraist/pytumblr2)


## Twitter

### API
[Twitter api](https://developer.twitter.com/en/docs) using [tweepy](https://www.tweepy.org/),

I'm was getting a lot of disconnect errors, but [this](https://github.com/tweepy/tweepy/commit/51a5d61bfd6699ab844449698b34befd6a170857) to tweepy seems to have fixed that. This is on the dev branch, so that is why tweepy is now a git dependency.

### Screenshots
Renders tweets using [selenium](https://stackoverflow.com/questions/68834123/convert-html-to-image-using-python).

Assumptions about the layout of twitter:
- The xpath for a tweet
- The height of the header
- The height of the footer

These values can be found in renderer.py

### Users
Twitter api sends back information (username, displayname, etc) about all users involved in an includes block.
I am assuming the _first_ user in includes.users is always the author.

## Twitch
[api](https://dev.twitch.tv/docs/api/)

Will only need a few things:
- EventSub to stream start and end
- EventSub to channel changed (for title changes)
- Query a live channel to see how long it has been running
  (for things like, "X joined Y's stream (currently h:mm:ss into the stream))

## Youtube
[api](https://developers.google.com/youtube/v3)

Subscription information is the only thing we need and is done trough pubsubhubbub ([link](https://developers.google.com/youtube/v3/guides/push_notifications))

[link](youtube_push_notifications_to_discord_via) to reddit thread of someone who made a project with it. The github readme is very instructive too.

## Instagram
[api](https://developers.facebook.com/docs/instagram-basic-display-api)
~~Stories are not supported :(~~
but there _is_ an api for it: [link](https://instaloader.github.io/).
Does have webhooks, but not for "user posted"

## Reddit
[api](https://www.reddit.com/dev/api/)
[PRAW](https://asyncpraw.readthedocs.io/en/stable/getting_started/quick_start.html) Python Reddit API Wrapper. Redditor stream seems interesting.

## Tiktok
[api](https://developers.tiktok.com/doc/getting-started-ios-quickstart-objective-c/)
[docs](https://davidteather.github.io/TikTok-Api/docs/TikTokApi.html) for a python wrapper
Does have webhooks, but not for "user posted video"

## Croudsourcing updates
Maybe an ask containing `!update` and `name is on twitchchannel's stream` could automatically draft a post with the update for `name is on twitch`
If like 3 non anons send the same thing it gets posted regardless
If they include `!dontpost` or `!anon` or something their ask doesn't get published and they are thanked as "Anon".
Maybe there could be a list of trusted people who immediatly get posted if they send an update. They wouldn't have any responsebilities but if they _do_ report it gets posted immediatly

There could also be `!update` `!youtube` `specific link`
`!tweet` `link to tweet`


## (Seemingly) not updatable automatically
- Ranmail
- private twitters
- _ is on _'s stream!
- _ is in this video
- _ tweeted about _
- ...
