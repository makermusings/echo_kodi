#!/bin/bash

curl -v -X POST -d '{"request":{"type":"IntentRequest","intent":{"name":"WhatNewShows","slots":{}}}}' http://YOURSERVER.com/alexa
echo

