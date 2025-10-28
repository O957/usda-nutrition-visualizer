"""
Streamlit application for food nutrient analysis and visualization.
"""

import altair as alt
import polars as pl
import streamlit as st

from nutrient_processor import NutrientProcessor
from nutritional_guidelines import NutritionalGuidelines
from usda_api import USDAFoodDataClient, fetch_and_save_food_database


def format_nutrient_name(nutrient_name: str) -> str:
    """
    Format nutrient name for display (e.g., vitamin_e_mg -> Vitamin E (Mg)).

    Parameters
    ----------
    nutrient_name : str
        Raw nutrient column name

    Returns
    -------
    str
        Formatted display name
    """
    if not isinstance(nutrient_name, str):
        return str(nutrient_name)

    # split by underscores
    parts = nutrient_name.split("_")

    if len(parts) < 2:
        return nutrient_name.title()

    # last part is usually the unit
    unit = parts[-1].upper()

    # join the rest and capitalize each word
    nutrient_part = " ".join(parts[:-1])
    nutrient_part = nutrient_part.title()

    # special cases for vitamins
    nutrient_part = nutrient_part.replace("B6", "B6")
    nutrient_part = nutrient_part.replace("B12", "B12")

    return f"{nutrient_part} ({unit})"


def initialize_data():
    """Initialize data and return processor instance."""
    if "processor" not in st.session_state:
        with st.spinner("Loading food database..."):
            try:
                processor = NutrientProcessor()
                st.session_state.processor = processor
            except Exception as e:
                st.error(f"Error loading data: {e}")
                st.session_state.processor = NutrientProcessor()
                st.session_state.processor.df = pl.DataFrame()

    return st.session_state.processor


def create_nutrient_bar_chart(nutrient_data: pl.DataFrame, title: str) -> alt.Chart:
    """
    Create Altair bar chart for nutrient data.

    Parameters
    ----------
    nutrient_data : pl.DataFrame
        DataFrame with nutrient data.
    title : str
        Chart title.

    Returns
    -------
    alt.Chart
        Altair chart object.
    """
    if nutrient_data.is_empty():
        return alt.Chart().mark_text().encode(text=alt.value("No data available"))

    # format nutrient names for display
    formatted_data = nutrient_data.with_columns(
        pl.col("nutrient").map_elements(format_nutrient_name, return_dtype=pl.Utf8).alias("nutrient_display")
    )

    # convert to pandas for altair
    df_pandas = formatted_data.to_pandas()

    # create bar chart - sort by the original amount values, not display names
    chart = (
        alt.Chart(df_pandas)
        .mark_bar()
        .encode(
            x=alt.X("amount:Q", title="Amount"),
            y=alt.Y("nutrient_display:N", sort=alt.EncodingSortField(field="amount", order="descending"), title="Nutrient"),
            color=alt.Color("amount:Q", scale=alt.Scale(scheme="viridis")),
            tooltip=[
                alt.Tooltip("nutrient_display:N", title="Nutrient"),
                alt.Tooltip("amount:Q", title="Amount", format=".2f")
            ]
        )
        .properties(title=title, width=600, height=400)
        .interactive()
    )

    return chart


def create_food_ranking_chart(food_data: pl.DataFrame, nutrient_name: str) -> alt.Chart:
    """
    Create Altair bar chart for food rankings by nutrient.

    Parameters
    ----------
    food_data : pl.DataFrame
        DataFrame with food ranking data.
    nutrient_name : str
        Name of the nutrient.

    Returns
    -------
    alt.Chart
        Altair chart object.
    """
    if food_data.is_empty():
        return alt.Chart().mark_text().encode(text=alt.value("No data available"))

    # convert to pandas
    df_pandas = food_data.to_pandas()

    # create horizontal bar chart
    chart = (
        alt.Chart(df_pandas)
        .mark_bar()
        .encode(
            x=alt.X("amount_per_ounce:Q", title="Amount per Ounce"),
            y=alt.Y("description:N", sort="-x", title="Food"),
            color=alt.Color("amount_per_ounce:Q", scale=alt.Scale(scheme="blues")),
            tooltip=["description", "amount_per_100g", "amount_per_ounce"]
        )
        .properties(
            title=f"Top Foods for {nutrient_name} (per ounce)",
            width=600,
            height=500
        )
        .interactive()
    )

    return chart


