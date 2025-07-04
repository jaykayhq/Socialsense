import spacy
from collections import Counter
import logging

# Load the spaCy model
# This might take a moment the first time it's run after download.
try:
    nlp = spacy.load("en_core_web_sm")
    # An alternative for sentiment if not using a dedicated library initially:
    # Add a sentencizer if you want to ensure sentence boundaries for context.
    # nlp.add_pipe("sentencizer")
except OSError:
    logging.error("spaCy model 'en_core_web_sm' not found. Please download it by running: python -m spacy download en_core_web_sm")
    # Fallback to a mock nlp object if the model isn't available,
    # so the rest of the code can be syntactically checked.
    nlp = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# For a more robust sentiment analysis, consider libraries like:
# - VADER (Valence Aware Dictionary and sEntiment Reasoner) - good for social media text
# - TextBlob
# - Transformers library from Hugging Face for state-of-the-art models
# For now, we'll create a placeholder or a very basic spaCy-based approach if possible.
# spaCy's core models don't do sentiment out-of-the-box without an extension or custom component.
# We'll use a very simplistic keyword-based approach for demonstration if a dedicated library isn't added yet.

class SentimentAnalyzer:
    def __init__(self):
        """
        Initializes the SentimentAnalyzer.
        A more advanced version would load a sentiment model or lexicon.
        """
        # Simple keyword-based sentiment for demonstration
        self.positive_keywords = {"good", "great", "awesome", "love", "happy", "best", "excellent", "nice", "superb", "yay", "wow"}
        self.negative_keywords = {"bad", "terrible", "awful", "hate", "sad", "worst", "poor", "crap", "sucks", "boo"}
        logging.info("SentimentAnalyzer initialized (using basic keyword matching).")

    def analyze_sentiment(self, text):
        """
        Analyzes the sentiment of a given text.
        Returns a dictionary with 'label' (positive, negative, neutral) and 'score'.
        This is a very basic implementation.
        """
        if not text or not isinstance(text, str):
            return {"label": "neutral", "score": 0.0, "error": "Invalid input text"}

        text_lower = text.lower()
        # Sentiment analysis currently does not use spaCy's doc object directly for keyword matching,
        # but if it did, it would need access to an nlp instance.
        # For current keyword matching, it splits tokens if nlp is not available or doesn't provide lemmas.
        # Let's assume for now SentimentAnalyzer might also benefit from an nlp instance if provided.
        # However, the primary DI need is for TrendIdentifier.

        # Simple tokenization for keyword matching:
        tokens_for_sentiment = text_lower.split()
        # If we had a spaCy instance available here (e.g. self.nlp if passed to SentimentAnalyzer),
        # we could use tokens = [token.lemma_ for token in self.nlp(text_lower)]

        positive_score = 0
        negative_score = 0

        punctuation_to_strip_sentiment = '.,!?;:"\'()[]{}'

        for token in tokens_for_sentiment: # Use simple split tokens for now
            cleaned_token = token.strip(punctuation_to_strip_sentiment)
            if cleaned_token in self.positive_keywords:
                positive_score += 1
            elif cleaned_token in self.negative_keywords:
                negative_score += 1

        if positive_score > negative_score:
            return {"label": "positive", "score": positive_score - negative_score}
        elif negative_score > positive_score:
            return {"label": "negative", "score": positive_score - negative_score} # score will be negative
        else:
            return {"label": "neutral", "score": 0.0}

