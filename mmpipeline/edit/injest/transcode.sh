#!/bin/bash

code=0

scale_vf="-vf scale=w=-2:h=720"
#scale_vf=""
bitrate=8000k

if [[ "$2" ]]; then
	vcodec="-vcodec libx264 -pix_fmt yuv420p $scale_vf -g 30 -b:v $bitrate -vprofile high -bf 0"
	acodec="-strict experimental -acodec aac -ab 160k -ac 2"
	ffmpeg -y -i "$1" $acodec $vcodec -f mp4 "$2.inProgress.mp4"
	code=$?
	if [[ $code == 0 ]]; then
		mv "$2.inProgress.mp4" "$2"
	fi
fi

if [[ "$3" ]]; then
	vcodec=" -pix_fmt yuv420p -vcodec libvpx $scale_vf -g 30 -b:v $bitrate -vpre 720p -quality realtime -cpu-used 0 -qmin 10 -qmax 42"
	acodec="-acodec libvorbis -aq 60 -ac 2"
	ffmpeg -y -i "$1" $acodec $vcodec -f webm "$3.inProgress.webm"
	code=$?
	if [[ $code == 0 ]]; then
		mv "$3.inProgress.webm" "$3"
	fi
fi

exit $code
