class ModelTrainer(object):
	MULTIVARIATE = 1
	MULTINOMIAL = 2
	SMOOTHED = 3

	def __init__(self, type):
		if type == MULTIVARIATE:
			self.train_multivariate()
		elif type == MULTINOMIAL:
			self.train_multinomial()
		if type == SMOOTHED:
			self.train_smoothed()

	def train_multivariate(self):
		pass

	def train_multinomial(self):
		pass

	def train_smoothed(self):
		pass
