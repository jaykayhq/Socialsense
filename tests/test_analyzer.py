import unittest
import sys
import os

# Adjust Python path to import modules from 'src'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Conditional import for spaCy to allow tests to run even if spaCy or model is missing,
# though some tests might be skipped or have limited scope.
try:
    import spacy
    # Try to load the model to see if it's available.
    # This also makes it available for tests that use it.
    nlp_spacy = spacy.load("en_core_web_sm")
    SPACY_AVAILABLE = True
except (ImportError, OSError):
    nlp_spacy = None
    SPACY_AVAILABLE = False
    print("Warning: spaCy or en_core_web_sm model not found. Some TrendIdentifier tests may be skipped or limited.")

from ai_analysis.analyzer import SentimentAnalyzer, TrendIdentifier, AIAnalyzerService

class TestSentimentAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = SentimentAnalyzer()

    def test_positive_sentiment(self):
        result = self.analyzer.analyze_sentiment("This is a great and awesome product! Love it.")
        self.assertEqual(result["label"], "positive")
        self.assertTrue(result["score"] > 0)

    def test_negative_sentiment(self):
        result = self.analyzer.analyze_sentiment("This is terrible and awful. I hate this poor experience.")
        self.assertEqual(result["label"], "negative")
        self.assertTrue(result["score"] < 0)

    def test_neutral_sentiment_no_keywords(self):
        result = self.analyzer.analyze_sentiment("The sky is blue and the weather is calm.")
        self.assertEqual(result["label"], "neutral")
        self.assertEqual(result["score"], 0.0)

    def test_neutral_sentiment_balanced_keywords(self):
        result = self.analyzer.analyze_sentiment("It's a good product, but the setup was bad.")
        # Current basic logic: good=1, bad=1 -> neutral
        self.assertEqual(result["label"], "neutral")
        self.assertEqual(result["score"], 0)

    def test_empty_input(self):
        result = self.analyzer.analyze_sentiment("")
        self.assertEqual(result["label"], "neutral") # Default for empty/invalid
        self.assertEqual(result["score"], 0.0)
        self.assertIn("error", result)

    def test_none_input(self):
        result = self.analyzer.analyze_sentiment(None)
        self.assertEqual(result["label"], "neutral")
        self.assertEqual(result["score"], 0.0)
        self.assertIn("error", result)

    def test_case_insensitivity(self):
        # Sentiment keywords are checked in lowercase.
        result_upper = self.analyzer.analyze_sentiment("This is GREAT!")
        result_lower = self.analyzer.analyze_sentiment("This is great!")
        self.assertEqual(result_upper["label"], "positive")
        self.assertEqual(result_lower["label"], "positive")
        self.assertEqual(result_upper["score"], result_lower["score"])

@unittest.skipUnless(SPACY_AVAILABLE, "spaCy or en_core_web_sm model not available, skipping TrendIdentifier tests that require it.")
class TestTrendIdentifierSpacy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure the global nlp object in analyzer.py is the one we loaded, if available
        # This is a bit of a hack for testing; ideally, nlp would be injected.
        if SPACY_AVAILABLE:
            # Pass the loaded spaCy model to TrendIdentifier instance for this test class
            cls.identifier = TrendIdentifier(nlp_engine=nlp_spacy)
        else:
            # Should not happen if skipUnless works, but as a fallback:
            cls.identifier = TrendIdentifier(nlp_engine=None)


    def test_extract_keywords_basic_hashtags_and_nouns(self):
        texts = [
            "Loving the new #NaijaTech trends! #Innovation is key.",
            "Big data and #AI are shaping the future of #NaijaTech.",
            "Another great #NaijaTech event in Lagos."
        ]
        # Expected: naijatech (3), innovation (1), ai (1), data (1), future (1), event (1), lagos (1)
        # The exact nouns depend on spaCy's POS tagging and lemmatization.
        # Hashtags: naijatech, innovation, ai
        # Nouns: trends, key, data, future, event, lagos (lemmatized)
        keywords = self.identifier.extract_keywords(texts, top_n=5)

        self.assertTrue(len(keywords) <= 5)
        # Check for the most prominent hashtag
        found_naijatech = any(kw[0] == "naijatech" for kw in keywords)
        self.assertTrue(found_naijatech, "Expected '#naijatech' to be a top trend.")
        if found_naijatech:
            naijatech_trend = next(kw for kw in keywords if kw[0] == "naijatech")
            self.assertEqual(naijatech_trend[1], 3) # Count for #naijatech

    def test_extract_keywords_stop_word_and_punct_removal(self):
        texts = ["This is a test, with many common words like 'the' and 'a'. Check #TestKeyword."]
        # Expect "testkeyword" (hashtag) and "test" (noun), "word" (noun) etc.
        # "this", "is", "a", "with", "many", "common", "like", "the", "and" should be ignored if stop words.
        # Punctuation like ',' '.' should be ignored.
        keywords = self.identifier.extract_keywords(texts, top_n=3)
        keyword_terms = [kw[0] for kw in keywords]

        self.assertIn("testkeyword", keyword_terms)
        self.assertNotIn("this", keyword_terms)
        self.assertNotIn(",", keyword_terms)

    def test_extract_keywords_top_n(self):
        texts = ["#one #two #three #four #five #six"]
        keywords_top_3 = self.identifier.extract_keywords(texts, top_n=3)
        self.assertEqual(len(keywords_top_3), 3)
        keywords_top_all = self.identifier.extract_keywords(texts, top_n=10) # Ask for more than available
        self.assertEqual(len(keywords_top_all), 6) # Should return all 6 unique hashtags

    def test_extract_keywords_empty_list_or_empty_strings(self):
        self.assertEqual(self.identifier.extract_keywords([]), [])
        self.assertEqual(self.identifier.extract_keywords(["", "   "]), [])
        # Changed test string to be truly devoid of extractable nouns/hashtags by spaCy
        self.assertEqual(self.identifier.extract_keywords(["!!! ???"], top_n=5), [])


