"""
USDA FoodData Central API client for fetching food and nutrient data.
"""

import argparse
import json
import os
import time
from pathlib import Path

import polars as pl
import requests


class USDAFoodDataClient:
    """Client for interacting with USDA FoodData Central API."""

    def __init__(self, api_key: str | None = None):
        """
        Initialize USDA API client.

        Parameters
        ----------
        api_key : str | None
            API key for USDA FoodData Central. If None, will try to load from
            environment. Get a free API key at:
            https://fdc.nal.usda.gov/api-key-signup.html
        """
        self.api_key = api_key or os.getenv("USDA_API_KEY")

        if not self.api_key:
            raise ValueError(
                "USDA API key required. Get one at: "
                "https://fdc.nal.usda.gov/api-key-signup.html\n"
                "Pass via --api-key argument or set USDA_API_KEY environment "
                "variable"
            )

        self.base_url = "https://api.nal.usda.gov/fdc/v1"
        self.cache_dir = Path("data/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def search_foods(
        self, query: str, page_size: int = 50, max_retries: int = 3
    ) -> dict:
        """
        Search for foods by name with retry logic for rate limiting.

        Parameters
        ----------
        query : str
            Search query for food items.
        page_size : int
            Number of results to return.
        max_retries : int
            Maximum number of retries on rate limit errors.

        Returns
        -------
        dict
            API response with search results.
        """
        cache_file = self.cache_dir / f"search_{query.replace(' ', '_')}.json"

        if cache_file.exists():
            with open(cache_file) as f:
                return json.load(f)

        url = f"{self.base_url}/foods/search"
        params = {
            "api_key": self.api_key,
            "query": query,
            "pageSize": page_size,
            "dataType": ["Foundation", "SR Legacy"],
        }

        # retry logic with exponential backoff
        for attempt in range(max_retries):
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                with open(cache_file, "w") as f:
                    json.dump(data, f, indent=2)

                return data
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429 and attempt < max_retries - 1:
                    # exponential backoff: 5s, 15s, 45s
                    wait_time = 5 * (3**attempt)
                    time.sleep(wait_time)
                else:
                    raise

        return {}

    def get_food_nutrients(self, fdc_id: int, max_retries: int = 3) -> dict:
        """
        Get detailed nutrient information for a specific food with retry logic.

        Parameters
        ----------
        fdc_id : int
            FoodData Central ID of the food item.
        max_retries : int
            Maximum number of retries on rate limit errors.

        Returns
        -------
        dict
            Detailed food and nutrient information.
        """
        cache_file = self.cache_dir / f"food_{fdc_id}.json"

        if cache_file.exists():
            with open(cache_file) as f:
                return json.load(f)

        url = f"{self.base_url}/food/{fdc_id}"
        params = {"api_key": self.api_key}

        # retry logic with exponential backoff
        for attempt in range(max_retries):
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                with open(cache_file, "w") as f:
                    json.dump(data, f, indent=2)

                return data
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429 and attempt < max_retries - 1:
                    # exponential backoff: 5s, 15s, 45s
                    wait_time = 5 * (3**attempt)
                    time.sleep(wait_time)
                else:
                    raise

        return {}

    def get_common_foods(self) -> pl.DataFrame:
        """
        Get a list of common foods with their nutrients.

        Returns
        -------
        pl.DataFrame
            DataFrame with common foods and their nutrient data.
        """
        cache_file = self.cache_dir / "common_foods.parquet"

        if cache_file.exists():
            return pl.read_parquet(cache_file)

        # search for common food categories
        common_queries = [
            "apple",
            "banana",
            "orange",
            "strawberry",
            "grapes",
            "carrot",
            "broccoli",
            "spinach",
            "potato",
            "tomato",
            "chicken",
            "beef",
            "pork",
            "fish",
            "egg",
            "milk",
            "cheese",
            "yogurt",
            "bread",
            "rice",
            "beans",
            "nuts",
            "almonds",
            "peanuts",
            "oatmeal",
        ]

        all_foods = []

        for query in common_queries:
            print(f"Fetching data for: {query}")
            try:
                results = self.search_foods(query, page_size=5)
                if "foods" in results:
                    for food in results["foods"][
                        :3
                    ]:  # top 3 results per query
                        food_data = self.get_food_nutrients(food["fdcId"])
                        processed = self._process_food_data(food_data)
                        if processed:
                            all_foods.append(processed)
            except Exception as e:
                print(f"Error fetching {query}: {e}")
                continue

        if all_foods:
            df = pl.DataFrame(all_foods)
            df.write_parquet(cache_file)
            return df

        return pl.DataFrame()

    def _process_food_data(self, food_data: dict) -> dict | None:
        """
        Process raw food data into a structured format.

        Parameters
        ----------
        food_data : dict
            Raw food data from API.

        Returns
        -------
        dict | None
            Processed food data or None if processing fails.
        """

        def format_food_name(name: str) -> str:
            """
            Format food name by capitalizing and replacing commas with p
            arentheses."""
            if "," in name:
                main, descriptor = name.split(",", 1)
                return f"{main.strip().title()} ({descriptor.strip().title()})"
            return name.title()

        try:
            description = food_data.get("description", "")
            processed = {
                "fdc_id": food_data.get("fdcId"),
                "description": format_food_name(description),
                "data_type": food_data.get("dataType", ""),
                "serving_size": 100.0,  # default to 100g
                "serving_unit": "g",
            }

            # extract nutrients
            if "foodNutrients" in food_data:
                for nutrient in food_data["foodNutrients"]:
                    if "nutrient" in nutrient:
                        name = (
                            nutrient["nutrient"]
                            .get("name", "")
                            .replace(",", "")
                        )
                        unit = nutrient["nutrient"].get("unitName", "")
                        amount = nutrient.get("amount")

                        if amount is not None:
                            # normalize nutrient names
                            name_normalized = (
                                name.lower()
                                .replace(" ", "_")
                                .replace("-", "_")
                            )
                            processed[f"{name_normalized}_{unit}"] = float(
                                amount
                            )

            return processed
        except Exception as e:
            print(f"Error processing food data: {e}")
            return None


