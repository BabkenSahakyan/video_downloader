# video_downloader
Downloading bilibili, TTC (TGC) plus (and not only) videos using youtube4kdownloader API or yt-dlp. 

## TTC (TGC)
Extract titles from TTC (TGC) and TTC+ html page:  
$('.AccordionToggle').map((idx, val) => val.innerText)  
Object.assign({}, Array.from(document.querySelectorAll('span.title')).map(el => el.textContent))

> python --version  
Python 3.13.0

### How to use

After configuring conf.json either run:
```shell
#this uses yt-dlp to download directly
./yt_downloader.sh
#or
python3 yt_downloader.py
```

or:  
```shell
#this uses youtube4kdownloader API
python3 url_extractor.py
#and after urls are extracted into csv file run
python3 downloader.py
```