class TestTrendIdentifierNoSpacy(unittest.TestCase):
    def setUp(self):
        # For this test class, ensure TrendIdentifier is instantiated without an nlp_engine
        self.identifier = TrendIdentifier(nlp_engine=None)

    def test_extract_keywords_no_spacy_fallback_hashtags_only(self):
        texts = [
            "Loving the new #NaijaTech trends! #Innovation is key.",
            "Big data and #AI are shaping the future of #NaijaTech.",
            "No spaCy, so only #NaijaTech and #AI and #Innovation should appear."
        ]
        # Fallback logic only extracts hashtags.
        # Expected: naijatech (3), innovation (2), ai (1)
        keywords = self.identifier.extract_keywords(texts, top_n=3)
        self.assertEqual(len(keywords), 3)

        keyword_map = {kw[0]: kw[1] for kw in keywords}
        self.assertEqual(keyword_map.get("naijatech"), 3) # Correct: #NaijaTech, #NaijaTech., #NaijaTech
        self.assertEqual(keyword_map.get("innovation"), 2)
        self.assertEqual(keyword_map.get("ai"), 2) # Corrected: #AI appears twice
        self.assertNotIn("trends", keyword_map) # Nouns should not be extracted by fallback

    # No tearDown needed as we are not modifying globals anymore for this test class.


class TestAIAnalyzerService(unittest.TestCase):
    def setUp(self):
        # AIAnalyzerService will now also need the nlp_engine if its TrendIdentifier is to use spaCy
        # For tests here, we can pass the globally loaded nlp_spacy from the test file
        self.service_with_spacy = AIAnalyzerService(nlp_engine=nlp_spacy if SPACY_AVAILABLE else None)
        self.service_no_spacy = AIAnalyzerService(nlp_engine=None) # For testing fallback within service

        # Mock posts data
        self.sample_posts = [
            {"post_id": "1", "platform": "twitter", "content": "This is a great post about #AwesomeTech."},
            {"post_id": "2", "platform": "twitter", "content": "Feeling sad and disappointed with #BadService."},
            {"post_id": "3", "platform": "instagram", "content": "Just a neutral statement here."},
            {"post_id": "4", "platform": "twitter", "content": None}, # Post with no content
        ]

    def test_analyze_posts_basic_flow_with_spacy(self):
        if not SPACY_AVAILABLE:
            self.skipTest("Skipping spaCy-dependent AIAnalyzerService test as spaCy is not available.")

        results = self.service_with_spacy.analyze_posts(self.sample_posts)
        analyzed_posts = results["analyzed_posts"]
        trends = results["trends"]

        self.assertEqual(len(analyzed_posts), len(self.sample_posts))
        self.assertEqual(analyzed_posts[0]["sentiment"]["label"], "positive")
        self.assertEqual(analyzed_posts[1]["sentiment"]["label"], "negative")

        self.assertIsInstance(trends, list)
        if trends: # Check only if trends were found
            trend_terms = [t["term"] for t in trends]
            self.assertIn("awesometech", trend_terms) # Hashtag
            self.assertIn("badservice", trend_terms) # Hashtag
            # self.assertIn("post", trend_terms) # Noun from "great post"
            # self.assertIn("statement", trend_terms) # Noun

    def test_analyze_posts_basic_flow_no_spacy(self):
        results = self.service_no_spacy.analyze_posts(self.sample_posts)
        analyzed_posts = results["analyzed_posts"]
        trends = results["trends"]

        self.assertEqual(len(analyzed_posts), len(self.sample_posts))
        self.assertEqual(analyzed_posts[0]["sentiment"]["label"], "positive")

        self.assertIsInstance(trends, list)
        if trends: # Fallback trend identification (hashtags only)
            trend_terms = [t["term"] for t in trends]
            self.assertIn("awesometech", trend_terms)
            self.assertIn("badservice", trend_terms)
            self.assertNotIn("post", trend_terms) # Nouns should not be present

    def test_analyze_posts_empty_input(self):
        results_spacy = self.service_with_spacy.analyze_posts([])
        self.assertEqual(len(results_spacy["analyzed_posts"]), 0)
        self.assertEqual(len(results_spacy["trends"]), 0)

        results_no_spacy = self.service_no_spacy.analyze_posts([])
        self.assertEqual(len(results_no_spacy["analyzed_posts"]), 0)
        self.assertEqual(len(results_no_spacy["trends"]), 0)

if __name__ == '__main__':
    unittest.main()
