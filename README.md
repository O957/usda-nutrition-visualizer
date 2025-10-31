# USDA Nutrition Visualizer

_Streamlit application for visualizing vitamin, mineral, and macronutrient content from the USDA FoodData Central API._

> [!IMPORTANT]
>
> The application is live at: <https://usda-nutri-viz.streamlit.app/>. You may need to "wake up" the application, as `streamlit` cloud will shut down the application during periods of inactivity.

## Features

- **USDA FoodData Central Integration**: Direct access to comprehensive nutritional data for ~8100 foods.
- **Interactive Visualizations**: Built with `altair` for clear, responsive data visualization.
- **Food Analysis By Nutrient**: Compare vitamins, minerals, and macronutrients across foods.
- **Nutrient Analysis By Food**: Compare foods across vitamins, minerals, and macronutrients.

## Installation

This project uses `uv` for dependency management. Installation instructions for `uv` can be found here: <https://github.com/astral-sh/uv>.

To install `sort-by-citations`:

```bash
# clone the repository
git clone https://github.com/O957/usda-nutrition-visualizer.git
cd usda-nutrition-visualizer

# install dependencies with uv
uv sync
```

## Usage

Run the application locally:

```bash
uv run streamlit run src/app.py
```

or just

```bash
streamlit run src/app.py
```

Then open your browser to `http://localhost:8501` (paste this in your browser).

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License Standard Notice

```
Copyright 2025 O957 (Pseudonym)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```
