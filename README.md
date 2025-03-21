# SMITE 2 CombatLog Parser

A comprehensive SDK for parsing and analyzing SMITE 2 CombatLog files, providing performance metrics, visualizations, and insights.

## Overview

The SMITE 2 CombatLog Parser transforms raw log data into structured formats and provides analytical tools for advanced MOBA game analysis. The SDK features:

- **Core Parser**: Transforms raw CombatLog JSON into structured dataframes
- **Analytics Framework**: Calculates player performance metrics, damage statistics, healing, and economy
- **Visualization Tools**: Generates charts and visualizations for performance data
- **Defensive Programming**: Robust error handling and validation throughout

## Installation

### Requirements

- Python 3.8+
- pandas
- numpy
- matplotlib
- seaborn

### Setup

```bash
# Clone the repository
git clone https://github.com/your-username/CombatLogParser2.git
cd CombatLogParser2

# Install dependencies
pip install -r requirements.txt
```

## Core Components

### Parser

The `CombatLogParser` class transforms raw log data into structured dataframes:

```python
from src.parser import CombatLogParser

# Create a parser instance
parser = CombatLogParser()

# Parse a log file
parser.parse("path/to/CombatLogExample.log")

# Access structured data
events_df = parser.get_events_dataframe()
players_df = parser.get_players_dataframe()
combat_df = parser.get_combat_dataframe()
enhanced_combat_df = parser.get_enhanced_combat_dataframe()
economy_df = parser.get_economy_dataframe()
```

### Analytics

The SDK provides several analytics modules to analyze different aspects of the game:

```python
from src.parser import CombatLogParser
from src.analytics.performance import PerformanceAnalyzer

# Parse a log file
parser = CombatLogParser()
parser.parse("path/to/CombatLogExample.log")

# Create a performance analyzer
analyzer = PerformanceAnalyzer(parser)

# Get various performance metrics
performance_df = analyzer.to_dataframe()  # All metrics in one DataFrame
results = analyzer.analyze()              # Comprehensive results dictionary
kda_df = analyzer._calculate_kda()        # KDA metrics
damage_df = analyzer._calculate_damage_stats()  # Damage statistics
healing_df = analyzer._calculate_healing_stats()  # Healing statistics
economy_df = analyzer._calculate_economy_stats()  # Economy metrics

# Get top performers
top_kda = analyzer.get_top_performers(metric='kda_ratio', limit=3)
top_damage = analyzer.get_top_performers(metric='player_damage', limit=3)
top_healing = analyzer.get_top_performers(metric='healing_done', limit=3)

# Get performance for a specific player
player_stats = analyzer.get_player_performance("PlayerName")
```

### Visualization

The SDK provides visualization tools to create charts from performance metrics:

```python
from src.parser import CombatLogParser
from src.analytics.performance import PerformanceAnalyzer
from src.visualization.performance import PerformanceVisualizer

# Setup parser and analyzer
parser = CombatLogParser()
parser.parse("path/to/CombatLogExample.log")
analyzer = PerformanceAnalyzer(parser)

# Create a visualizer
visualizer = PerformanceVisualizer(analyzer)

# Generate different visualizations
kda_chart = visualizer.create_kda_chart()
damage_distribution = visualizer.create_damage_distribution()
performance_radar = visualizer.create_performance_radar()

# Export visualizations
kda_chart.export("output/kda_chart.png")
damage_distribution.export("output/damage_distribution.png")
```

## Example Scripts

The SDK includes several example scripts demonstrating its functionality:

1. **Basic Performance Analysis**: `examples/performance_analysis.py`
   - Demonstrates basic player performance analysis and visualization

2. **Enhanced Visualizations**: `examples/enhanced_performance_visualization.py`
   - Shows advanced visualization capabilities with customization

3. **DataFrame Generation**: `examples/generate_dataframes.py`
   - Illustrates how to generate and work with various dataframes

To run an example:

```bash
python3 examples/performance_analysis.py path/to/CombatLogExample.log
```

## DataFrame Schemas

The parser generates several dataframes with different schemas:

