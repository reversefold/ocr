#!/usr/bin/python
from gevent import monkey
monkey.patch_all()

from gevent import Greenlet
import urllib
import locale
import hashlib
import os
from pyquery import PyQuery
import random
import sys
import time

def download_mix(num):
    while True:
        try:
            url = 'http://ocremix.org/remix/OCR%.5i/' % (num,)
            page = PyQuery(url=url, opener=lambda url: urllib.urlopen(url).read())
            size, hash = page('#panel-download ul.nav li')
            size = int(size.text_content().replace('Size: ', '').replace(' bytes', '').replace(',', ''))
            hash = hash.text_content().replace('MD5 Checksum: ', '')
            links = [link.attrib['href'] for link in page('#panel-download ul li a')]
            break
        except Exception, e:
            print "Exception while getting page, trying again %r" % (e,)
            time.sleep(1)

    while True:
        try:
            if not links:
                print "No links for %r" % (num,)
                return
            link = random.choice(links)
            filename = os.path.split(link)[1]
            print "Downloading %s" % (filename,)
            print "Size: %s bytes md5: %s" % (locale.format("%d", size, grouping=True), hash)
            path = 'mp3/%s' % (filename,)
            if os.path.exists(path):
                print "File exists"
                data = open(path, 'rb').read()
                h = hashlib.md5(data)
                if len(data) != size:
                    print "Size of existing file (%r) does not match recorded size (%r), continuing to download" % (len(data), size)
                elif h.hexdigest() != hash:
                    print "MD5 of existing file (%s) doesn't match recorded MD5 (%r), continuing to download" % (h.hexdigest(), hash)
                else:
                    print "Existing file matches size and md5, skipping"
                    return
                # don't keep this in memory
                data = None
                os.remove(path)
            f = open(path, 'wb')
            u = urllib.urlopen(link)
            l = 0
            h = hashlib.md5()
            while True:
                data = u.read(102400)
                if not data:
                    break
                l += len(data)
                h.update(data)
                f.write(data)
            if l != size:
                print "Size of data (%r) doesn't match recorded size (%r), trying again" % (l, size)
                links.remove(link)
                continue
            if h.hexdigest() != hash:
                print "MD5 of data (%s) doesn't match recorded MD5 (%r), trying again" % (h.hexdigest(), hash)
                links.remove(link)
                continue
            f.close()
            u.close()
            break
        except  Exception, e:
            if not links:
                print "No more links to try for %r...." % (num,)
                return
            print "Exception downloading file, trying again %r" % (e,)
            links.remove(link)
            continue
    print "Done downloading for %r (%s)" % (num, filename)

def download_range(start, end, max_threads):
    running = []
    max_threads = min(max_threads, end - start + 1)
    for num in xrange(start, end + 1):
        if len(running) < max_threads:
            running.append(Greenlet.spawn(download_mix, num))
        while len(running) == max_threads:
            running = [gl for gl in running if not gl.ready()]
            time.sleep(0.5)

    while running:
        running = [gl for gl in running if not gl.ready()]
        time.sleep(0.5)

if __name__ == '__main__':
    import argparse

    locale.setlocale(locale.LC_ALL, 'en_US')

    parser = argparse.ArgumentParser(description='Download OCRemix tracks')
    parser.add_argument('-s', '--start', help='starting number', required=True, type=int)
    parser.add_argument('-e', '--end', help='ending number', required=True, type=int)
    parser.add_argument('-t', '--threads', help='number of concurrent downloads', default=5)
    args = parser.parse_args()

    download_range(args.start, args.end, args.threads)