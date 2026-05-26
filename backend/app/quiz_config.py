ANSWER_EFFECTS: dict[str, dict[str, dict[str, list[str]]]] = {
    "diet": {
        "vegan": {
            "boost": ["vegan", "vegetarian"],
            "exclude": ["contains_dairy", "chicken", "beef", "pork", "fish"],
        },
        "vegetarian": {
            "boost": ["vegetarian"],
            "exclude": ["chicken", "beef", "pork", "fish"],
        },
        "gluten_free": {
            "boost": ["gluten_free"],
            "exclude": [],
        },
        "no_restrictions": {
            "boost": [],
            "exclude": [],
        },
    },
    "protein": {
        "chicken": {"boost": ["chicken"], "exclude": []},
        "beef": {"boost": ["beef"], "exclude": []},
        "fish": {"boost": ["fish"], "exclude": []},
        "no_meat": {
            "boost": ["tofu", "vegetarian"],
            "exclude": ["chicken", "beef", "pork", "fish"],
        },
    },
    "flavor": {
        "spicy": {"boost": ["spicy"], "exclude": []},
        "sweet": {"boost": ["sweet"], "exclude": []},
        "savory": {"boost": ["savory", "umami"], "exclude": []},
        "mild": {"boost": [], "exclude": ["spicy"]},
    },
    "appetite": {
        "light": {"boost": ["light"], "exclude": ["filling"]},
        "hearty": {"boost": ["filling"], "exclude": ["light"]},
        "adventurous": {"boost": ["adventurous"], "exclude": []},
        "comforting": {"boost": ["comforting"], "exclude": []},
    },
    "budget": {
        "budget": {"boost": ["budget"], "exclude": ["premium"]},
        "mid": {"boost": ["mid"], "exclude": []},
        "splurge": {"boost": ["premium"], "exclude": []},
    },
}
