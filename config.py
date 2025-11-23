import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Gemini Model Configuration
GEMINI_MODEL = "gemini-2.5-flash"  # Latest fast model

# Interview Duration Settings (in minutes)
INTERVIEW_DURATIONS = {
    "Quick Practice (5 min)": 5,
    "Standard Interview (15 min)": 15,
    "Full Interview (30 min)": 30,
    "Extended Interview (45 min)": 45
}

# Answer Time Limits (in seconds)
ANSWER_TIME_WARNING = 90  # Warning after 90 seconds
ANSWER_TIME_LIMIT = 180   # Skip question after 180 seconds (3 minutes)

# Interview Configuration
INTERVIEW_ROLES = {
    "Software Engineer": {
        "focus_areas": ["technical skills", "problem-solving", "system design", "coding practices", "data structures", "algorithms"],
        "common_questions": [
            "Tell me about a challenging technical problem you solved",
            "How do you approach debugging complex issues?",
            "Describe your experience with version control and collaboration",
            "Walk me through a system design you've implemented"
        ],
        "resume_keywords": ["python", "java", "javascript", "react", "node", "aws", "docker", "kubernetes", "api", "database"]
    },
    "Sales Representative": {
        "focus_areas": ["communication", "persuasion", "customer handling", "negotiation", "relationship building"],
        "common_questions": [
            "How do you handle rejection?",
            "Describe your sales process from lead to close",
            "Tell me about your biggest sales achievement",
            "How do you build rapport with difficult clients?"
        ],
        "resume_keywords": ["sales", "revenue", "quota", "crm", "b2b", "b2c", "pipeline", "prospecting"]
    },
    "Retail Associate": {
        "focus_areas": ["customer service", "teamwork", "conflict resolution", "multitasking", "product knowledge"],
        "common_questions": [
            "How do you handle difficult customers?",
            "Describe a time you went above and beyond for a customer",
            "How do you work in a team environment?",
            "Tell me about handling multiple customers at once"
        ],
        "resume_keywords": ["retail", "customer service", "sales", "cash handling", "inventory", "merchandising"]
    },
    "Marketing Manager": {
        "focus_areas": ["strategy", "creativity", "analytics", "campaign management", "ROI optimization"],
        "common_questions": [
            "Describe a successful marketing campaign you led",
            "How do you measure marketing success?",
            "Tell me about a campaign that didn't work and what you learned",
            "How do you balance creativity with data-driven decisions?"
        ],
        "resume_keywords": ["marketing", "seo", "sem", "social media", "analytics", "campaign", "brand", "content"]
    },
    "Customer Support": {
        "focus_areas": ["empathy", "problem-solving", "patience", "communication", "technical knowledge"],
        "common_questions": [
            "How do you handle an angry customer?",
            "Describe your approach to troubleshooting customer issues",
            "Tell me about a time you turned a negative experience into a positive one",
            "How do you prioritize multiple support tickets?"
        ],
        "resume_keywords": ["support", "customer service", "troubleshooting", "ticketing", "zendesk", "helpdesk"]
    },
    "Product Manager": {
        "focus_areas": ["product strategy", "stakeholder management", "prioritization", "user research", "roadmap planning"],
        "common_questions": [
            "How do you prioritize features for a product roadmap?",
            "Describe a time you had to make a difficult product decision",
            "How do you gather and validate user requirements?",
            "Tell me about a product launch you led"
        ],
        "resume_keywords": ["product", "roadmap", "agile", "scrum", "user research", "metrics", "kpi"]
    },
    "Data Analyst": {
        "focus_areas": ["data analysis", "SQL", "visualization", "statistics", "business intelligence"],
        "common_questions": [
            "Describe your approach to analyzing a new dataset",
            "How do you communicate insights to non-technical stakeholders?",
            "Tell me about a time your analysis led to business impact",
            "What tools do you use for data visualization?"
        ],
        "resume_keywords": ["sql", "python", "tableau", "power bi", "excel", "statistics", "data", "analytics"]
    }
}

# Feedback Categories
FEEDBACK_CATEGORIES = [
    "Communication Clarity",
    "Technical/Domain Knowledge",
    "Confidence Level",
    "Answer Structure (STAR method)",
    "Use of Specific Examples",
    "Relevance to Role",
    "Areas for Improvement"
]

# Interview Settings
TEMPERATURE = 0.7  # AI creativity level

# Voice Settings
VOICE_ENABLED = True
TTS_LANGUAGE = "en"
TTS_SLOW = False  # Speak at normal speed

# Resume Parsing Settings
SUPPORTED_RESUME_FORMATS = [".pdf", ".docx", ".txt"]
MAX_RESUME_SIZE_MB = 5