### Players DataFrame
| Column | Description |
|--------|-------------|
| player_id | Unique identifier for the player |
| player_name | Player's name |
| god_name | Name of the god played |
| team_id | Team identifier (1 or 2) |
| role | Player's role (if available) |

### Combat DataFrame
| Column | Description |
|--------|-------------|
| event_id | Unique identifier for the event |
| event_timestamp | Timestamp of the event |
| event_subtype | Combat event type (Damage, Healing, etc.) |
| source_owner | Name of the source entity |
| target_owner | Name of the target entity |
| damage_amount | Amount of damage (for Damage events) |
| mitigated_amount | Amount of damage mitigated |
| value1 | Additional numeric value (e.g., healing amount) |

### Enhanced Combat DataFrame
Extends the Combat DataFrame with:
| Column | Description |
|--------|-------------|
| source_entity_type | Type of source entity (Player, Minion, etc.) |
| target_entity_type | Type of target entity (Player, Minion, etc.) |

### Economy DataFrame
| Column | Description |
|--------|-------------|
| event_id | Unique identifier for the event |
| event_timestamp | Timestamp of the event |
| reward_type | Type of reward (Currency, Experience) |
| target_owner | Player receiving the reward |
| amount | Amount of currency or experience |
| source_entity_type | Type of source entity |

## API Reference

### Parser Methods

| Method | Description |
|--------|-------------|
| `parse(log_file_path)` | Parse a CombatLog file |
| `get_events_dataframe()` | Get a DataFrame with all events |
| `get_players_dataframe()` | Get a DataFrame with player information |
| `get_combat_dataframe()` | Get a DataFrame with combat events |
| `get_enhanced_combat_dataframe()` | Get combat events with entity type classification |
| `get_economy_dataframe()` | Get a DataFrame with economy events |
| `get_item_dataframe()` | Get a DataFrame with item purchase events |

### PerformanceAnalyzer Methods

| Method | Description |
|--------|-------------|
| `analyze()` | Analyze all performance metrics |
| `to_dataframe()` | Get all metrics in a single DataFrame |
| `get_top_performers(metric, limit)` | Get top performers for a specific metric |
| `get_player_performance(player_name)` | Get performance metrics for a specific player |
| `update_config(config_dict)` | Update the analyzer configuration |

### ColumnMapper Utility

The SDK includes a `ColumnMapper` utility to standardize column naming across the system:

```python
from src.utils.data_validation import ColumnMapper

# Standardize column names in a DataFrame
df = ColumnMapper.standardize_columns(df)

# Ensure required columns exist
df = ColumnMapper.ensure_columns(df, ['col1', 'col2'])

# Combined operation
df = ColumnMapper.map_and_ensure(df, 
                                required_columns=['source_entity_type', 'target_entity_type'],
                                mappings={'source_type': 'source_entity_type'})
```

## Testing

The SDK includes comprehensive test suites:

```bash
# Run all tests
python run_tests.py

# Run specific test modules
python -m unittest tests.test_parser
python -m unittest tests.test_performance_analyzer
```

## Defensive Programming

The SDK implements robust defensive programming techniques:

1. **Column Validation**: Checks for required columns before operations
2. **Type Conversion**: Safely converts data types with error handling
3. **Null Handling**: Provides proper defaults for missing values
4. **Error Recovery**: Returns partial results instead of failing entirely

## Troubleshooting

### Common Issues

1. **Missing Columns Error**: Ensure you're using the ColumnMapper utility to standardize column names
2. **Empty Results**: Check that the log file was parsed correctly with `parser.events` 
3. **Visualization Errors**: Verify matplotlib is properly installed

### Debugging

Enable detailed logging to help diagnose issues:

```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
```

## Contributing

Contributions to improve the SDK are welcome! Here are some ways to contribute:

1. Report bugs or request features by opening issues
2. Submit pull requests with improvements or fixes
3. Help with documentation
4. Develop new analyzers for different aspects of gameplay

## License

This project is licensed under the MIT License - see the LICENSE file for details.
