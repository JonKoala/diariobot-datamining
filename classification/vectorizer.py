from sklearn.feature_extraction.text import TfidfVectorizer


class Vectorizer:

    def __init__(self, corpus, stopwords=None):
        self.vectorspace = TfidfVectorizer(stop_words=stopwords)
        self.corpus = corpus

    def _learn(self, data):
        self.vectorspace.fit(data)
        self.features = self.vectorspace.get_feature_names()

    def transform(self, data):
        return self.vectorspace.transform(data)

    @property
    def corpus(self):
        return self._corpus

    @corpus.setter
    def corpus(self, value):
        self._corpus = value
        self._learn(self._corpus)