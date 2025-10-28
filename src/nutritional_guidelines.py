"""
Official nutritional guidelines and daily requirements from USDA/NIH.
Based on Dietary Reference Intakes (DRIs) and Recommended Dietary Allowances
(RDAs).
"""

import json
from dataclasses import dataclass


@dataclass
class NutrientRequirement:
    """Individual nutrient requirement with min/max values."""

    rda_male: float | None = None
    rda_female: float | None = None
    upper_limit: float | None = None
    unit: str = ""
    name: str = ""


class NutritionalGuidelines:
    """Official nutritional guidelines database."""

    def __init__(self):
        """Initialize with official RDA values for adults (19-70 years)."""
        self.guidelines = self._load_official_guidelines()

    def _load_official_guidelines(self) -> dict[str, NutrientRequirement]:
        """Load official RDA values from NIH/USDA sources."""
        return {
            # vitamins (fat-soluble)
            "vitamin_a_ug": NutrientRequirement(
                rda_male=900,
                rda_female=700,
                upper_limit=3000,
                unit="μg",
                name="Vitamin A",
            ),
            "vitamin_d_ug": NutrientRequirement(
                rda_male=15,
                rda_female=15,
                upper_limit=100,
                unit="μg",
                name="Vitamin D",
            ),
            "vitamin_e_mg": NutrientRequirement(
                rda_male=15,
                rda_female=15,
                upper_limit=1000,
                unit="mg",
                name="Vitamin E",
            ),
            "vitamin_k_ug": NutrientRequirement(
                rda_male=120,
                rda_female=90,
                upper_limit=None,
                unit="μg",
                name="Vitamin K",
            ),
            # vitamins (water-soluble)
            "vitamin_c_mg": NutrientRequirement(
                rda_male=90,
                rda_female=75,
                upper_limit=2000,
                unit="mg",
                name="Vitamin C",
            ),
            "thiamin_mg": NutrientRequirement(
                rda_male=1.2,
                rda_female=1.1,
                upper_limit=None,
                unit="mg",
                name="Thiamin (B1)",
            ),
            "riboflavin_mg": NutrientRequirement(
                rda_male=1.3,
                rda_female=1.1,
                upper_limit=None,
                unit="mg",
                name="Riboflavin (B2)",
            ),
            "niacin_mg": NutrientRequirement(
                rda_male=16,
                rda_female=14,
                upper_limit=35,
                unit="mg",
                name="Niacin (B3)",
            ),
            "vitamin_b6_mg": NutrientRequirement(
                rda_male=1.3,
                rda_female=1.3,
                upper_limit=100,
                unit="mg",
                name="Vitamin B6",
            ),
            "folate_ug": NutrientRequirement(
                rda_male=400,
                rda_female=400,
                upper_limit=1000,
                unit="μg",
                name="Folate",
            ),
            "vitamin_b12_ug": NutrientRequirement(
                rda_male=2.4,
                rda_female=2.4,
                upper_limit=None,
                unit="μg",
                name="Vitamin B12",
            ),
            # minerals
            "calcium_mg": NutrientRequirement(
                rda_male=1000,
                rda_female=1000,
                upper_limit=2500,
                unit="mg",
                name="Calcium",
            ),
            "iron_mg": NutrientRequirement(
                rda_male=8,
                rda_female=18,
                upper_limit=45,
                unit="mg",
                name="Iron",
            ),
            "magnesium_mg": NutrientRequirement(
                rda_male=400,
                rda_female=310,
                upper_limit=350,
                unit="mg",
                name="Magnesium",
            ),
            "phosphorus_mg": NutrientRequirement(
                rda_male=700,
                rda_female=700,
                upper_limit=4000,
                unit="mg",
                name="Phosphorus",
            ),
            "potassium_mg": NutrientRequirement(
                rda_male=3400,
                rda_female=2600,
                upper_limit=None,
                unit="mg",
                name="Potassium",
            ),
            "sodium_mg": NutrientRequirement(
                rda_male=1500,
                rda_female=1500,
                upper_limit=2300,
                unit="mg",
                name="Sodium",
            ),
            "zinc_mg": NutrientRequirement(
                rda_male=11,
                rda_female=8,
                upper_limit=40,
                unit="mg",
                name="Zinc",
            ),
            "copper_mg": NutrientRequirement(
                rda_male=0.9,
                rda_female=0.9,
                upper_limit=10,
                unit="mg",
                name="Copper",
            ),
            "selenium_ug": NutrientRequirement(
                rda_male=55,
                rda_female=55,
                upper_limit=400,
                unit="μg",
                name="Selenium",
            ),
            "manganese_mg": NutrientRequirement(
                rda_male=2.3,
                rda_female=1.8,
                upper_limit=11,
                unit="mg",
                name="Manganese",
            ),
            "chromium_ug": NutrientRequirement(
                rda_male=35,
                rda_female=25,
                upper_limit=None,
                unit="μg",
                name="Chromium",
            ),
            "molybdenum_ug": NutrientRequirement(
                rda_male=45,
                rda_female=45,
                upper_limit=2000,
                unit="μg",
                name="Molybdenum",
            ),
            "iodine_ug": NutrientRequirement(
                rda_male=150,
                rda_female=150,
                upper_limit=1100,
                unit="μg",
                name="Iodine",
            ),
            # macronutrients (general guidelines)
            "protein_g": NutrientRequirement(
                rda_male=56,
                rda_female=46,
                upper_limit=None,
                unit="g",
                name="Protein",
            ),
            "fiber_g": NutrientRequirement(
                rda_male=38,
                rda_female=25,
                upper_limit=None,
                unit="g",
                name="Dietary Fiber",
            ),
            # limits for harmful nutrients
            "saturated_fat_g": NutrientRequirement(
                rda_male=None,
                rda_female=None,
                upper_limit=20,
                unit="g",
                name="Saturated Fat",
            ),
            "cholesterol_mg": NutrientRequirement(
                rda_male=None,
                rda_female=None,
                upper_limit=300,
                unit="mg",
                name="Cholesterol",
            ),
            "sugars_g": NutrientRequirement(
                rda_male=None,
                rda_female=None,
                upper_limit=50,
                unit="g",
                name="Added Sugars",
            ),
        }

    def get_requirement(
        self, nutrient_key: str, gender: str = "average"
    ) -> dict:
        """
        Get requirement for a specific nutrient.

        Parameters
        ----------
        nutrient_key : str
            Nutrient identifier (e.g., 'vitamin_c_mg').
        gender : str
            'male', 'female', or 'average'.

        Returns
        -------
        Dict
            Requirement information with min/max values.
        """
        if nutrient_key not in self.guidelines:
            return {}

        req = self.guidelines[nutrient_key]

        if gender == "male" and req.rda_male is not None:
            rda_value = req.rda_male
        elif gender == "female" and req.rda_female is not None:
            rda_value = req.rda_female
        else:
            # use average of male/female values
            if req.rda_male is not None and req.rda_female is not None:
                rda_value = (req.rda_male + req.rda_female) / 2
            elif req.rda_male is not None:
                rda_value = req.rda_male
            elif req.rda_female is not None:
                rda_value = req.rda_female
            else:
                rda_value = None

        return {
            "nutrient": req.name,
            "rda": rda_value,
            "upper_limit": req.upper_limit,
            "unit": req.unit,
            "gender_specific": {
                "male": req.rda_male,
                "female": req.rda_female,
            },
        }

    def get_all_requirements(self, gender: str = "average") -> dict:
        """
        Get all nutrient requirements.

        Parameters
        ----------
        gender : str
            'male', 'female', or 'average'.

        Returns
        -------
        Dict
            All nutrient requirements.
        """
        return {
            nutrient_key: self.get_requirement(nutrient_key, gender)
            for nutrient_key in self.guidelines
        }

    def save_to_json(self, filepath: str = "data/nutritional_guidelines.json"):
        """Save guidelines to JSON file."""
        data = {}
        for key, req in self.guidelines.items():
            data[key] = {
                "rda_male": req.rda_male,
                "rda_female": req.rda_female,
                "upper_limit": req.upper_limit,
                "unit": req.unit,
                "name": req.name,
            }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    def match_nutrient_key(self, nutrient_column: str) -> str:
        """
        Match a nutrient column name to guideline key.

        Parameters
        ----------
        nutrient_column : str
            Column name from food database.

        Returns
        -------
        str
            Matching guideline key or empty string.
        """
        # direct match
        if nutrient_column in self.guidelines:
            return nutrient_column

        # fuzzy matching for common variations
        nutrient_lower = nutrient_column.lower()

        for key in self.guidelines:
            key_base = key.split("_")[0]  # e.g., "vitamin" from "vitamin_c_mg"
            if key_base in nutrient_lower and key.replace(
                "_", ""
            ) in nutrient_column.replace("_", ""):
                # check for more specific match
                return key

        return ""


def create_guidelines_database():
    """Create and save nutritional guidelines database."""
    guidelines = NutritionalGuidelines()

    # save to JSON
    guidelines.save_to_json("data/nutritional_guidelines.json")

    print("Created nutritional guidelines database:")
    print(f"- {len(guidelines.guidelines)} nutrients")
    print("- Based on official USDA/NIH RDA values")
    print("- Saved to: data/nutritional_guidelines.json")

    # display sample
    print("\nSample requirements:")
    for nutrient in ["vitamin_c_mg", "iron_mg", "calcium_mg", "protein_g"]:
        req = guidelines.get_requirement(nutrient, "average")
        print(f"- {req['nutrient']}: {req['rda']} {req['unit']}")

    return guidelines


if __name__ == "__main__":
    create_guidelines_database()
