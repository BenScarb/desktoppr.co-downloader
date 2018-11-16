import requests
import random
import json
import time
import sys
import os

from resolution import Resolution

class ImageToDownload:
	def __init__(self, url, res):
		self.url = url
		self.res = res

	def __str__(self):
		return "%s - %s" % (self.url, self.res)

class Downloader:
	def __init__(self, store_path, start_page=-1):
		self.storage = store_path

		if start_page==-1:
			if os.path.exists(os.path.join(self.storage,"GotTo.txt")):
				with open(os.path.join(self.storage,"GotTo.txt"), 'r') as f:
					strPage = f.readline()
				self.page = int(strPage)
			else:
				self.page = 1
		else:
			self.page = start_page

		self.__next_page = -1
		self.__url = 'https://api.desktoppr.co/1/wallpapers?page=%d'
		self.__to_get = []

	def ParsePage(self):
		print("Getting page %d %s" % (self.page, '-' * (150 - len(str(self.page)))))
		r = requests.get(self.__url % self.page, allow_redirects=True)
		data = json.loads(r.text)

		self.__next_page = data['pagination']['next']
		
		for wallpaper in data['response']:
			image_resolution = Resolution(wallpaper['width'], wallpaper['height'])
			wallpaper_url = wallpaper['image']['url']
			self.__to_get.append(ImageToDownload(wallpaper_url, image_resolution))

	def DoDownload(self):
		if len(self.__to_get) > 0:
			to_remove = []
		
			for download in self.__to_get:
				file_name = os.path.basename(download.url)
				output_path = os.path.join(self.storage, str(download.res))

				if not os.path.isdir(output_path):
					print("Creating folder: " + output_path)
					os.makedirs(output_path)

				if not os.path.exists(os.path.join(output_path, file_name)):
					with open(os.path.join(output_path, file_name), "wb") as f:
						print("Downloading %s (%s)" % (file_name, str(download.res)))
						response = requests.get(download.url, stream=True)
						total_length = response.headers.get('content-length')

						if total_length is None: # no content length header
							f.write(response.content)
						else:
							dl = 0
							total_length = int(total_length)
							for data in response.iter_content(chunk_size=4096):
								dl += len(data)
								f.write(data)
								done = int(50 * dl / total_length)
								sys.stdout.write("\r[%s%s]" % ('=' * done, ' ' * (50-done)) )    
								sys.stdout.flush()
							sys.stdout.write("\rDone%s" % (' ' * 98))
							sys.stdout.flush()
							print("")

				to_remove.append(download)
			
			for done in to_remove:
				self.__to_get.remove(done)

		open(os.path.join(self.storage,"GotTo.txt"), 'w').write(str(self.__next_page))

	def GoToNextPage(self):
		self.page = self.__next_page

if __name__ == "__main__":
	random.seed()
	d = Downloader("\\\\nas3tb\\root\\Storage\\Desktoppr_Images")
	for i in range(0, 100):
		if not os.path.exists("stop.txt"):
			d.ParsePage()
			wait_time = random.randint(1, 5)
			print("Waiting for %d seconds before download" % wait_time)
			time.sleep(wait_time)
			d.DoDownload()
			d.GoToNextPage()
			wait_time = random.randint(5, 60)
			print("Waiting for %d seconds before next page" % wait_time)
			time.sleep(wait_time)
