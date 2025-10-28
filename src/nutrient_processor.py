"""
Nutrient data processing and analysis functions.
"""

import polars as pl

from nutritional_guidelines import NutritionalGuidelines


class NutrientProcessor:
    """Process and analyze nutrient data from food database."""

    def __init__(self, database_path: str = "data/food_nutrient_database.parquet", gender: str = "average"):
        """
        Initialize nutrient processor.

        Parameters
        ----------
        database_path : str
            Path to the food nutrient database parquet file.
        gender : str
            Gender for RDA values: 'male', 'female', or 'average'.
        """
        self.guidelines = NutritionalGuidelines()
        self.gender = gender
        try:
            self.df = pl.read_parquet(database_path)
            self._clean_data()
        except FileNotFoundError:
            self.df = pl.DataFrame()
        except Exception as e:
            print(f"Warning: Error loading {database_path}: {e}")
            self.df = pl.DataFrame()

    def _clean_data(self):
        """Clean and standardize the nutrient data."""
        if self.df.is_empty():
            return

        # remove duplicates based on description
        self.df = self.df.unique(subset=["description"])

        # fill null values with 0 for nutrient columns
        nutrient_cols = [col for col in self.df.columns if col not in
                        ["fdc_id", "description", "data_type", "serving_size", "serving_unit"]]

        fill_expr = [
            pl.col(col).fill_null(0.0) if col in nutrient_cols else pl.col(col)
            for col in self.df.columns
        ]
        self.df = self.df.select(fill_expr)

    def get_available_nutrients(self) -> list[str]:
        """
        Get list of available nutrients in the database.

        Returns
        -------
        list[str]
            List of nutrient column names.
        """
        if self.df.is_empty():
            return []

        exclude_cols = ["fdc_id", "description", "data_type", "serving_size", "serving_unit"]
        return [col for col in self.df.columns if col not in exclude_cols]

    def get_food_nutrients(self, food_name: str) -> pl.DataFrame:
        """
        Get nutrient information for a specific food.

        Parameters
        ----------
        food_name : str
            Name or partial name of the food.

        Returns
        -------
        pl.DataFrame
            DataFrame with nutrient information for matching foods.
        """
        if self.df.is_empty():
            return pl.DataFrame()

        # first try exact match
        exact_matches = self.df.filter(
            pl.col("description") == food_name
        )

        if not exact_matches.is_empty():
            matches = exact_matches
        else:
            # escape special regex characters and do partial search
            import re
            escaped_name = re.escape(food_name.lower())
            matches = self.df.filter(
                pl.col("description").str.to_lowercase().str.contains(escaped_name)
            )

            # if still no matches, try without parentheses
            if matches.is_empty():
                # remove content in parentheses and try simpler search
                simple_name = re.sub(r'\([^)]*\)', '', food_name).strip().lower()
                matches = self.df.filter(
                    pl.col("description").str.to_lowercase().str.contains(re.escape(simple_name))
                )

        if matches.is_empty():
            return pl.DataFrame()

        # get nutrient columns
        nutrient_cols = self.get_available_nutrients()

        # melt to long format for easier visualization
        result = matches.select(["description"] + nutrient_cols).melt(
            id_vars=["description"],
            variable_name="nutrient",
            value_name="amount"
        ).filter(pl.col("amount") > 0)  # only non-zero nutrients

        return result

    def get_top_foods_for_nutrient(self, nutrient_name: str, top_n: int = 20) -> pl.DataFrame:
        """
        Get foods with highest content of a specific nutrient.

        Parameters
        ----------
        nutrient_name : str
            Name of the nutrient to rank by.
        top_n : int
            Number of top foods to return.

        Returns
        -------
        pl.DataFrame
            DataFrame with top foods for the nutrient.
        """
        if self.df.is_empty():
            return pl.DataFrame()

        # find matching nutrient column
        nutrient_cols = [col for col in self.df.columns if nutrient_name.lower() in col.lower()]

        if not nutrient_cols:
            return pl.DataFrame()

        nutrient_col = nutrient_cols[0]  # use first match

        # get top foods
        result = (
            self.df
            .select(["description", nutrient_col, "serving_size"])
            .filter(pl.col(nutrient_col) > 0)
            .with_columns(
                # calculate per ounce (28.35g)
                (pl.col(nutrient_col) * 28.35 / pl.col("serving_size"))
                .alias("amount_per_ounce")
            )
            .sort("amount_per_ounce", descending=True)
            .head(top_n)
            .rename({nutrient_col: "amount_per_100g"})
        )

        return result

    def get_nutrient_profile(self, food_items: list[dict]) -> pl.DataFrame:
        """
        Calculate combined nutrient profile for multiple food items.

        Parameters
        ----------
        food_items : list[dict]
            List of dicts with 'food' and 'amount_g' keys.

        Returns
        -------
        pl.DataFrame
            Combined nutrient profile.
        """
        if self.df.is_empty():
            return pl.DataFrame()

        nutrient_totals = {}
        nutrient_cols = self.get_available_nutrients()

        for item in food_items:
            food_name = item["food"]
            amount_g = item["amount_g"]

            # find matching food
            matches = self.df.filter(
                pl.col("description").str.to_lowercase().str.contains(food_name.lower())
            )

            if not matches.is_empty():
                food_data = matches[0]  # use first match
                serving_size = food_data["serving_size"][0]

                for nutrient in nutrient_cols:
                    if nutrient in food_data.columns:
                        value = food_data[nutrient][0]
                        if value is not None:
                            # scale to actual amount
                            scaled_value = (value * amount_g) / serving_size
                            if nutrient not in nutrient_totals:
                                nutrient_totals[nutrient] = 0
                            nutrient_totals[nutrient] += scaled_value

        # convert to dataframe
        if nutrient_totals:
            result = pl.DataFrame({
                "nutrient": list(nutrient_totals.keys()),
                "total_amount": list(nutrient_totals.values())
            })

            # add daily value percentages
            dv_percentages = []
            for nutrient in result["nutrient"]:
                # try to match with guidelines
                matched_key = self.guidelines.match_nutrient_key(nutrient)
                if matched_key:
                    req = self.guidelines.get_requirement(matched_key, self.gender)
                    if req.get("rda"):
                        idx = result["nutrient"].to_list().index(nutrient)
                        percentage = (result["total_amount"][idx] / req["rda"]) * 100
                        dv_percentages.append(percentage)
                    else:
                        dv_percentages.append(None)
                else:
                    dv_percentages.append(None)

            result = result.with_columns(
                pl.Series("daily_value_pct", dv_percentages)
            )

            return result

        return pl.DataFrame()

    def check_daily_requirements(self, nutrient_profile: pl.DataFrame) -> dict:
        """
        Check if nutrient profile meets daily requirements.

        Parameters
        ----------
        nutrient_profile : pl.DataFrame
            Nutrient profile to check.

        Returns
        -------
        dict
            Status of each nutrient relative to daily requirements.
        """
        status = {}

        for nutrient, amount in zip(nutrient_profile["nutrient"], nutrient_profile["total_amount"]):
            # match with guidelines
            matched_key = self.guidelines.match_nutrient_key(nutrient)
            if matched_key:
                req = self.guidelines.get_requirement(matched_key, self.gender)
                rda = req.get("rda")
                upper_limit = req.get("upper_limit")

                status[nutrient] = {
                    "amount": amount,
                    "min": rda,
                    "max": upper_limit,
                    "unit": req["unit"]
                }

                if rda and amount < rda:
                    status[nutrient]["status"] = "below_minimum"
                elif upper_limit and amount > upper_limit:
                    status[nutrient]["status"] = "above_maximum"
                else:
                    status[nutrient]["status"] = "adequate"

        return status