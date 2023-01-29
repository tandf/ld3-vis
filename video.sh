ffmpeg -y -framerate 60 -i out/%06d.png -c:v libx264 -profile:v high -crf 20 -pix_fmt yuv420p out.mp4 -hide_banner -loglevel error