class TrendIdentifier:
    def __init__(self, nlp_engine=None):
        """
        Initializes the TrendIdentifier.
        nlp_engine: A loaded spaCy model instance.
        """
        self.nlp = nlp_engine
        if not self.nlp:
            logging.warning("TrendIdentifier initialized without a spaCy model. Fallback functionality will be used.")
        else:
            logging.info("TrendIdentifier initialized with a spaCy model.")

    def extract_keywords(self, text_list, top_n=10):
        """
        Extracts potential trending keywords/hashtags from a list of texts.
        Uses basic noun phrase and hashtag extraction.
        """
        if not self.nlp:
            logging.info("TrendIdentifier: spaCy model not available, using fallback for keyword extraction.")
            # Fallback: very simple hashtag extraction if no NLP
            all_hashtags = []
            punctuation_to_strip = '.,!?;:' # Common trailing punctuation on hashtags
            for text in text_list:
                if not isinstance(text, str): continue
                words = text.split()
                for word in words:
                    if word.startswith("#"):
                        cleaned_hashtag = word.lower().strip().lstrip('#').rstrip(punctuation_to_strip)
                        if cleaned_hashtag: # Ensure not empty
                            all_hashtags.append(cleaned_hashtag)
            if not all_hashtags:
                return []
            return Counter(all_hashtags).most_common(top_n)


        all_keywords = []
        for text in text_list:
            if not isinstance(text, str):
                logging.warning(f"Skipping non-string item in text_list: {type(text)}")
                continue
            doc = self.nlp(text) # Use self.nlp - Corrected Indentation

            # Specific logging for the problematic test case
            if text == "#one #two #three #four #five #six":
                logging.info(f"TrendIdentifier: Special Log for '#one #two ...': Processing doc with {len(doc)} tokens.")
                for i, token_debug in enumerate(doc):
                    logging.info(
                        f"  Token {i}: '{token_debug.text}' "
                        f"| Lemma: '{token_debug.lemma_}' "
                        f"| POS: {token_debug.pos_} "
                        f"| is_stop: {token_debug.is_stop} "
                        f"| is_punct: {token_debug.is_punct} "
                        f"| is_space: {token_debug.is_space}"
                    )

            # Extract nouns, proper nouns, and noun chunks
            # Also extract hashtags directly
            punctuation_to_strip_spacy = '.,!?;:'
            for token in doc:
                if token.text.startswith("#"): # Hashtags
                    cleaned_hashtag_spacy = token.text.lower().strip().lstrip('#').rstrip(punctuation_to_strip_spacy)
                    if cleaned_hashtag_spacy: # Ensure not empty
                        all_keywords.append(cleaned_hashtag_spacy)
                        if text == "#one #two #three #four #five #six": # More specific logging
                            logging.info(f"    Added hashtag: {cleaned_hashtag_spacy}")
                elif not token.is_stop and not token.is_punct and not token.is_space:
                    if token.pos_ in ["NOUN", "PROPN"]:
                        all_keywords.append(token.lemma_.lower())
                        if text == "#one #two #three #four #five #six": # More specific logging
                            logging.info(f"    Added NON-HASHTAG keyword: {token.lemma_.lower()}")
            # for chunk in doc.noun_chunks: # Noun phrases
            #     all_keywords.append(chunk.lemma_.lower().strip())

        if not all_keywords:
            return []

        keyword_counts = Counter(all_keywords)
        return keyword_counts.most_common(top_n)

class AIAnalyzerService:
    def __init__(self, nlp_engine=None): # Accept nlp_engine
        self.sentiment_analyzer = SentimentAnalyzer() # SentimentAnalyzer could also take nlp_engine if needed
        self.trend_identifier = TrendIdentifier(nlp_engine=nlp_engine) # Pass it to TrendIdentifier
        self.nlp_engine = nlp_engine # Store if needed for other tasks by AIAnalyzerService
        logging.info("AIAnalyzerService initialized.")

    def analyze_posts(self, posts_data):
        """
        Analyzes a list of post data (expected to be dicts with a 'content' key).
        Returns a list of posts, each augmented with sentiment, and a list of overall trends.
        """
        if not posts_data:
            return {"analyzed_posts": [], "trends": []}

        analyzed_posts = []
        all_text_content = []

        for post in posts_data:
            content = post.get('content')
            if content:
                all_text_content.append(content)
                sentiment_result = self.sentiment_analyzer.analyze_sentiment(content)
                # Augment the original post data with sentiment
                # In a real app, you'd likely create new objects or update specific fields
                augmented_post = post.copy()
                augmented_post['sentiment'] = sentiment_result
                analyzed_posts.append(augmented_post)
            else:
                # Handle posts with no content if necessary
                augmented_post = post.copy()
                augmented_post['sentiment'] = {"label": "neutral", "score": 0.0, "error": "No content to analyze"}
                analyzed_posts.append(augmented_post)

        trends = []
        if all_text_content:
            trends = self.trend_identifier.extract_keywords(all_text_content, top_n=10)
            # Format trends for consistency (list of dicts)
            trends = [{"term": term, "count": count} for term, count in trends]

        logging.info(f"Analyzed {len(analyzed_posts)} posts. Identified {len(trends)} potential trends.")
        return {"analyzed_posts": analyzed_posts, "trends": trends}

