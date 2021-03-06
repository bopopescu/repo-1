# -*- coding: utf-8 -*-

'''
	Gaia Add-on
	Copyright (C) 2016 Gaia

	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import re,urllib,urlparse
from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.extensions import metadata
from resources.lib.extensions import tools
from resources.lib.externals.beautifulsoup import BeautifulSoup

class source:

	def __init__(self):
		self.pack = True # Checked by provider.py
		self.priority = 0
		self.language = ['fr']
		self.domains = ['ww1.cpabien.xyz']
		self.base_link = 'http://ww1.cpabien.xyz'
		self.search_link = '/search.php?t=%s'
		self.download_movies_link = '/telechargement/%s.torrent'
		self.download_shows_link = '/torrent_serie_m/%s.torrent'

	def movie(self, imdb, title, localtitle, year):
		try:
			url = {'imdb': imdb, 'title': title, 'year': year}
			url = urllib.urlencode(url)
			return url
		except:
			return

	def tvshow(self, imdb, tvdb, tvshowtitle, localtitle, year):
		try:
			url = {'imdb': imdb, 'tvdb': tvdb, 'tvshowtitle': tvshowtitle, 'year': year}
			url = urllib.urlencode(url)
			return url
		except:
			return

	def episode(self, url, imdb, tvdb, title, premiered, season, episode):
		try:
			if url == None: return
			url = urlparse.parse_qs(url)
			url = dict([(i, url[i][0]) if url[i] else (i, '') for i in url])
			url['title'], url['premiered'], url['season'], url['episode'] = title, premiered, season, episode
			url = urllib.urlencode(url)
			return url
		except:
			return

	def sources(self, url, hostDict, hostprDict):
		sources = []
		try:
			if url == None:
				raise Exception()

			data = urlparse.parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])
			pack = None

			if 'exact' in data and data['exact']:
				query = title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
				year = None
				season = None
				episode = None
				pack = False
				packCount = None
			else:
				title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
				year = int(data['year']) if 'year' in data and not data['year'] == None else None
				season = int(data['season']) if 'season' in data and not data['season'] == None else None
				episode = int(data['episode']) if 'episode' in data and not data['episode'] == None else None
				pack = data['pack'] if 'pack' in data else False
				packCount = data['packcount'] if 'packcount' in data else None

				if 'tvshowtitle' in data:
					if pack: query = '%s saison %d' % (title, season)
					else: query = '%s S%02dE%02d' % (title, season, episode)
				else:
					query = title # Do not include year, otherwise there are few results.
				query = re.sub('(\\\|/| -|:|;|\*|\?|"|\'|<|>|\|)', ' ', query)

			download = urlparse.urljoin(self.base_link, self.download_shows_link if 'tvshowtitle' in data else self.download_movies_link)
			url = urlparse.urljoin(self.base_link, self.search_link) % urllib.quote_plus(query)
			html = BeautifulSoup(client.request(url))

			htmlTable = html.find_all('div', id = 'gauche')[0]
			htmlRows = htmlTable.find_all('div')
			for i in range(len(htmlRows)):
				htmlRow = htmlRows[i]
				try:
					if not htmlRow['class'][0] == 'ligne0' and not htmlRow['class'][0] == 'ligne1':
						continue
				except:
					continue

				# Name
				htmlName = htmlRow.find_all('a', recursive = False)[0].getText().strip()

				# Link
				htmlLink = htmlRow.find_all('a', recursive = False)[0]['href']
				htmlLink = htmlLink.split('/')[-1].replace('.html', '')
				htmlLink = download % htmlLink

				# Size
				htmlSize = htmlRow.find_all('div', class_ = 'poid', recursive = False)[0].getText().strip().lower().replace('mo', 'MB').replace('go', 'GB').replace('o', 'b').replace('&nbsp;', '')

				# Seeds
				try: htmlSeeds = int(htmlRow.find_all('div', class_ = 'up', recursive = False)[0].getText().strip())
				except: htmlSeeds = None

				# Metadata
				meta = metadata.Metadata(name = htmlName, title = title, year = year, season = season, episode = episode, pack = pack, packCount = packCount, link = htmlLink, size = htmlSize, seeds = htmlSeeds)

				# Ignore
				if meta.ignore(False):
					continue

				# Add
				sources.append({'url' : htmlLink, 'debridonly' : False, 'direct' : False, 'source' : 'torrent', 'language' : self.language[0], 'quality': meta.videoQuality(), 'metadata' : meta, 'file' : htmlName})

			return sources
		except:
			return sources

	def resolve(self, url):
		return url
