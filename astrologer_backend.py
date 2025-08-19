from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import logging
from datetime import datetime
from groq import Groq
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# API Keys
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Groq client
groq_client = Groq(api_key=GROQ_API_KEY)

# Model to use (options: "llama3-8b-8192", "mixtral-8x7b-32768", "gemma-7b-it")
MODEL_NAME = "llama3-8b-8192"

# ------------------- Astrology Utils -------------------

def get_zodiac_sign(birth_date):
    """Determine zodiac sign from birth date"""
    month, day = birth_date.month, birth_date.day
    zodiac_signs = [
        (3, 21, "Aries"), (4, 20, "Taurus"), (5, 21, "Gemini"),
        (6, 21, "Cancer"), (7, 23, "Leo"), (8, 23, "Virgo"),
        (9, 23, "Libra"), (10, 23, "Scorpio"), (11, 22, "Sagittarius"),
        (12, 22, "Capricorn"), (1, 20, "Aquarius"), (2, 19, "Pisces")
    ]
    for start_month, start_day, sign in zodiac_signs:
        if month == start_month and day >= start_day:
            return sign
        elif month == (start_month % 12) + 1 and day < start_day:
            return sign
    return "Capricorn"  # fallback

def search_astrology_info(birth_data):
    """Use Tavily API to search for astrology information"""
    try:
        birth_date = datetime.strptime(birth_data['birthDate'], '%Y-%m-%d')
        today = datetime.now()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        zodiac_sign = get_zodiac_sign(birth_date)

        search_queries = [
            f"{zodiac_sign} astrology personality traits characteristics",
            f"{zodiac_sign} horoscope career love relationships",
            f"birth chart astrology {birth_data['birthPlace']} {birth_data['birthDate']}"
        ]

        all_results = []
        for query in search_queries:
            tavily_url = "https://api.tavily.com/search"
            payload = {
                "api_key": TAVILY_API_KEY,
                "query": query,
                "search_depth": "basic",
                "include_answer": True,
                "max_results": 3
            }
            try:
                response = requests.post(tavily_url, json=payload, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    if 'results' in data:
                        all_results.extend(data['results'][:2])
                    if 'answer' in data and data['answer']:
                        all_results.append({'content': data['answer'], 'title': f'Summary for {query}'})
            except requests.RequestException as e:
                logger.warning(f"Tavily search failed for query '{query}': {e}")
                continue

        return {'zodiac_sign': zodiac_sign, 'age': age, 'search_results': all_results}
    except Exception as e:
        logger.error(f"Error in search_astrology_info: {e}")
        return None

# ------------------- Groq LLM -------------------

def generate_response_with_llm(prompt):
    """Generate response using Groq API"""
    if not GROQ_API_KEY:
        return "Sorry, Groq API is not configured."

    try:
        response = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are an expert astrologer."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=800,
            top_p=0.9
        )
        # FIX: use .content instead of dict subscript
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error calling Groq API: {e}")
        return "I'm having trouble accessing my astrological insights right now. Please try again later."

# ------------------- Reading Generators -------------------

def create_astrology_reading(birth_data, search_info):
    """Create personalized astrology reading"""
    context = ""
    if search_info and 'search_results' in search_info:
        for result in search_info['search_results'][:5]:
            if 'content' in result:
                context += f"{result['content']}\n"

    prompt = f"""Create a personalized astrology reading for:

Name: {birth_data['name']}
Birth Date: {birth_data['birthDate']}
Birth Time: {birth_data['birthTime']}
Birth Place: {birth_data['birthPlace']}
Zodiac Sign: {search_info['zodiac_sign'] if search_info else 'Unknown'}

Astrological context:
{context}

Please provide ~300–400 words covering:
1. Personality traits and characteristics
2. Strengths and challenges
3. Career and life path insights
4. Relationship and compatibility
5. A brief outlook for the current period

Tone: warm, personal, insightful."""
    return generate_response_with_llm(prompt)

def answer_astrology_question(birth_data, question, search_info):
    """Answer specific astrology question"""
    context = ""
    if search_info and 'search_results' in search_info:
        for result in search_info['search_results'][:3]:
            if 'content' in result:
                context += f"{result['content']}\n"

    prompt = f"""Answer this astrology question for:

Name: {birth_data['name']}
Birth Date: {birth_data['birthDate']}
Birth Time: {birth_data['birthTime']}
Birth Place: {birth_data['birthPlace']}
Zodiac Sign: {search_info['zodiac_sign'] if search_info else 'Unknown'}

Question: {question}

Astrological context:
{context}

Provide 150–250 words, personal, thoughtful, and practical."""
    return generate_response_with_llm(prompt)

# ------------------- Routes -------------------

@app.route('/generate-reading', methods=['POST'])
def generate_reading():
    try:
        birth_data = request.json
        required_fields = ['name', 'birthDate', 'birthTime', 'birthPlace']
        for field in required_fields:
            if not birth_data.get(field):
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400

        logger.info(f"Generating reading for {birth_data['name']}")
        search_info = search_astrology_info(birth_data)
        reading = create_astrology_reading(birth_data, search_info)

        return jsonify({'success': True, 'reading': reading,
                        'zodiac_sign': search_info['zodiac_sign'] if search_info else None})
    except Exception as e:
        logger.error(f"Error in generate_reading: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/ask-question', methods=['POST'])
def ask_question():
    try:
        data = request.json
        birth_data = {
            'name': data.get('name'),
            'birthDate': data.get('birthDate'),
            'birthTime': data.get('birthTime'),
            'birthPlace': data.get('birthPlace')
        }
        question = data.get('question')
        if not question:
            return jsonify({'success': False, 'error': 'Question is required'}), 400

        logger.info(f"Answering question for {birth_data['name']}: {question}")
        search_info = search_astrology_info(birth_data)
        answer = answer_astrology_question(birth_data, question, search_info)

        return jsonify({'success': True, 'answer': answer})
    except Exception as e:
        logger.error(f"Error in ask_question: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'groq_configured': GROQ_API_KEY is not None,
        'tavily_configured': TAVILY_API_KEY is not None
    })

# ------------------- Main -------------------

if __name__ == '__main__':
    print("🌟 AI Astrologer Backend (Groq-powered) Starting...")
    print(f"Groq API configured: {'✅' if GROQ_API_KEY else '❌'}")
    print(f"Tavily API configured: {'✅' if TAVILY_API_KEY else '❌'}")
    print("Server running on http://localhost:8000")

    app.run(debug=True, host='0.0.0.0', port=8000)