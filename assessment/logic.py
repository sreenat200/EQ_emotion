import logging
from transformers import pipeline
import math
from django.conf import settings

logger = logging.getLogger(__name__)

class AdvancedEQAssessmentModel:
    _sentiment_analyzer = None
    def __init__(self):
        self.categories = [
            "Self-awareness",
            "Emotional regulation",
            "Conflict resolution",
            "Emotional resilience",
            "Empathy / cultural awareness"
        ]


    @classmethod
    def get_sentiment_analyzer(cls):
        if cls._sentiment_analyzer is None:
            logger.info("Loading NLP model...")
            try:
                print(f"Attempting to load Primary Model: {settings.EQ_MODEL_NAME}...")
                logger.info(f"Attempting to load Primary Model: {settings.EQ_MODEL_NAME}...")
                cls._sentiment_analyzer = pipeline(
                    "sentiment-analysis", 
                    model=settings.EQ_MODEL_NAME
                )
                print(f"Primary Model ({settings.EQ_MODEL_NAME}) loaded successfully.")
                logger.info(f"Primary Model ({settings.EQ_MODEL_NAME}) loaded successfully.")
            except Exception as e:
                print(f"Primary model failed to load ({e}). Falling back to DistilBERT...")
                logger.warning(f"Primary model failed to load ({e}). Falling back to DistilBERT...")
                try:
                    cls._sentiment_analyzer = pipeline(
                        "sentiment-analysis", 
                        model=settings.EQ_FALLBACK_MODEL_NAME
                    )
                    print(f"Fallback Model ({settings.EQ_FALLBACK_MODEL_NAME}) loaded successfully.")
                    logger.info(f"Fallback Model ({settings.EQ_FALLBACK_MODEL_NAME}) loaded successfully.")
                except Exception as e2:
                    print(f"Critical: Failed to load both primary and fallback models: {e2}")
                    logger.error(f"Critical: Failed to load both primary and fallback models: {e2}")
                    raise
        return cls._sentiment_analyzer


    def generate_scenario(self, age, profession):
        age = int(age)
        if age < 30:
            level = "Junior"
        elif age <= 45:
            level = "Mid-Senior"
        else:
            level = "Senior"
        scenarios = {
            "IT Professional": {
                "Junior": "You are working on a critical bug fix that is due today. A senior developer critiques your code publicly in a team meeting, calling it 'messy and inefficient'. You feel embarrassed and frustrated.",
                "Mid-Senior": "You are leading a small team and one of your developers is consistently missing deadlines, affecting the project timeline. You need to address this without demotivating them.",
                "Senior": "A critical production issue has caused downtime for a major client. Your team is stressed and blaming each other. Upper management is demanding immediate answers while you are trying to coordinate the fix."
            },
            "Healthcare": {
                "Junior": "A patient's family member is shouting at you because they feel the wait time is too long, even though you are understaffed and doing your best.",
                "Mid-Senior": "You notice a junior nurse making a medication error. You need to intervene immediately to ensure patient safety while handling the situation discreetly and educationally.",
                "Senior": "You have to deliver difficult news to a patient's family about a treatment failure. The family is in denial and accuses the medical team of incompetence."
            },
            "Teacher": {
                "Junior": "A parent accuses you of grading their child unfairly and demands a grade change, threatening to go to the principal if you don't comply.",
                "Mid-Senior": "You are mentoring a new teacher who is struggling with classroom management. They seem defensive when you offer advice.",
                "Senior": "You notice a conflict between two colleagues that is affecting the school atmosphere. One colleague is spreading rumors about the other."
            },
            "Law Enforcement & Social Work": {
                "Junior": "You arrive at a chaotic scene where two neighbors are shouting threats at each other. One is recording you with a phone, trying to provoke a reaction.",
                "Mid-Senior": "You are managing a high-risk case involving a vulnerable family. A partner agency has failed to deliver promised support, endangering the client's safety, and you must address this professional failure.",
                "Senior": "Public trust in your department has dropped due to a recent incident. You must lead a community town hall meeting where attendees are angry, vocal, and demanding immediate policy changes."
            },
            "Business & Management": {
                "Junior": "You present a new strategy idea in a meeting, but a senior manager dismisses it without discussion, making a sarcastic comment about your lack of experience.",
                "Mid-Senior": "Two of your top performers have a personal conflict that is disrupting the team's workflow. One threatens to resign if the other isn't moved to a different department.",
                "Senior": "The company is facing a financial downturn, and you must announce significant budget cuts and potential layoffs to your department while maintaining morale and productivity."
            },
            "Creative & Media": {
                "Junior": "A client rejects your design work for the third time with vague feedback like 'make it pop', and your deadline is tomorrow. You are feeling burnt out and undervalued.",
                "Mid-Senior": "A key client is demanding changes that compromise the artistic integrity and ethical standards of a project. You need to push back firmly but diplomatically to save the account.",
                "Senior": "Your creative agency is merging with a larger corporate firm. Your team fears losing their creative freedom and unique culture. You must navigate this transition while advocating for their identity."
            },
            "Other": {
                "Junior": "You are working on a group project where one member is not contributing but expects full credit. The deadline is approaching fast.",
                "Mid-Senior": "You are managing a project where resources have been suddenly cut. You need to renegotiate deliverables with stakeholders who are resistant to change.",
                "Senior": "You are leading a project where key stakeholders have conflicting requirements and are refusing to compromise, stalling progress."
            }
        }
        prof_key = profession if profession in scenarios else "Other"
        return scenarios[prof_key].get(level, scenarios[prof_key]["Junior"])


    def generate_questions(self, profession, age, scenario):
        questions = {}
        for category in self.categories:
            if category == "Self-awareness":
                questions[category] = f"Reflecting on this {profession} scenario, what specific emotions are you feeling right now and why?"
            elif category == "Emotional regulation":
                questions[category] = "How would you manage your immediate emotional reaction upon hearing this to ensure you remain professional?"
            elif category == "Conflict resolution":
                questions[category] = f"As a {profession}, what specific steps would you take to address the conflict or tension in this situation?"
            elif category == "Emotional resilience":
                questions[category] = "If the situation worsens, how will you maintain your focus and morale?"
            elif category == "Empathy / cultural awareness":
                questions[category] = "Try to see the situation from the other person's perspective. What might they be feeling or experiencing?"
        return questions


    def validate_response(self, response_text):
        if not response_text:
            return False, "Response cannot be empty."
        words = response_text.split()
        if len(words) < 5:
             return False, "Response is too short. Please elaborate."
        return True, "Valid"

    def analyze_sentiment(self, response_text):
        analyzer = self.get_sentiment_analyzer()
        truncated_text = response_text[:512]
        logger.info(f"Analyzing sentiment for text: '{truncated_text[:50]}...'")
        result = analyzer(truncated_text)
        logger.info(f"Model Output: {result}")
        return result


    def calculate_eq_scores(self, sentiment_outputs_map, responses_map=None, user_data=None):
        scores = {}
        overall_sum = 0
        logger.info("Calculating EQ scores...")

        # EQ Keywords for heuristic analysis
        high_eq_keywords = [
            "listen", "understand", "perspective", "calm", "breathe", "reflect", 
            "empathy", "solution", "team", "growth", "learn", "ask", "support", "sorry"
        ]

        for category, result in sentiment_outputs_map.items():
            label = str(result[0]['label']).upper()
            confidence = result[0]['score']
            
            base_score = 60 

            if confidence < 0.75:
                 label = 'NEUTRAL'

            if '0' in label or 'NEGATIVE' == label:
                base_score = 50 - (confidence * 30) 
            elif '1' in label or 'NEUTRAL' == label:
                base_score = 50 + (confidence * 15)
            elif '2' in label or 'POSITIVE' == label:
                base_score = 60 + (confidence * 25)
            
            if responses_map and category in responses_map:
                text = responses_map[category]
                word_count = len(text.split())
                
                if word_count < 15:
                    base_score -= 10 
                elif word_count > 80:
                    base_score += 10 
                elif word_count > 40:
                    base_score += 5  
                
                if any(kw in text.lower() for kw in high_eq_keywords):
                    base_score += 5

            if user_data:
                age = int(user_data.get('age', 25))
                gender = user_data.get('gender', 'Other').lower()

                if category == "Emotional regulation" and age > 40:
                     if 'POSITIVE' not in label and 'LABEL_2' not in label:
                         base_score -= 5 
                
                if category == "Empathy / cultural awareness" and gender == 'male': 
                    if 'POSITIVE' in label or 'LABEL_2' in label:
                        base_score += 2

            base_score = max(0, min(100, base_score))
            
            logger.info(f"Category: {category} | Label: {label} ({confidence:.2f}) -> Score: {base_score:.1f}")
            scores[category] = round(base_score, 1)
            overall_sum += base_score
            
        scores['Overall'] = round(overall_sum / len(self.categories), 1)
        logger.info(f"Overall Score Calculated: {scores['Overall']}")
        return scores

        
    def interpret_results(self, eq_scores):
        overall = eq_scores.get('Overall', 0)
        if overall >= 80:
            rating = "High EQ"
            feedback = "You demonstrate exceptional emotional intelligence. You are likely very good at understanding yourself and others, and navigating complex social situations effectively."
        elif overall >= 60:
            rating = "Above Average EQ"
            feedback = "You have strong emotional intelligence skills. You generally handle situations well but may have specific areas for growth."
        elif overall >= 40:
            rating = "Average EQ"
            feedback = "Your emotional intelligence is average. You are functional in social settings but might struggle with high-stress or complex interpersonal dynamics."
        else:
            rating = "Developing EQ"
            feedback = "You may find emotional situations challenging. Focusing on self-awareness and empathy exercises could be very beneficial."
        return {
            "rating": rating,
            "feedback": feedback,
            "breakdown": eq_scores
        }
