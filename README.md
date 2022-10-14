# Hopperbot
bc hopper takes something from one place to another
# Project Design
## Language
I kinda really want to do this in rust, bc I really like it, but it seems there is basically no support for this type of api for rust
I am using python, loads of libraries are already written for python, besides, Rust is more aimed at system level stuf, this isn't really that.
## Design
I want this to be datadriven:
I can put in a file with some people and their socialmedia handles and the program uses that to figure out what to update on

## Setup
I'm using [this](https://mitelman.engineering/blog/python-best-practice/automating-python-best-practices-for-a-new-project/) setup right now. Really quite usefull :]

### Setup selenium
Imports like selenium are automatically handled with this, however to use selenium we do need to install geckodriver and make sure firefox is intalled [src]:

(https://askubuntu.com/questions/870530/how-to-install-geckodriver-in-ubuntu) get the link for the latest release at the [relase page](https://github.com/mozilla/geckodriver/releases). (at time of writing this is https://github.com/mozilla/geckodriver/releases/download/v0.31.0/geckodriver-v0.31.0-linux64.tar.gz)
```
wget <link to release>
tar -xvzf <tarbal you just downloaded>
chmod +x geckodriver
sudo mv geckodriver /usr/local/bin/
```
I also had to install firefox: `sudo apt install firefox`

## Posting Images to tumblr
This seems harder than it should be. There does not seem to be a way to do this automatically with pytumblr ór pytumblr2.

From the tumblr api i gathered i need to do this as a multipart-encoded thing. I can do this with [requests](https://requests.readthedocs.io/en/latest/user/quickstart/#post-a-multipart-encoded-file)

# Project Content

## Posting to
- Tumblr [api](https://www.tumblr.com/oauth/apps) (oauth2)
  - using [pytumblr](https://github.com/tumblr/pytumblr)

## Automated Updates
- Twitter [api](https://developer.twitter.com/en/docs) (oauth2)
  - using [tweepy](https://www.tweepy.org/)
  - Renders tweets using [selenium](https://stackoverflow.com/questions/68834123/convert-html-to-image-using-python)
- Twitch [api](https://dev.twitch.tv/docs/api/) (oauth2)
- Youtube [api](https://developers.google.com/youtube/v3)
- Instagram [api](https://developers.facebook.com/docs/instagram-basic-display-api)
  - ~~Stories are not supported :(~~
  - but there _is_ an api for it: [link](https://instaloader.github.io/)
- Reddit? [api](https://www.reddit.com/dev/api/)
- Tiktok [api](https://developers.tiktok.com/doc/getting-started-ios-quickstart-objective-c/)
  - [docs](https://dteather.com/TikTok-Api/docs/TikTokApi.html) for a python wrapper

## (Seemingly) Unautoupdatables
- Ranmail
- private twitters
- _ is on _ stream!
- _ is in this video
- _ tweeted about _
- ...
-
## CCs to update on
- Tommy
- Wilbur
- Ranboo
- Tubbo
- Aimsey?
- ...
