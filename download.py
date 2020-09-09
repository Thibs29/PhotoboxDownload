#!/usr/bin/python2
# coding: utf-8

import warnings
import requests
import bs4
from bs4 import BeautifulSoup
import re
import urlparse
import urllib
import os
from tqdm import tqdm
from six.moves.html_parser import HTMLParser

warnings.filterwarnings("ignore")

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def request_url(url, cookie):
    return requests.get(url, cookies=cookie)

def download_picture(url, pathname, picture_name):
    '''
        Downloads a file given an URL and puts it in the folder `pathname`
    '''
    if not os.path.isdir(pathname):
        os.makedirs(pathname)
    response = requests.get(url, stream=True)
    file_size = int(response.headers.get("Content-Length", 0))
    filename = os.path.join(pathname, picture_name)
    progress = tqdm(response.iter_content(1024), "Downloading "+picture_name, total=file_size, unit="B", unit_scale=True, unit_divisor=1024)
    with open(filename, "wb") as f:
        for data in progress:
            f.write(data)
            progress.update(len(data))
            
def get_AllAlbumsFormPhotobox(cookie):
    '''
        Get all albums 
    '''
    list_albums = []
    h = HTMLParser()
    base_url = 'https://www.photobox.fr/mon-photobox/albums'
    
    r = request_url(base_url, cookie)
    soup = BeautifulSoup(r.content)
    blocks = soup.findAll("a", {'class': re.compile(r'^pbx_object_title$')})
    for block in blocks:
        album_name = block['title']
        parsed = urlparse.urlparse(block['href'])
        album_id = urlparse.parse_qs(parsed.query)['album_id'][0]
        list_albums.append((album_id,h.unescape(album_name)))
    return list_albums

def get_AllPictureFromAlbum(album_id,cookie):
    '''
        Get all picture from album_id
    '''
    list_pics = []
    h = HTMLParser()
    base_url = 'https://www.photobox.fr/mon-photobox/album?album_id='
    
    r = request_url(base_url + album_id, cookie)
    soup = BeautifulSoup(r.content)
    nb_pages = len(soup.findAll("div", {'class': re.compile(r'^pbx_pagination$')}))
    '''
    
    '''
    blocks = soup.findAll("div", {'class': re.compile(r'pbx_photo_thumb')})
    for block in blocks:
        picture_url = block.h4.a['href']
        parsed = urlparse.urlparse(picture_url)
        picture_name = block.div.img['title']
        list_pics.append((album_id,urlparse.parse_qs(parsed.query)['photo_id'][0],h.unescape(picture_name)))
    
    for page in range(1,nb_pages):
        base_url_pagination = "https://www.photobox.fr/includes/ajax/my/album/content?cat=album&action=paginate&album_id="+album_id+"&page="+str(page)
        r = request_url(base_url_pagination + album_id, cookie)
        soup = BeautifulSoup(r.content)
        blocks = soup.findAll("div", {'class': re.compile(r'pbx_photo_thumb')})
        for block in blocks:
            picture_url = block.h4.a['href']
            parsed = urlparse.urlparse(picture_url)
            picture_name = block.div.img['title']
            list_pics.append((album_id,urlparse.parse_qs(parsed.query)['photo_id'][0],h.unescape(picture_name)))
    return list_pics


def get_FullSize(photo_id,cookie):
    '''
        Get url of full size picture
    '''
    base_url = 'https://www.photobox.fr/mon-photobox/photo/agrandie?photo_id='
    r = request_url(base_url + photo_id, cookie)
    soup = BeautifulSoup(r.content)
    
    imgs = soup.findAll("img", {'src': re.compile(r'serving.photos.photobox.com')})
    for img in imgs:
        return img['src']

print (bcolors.BOLD + bcolors.HEADER + "\n\n")
cookie_value = raw_input ("Saisir votre cookie de connexion (pbx_www_photobox_fr) :")
print (bcolors.ENDC)
cookie = {'pbx_www_photobox_fr': cookie_value}

print(bcolors.BOLD + bcolors.WARNING + "Obtention des albums" + bcolors.ENDC)
liste_album = get_AllAlbumsFormPhotobox(cookie)
for album in liste_album:
    print(bcolors.BOLD + bcolors.WARNING + "Obtention des photos de l'abum "+ album[0] + bcolors.ENDC)
    liste = get_AllPictureFromAlbum(album[0],cookie)
    print ("\nDébut du téléchargement")
    for file in liste:
        url = get_FullSize(file[1],cookie)
        download_picture(url,"/tmp/albums_photobox/"+album[1], file[2]+".jpg")
    print "Téléchargement complet pour l'album "+album[1]+" \n"+str(len(liste))+" éléments téléchargés"
