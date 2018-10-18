import argarse
from score import ViralityScorer
if __name__ == "__main__":

	parser = argparse.ArgumentParser(description="Calculate viral score.")
	parser.add_argument("--cluster-location", help="Location of clusters", required=True)
	parser.add_argument("--titles", help="Title count", type=int)
	parser.add_argument("--locations", help="Location count", type=int)
	parser.add_argument("--absolute", help="Whether to use absolute or not", action="store_true")
	parser.add_argument("--save-location", help="Save folder", required=True)

	args = parser.parse_args()

	scorer = ViralityScorer(args.cluster_location, args.titles, args.locations, args.absolute, args.save_location)
	scorer.calculate_scores()