def render_food_analysis(processor: NutrientProcessor):
    """Render the food analysis page."""
    st.header("Food Nutrient Analysis")
    st.markdown("Select a food to view its nutrient content")

    # get unique food descriptions
    food_list = processor.df["description"].unique().to_list()
    food_list.sort()

    # food selection
    col1, col2 = st.columns([2, 1])
    with col1:
        selected_food = st.selectbox(
            "Select a food:",
            food_list,
            index=0
        )

    if selected_food:
        # get nutrient data
        nutrient_data = processor.get_food_nutrients(selected_food)

        if not nutrient_data.is_empty():
            # display basic info
            st.subheader(f"Nutrient Profile: {selected_food}")

            # filter for significant nutrients
            significant_nutrients = nutrient_data.filter(pl.col("amount") > 0.1)

            # create tabs for different nutrient categories
            tab1, tab2, tab3 = st.tabs(["Vitamins", "Minerals", "Macronutrients"])

            with tab1:
                # filter for vitamins
                vitamin_data = significant_nutrients.filter(
                    pl.col("nutrient").str.contains("(?i)vitamin") |
                    pl.col("nutrient").str.contains("(?i)folate") |
                    pl.col("nutrient").str.contains("(?i)thiamin") |
                    pl.col("nutrient").str.contains("(?i)riboflavin") |
                    pl.col("nutrient").str.contains("(?i)niacin")
                )
                if not vitamin_data.is_empty():
                    st.write(f"Found {len(vitamin_data)} vitamins:")
                    chart = create_nutrient_bar_chart(
                        vitamin_data,
                        f"Vitamin Content in {selected_food}"
                    )
                    st.altair_chart(chart, use_container_width=True)
                else:
                    st.info("No vitamin data available")

            with tab2:
                # filter for minerals
                mineral_keywords = ["calcium", "iron", "magnesium", "phosphorus",
                                  "potassium", "sodium", "zinc", "copper", "selenium"]
                mineral_conditions = [
                    pl.col("nutrient").str.contains(f"(?i){keyword}")
                    for keyword in mineral_keywords
                ]
                mineral_filter = mineral_conditions[0]
                for condition in mineral_conditions[1:]:
                    mineral_filter = mineral_filter | condition

                mineral_data = significant_nutrients.filter(mineral_filter)

                if not mineral_data.is_empty():
                    chart = create_nutrient_bar_chart(
                        mineral_data,
                        f"Mineral Content in {selected_food}"
                    )
                    st.altair_chart(chart, use_container_width=True)
                else:
                    st.info("No mineral data available")

            with tab3:
                # filter for macronutrients
                macro_keywords = ["protein", "fat", "carbohydrate", "fiber", "sugar", "energy"]
                macro_conditions = [
                    pl.col("nutrient").str.contains(f"(?i){keyword}")
                    for keyword in macro_keywords
                ]
                macro_filter = macro_conditions[0]
                for condition in macro_conditions[1:]:
                    macro_filter = macro_filter | condition

                macro_data = significant_nutrients.filter(macro_filter)

                if not macro_data.is_empty():
                    chart = create_nutrient_bar_chart(
                        macro_data,
                        f"Macronutrient Content in {selected_food}"
                    )
                    st.altair_chart(chart, use_container_width=True)
                else:
                    st.info("No macronutrient data available")

            # show raw data
            with st.expander("View Raw Data"):
                st.dataframe(significant_nutrients.to_pandas())



def render_nutrient_ranking(processor: NutrientProcessor):
    """Render the nutrient ranking page."""
    st.header("Foods Ranked by Nutrient Content")
    st.markdown("Select a nutrient to see foods with the highest content per ounce")

    # get available nutrients
    available_nutrients = processor.get_available_nutrients()

    # clean up nutrient names for display
    nutrient_display_names = []
    for nutrient in available_nutrients:
        # extract main nutrient name
        parts = nutrient.split("_")
        if len(parts) > 1:
            name = " ".join(parts[:-1]).title()
            unit = parts[-1].upper()
            display_name = f"{name} ({unit})"
        else:
            display_name = nutrient.title()
        nutrient_display_names.append(display_name)

    # create mapping
    nutrient_map = dict(zip(nutrient_display_names, available_nutrients))

    # nutrient selection
    selected_display = st.selectbox(
        "Select a nutrient:",
        nutrient_display_names,
        index=0
    )

    if selected_display:
        selected_nutrient = nutrient_map[selected_display]

        # get top foods to determine available count
        all_foods_for_nutrient = processor.get_top_foods_for_nutrient(
            selected_nutrient.split("_")[0],  # use base nutrient name
            top_n=1000  # high number to get all available
        )
        available_count = all_foods_for_nutrient.shape[0]

        # check if data is available
        if available_count == 0:
            st.warning(f"No foods in the database have {selected_display} data.")
        else:
            # get top foods
            col1, col2 = st.columns([3, 1])
            with col1:
                st.info(f"**{available_count}** foods available with {selected_display} data")
            with col2:
                max_foods = min(available_count, 150)  # cap at 150 for performance
                min_foods = min(5, max_foods)  # ensure min <= max
                default_foods = min(15, max_foods)
                top_n = st.slider("Number of foods to show:", min_foods, max_foods, default_foods)

            top_foods = processor.get_top_foods_for_nutrient(
                selected_nutrient.split("_")[0],  # use base nutrient name
                top_n=top_n
            )

            if not top_foods.is_empty():
                # create visualization
                chart = create_food_ranking_chart(top_foods, selected_display)
                st.altair_chart(chart, use_container_width=True)

                # show data table
                with st.expander("View Data Table"):
                    display_df = top_foods.select([
                        pl.col("description").alias("Food"),
                        pl.col("amount_per_100g").round(2).alias("Per 100g"),
                        pl.col("amount_per_ounce").round(2).alias("Per Ounce")
                    ])
                    st.dataframe(display_df.to_pandas())
            else:
                st.warning(f"No data available for {selected_display}")






def main():
    """Main streamlit application."""
    st.set_page_config(
        page_title="Food Nutrient Analysis",
        layout="wide"
    )

    st.title("Food Nutrient Analysis")
    st.markdown("Analyze nutrient content of foods using USDA FoodData Central")

    # initialize data
    processor = initialize_data()

    if processor.df.is_empty():
        st.error("No food database found.")
        st.info(
            "To use this application, you need to fetch data from the USDA API.\n\n"
            "Run the following command:\n"
            "```bash\n"
            "python3 src/usda_api.py --api-key YOUR_API_KEY\n"
            "```\n\n"
            "Get a free API key at: https://fdc.nal.usda.gov/api-key-signup.html"
        )
        return

    # sidebar for navigation
    st.sidebar.header("Navigation")
    mode = st.sidebar.radio(
        "Select Mode",
        ["Food Analysis", "Nutrient Ranking"]
    )

    if mode == "Food Analysis":
        render_food_analysis(processor)
    elif mode == "Nutrient Ranking":
        render_nutrient_ranking(processor)

    # footer
    st.divider()
    st.caption("Data source: USDA FoodData Central API")


if __name__ == "__main__":
    main()