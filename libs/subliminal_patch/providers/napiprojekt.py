# coding=utf-8
from __future__ import absolute_import
import logging
from subliminal import Episode, Movie
from subliminal.providers.napiprojekt import NapiProjektProvider as _NapiProjektProvider, \
    NapiProjektSubtitle as _NapiProjektSubtitle, get_subhash
from subzero.language import Language
import subprocess
import requests
import time
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class NapiProjektSubtitle(_NapiProjektSubtitle):
    """NapiProjekt Subtitle."""
    provider_name = 'napiprojekt'

    def __init__(self, language, hash, duration, downloads):
        super(NapiProjektSubtitle, self).__init__(language, hash)
        self.hash = hash
        self.release_info = hash
        self.duration = duration
        self.downloads = downloads
        self.content = None

    @property
    def id(self):
        return self.hash

    def __repr__(self):
        return '<%s %r [%s]>' % (
        self.__class__.__name__, self.release_info, self.language)

    def get_matches(self, video):
        matches = set()

        # hash
        #if 'napiprojekt' in video.hashes and video.hashes['napiprojekt'] == self.hash:
        matches.add('hash')

        return matches


class NapiProjektProvider(_NapiProjektProvider):
    languages = {Language.fromalpha2(l) for l in ['pl']}
    subtitle_class = NapiProjektSubtitle
    required_hash = 'napiprojekt'
    server_url = 'http://napiprojekt.pl/unit_napisy/dl.php'

    def query(self, language, subq):
        subtitle = subq
        logger.debug('Found subtitle %r', subtitle)
        return subtitle

    def get_length(self, filename):
        result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                 "format=duration", "-of",
                                 "default=noprint_wrappers=1:nokey=1", filename],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        return float(result.stdout)

    def list_subtitles(self, video, languages):
        season = episode = None
        year=video.year
        duration = self.get_length(video.original_path)
        if isinstance(video, Episode):
            title = video.series
            season = video.season
            episode = video.episode
            v_type = "series"
        else:
            title = video.title
            v_type = "movie"

        subs = []

        url = 'https://www.napiprojekt.pl/ajax/search_catalog.php'
        req = {'queryString': title, '&queryKind': v_type, '&queryYear': year, '&associate': ''}
        searchsub = requests.post(url, data = req)
        soup2 = BeautifulSoup(searchsub.text, 'html.parser')
        result = soup2.find('a', {'class': 'movieTitleCat'})
        if result:
            sub_link = "https://www.napiprojekt.pl/" + result['href']   
            sub_link = sub_link.replace("napisy-","napisy1,1,1-dla-",1)
            if v_type == "series":
              sub_link = sub_link + "-s" + str(season).zfill(2) + "e" + str(episode).zfill(2)
            logger.debug ("Checking subs on: " + sub_link)
            page = requests.get(sub_link)
            soup = BeautifulSoup(page.text, 'html.parser')
            slider = soup.find('div', {'class': 'sliderContent _oF'})
            if slider:
              alinks = slider.findAll('a')
              howmany = len(alinks)
            else:
              howmany = 1
            lang = ""
            for e in languages:
                lang = e
                break
            for x in range(1,howmany+1):
                sub_link_loop = sub_link.replace("napisy1,1,1-dla-","napisy" + str(x) + ",1,1-dla-",1)
                #print(sub_link_loop)
                page = requests.get(sub_link_loop)
                soup = BeautifulSoup(page.text, 'html.parser')
                table = soup.find('tbody')
                #print(slider.prettify())
                if table:
                    for row in table.findAll(lambda tag: tag.name=='tr'):
                        napid = row.findAll('td')[0].find('a', href=True)['href'].replace("napiprojekt:","")
                        size = row.findAll('td')[1].text
                        fps = row.findAll('td')[2].text
                        length = row.findAll('td')[3].text
                        downloads = row.findAll('td')[6].text
                        # print("ID: " + napid)
                        # print("Rozmiar: " + size)
                        # print("FPS: " + fps)
                        # print("Czas trwania: " + length)
                        if length == "":
                          floatlength = 0
                        else:
                          lengtharray = length.split(":")
                          floatlength = int(lengtharray[0]) * 3600 + int(lengtharray[1]) * 60 + float(lengtharray[2])
                        # print("Czas trwania float: " + str(floatlength))
                        # print("Pobrań: " + downloads)
                        if duration-60 <= floatlength <= duration+60:
                            subtitle = self.subtitle_class(lang, napid, floatlength, downloads)
                            subs.append(subtitle)
            sortedsubs = sorted(subs, key=lambda subs: abs(subs.duration - duration))
            return [s for s in [self.query(lang, subsrt) for subsrt in sortedsubs] if s is not None]
        else:
            return None

        def download_subtitle(self, subtitle):
            hash = subtitle.hash
            params = {
                'v': 'dreambox',
                'kolejka': 'false',
                'nick': '',
                'pass': '',
                'napios': 'Linux',
                'l': "PL",
                'f': hash,
                't': get_subhash(hash)}
            logger.info('Searching subtitle %r', params)
            r = self.session.get(self.server_url, params=params, timeout=10)
            r.raise_for_status()

            # handle subtitles not found and errors
            if r.content[:4] == b'NPc0':
                logger.debug('No subtitles downloaded')

            subtitle2 = subtitle
            subtitle2.content = r.content
            logger.debug('Downloaded subtitle %r', subtitle2)