def fetch_all_foods_paginated():
    """
    Fetch all foods from USDA database using wildcard search and pagination.

    Returns
    -------
    list[dict]
        List of all food items with FDC IDs.
    """
    client = USDAFoodDataClient()
    base_url = client.base_url
    api_key = client.api_key

    print("Discovering total foods available...")

    # first request to get total
    response = requests.get(
        f"{base_url}/foods/search",
        params={
            "api_key": api_key,
            "query": "*",
            "dataType": ["Foundation", "SR Legacy"],
            "pageSize": 200,
            "pageNumber": 1,
        },
    )
    response.raise_for_status()
    first_page = response.json()

    total_foods = first_page.get("totalHits", 0)
    total_pages = first_page.get("totalPages", 0)

    print(f"Found {total_foods} foods across {total_pages} pages")
    print(f"This will take approximately {total_pages * 2 / 60:.1f} minutes\n")

    all_food_items = first_page.get("foods", [])

    # fetch remaining pages
    for page_num in range(2, total_pages + 1):
        print(
            f"Fetching page {page_num}/{total_pages} "
            f"({len(all_food_items)} foods so far)",
            end="\r",
        )

        try:
            response = requests.get(
                f"{base_url}/foods/search",
                params={
                    "api_key": api_key,
                    "query": "*",
                    "dataType": ["Foundation", "SR Legacy"],
                    "pageSize": 200,
                    "pageNumber": page_num,
                },
            )
            response.raise_for_status()
            page_data = response.json()
            all_food_items.extend(page_data.get("foods", []))
            time.sleep(0.5)  # small delay between page requests
        except Exception as e:
            print(f"\nWarning: Page {page_num} failed - {str(e)[:50]}")
            continue

    print(f"\n✓ Collected {len(all_food_items)} food items")
    return all_food_items


