tweet-dump: Dump tweets from a user
===================================
"!http://api.coderwall.com/caseydunham/endorse.png!":http://coderwall.com/caseydunham

Retrieve as many tweets as possible from Twitter for a specific user. The total number of tweets that can
be retrieved depends on the user and Twitter itself. You may not be able to pull down all tweets for a user
if they have a lot of tweets.

Note that there is no authentication built in here so the twitter account must be public.

usage:

    usage: tweet-dump [-h] [--count COUNT] [--maxid MAXID] username file

    positional arguments:
      username       Twitter Screen Name
      file           File to write tweeets to

    optional arguments:
      -h, --help     show this help message and exit
      --count COUNT  Number of tweets to retrieve per request
      --maxid MAXID  ID of Tweet to start dumping after

Authors: Casey Dunham <casey.dunham@gmail.com>
Version: 0.1