"""
Pre-defined Q&A knowledge base for each business domain.

The hybrid agent checks these first (fast, ~90% accurate on common questions)
before falling back to Groq LLM for open-ended queries.
"""

DOMAINS = {
    "it_services": {
        "label": "IT Services Company",
        "company_name": "TechNova Solutions",
        "greeting": (
            "Hello! This is Alex from TechNova Solutions. "
            "We provide web development, cloud services, cybersecurity, "
            "graphic design, mobile apps, and IT support. "
            "How can I help you today?"
        ),
        "services": [
            "Custom web and mobile app development",
            "Cloud migration and AWS/Azure management",
            "Cybersecurity audits and penetration testing",
            "Graphic design, branding, and UI/UX design",
            "24/7 IT helpdesk and managed services",
            "Software maintenance and bug fixes",
            "SEO and digital marketing",
            "Data analytics and business intelligence",
        ],
        "faqs": [
            {
                "keywords": ["web development", "website", "web app", "build a site", "create website"],
                "question": "Do you offer web development?",
                "answer": (
                    "Yes! We build responsive websites and web applications using "
                    "React, Node.js, Python, and modern frameworks. Projects typically "
                    "start at two weeks for a basic site, and we offer ongoing maintenance packages."
                ),
            },
            {
                "keywords": ["graphic design", "logo", "branding", "design", "ui", "ux", "poster", "banner"],
                "question": "Do you do graphic design?",
                "answer": (
                    "Absolutely! Our graphic design team handles logos, brand identity, "
                    "social media graphics, brochures, UI/UX design, and marketing materials. "
                    "We usually deliver initial concepts within three to five business days."
                ),
            },
            {
                "keywords": ["cloud", "aws", "azure", "migration", "hosting"],
                "question": "Cloud services?",
                "answer": (
                    "We specialize in cloud migration to AWS and Azure, including setup, "
                    "optimization, and 24/7 monitoring. We also manage serverless architectures "
                    "and help reduce cloud costs by up to thirty percent."
                ),
            },
            {
                "keywords": ["cyber", "security", "hack", "penetration", "audit", "firewall"],
                "question": "Cybersecurity services?",
                "answer": (
                    "Our cybersecurity team offers vulnerability assessments, penetration testing, "
                    "compliance audits for ISO and GDPR, and managed security monitoring. "
                    "We can schedule a free initial security consultation."
                ),
            },
            {
                "keywords": ["mobile app", "android", "ios", "app development"],
                "question": "Mobile app development?",
                "answer": (
                    "Yes, we develop native and cross-platform mobile apps for iOS and Android "
                    "using Flutter and React Native. Typical timelines are six to twelve weeks "
                    "depending on complexity."
                ),
            },
            {
                "keywords": ["price", "cost", "pricing", "how much", "rate", "charge", "fee", "budget"],
                "question": "Pricing?",
                "answer": (
                    "Pricing depends on the project scope. Web development starts around five hundred dollars "
                    "for basic sites. Graphic design packages start at one hundred fifty dollars. "
                    "We offer free consultations to provide an exact quote. Would you like to schedule one?"
                ),
            },
            {
                "keywords": ["support", "helpdesk", "maintenance", "fix", "bug", "it support"],
                "question": "IT support?",
                "answer": (
                    "We offer 24/7 IT helpdesk support with response times under two hours for critical issues. "
                    "Monthly maintenance plans start at ninety-nine dollars and include updates, "
                    "backups, and security patches."
                ),
            },
            {
                "keywords": ["hours", "open", "timing", "when", "available", "contact"],
                "question": "Business hours?",
                "answer": (
                    "Our office is open Monday through Friday, nine AM to six PM. "
                    "Emergency IT support is available 24/7 for managed service clients. "
                    "You can reach us at support at technova dot com."
                ),
            },
            {
                "keywords": ["consultation", "meeting", "appointment", "schedule", "book"],
                "question": "Schedule consultation?",
                "answer": (
                    "I'd be happy to arrange a free consultation! We have slots available "
                    "this week on Tuesday and Thursday afternoons. "
                    "Would you like me to note your preferred day and time?"
                ),
            },
            {
                "keywords": ["seo", "marketing", "digital marketing", "google", "ranking"],
                "question": "SEO and marketing?",
                "answer": (
                    "We provide SEO optimization, Google Ads management, social media marketing, "
                    "and content strategy. Most clients see measurable ranking improvements within "
                    "three months of starting a campaign."
                ),
            },
        ],
    },
    "restaurant": {
        "label": "Restaurant",
        "company_name": "Spice Garden Restaurant",
        "greeting": (
            "Hello! Thank you for calling Spice Garden Restaurant. "
            "We serve authentic Pakistani and continental cuisine with dine-in, "
            "takeaway, and home delivery. How may I assist you?"
        ),
        "services": [
            "Dine-in with family seating",
            "Home delivery within 5 km radius",
            "Takeaway and curbside pickup",
            "Catering for events and weddings",
            "Private dining room for parties",
            "Daily lunch buffet (weekdays)",
            "Online table reservations",
            "Custom cake and dessert orders",
        ],
        "faqs": [
            {
                "keywords": ["menu", "food", "dishes", "serve", "what do you have", "special"],
                "question": "What's on the menu?",
                "answer": (
                    "Our menu features biryani, karahi, BBQ platters, burgers, pasta, "
                    "Chinese cuisine, and fresh salads. Today's specials are chicken tikka "
                    "karahi and mutton pulao. Would you like to hear about a specific category?"
                ),
            },
            {
                "keywords": ["reservation", "book table", "table", "reserve", "booking"],
                "question": "Table reservation?",
                "answer": (
                    "We'd love to reserve a table for you! We accept reservations for parties "
                    "of two to twenty. For weekends, we recommend booking at least one day ahead. "
                    "How many guests and what date and time work for you?"
                ),
            },
            {
                "keywords": ["delivery", "deliver", "home delivery", "order online"],
                "question": "Delivery?",
                "answer": (
                    "We deliver within a five kilometer radius. Delivery is free on orders "
                    "above one thousand rupees. Average delivery time is thirty to forty five minutes. "
                    "You can order through our website or by telling me your order now."
                ),
            },
            {
                "keywords": ["hours", "open", "close", "timing", "when"],
                "question": "Opening hours?",
                "answer": (
                    "We're open daily from eleven AM to eleven PM. "
                    "On Fridays and Saturdays we stay open until midnight. "
                    "The kitchen closes thirty minutes before closing time."
                ),
            },
            {
                "keywords": ["price", "cost", "how much", "expensive", "cheap", "rate"],
                "question": "Pricing?",
                "answer": (
                    "Our prices are very reasonable. Biryani starts at four hundred fifty rupees, "
                    "karahi from six hundred rupees, and BBQ platters from twelve hundred rupees. "
                    "We also have combo deals starting at eight hundred ninety nine rupees."
                ),
            },
            {
                "keywords": ["catering", "event", "wedding", "party", "function"],
                "question": "Catering services?",
                "answer": (
                    "We offer full catering for weddings, corporate events, and private parties. "
                    "Packages start at five hundred rupees per person with a minimum of fifty guests. "
                    "We provide setup, serving staff, and custom menus."
                ),
            },
            {
                "keywords": ["vegetarian", "vegan", "halal", "allergy", "gluten"],
                "question": "Dietary options?",
                "answer": (
                    "All our meat is halal certified. We have vegetarian options including "
                    "dal makhani, vegetable biryani, and paneer dishes. Please let us know about "
                    "any allergies when ordering and our kitchen will accommodate."
                ),
            },
            {
                "keywords": ["location", "address", "where", "find", "directions", "parking"],
                "question": "Location?",
                "answer": (
                    "We're located at Main Boulevard, Gulberg, Lahore. "
                    "Free parking is available in our basement lot. "
                    "We're near the Liberty Market roundabout, easy to find on Google Maps."
                ),
            },
            {
                "keywords": ["buffet", "lunch", "deal", "offer", "discount", "promo"],
                "question": "Deals and buffet?",
                "answer": (
                    "Our weekday lunch buffet runs Monday to Friday, twelve PM to three PM, "
                    "for only six hundred ninety nine rupees per person. "
                    "We also have a family deal: any two karahis plus naan and drinks for nineteen ninety nine rupees."
                ),
            },
            {
                "keywords": ["payment", "card", "cash", "online payment", "pay"],
                "question": "Payment methods?",
                "answer": (
                    "We accept cash, all major credit and debit cards, and mobile wallets "
                    "including JazzCash and EasyPaisa. Online orders can be paid on delivery or prepaid."
                ),
            },
        ],
    },
    "petrol_pump": {
        "label": "Petrol Pump / Gas Station",
        "company_name": "SpeedFuel Gas Station",
        "greeting": (
            "Hello! Welcome to SpeedFuel Gas Station. "
            "We offer petrol, diesel, high-speed diesel, car wash, tire air, "
            "oil change, and a convenience store. How can I help you?"
        ),
        "services": [
            "Petrol (Super / Premium)",
            "High Speed Diesel (HSD)",
            "Light Diesel Oil (LDO)",
            "Automated and manual car wash",
            "Free tire air pressure check",
            "Engine oil change service",
            "24/7 convenience store",
            "ATM and mobile top-up",
        ],
        "faqs": [
            {
                "keywords": ["petrol", "gasoline", "super", "premium", "fuel price"],
                "question": "Petrol price?",
                "answer": (
                    "Current petrol price is two hundred eighty nine rupees per liter for Super "
                    "and two hundred ninety five for Premium. Prices are updated daily as per "
                    "government notification. We have all pumps operational right now."
                ),
            },
            {
                "keywords": ["diesel", "hsd", "high speed"],
                "question": "Diesel price?",
                "answer": (
                    "High Speed Diesel is currently two hundred ninety two rupees per liter. "
                    "We also stock Light Diesel Oil for commercial vehicles at two hundred seventy five "
                    "rupees per liter. Both are available 24/7."
                ),
            },
            {
                "keywords": ["car wash", "wash", "cleaning", "vehicle wash"],
                "question": "Car wash?",
                "answer": (
                    "We offer automated car wash for three hundred rupees and full manual detailing "
                    "starting at eight hundred rupees. Express wash takes about ten minutes. "
                    "Free vacuum cleaning is included with every wash."
                ),
            },
            {
                "keywords": ["air", "tire", "tyre", "pressure", "pump air"],
                "question": "Tire air?",
                "answer": (
                    "Tire air pressure check and fill is completely free for all customers. "
                    "We have digital pressure gauges at bay two and bay four. "
                    "Just pull up and our attendant will assist you."
                ),
            },
            {
                "keywords": ["oil change", "engine oil", "lubricant", "service"],
                "question": "Oil change?",
                "answer": (
                    "We provide quick oil change service starting at twelve hundred rupees including "
                    "filter and standard engine oil. Premium synthetic oil packages start at "
                    "two thousand five hundred rupees. No appointment needed."
                ),
            },
            {
                "keywords": ["hours", "open", "24", "timing", "when", "close"],
                "question": "Operating hours?",
                "answer": (
                    "SpeedFuel is open 24 hours a day, seven days a week including public holidays. "
                    "The convenience store and car wash operate during the same hours."
                ),
            },
            {
                "keywords": ["card", "payment", "pay", "credit", "debit", "cash"],
                "question": "Payment options?",
                "answer": (
                    "We accept cash, all major credit and debit cards, and fleet fuel cards. "
                    "Contactless payment is available at all pumps. "
                    "Corporate accounts with monthly billing are also available."
                ),
            },
            {
                "keywords": ["store", "shop", "convenience", "snacks", "buy"],
                "question": "Convenience store?",
                "answer": (
                    "Our store stocks snacks, beverages, motor oil, car accessories, "
                    "phone chargers, and basic groceries. We also have an ATM and mobile "
                    "top-up services. Store hours match our 24/7 station operation."
                ),
            },
            {
                "keywords": ["location", "address", "where", "find", "near"],
                "question": "Location?",
                "answer": (
                    "We're on Motorway M2, Service Area Sukheki, near Lahore exit. "
                    "Look for the blue and orange SpeedFuel sign. "
                    "We have separate lanes for cars and heavy vehicles."
                ),
            },
            {
                "keywords": ["loyalty", "discount", "card", "points", "membership"],
                "question": "Loyalty program?",
                "answer": (
                    "Our SpeedFuel Rewards card gives you two rupees off per liter after every "
                    "five hundred liter purchase. Sign up is free at the counter. "
                    "Corporate fleet accounts get additional volume discounts."
                ),
            },
        ],
    },
}


def get_domain(domain_key: str) -> dict | None:
    return DOMAINS.get(domain_key)


def list_domains() -> dict:
    return {k: v["label"] for k, v in DOMAINS.items()}