# Example Usage
if __name__ == "__main__":
    logging.info("AI Analyzer Module Demonstration")

    # Ensure NLP model is loaded for the demo to work best
    if not nlp: # nlp here is the global one loaded at the top of the file
        print("spaCy 'en_core_web_sm' model not loaded for demo. Functionality will be limited.")
        print("Please run: python -m spacy download en_core_web_sm")
        # In this case, AIAnalyzerService will instantiate TrendIdentifier without an nlp_engine.

    ai_service = AIAnalyzerService(nlp_engine=nlp) # Pass the loaded nlp (or None)

    # Sample posts (mimicking data from DataCollectionManager)
    sample_posts = [
        {"post_id": "1", "platform": "twitter", "content": "Having a great time at #NaijaTechSummit! So many innovative ideas."},
        {"post_id": "2", "platform": "twitter", "content": "This traffic in Lagos is terrible. I hate it."},
        {"post_id": "3", "platform": "instagram", "content": "Loving the new ankara styles! #LagosFashion #AnkaraLove"},
        {"post_id": "4", "platform": "twitter", "content": "Just a regular Tuesday. Nothing special."},
        {"post_id": "5", "platform": "twitter", "content": "Wow, this jollof rice is the best! #NigerianFood is awesome."},
        {"post_id": "6", "platform": "instagram", "content": "Feeling sad about the news today."},
        {"post_id": "7", "platform": "twitter", "content": "#NaijaTechSummit discussions on AI are super exciting!"},
        {"post_id": "8", "platform": "twitter", "content": None}, # Post with no content
    ]

    analysis_results = ai_service.analyze_posts(sample_posts)

    print("\n--- Analyzed Posts ---")
    for post in analysis_results["analyzed_posts"]:
        sentiment_label = post['sentiment'].get('label', 'N/A')
        sentiment_score = post['sentiment'].get('score', 'N/A')
        print(f"Post ID: {post['post_id']}, Content: '{post.get('content', 'N/A')[:50]}...', Sentiment: {sentiment_label} (Score: {sentiment_score})")

    print("\n--- Identified Trends ---")
    if analysis_results["trends"]:
        for trend in analysis_results["trends"]:
            print(f"Trend: {trend['term']}, Count: {trend['count']}")
    else:
        print("No trends identified (or NLP model issue).")

    # Test sentiment analyzer directly
    print("\n--- Direct Sentiment Test ---")
    sa = SentimentAnalyzer()
    test_sentence_positive = "This is a wonderful and excellent product!"
    test_sentence_negative = "I am very disappointed, this is poor quality."
    test_sentence_neutral = "The sky is blue."
    print(f"'{test_sentence_positive}' -> {sa.analyze_sentiment(test_sentence_positive)}")
    print(f"'{test_sentence_negative}' -> {sa.analyze_sentiment(test_sentence_negative)}")
    print(f"'{test_sentence_neutral}' -> {sa.analyze_sentiment(test_sentence_neutral)}")

    # Test trend identifier directly
    print("\n--- Direct Trend Test ---")
    ti = TrendIdentifier()
    test_texts_for_trends = [
        "Learning about #Python programming and #DataScience.",
        "Excited for the #Python conference next week! #PyCon",
        "Data science is revolutionizing industries.",
        "Another post about #Python.",
        "Is #AI the future? Many think so. #FutureTech"
    ]
    trends = ti.extract_keywords(test_texts_for_trends, top_n=5)
    print(f"Trends from test texts: {trends}")

    print("\nAI Analyzer demo finished.")
