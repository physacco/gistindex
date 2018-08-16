#!/bin/sh

kill -QUIT `cat /srv/www/gistindex/log/uwsgi.pid`
