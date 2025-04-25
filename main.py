import streamlit as st
from streamlit_elements import elements, mui, dashboard, nivo
from google import genai
import prompts as pr
import random
import json

client = genai.Client(api_key="YOUR_API_KEY")  # Replace with your actual API key

st.set_page_config(page_title="NutriChef", layout="wide")

#  Initialize session state for user data
if "user_data" not in st.session_state:
    st.session_state.user_data = {
        "gender": "Male",
        "age": 20,
        "height": 175,
        "weight": 70,
        "course_type": "Anything",
        "activity_level": "Sedentary (Little to no exercise)",
        "allergies": ""
    }

# Logo
full_logo= "images/full_logo.png"
sidebar_logo= "images/logo.png"

st.logo( image=full_logo, size="large",icon_image=sidebar_logo)
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] img {
            width: 85%; 
            height: auto; 
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Sidebar for user input
with st.sidebar:
    st.title("NutriChef - Your Personalized Meal Planner")

    st.header("User Details")

    gender = st.selectbox(
        "Gender", 
        ["Male", "Female"], 
        index=["Male", "Female"].index(st.session_state.user_data["gender"])
    )

    age = st.number_input(
        "Age (Years)", 
        min_value=10, max_value=100, step=1, 
        value=st.session_state.user_data["age"]
    )
  
    height = st.number_input(
        "Height (cm)", 
        min_value=50, max_value=250, step=1, 
        value=st.session_state.user_data["height"]
    )

    weight = st.number_input(
        "Weight (kg)", 
        min_value=25, max_value=150, step=1, 
        value=st.session_state.user_data["weight"]
    )

    course_type = st.selectbox(
        "Course Type", 
        ["Anything", "Vegetarian", "Non-Vegatarian", "Vegan"],
        index=["Anything", "Vegetarian", "Non-Vegatarian", "Paleo", "Vegan"].index(st.session_state.user_data["course_type"]) 
    )

    activity_options = [
        "Sedentary (Little to no exercise)",
        "Lightly Active (1-3 workouts per week)",
        "Moderately Active (3-5 workouts per week)",
        "Very Active (6-7 intense workouts per week)",
        "Super Active (Athlete level)"
    ]
    
    activity_level = st.selectbox(
        "Select Activity Level", 
        activity_options, 
        index=activity_options.index(st.session_state.user_data["activity_level"])
    )

    allergy_list=[]  # Initialize an empty list for allergies
    any_allergies=st.checkbox("Do you have any food allergies?")
    if any_allergies:
        st.header("Food Allergies")
        allergies = st.text_area(
            "Enter any food allergies (comma-separated)", 
            placeholder="e.g., Peanuts, Dairy, Gluten", 
            value=st.session_state.user_data["allergies"]
        )
        allergy_list = [allergy.strip() for allergy in allergies.split(",") if allergy.strip()]
        if allergy_list:
            st.write(f"**Your Allergies:** {', '.join(allergy_list)}")
    
# Main page 
st.write("## Welcome to NutriChef! Please enter your details in the sidebar to generate a personalized meal plan.")
diet_goals = [
    "High-Protein Diet",
    "Weight Loss (Fat Loss)",
    "Muscle Gain (Bulk)"
]

# Initialize session state for selected goal
if "selected_goal" not in st.session_state:
    st.session_state.selected_goal = diet_goals[0]  # Default selection

st.write("### Select Your Diet Goal")
st.markdown("""
    <style>
    button {
        padding: 15px 20px;
        color: #212121;
        z-index: 1;
        position: relative;
        font-size: 17px;
    }

    button::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        height: 100%;
        width: 0;
        border-radius: 15px;
        background-color: #212121;
        z-index: -1;
        transition: all 250ms;
    }

    button:hover {
        color: #e8e8e8;
    }

    button:hover::before {
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

cols = st.columns(len(diet_goals))

for i, goal in enumerate(diet_goals):
    btn_class = "selected-button" if goal == st.session_state.selected_goal else "default-button"

    with cols[i]:
        if st.button(f"{goal}", key=goal, use_container_width=True):
            st.session_state.selected_goal = goal

# Store selected goal
diet_goal = st.session_state.selected_goal
st.write(f"**Selected Goal:** {diet_goal}")

activity_multipliers = {
    "Sedentary (Little to no exercise)": 1.2,
    "Lightly Active (1-3 workouts per week)": 1.375,
    "Moderately Active (3-5 workouts per week)": 1.55,
    "Very Active (6-7 intense workouts per week)": 1.725,
    "Super Active (Athlete level)": 1.9
}
macro_ratios = {
    "High-Protein Diet": {"protein": 0.35, "carbs": 0.40, "fats": 0.25},
    "Weight Loss (Fat Loss)": {"protein": 0.30, "carbs": 0.40, "fats": 0.30},
    "Muscle Gain (Bulk)": {"protein": 0.25, "carbs": 0.50, "fats": 0.25}
}
bmr = (10 * weight) + (6.25 * height) - (5 * age) + (5 if gender == "Male" else -161)   #Mifflin-St Jeor Equation
total_calories = bmr * activity_multipliers[activity_level]

col1, col2 = st.columns([1, 1])  # Equal width columns
with col1:  # Right side: Meal Options
    st.header("Meals per day")  
    meals_per_day = st.slider("Select the number of meals", min_value=1, max_value=6, value=3)

    meal_options = {
        1: ["Dinner"],
        2: ["Breakfast", "Dinner"],
        3: ["Breakfast", "Lunch", "Dinner"],
        4: ["Breakfast", "Lunch", "Snack", "Dinner"],
        5: ["Breakfast", "Snack(1)", "Lunch", "Snack(2)", "Dinner"],
        6: ["Breakfast", "Snack(1)", "Lunch", "Snack(2)", "Dinner", "Snack(3)"]
    }
    selected_meals = meal_options[meals_per_day]
    meal_queries = {}

    for meal in selected_meals:
        with st.expander(f"{meal} Options"):
            search_query = st.text_input(f"🔍 Search for {meal} meal (optional)", key=meal)
            meal_queries[meal] = search_query if search_query else meal

    custom_calories = st.checkbox("Enter your own calorie intake?")
    if custom_calories:
        user_calories = st.number_input("Enter daily calorie target", min_value=500, max_value=5000, step=100)
        reval=st.button("Revaluate")
        if reval:
            total_calories = user_calories

with col2:  # Left side: Nutrient Requirements
    st.header("Estimate Nutrient Requirements")
    st.write("Based on your inputs, your estimated daily requirements:")

    ratios = macro_ratios[diet_goal]

    if custom_calories:
        total_calories = user_calories

    est_protein = (total_calories * ratios["protein"]) / 4 
    est_carbs = (total_calories * ratios["carbs"]) / 4    
    est_fats = (total_calories * ratios["fats"]) / 9      
    
    st.write(f"### Daily Caloric Needs: **{total_calories:.0f} kcal**")
    st.write(f"🟡 **Protein:** {est_protein:.1f} g")
    st.write(f"🔵 **Carbohydrates:** {est_carbs:.1f} g")
    st.write(f"🟣 **Fats:** {est_fats:.1f} g")

    generate=st.button("Generate Meal Plan")
    
if client:
    st.success("Gemini API client initialized successfully.")
    if generate:
        meal_plan = {}
        st.header("Meal Plan") 
        for meal in selected_meals:
            if meal in meal_queries and meal_queries[meal]:
                search_query = meal_queries[meal]
            else:
                search_query = meal 

            try:
                prompt = pr.create_meal_recipe_prompt(
                    meal_type=meal,
                    search_query=search_query,
                    diet_goal=diet_goal,
                    course_type=course_type,
                    est_protein=est_protein,
                    est_carbs=est_carbs,
                    est_fats=est_fats,
                    total_calories=total_calories, 
                    meals_per_day=meals_per_day,  
                    allergies=allergy_list          
                )
                
                # Generate the meal plan using the Gemini API
                response = client.models.generate_content(  
                    model="gemini-2.0-flash",
                    contents=prompt
                )

                # Check if the response is valid
                if not response or not hasattr(response, 'text'):
                    st.error(f"The API response for {meal} is invalid or empty.")
                    continue
                if not response.text:
                    st.error(f"The API response for {meal} is empty. Skipping this meal.")
                    continue

                # Clean the response (remove Markdown-style code block delimiters)
                cleaned_response = response.text.strip("```json").strip("```").strip()
                try:
                    recipe_data = json.loads(cleaned_response)
                except json.JSONDecodeError:
                    st.error(f"Failed to generate {meal}. Response from API: {cleaned_response}")
                    continue

                meal_plan[meal] = recipe_data

                # Extract recipe details
                recipe_name = recipe_data["recipe"]["recipe_name"]
                calories_per_serving = recipe_data["recipe"]["nutrition_info"]["calories"]
                serving_size = recipe_data["recipe"]["servings"]["serving"][0]["serving_description"]

                st.subheader(meal)  # Meal name as a header
                st.write(f"### {recipe_name}")  
                st.write(f"**Calories:** {calories_per_serving} kcal | **Serving Size:** {serving_size}")

 
                with st.expander(f"Veiw nutrition info."):

                    # Flatten the nutrition_info dictionary
                    nutrition_info = recipe_data["recipe"]["nutrition_info"]
                    flattened_nutrition_info = []

                    for key, value in nutrition_info.items():
                        if isinstance(value, dict):  # If the value is a nested dictionary
                            for sub_key, sub_value in value.items():
                                flattened_nutrition_info.append({
                                    "Nutrient": f"{key.replace('_', ' ').title()} - {sub_key.replace('_', ' ').title()}",
                                    "Value": f"{sub_value:.1f}" if isinstance(sub_value, (int, float)) else sub_value
                                })
                        else:
                            flattened_nutrition_info.append({
                                "Nutrient": key.replace("_", " ").title(),
                                "Value": f"{value:.1f}" if isinstance(value, (int, float)) else value
                            })

                    #layout for the dashboard
                    layout = [
                        dashboard.Item("nutrition_table", 0, 0, 6, 6),  
                        dashboard.Item("pie_chart", 8, 0, 4, 3),     
                        dashboard.Item("ingredients", 6, 0, 2, 3),    
                        dashboard.Item("instructions", 6, 3, 6, 3),  
                    ]

                    # Draggable dashboard 
                    with elements(f"dashboard_{meal}"):
                        with dashboard.Grid(layout, draggableHandle=".draggable", resizable=True, style={"height": "800px"}):
                            # Nutrition Table Panel
                            with mui.Paper(key="nutrition_table", elevation=3, sx={"padding": "16px", "overflow": "auto"}):
                                mui.Typography("Nutrition Table", variant="h6", className="draggable", sx={"marginBottom": "8px"})
                                with mui.TableContainer:
                                    with mui.Table:
                                        with mui.TableHead:
                                            with mui.TableRow:
                                                mui.TableCell("Nutrient")
                                                mui.TableCell("Value")
                                        with mui.TableBody:
                                            for item in flattened_nutrition_info:
                                                with mui.TableRow:
                                                    mui.TableCell(item["Nutrient"])
                                                    mui.TableCell(item["Value"])

                            # Pie Chart Panel
                            with mui.Paper(key="pie_chart", elevation=3, sx={"padding": "16px", "overflow": "auto"}):
                                mui.Typography("Nutrient Distribution", variant="h6", className="draggable", sx={"marginBottom": "8px"})
                                pie_chart_data = [
                                    {"id": "Protein", "label": "Protein", "value": nutrition_info["protein"]},
                                    {"id": "Carbs", "label": "Carbs", "value": nutrition_info["carbohydrate"]},
                                    {"id": "Fat", "label": "Fat", "value": nutrition_info["fat"]}
                                ]
                                nivo.Pie(
                                    data=pie_chart_data,
                                    margin={"top": 40, "right": 80, "bottom": 80, "left": 80},
                                    innerRadius=0.5,
                                    padAngle=0.7,
                                    cornerRadius=3,
                                    activeOuterRadiusOffset=8,
                                    borderWidth=1,
                                    borderColor={"from": "color", "modifiers": [["darker", 0.2]]},
                                    arcLinkLabelsSkipAngle=10,
                                    arcLinkLabelsTextColor="#ffffff",
                                    arcLinkLabelsThickness=2,
                                    arcLinkLabelsColor={"from": "color"},
                                    arcLabelsSkipAngle=10,
                                    arcLabelsTextColor={"from": "color", "modifiers": [["darker", 6]]},
                                    colors=["#FCD53F", "#0074BA", "#8D65C5"],
                                    theme={
                                        "tooltip": {
                                            "container": {
                                                "background": "#ffffff",  # Tooltip background color (white)
                                                "color": "#000000",       # Tooltip text color (black)
                                                "fontSize": "14px",       # Tooltip font size
                                                "borderRadius": "4px",    # Tooltip border radius
                                                "boxShadow": "0 2px 4px rgba(0, 0, 0, 0.2)",  # Tooltip shadow
                                                "padding": "8px"          # Tooltip padding
                                            }
                                        }
                                    }
                                )

                            # Ingredients Panel
                            with mui.Paper(key="ingredients", elevation=3, sx={"padding": "16px", "overflow": "auto"}):
                                mui.Typography("Ingredients", variant="h6", className="draggable", sx={"marginBottom": "8px"})
                                for ingredient in recipe_data["recipe"]["ingredients"]:
                                    mui.Typography(f"- {ingredient}", sx={"marginBottom": "4px"})

                            # Recipe Instructions Panel
                            with mui.Paper(key="instructions", elevation=3, sx={"padding": "16px", "overflow": "auto"}):
                                mui.Typography("Recipe Instructions", variant="h6", className="draggable", sx={"marginBottom": "8px"})
                                for i, step in enumerate(recipe_data["recipe"]["instructions"], start=1):
                                    mui.Typography(f"{i}. {step}", sx={"marginBottom": "4px"})

            except Exception as e:
                st.error(f"An error occurred while generating the meal plan for {meal}: {str(e)}")
                continue
else:
    st.error("Failed to initialize the Gemini API client. Please check your API key and internet connection.")