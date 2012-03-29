"""
Copyright (c) 2012 Casey Dunham <casey.dunham@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS
OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

__author__ = 'Casey Dunham <casey.dunham@gmail.com>'
__version__ = '0.1'

import argparse
import urllib
import sys

from urllib2 import (Request, urlopen, HTTPError, URLError)

try:
    # Python >= 2.6
    import json
except ImportError:
    try:
        # Python < 2.6
        import simplejson as json
    except ImportError:
        try:
            # Google App Engine
            from django.utils import simplejson as json
        except ImportError:
            raise ImportError, "Unable to load a json library"


class TweetDumpError(Exception):

    @property
    def message(self):
        return self.args[0]

class RateLimitError(TweetDumpError):
    pass

API_URL = "https://api.twitter.com/1/statuses/user_timeline.json?%s"

# we are not authenticating so this will return the rate limit based on our IP
# see (https://dev.twitter.com/docs/api/1/get/account/rate_limit_status)
RATE_LIMIT_API_URL = "https://api.twitter.com/1/account/rate_limit_status.json"

parser = argparse.ArgumentParser(description="dump all tweets from user")
parser.add_argument("handle", type=str, help="twitter screen name")


def get_tweets(screen_name, count, maxid=None):
    params = {
        "screen_name": screen_name,
        "count": count,
        "exclude_replies": "true",
        "include_rts": "true"
    }

    # if we include the max_id from the last tweet we retrieved, we will retrieve the same tweet again
    # so decrement it by one to not retrieve duplicate tweets
    if maxid:
        params["max_id"] = int(maxid) - 1

    encoded_params = urllib.urlencode(params)
    query = API_URL % encoded_params
    resp = fetch_url(query)

    ratelimit_limit = resp.headers["X-RateLimit-Limit"]
    ratelimit_remaining = resp.headers["X-RateLimit-Remaining"]
    ratelimit_reset = resp.headers["X-RateLimit-Reset"]
    tweets = json.loads(resp.read())
    return ratelimit_remaining, tweets

def get_initial_rate_info():
    resp = fetch_url(RATE_LIMIT_API_URL)
    rate_info = json.loads(resp.read())
    return rate_info["remaining_hits"], rate_info["reset_time_in_seconds"], rate_info["reset_time"]

def fetch_url(url):
    try:
        return urlopen(Request(url))
    except HTTPError, e:
        if e.code == 400: # twitter api limit reached
            raise RateLimitError(e.code)
        if e.code == 502: # Bad Gateway, sometimes get this when making requests. just try again
            raise TweetDumpError(e.code)
        print >> sys.stderr, "[!] HTTP Error %s: %s" % (e.code, e.msg)
    except URLError, e:
        print  >> sys.stderr, "[!] URL Error: %s   URL: %s" % (e.reason, url)
    exit(1)

def print_banner():
    print "tweet-dump %s (c) 2012 %s" % (__version__, __author__)
    print """     .-.
    (. .)__,')
    / V      )
    \  (   \/ .
     `._`.__\\ o ,
        <<  `'   .o..
    """

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog="tweet-dump")
    parser.add_argument('username', help="Twitter Screen Name")
    parser.add_argument('file', help="File to write tweeets to")
    parser.add_argument('--count', help="Number of tweets to retrieve per request", default=200)
    parser.add_argument('--maxid', help="ID of Tweet to start dumping after", default=None)
    args = parser.parse_args()

    screen_name = args.username
    count = args.count
    maxid = args.maxid
    out_file_name = args.file

    out_file = None
    try:
        out_file = open(out_file_name, 'w')
    except IOError, e:
        print >> sys.stderr, "[!] error creating file %s" % out_file_name
        exit(1)

    print_banner()
    print "[*] writing tweets to %s " % out_file_name
    print "[*] dumping tweets for user %s" % screen_name,

    max_requests = 5
    requests_made = 0
    tweet_count = 0

    while True:
        # get initial rate information
        (remaining, rst_time_s, rst_time) = get_initial_rate_info()

        while remaining > 0:
            try:
                (remaining, tweets) = get_tweets(screen_name, count, maxid)
            except RateLimitError:
                pass
            except TweetDumpError, e:
                pass
            else:
                requests_made += 1
                if len(tweets) > 0:
                    for tweet in tweets:
                        maxid = tweet["id"]
                        out_file.write(u"%s    %s: %s\n" % (tweet["created_at"], maxid, repr(tweet["text"])))
                        tweet_count += 1
                else:
                    print "[*] reached end of tweets"
                    break

        break

    print "[*] %d tweets dumped!" % tweet_count

