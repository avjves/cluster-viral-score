import gzip, json, os, tqdm
from dateutil import parser as dateparser
import numpy as np

class ViralityScorer:

	def __init__(self, cluster_location, titles, locations, absolute, save_location):
		self.cluster_location = cluster_location
		self.save_location = save_location
		self.title_count = titles
		self.location_count = locations
		self.absolute = absolute

	def count_title_and_location_count(self):
		files = os.listdir(self.cluster_location)
		titles = set()
		locations = set()
		for filename in tqdm.tqdm(files, desc="Going through files to calculate titles and locations"):
			data = json.load(gzip.open(self.cluster_location + "/" + filename, "rt"))
			for cluster_key, cluster_data in data.items():
				for hit in cluster_data["hits"]:
					titles.add(hit["title"])
					locations.add(hit["location"])
		print("Title count: {}\tLocation count: {}".format(len(titles), len(locations)))
		return len(titles), len(locations)

	def calculate_scores(self):
		if self.title_count == None or self.location_count == None:
			self.title_count, self.location_count = self.count_title_and_location_count()

		files = os.listdir(self.cluster_location)
		min_vsc = 10
		max_vsc = 0
		for filename in tqdm.tqdm(files, desc="Calculating viral scores..."):
			data = json.load(gzip.open(self.cluster_location + "/" + filename, "rt"))
			for cluster_key, cluster_data in data.items():
				viral_score, timespan, locations, titles = self.calculate_viral_score(cluster_data)
				cluster_data["viral_score"] = viral_score
				cluster_data["timespan"] = timespan
				cluster_data["locations"] = len(locations)
				cluster_data["titles"] = len(titles)
				if viral_score > max_vsc:
					max_vsc = viral_score
				if viral_score < min_vsc:
					min_vsc = viral_score

			self.save_cluster(filename, data)

		self.normalize_scores(min_vsc, max_vsc, 0, 100)

	def normalize_scores(self, min_vsc, max_vsc, new_min, new_max):
		files = os.listdir(self.save_location)
		for filename in tqdm.tqdm(files, desc="Normalizing values..."):
			data = json.load(gzip.open(self.save_location + "/" + filename, "rt"))
			for cluster_key, cluster_data in data.items():
				score = cluster_data["viral_score"]
				new_score = self.normalize_score(score, min_vsc, max_vsc, new_min, new_max)
				cluster_data["viral_score"] = new_score
			self.save_cluster(filename, data)

	def normalize_score(score, old_min, old_max, new_min, new_max):
		new_score = ((score - old_min) / (old_max - old_min)) * (new_max - new_min) + new_min
		return new_score


	def save_cluster(self, filename, data):
		gzip.open(self.save_location + "/" + filename, "wt").write(json.dumps(data))


	def calculate_viral_score(self, cluster_data):
		dates = []
		locations = set()
		titles = set()
		for hit in cluster_data["hits"]:
			date = dateparser.parse(hit["date"])
			dates.append(date)
		dates.sort()
		timespan = (dates[-1] - dates[0]).days + 1
		if timespan > 20 and len(dates) > 10:
			dates = self.remove_outliers(dates)

		for hit in cluster_data["hits"]:
			date = dateparser.parse(hit["date"])
			if date in dates:
				locations.add(hit["location"])
				titles.add(hit["title"])
		timespan = (dates[-1] - dates[0]).days + 1
		return (len(locations) / self.location_count) * (len(titles) / self.title_count) * (1 / timespan), timespan, locations, titles


	def remove_outliers(self, dates):
		origin = dates[0]
		days = []
		for date in dates:
			diff = (date - origin).days
			days.append(diff)
		days = np.array(days)
		q1 = np.percentile(days, 25)
		q2 = np.percentile(days, 50)
		q3 = np.percentile(days, 75)
		iqrc = q3-q1
		if iqrc > 100:
			return dates
		q1bound = int(q1 - iqrc)
		q3bound = int(q3 + iqrc)
		outliers, out = [], []
		for date in dates:
			diff = (date - origin).days
			if q1bound <= diff <= q3bound:
				out.append(date)
			else:
				outliers.append(date)
		return out
