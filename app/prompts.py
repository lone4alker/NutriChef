def create_meal_recipe_prompt(meal_type, search_query, diet_goal, cuisine_type, dietary_type, est_protein, est_carbs, est_fats, total_calories, meals_per_day, allergies):
    # Base calorie distribution hierarchy
    base_distribution = {
        "Dinner": 0.35,  # 35% of total calories
        "Lunch": 0.35,   # 35% of total calories
        "Breakfast": 0.20,  # 20% of total calories
        "Snack": 0.10    # 10% of total calories
    }

    # Adjust calorie distribution dynamically based on the number of meals
    if meals_per_day == 1:
        calorie_distribution = {"Dinner": 1.0}  # All calories go to Dinner
    elif meals_per_day == 2:
        calorie_distribution = {"Breakfast": 0.4, "Dinner": 0.6}  # Breakfast and Dinner
    elif meals_per_day == 3:
        calorie_distribution = {"Breakfast": 0.25, "Lunch": 0.35, "Dinner": 0.4}  # Breakfast, Lunch, Dinner
    elif meals_per_day == 4:
        calorie_distribution = {"Breakfast": 0.2, "Lunch": 0.3, "Snack": 0.1, "Dinner": 0.4}  # Add Snack
    elif meals_per_day == 5:
        calorie_distribution = {"Breakfast": 0.2, "Snack(1)": 0.1, "Lunch": 0.3, "Snack(2)": 0.1, "Dinner": 0.3}  # Two Snacks
    elif meals_per_day == 6:
        calorie_distribution = {"Breakfast": 0.2, "Snack(1)": 0.1, "Lunch": 0.25, "Snack(2)": 0.1, "Dinner": 0.25, "Snack(3)": 0.1}  # Three Snacks
    else:
        calorie_distribution = base_distribution  # Default to base distribution

    # Get the calorie percentage for the current meal type
    calorie_percentage = calorie_distribution.get(meal_type, 1 / meals_per_day)  # Default to equal distribution if not specified

    # Calculate maximum nutrients per meal based on the hierarchy
    max_calories_per_meal = total_calories * calorie_percentage
    max_protein_per_meal = est_protein * calorie_percentage
    max_carbs_per_meal = est_carbs * calorie_percentage
    max_fats_per_meal = est_fats * calorie_percentage

    # Format allergies into a comma-separated string
    allergy_list = ", ".join(allergies) if allergies else "None"

    # Create the prompt
    prompt = f"""
    Generate a {meal_type} recipe with {search_query} for {diet_goal} in JSON format.

    The recipe must strictly adhere to the following requirements:

    1. Course Type:
       - The recipe should be a {dietary_type} dish from {cuisine_type} cuisine, suitable as a complete course.

    2. Nutrition Values:
       - Provide the total nutrition values for the entire recipe.
       - The recipe should be flexible to serve either a single person (maximum meal size) or a single serving (minimum size).
       - Calories: Up to {max_calories_per_meal:.0f} kcal with maximum fluctuation of 20 kcal.
       - Protein: Up to {max_protein_per_meal:.1f} grams with maximum fluctuation of 6 grams.
       - Carbohydrates: Up to {max_carbs_per_meal:.1f} grams with maximum fluctuation of 6 grams.
       - Fats: Up to {max_fats_per_meal:.1f} grams with maximum fluctuation of 6 grams.
       - Saturated Fat: Up to 10% of {total_calories}.

    3. Calorie Distribution Hierarchy:
       - The calorie distribution is dynamically adjusted based on the number of meals:
         - {', '.join([f"{meal}: {percentage * 100:.0f}%" for meal, percentage in calorie_distribution.items()])}

    4. Meal-Specific Guidelines:
       - Breakfast and Snack meals should be high in protein and low in carbs and fats.
       - Lunch and Dinner meals should have balanced macronutrients with slightly higher calories.

    5. Ingredients and Instructions:
       - Provide all the required ingredients (till the last minute details) with their quantities in grams.
       - Include step-by-step instructions (every step in making the food till the last minute detail) for preparing the meal.
       - Use common, easily available ingredients.
       - Avoid any of the following ingredients due to allergies: {allergy_list}.

    6. Combined Nutrition Values:
       - The total calories and macronutrients of all meals combined (for {meals_per_day} meals) must stay within the following ranges: (strictly adhere to the ranges) 
         - Calories: {total_calories - 20:.0f} to {total_calories + 20:.0f} kcal
         - Protein: {est_protein - 6:.1f} to {est_protein + 6:.1f} grams
         - Carbohydrates: {est_carbs - 6:.1f} to {est_carbs + 6:.1f} grams
         - Fats: {est_fats - 6:.1f} to {est_fats + 6:.1f} grams

    7. Realistic and Nutritious:
       - The recipe should be realistic, easy to prepare, and nutritious.
       - Ensure the nutrition values are calculated for the entire recipe and are realistic based on the ingredients.

    The response must be in this exact JSON structure:
    {{
        "recipe": {{
            "recipe_id": "unique_id",
            "recipe_name": "Name of Recipe",
            "recipe_type": "{meal_type}",
            "nutrition_info": {{
                "calories": "000",
                "carbohydrate": "00.00",
                "protein": "00.00",
                "fat": "00.00",
                "saturated_fat": "00.000",
                "fiber": "0.0",
                "sugar": "0.00",
                "sodium": "000",
                "cholesterol": "00.00",
                "vitamin_a": "00.00",
                "vitamin_c": "00.00",
                "calcium": "00.00",
                "iron": "00.00"
            }},
            "servings": {{
                "serving": [
                    {{
                        "serving_description": "1 serving",
                        "serving_amount": "1",
                        "calories": "000",
                        "carbohydrate": "00.00",
                        "protein": "00.00",
                        "fat": "00.00"
                    }},
                    {{
                        "serving_description": "Meal for 1 person",
                        "serving_amount": "1",
                        "calories": "000",
                        "carbohydrate": "00.00",
                        "protein": "00.00",
                        "fat": "00.00"
                    }}
                ]
            }},
            "ingredients": [
                "Ingredient 1 with quantity",
                "Ingredient 2 with quantity",
                "Ingredient 3 with quantity"
            ],
            "instructions": [
                "Step 1 of the recipe instructions",
                "Step 2 of the recipe instructions",
                "Step 3 of the recipe instructions"
            ],
            "prep_time": "00 minutes",
            "cook_time": "00 minutes",
            "total_time": "00 minutes",
            "difficulty": "Easy/Medium/Hard",
            "dietary_tags": ["tag1", "tag2"]
        }}
    }}
    Ensure that all nutrition values are per 1 serving rather than per 100g.
    Ensure all numeric values in the nutrition section are numbers, not strings. Include at least 5 ingredients and at least 3 instruction steps.
    """
    return prompt