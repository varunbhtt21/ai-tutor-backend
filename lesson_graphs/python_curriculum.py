"""
Python Programming Curriculum Data
Contains structured learning concepts, prerequisites, and content for Python programming
"""

from typing import List, Dict, Any

PYTHON_CURRICULUM = {
    "concepts": [
        {
            "name": "Variables and Assignment",
            "slug": "variables",
            "description": "Understanding how to store and manipulate data using variables in Python",
            "difficulty_level": 1,
            "estimated_time_minutes": 45,
            "category": "python-basics",
            "learning_objectives": [
                "Define what a variable is",
                "Create variables with different data types",
                "Understand variable naming conventions",
                "Reassign variable values"
            ],
            "explanation_text": """Variables in Python are like labeled containers that store data. Think of them as boxes with name tags that hold different types of information. You can put data into a variable, change what's inside, and use the variable name to refer to that data throughout your program.""",
            "code_examples": [
                {
                    "title": "Basic Variable Assignment",
                    "code": "name = 'Alice'\nage = 25\nheight = 5.6\nis_student = True",
                    "explanation": "Creating variables of different types: string, integer, float, and boolean"
                },
                {
                    "title": "Variable Reassignment", 
                    "code": "score = 85\nprint(score)  # Output: 85\nscore = 92\nprint(score)  # Output: 92",
                    "explanation": "Variables can be changed by assigning new values"
                }
            ],
            "practice_exercises": [
                {
                    "question": "Create a variable called 'favorite_color' and assign it the value 'blue'",
                    "solution": "favorite_color = 'blue'",
                    "difficulty": 1
                }
            ],
            "assessment_questions": [
                {
                    "question": "What will happen if you try to use a variable before creating it?",
                    "options": ["It will be set to 0", "It will cause an error", "It will be set to None", "It will work fine"],
                    "correct_answer": 1,
                    "explanation": "Python will raise a NameError if you try to use a variable that hasn't been defined"
                }
            ],
            "mastery_threshold": 0.75
        },
        {
            "name": "Data Types",
            "slug": "data-types", 
            "description": "Understanding different types of data Python can work with",
            "difficulty_level": 1,
            "estimated_time_minutes": 50,
            "category": "python-basics",
            "learning_objectives": [
                "Identify different data types (int, float, str, bool)",
                "Convert between data types",
                "Use type() function to check data types",
                "Understand when to use each data type"
            ],
            "explanation_text": """Python has several built-in data types that determine what kind of information a variable can store and what operations you can perform on it. The main types are integers (whole numbers), floats (decimal numbers), strings (text), and booleans (True/False).""",
            "code_examples": [
                {
                    "title": "Data Type Examples",
                    "code": "# Integer\nage = 25\n\n# Float\npi = 3.14159\n\n# String\ngreeting = 'Hello, World!'\n\n# Boolean\nis_sunny = True",
                    "explanation": "Examples of the four main data types in Python"
                },
                {
                    "title": "Type Conversion",
                    "code": "# Convert string to integer\nnumber_str = '42'\nnumber_int = int(number_str)\n\n# Convert integer to string\nage = 25\nage_str = str(age)",
                    "explanation": "Converting between different data types using built-in functions"
                }
            ],
            "practice_exercises": [
                {
                    "question": "Convert the string '3.14' to a float and store it in a variable called 'pi_value'",
                    "solution": "pi_value = float('3.14')",
                    "difficulty": 2
                }
            ],
            "assessment_questions": [
                {
                    "question": "What data type is the result of: 5 + 2.0",
                    "options": ["int", "float", "str", "bool"],
                    "correct_answer": 1,
                    "explanation": "When an integer and float are added, the result is always a float"
                }
            ],
            "mastery_threshold": 0.8
        },
        {
            "name": "Lists and Indexing",
            "slug": "lists",
            "description": "Working with ordered collections of data using Python lists",
            "difficulty_level": 2,
            "estimated_time_minutes": 60,
            "category": "data-structures",
            "learning_objectives": [
                "Create and modify lists",
                "Access list elements using indexing",
                "Use negative indexing",
                "Add and remove items from lists",
                "Understand list methods"
            ],
            "explanation_text": """Lists are ordered collections that can hold multiple items. Think of a list like a numbered row of boxes where each box can contain any type of data. You can access, modify, add, or remove items using their position (index) in the list.""",
            "code_examples": [
                {
                    "title": "Creating and Accessing Lists",
                    "code": "fruits = ['apple', 'banana', 'orange']\nprint(fruits[0])  # apple\nprint(fruits[-1])  # orange (last item)",
                    "explanation": "Creating a list and accessing elements by index. Negative indices count from the end."
                },
                {
                    "title": "Modifying Lists",
                    "code": "numbers = [1, 2, 3]\nnumbers.append(4)  # Add to end\nnumbers.insert(0, 0)  # Insert at beginning\nnumbers.remove(2)  # Remove specific value",
                    "explanation": "Common operations for adding and removing list elements"
                }
            ],
            "practice_exercises": [
                {
                    "question": "Create a list of three colors and print the second color",
                    "solution": "colors = ['red', 'green', 'blue']\nprint(colors[1])",
                    "difficulty": 2
                }
            ],
            "assessment_questions": [
                {
                    "question": "What does fruits[-2] return if fruits = ['apple', 'banana', 'orange']?",
                    "options": ["apple", "banana", "orange", "Error"],
                    "correct_answer": 1,
                    "explanation": "Negative indexing -2 refers to the second item from the end"
                }
            ],
            "mastery_threshold": 0.75
        },
        {
            "name": "Functions",
            "slug": "functions",
            "description": "Creating reusable blocks of code with parameters and return values",
            "difficulty_level": 3,
            "estimated_time_minutes": 75,
            "category": "python-basics",
            "learning_objectives": [
                "Define functions with def keyword",
                "Use parameters and arguments",
                "Return values from functions",
                "Understand function scope",
                "Call functions and use return values"
            ],
            "explanation_text": """Functions are reusable blocks of code that perform specific tasks. Think of them as mini-programs within your program that take inputs (parameters), do something with those inputs, and often give back a result (return value).""",
            "code_examples": [
                {
                    "title": "Basic Function Definition",
                    "code": "def greet(name):\n    return f'Hello, {name}!'\n\nmessage = greet('Alice')\nprint(message)  # Hello, Alice!",
                    "explanation": "Defining a function that takes a parameter and returns a value"
                },
                {
                    "title": "Function with Multiple Parameters",
                    "code": "def add_numbers(a, b):\n    result = a + b\n    return result\n\nsum_value = add_numbers(5, 3)\nprint(sum_value)  # 8",
                    "explanation": "A function that takes two parameters and returns their sum"
                }
            ],
            "practice_exercises": [
                {
                    "question": "Write a function called 'square' that takes a number and returns its square",
                    "solution": "def square(num):\n    return num * num",
                    "difficulty": 3
                }
            ],
            "assessment_questions": [
                {
                    "question": "What happens if a function doesn't have a return statement?",
                    "options": ["Error occurs", "Returns None", "Returns 0", "Returns empty string"],
                    "correct_answer": 1,
                    "explanation": "Functions without explicit return statements return None by default"
                }
            ],
            "mastery_threshold": 0.8
        },
        {
            "name": "Conditional Statements",
            "slug": "conditionals",
            "description": "Making decisions in code using if, elif, and else statements",
            "difficulty_level": 2,
            "estimated_time_minutes": 65,
            "category": "control-flow",
            "learning_objectives": [
                "Use if statements for conditional execution",
                "Combine conditions with elif and else",
                "Understand comparison operators",
                "Use logical operators (and, or, not)",
                "Write nested conditional statements"
            ],
            "explanation_text": """Conditional statements allow your program to make decisions and execute different code based on certain conditions. Think of them as forks in the road where your program chooses which path to take based on the current situation.""",
            "code_examples": [
                {
                    "title": "Basic If Statement",
                    "code": "age = 18\nif age >= 18:\n    print('You can vote!')\nelse:\n    print('You cannot vote yet.')",
                    "explanation": "A simple if-else statement that checks a condition"
                },
                {
                    "title": "Multiple Conditions",
                    "code": "score = 85\nif score >= 90:\n    grade = 'A'\nelif score >= 80:\n    grade = 'B'\nelif score >= 70:\n    grade = 'C'\nelse:\n    grade = 'F'",
                    "explanation": "Using elif for multiple condition checks"
                }
            ],
            "practice_exercises": [
                {
                    "question": "Write code that prints 'positive' if a number is > 0, 'negative' if < 0, and 'zero' if equal to 0",
                    "solution": "if number > 0:\n    print('positive')\nelif number < 0:\n    print('negative')\nelse:\n    print('zero')",
                    "difficulty": 2
                }
            ],
            "assessment_questions": [
                {
                    "question": "What is the output of: x = 5; if x > 3 and x < 10: print('yes')",
                    "options": ["yes", "no", "Error", "Nothing"],
                    "correct_answer": 0,
                    "explanation": "The condition (5 > 3 and 5 < 10) is True, so 'yes' is printed"
                }
            ],
            "mastery_threshold": 0.75
        },
        {
            "name": "Loops",
            "slug": "loops",
            "description": "Repeating code execution using for and while loops",
            "difficulty_level": 3,
            "estimated_time_minutes": 70,
            "category": "control-flow", 
            "learning_objectives": [
                "Use for loops to iterate over sequences",
                "Use while loops for conditional repetition",
                "Understand loop control with break and continue",
                "Use range() function with loops",
                "Avoid infinite loops"
            ],
            "explanation_text": """Loops allow you to repeat code multiple times efficiently. For loops are great when you know how many times to repeat or want to go through each item in a collection. While loops continue as long as a condition is true.""",
            "code_examples": [
                {
                    "title": "For Loop with Range",
                    "code": "# Print numbers 0 to 4\nfor i in range(5):\n    print(i)\n\n# Print numbers 1 to 5\nfor i in range(1, 6):\n    print(i)",
                    "explanation": "Using range() to generate sequences of numbers for loops"
                },
                {
                    "title": "While Loop",
                    "code": "count = 0\nwhile count < 3:\n    print(f'Count is {count}')\n    count += 1\nprint('Done!')",
                    "explanation": "A while loop that continues until the condition becomes false"
                }
            ],
            "practice_exercises": [
                {
                    "question": "Write a for loop that prints each item in the list ['cat', 'dog', 'bird']",
                    "solution": "animals = ['cat', 'dog', 'bird']\nfor animal in animals:\n    print(animal)",
                    "difficulty": 2
                }
            ],
            "assessment_questions": [
                {
                    "question": "How many times will this loop run: for i in range(2, 8, 2)?",
                    "options": ["2", "3", "4", "6"],
                    "correct_answer": 1,
                    "explanation": "range(2, 8, 2) generates [2, 4, 6], so the loop runs 3 times"
                }
            ],
            "mastery_threshold": 0.8
        }
    ],
    "prerequisites": [
        # Variables should be learned before data types (soft prerequisite)
        {"concept": "data-types", "prerequisite": "variables", "type": "soft", "strength": 0.8},
        
        # Variables and data types should be learned before lists
        {"concept": "lists", "prerequisite": "variables", "type": "hard", "strength": 1.0},
        {"concept": "lists", "prerequisite": "data-types", "type": "soft", "strength": 0.7},
        
        # Variables should be learned before functions
        {"concept": "functions", "prerequisite": "variables", "type": "hard", "strength": 1.0},
        
        # Variables should be learned before conditionals
        {"concept": "conditionals", "prerequisite": "variables", "type": "hard", "strength": 1.0},
        
        # Conditionals should be learned before loops (soft prerequisite)
        {"concept": "loops", "prerequisite": "conditionals", "type": "soft", "strength": 0.6},
        {"concept": "loops", "prerequisite": "variables", "type": "hard", "strength": 1.0},
        
        # Functions and lists reinforce each other
        {"concept": "functions", "prerequisite": "lists", "type": "reinforcement", "strength": 0.5},
        {"concept": "lists", "prerequisite": "functions", "type": "reinforcement", "strength": 0.5}
    ]
}

def get_curriculum_data() -> Dict[str, Any]:
    """Get the complete Python curriculum data"""
    return PYTHON_CURRICULUM

def get_concepts() -> List[Dict[str, Any]]:
    """Get just the learning concepts"""
    return PYTHON_CURRICULUM["concepts"]

def get_prerequisites() -> List[Dict[str, str]]:
    """Get just the prerequisite relationships"""
    return PYTHON_CURRICULUM["prerequisites"] 