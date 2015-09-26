#!/bin/bash

result=$(curl -s -i --user-agent "" -H "User-Agent: Mozilla" -d "client=t" -d "ie=UTF-8" -d "tl=en" --data-urlencode "text=hi there" https://translate.google.com/translate_tts)


echo "result is $result"