def fetch_and_save_food_database(api_key: str, max_foods: int | None = None):
    """
    Fetch comprehensive food database from USDA and save to parquet.

    Uses wildcard pagination to discover ALL available foods instead of
    hardcoded search queries.

    Parameters
    ----------
    api_key : str
        USDA FoodData Central API key.
    max_foods : int | None
        Maximum number of foods to fetch (None = all foods).
        Useful for testing with smaller datasets.

    Returns
    -------
    pl.DataFrame
        DataFrame with fetched food data.
    """
    # create client with provided API key
    os.environ["USDA_API_KEY"] = api_key
    client = USDAFoodDataClient()

    # fetch all available foods using pagination
    all_food_items = fetch_all_foods_paginated()

    if max_foods:
        all_food_items = all_food_items[:max_foods]
        print(f"Limiting to first {max_foods} foods for testing")

    # now fetch detailed nutrient data for each food
    print(
        f"\nFetching detailed nutrient data for {len(all_food_items)} foods..."
    )
    print(f"Estimated time: {len(all_food_items) * 0.5 / 60:.1f} minutes\n")

    all_foods = []
    failed_count = 0

    for i, food_item in enumerate(all_food_items):
        fdc_id = food_item.get("fdcId")
        if not fdc_id:
            continue

        print(
            (
                f"Processing: {i + 1}/{len(all_food_items)} ({len(all_foods)} "
                f"saved, {failed_count} failed)"
            ),
            end="\r",
        )

        try:
            food_data = client.get_food_nutrients(fdc_id)
            processed = client._process_food_data(food_data)
            if processed:
                all_foods.append(processed)
            time.sleep(0.5)  # 500ms delay between requests
        except Exception as e:
            failed_count += 1
            if failed_count <= 5:  # only show first 5 errors
                print(f"\n  Warning: Food {fdc_id} failed - {str(e)[:50]}")
            continue

    print()  # newline after progress

    # save results
    if all_foods:
        df = pl.DataFrame(all_foods)
        df.write_parquet("data/food_nutrient_database.parquet")

        # calculate file size
        file_size_mb = Path(
            "data/food_nutrient_database.parquet"
        ).stat().st_size / (1024 * 1024)

        print("\n✓ Successfully saved database!")
        print(f"  Foods: {len(df)}")
        print(f"  Nutrients: {len(df.columns) - 5}")
        print(f"  File size: {file_size_mb:.1f} MB")
        print(f"  Failed: {failed_count}")
        print("  Location: data/food_nutrient_database.parquet")

        return df

    print("⚠ No foods fetched")
    return pl.DataFrame()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch USDA FoodData Central database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch entire database
  python3 usda_api.py --api-key YOUR_KEY

  # Test with first 100 foods
  python3 usda_api.py --api-key YOUR_KEY --max-foods 100

  # Use environment variable
  export USDA_API_KEY=YOUR_KEY
  python3 usda_api.py

Get a free API key at: https://fdc.nal.usda.gov/api-key-signup.html
        """,
    )

    parser.add_argument(
        "--api-key",
        type=str,
        help="USDA FoodData Central API key (or set USDA_API_KEY env var)",
    )
    parser.add_argument(
        "--max-foods",
        type=int,
        default=None,
        help="Maximum number of foods to fetch (for testing)",
    )

    args = parser.parse_args()

    # get API key from args or environment
    api_key = args.api_key or os.getenv("USDA_API_KEY")

    if not api_key:
        print("Error: USDA API key required")
        print("Get one at: https://fdc.nal.usda.gov/api-key-signup.html")
        print("\nUsage:")
        print("  python3 usda_api.py --api-key YOUR_KEY")
        print("  or")
        print("  export USDA_API_KEY=YOUR_KEY && python3 usda_api.py")
        exit(1)

    # fetch and save database
    print("USDA FoodData Central Database Fetcher")
    print("=" * 50)
    df = fetch_and_save_food_database(api_key, max_foods=args.max_foods)
