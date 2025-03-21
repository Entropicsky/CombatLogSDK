# Technical Specification: Performance Analyzer Enhancement and Visualization Framework

## Updated Architecture: SDK-Centric Design

After implementing our initial design, we've identified an architectural issue: our Streamlit application contains too much logic that should be part of the core SDK. This section outlines the correct architectural approach.

### Core Architectural Principles

1. **Separation of Concerns**
   - **SDK**: Contains all data processing, analysis, validation, and visualization logic
   - **Streamlit**: Provides UI, calls SDK methods, and displays results

2. **Data Flow Architecture**
   ```
   Parser (Raw Data) -> SDK Analyzers -> SDK Visualizations -> Streamlit UI
   ```

3. **Responsibility Boundaries**
   - SDK should provide complete, pre-formatted data ready for display
   - Streamlit should not contain data validation or transformation logic
   - Visualizations should be generated in the SDK, not in the UI layer

### Key Changes Needed

1. **Move Validation Logic to SDK**
   - Relocate model validation utilities from dashboard to core SDK
   - Implement defensive programming patterns throughout the SDK
   - Add column presence checking in the SDK layer

2. **Enhance Visualization Module**
   - Create standard visualization functions in the SDK
   - Generate chart data in the SDK, not in Streamlit
   - Provide visualization configuration options

3. **Streamline Streamlit Implementation**
   - Refactor to call SDK methods for data validation and transformation
   - Use pre-formatted chart data from the SDK
   - Focus on UI layout and user interaction only

4. **Update Testing Approach**
   - Test complex logic in SDK unit tests
   - Keep Streamlit tests focused on UI rendering and interaction
   - Add integration tests for the full data flow

## 1. Performance Analyzer Enhancements

### 1.1 Additional Performance Metrics

We'll enhance the current PerformanceAnalyzer with the following advanced metrics:

#### 1.1.1 Efficiency Metrics
- **Damage efficiency**: Damage dealt per gold spent
- **Gold efficiency**: Gold earned per minute
- **Combat contribution**: Player damage as a percentage of team total
- **Survival efficiency**: (Kills + Assists) / Deaths with weighted coefficients
- **Target prioritization**: Percentage of damage dealt to high-priority targets

#### 1.1.2 Comparative Metrics
- **Performance vs. average**: Compare player metrics against match average
- **Role benchmarking**: Compare metrics against role-specific benchmarks
- **Team contribution**: Percentage contribution to team's total performance

#### 1.1.3 Implementation Approach
```python
def _calculate_efficiency_metrics(self) -> pd.DataFrame:
    """Calculate advanced efficiency metrics based on core performance data."""
    damage_df = self._calculate_damage_stats()
    kda_df = self._calculate_kda()
    economy_df = self._calculate_economy_stats()
    
    # Merge dataframes
    merged_df = damage_df.merge(kda_df, on=['player_id', 'player_name', 'god_name'])
    merged_df = merged_df.merge(economy_df, on=['player_id', 'player_name', 'god_name'])
    
    # Calculate efficiency metrics
    merged_df['damage_efficiency'] = merged_df['player_damage'] / merged_df['gold_spent'].replace(0, 1)
    merged_df['gold_efficiency'] = merged_df['gold_earned'] / merged_df['match_duration_minutes'].replace(0, 1)
    # Additional metrics...
    
    return merged_df
```

### 1.2 Defensive Programming Enhancements

The PerformanceAnalyzer will be enhanced with defensive programming to:
- Check for missing columns before calculations
- Provide fallback values for missing or invalid data
- Validate input data against expected schema
- Gracefully handle calculation errors

Example implementation:

```python
def _get_required_columns(self, df: pd.DataFrame, required_cols: List[str]) -> List[str]:
    """Check which required columns are missing from the dataframe."""
    return [col for col in required_cols if col not in df.columns]

def _calculate_damage_stats(self) -> pd.DataFrame:
    """Calculate damage statistics with defensive column checking."""
    try:
        # Get combat events dataframe
        combat_df = self.parser.get_combat_dataframe()
        
        # Check required columns
        required_cols = ['source_owner', 'value1', 'type']
        missing_cols = self._get_required_columns(combat_df, required_cols)
        
        if missing_cols:
            self.logger.warning(f"Missing required columns for damage calculation: {missing_cols}")
            return pd.DataFrame()  # Return empty dataframe instead of raising exception
            
        # Continue with calculations using only available columns
        # ...
    except Exception as e:
        self.logger.error(f"Error calculating damage stats: {str(e)}")
        return pd.DataFrame()
```

## 2. Visualization Architecture

### 2.1 Core Visualization Module

We'll create a dedicated visualization module in the core SDK with the following structure:

```
src/
  visualization/
    __init__.py
    base.py            # Base visualization classes and interfaces
    performance.py     # Performance-specific visualizations
    common.py          # Common visualization utilities
    themes.py          # Styling themes
    exporters.py       # Export functionality
```

### 2.2 Visualization Framework

#### 2.2.1 BaseVisualization Abstract Class
```python
class BaseVisualization(ABC):
    """Abstract base class for all visualizations."""
    
    def __init__(self, analyzer, config=None):
        self.analyzer = analyzer
        self.config = self._merge_config(config or {})
        self.figure = None
    
    @abstractmethod
    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration for visualization."""
        pass
    
    @abstractmethod
    def generate(self) -> Any:
        """Generate the visualization."""
        pass
    
    def export(self, path, format='png', **kwargs):
        """Export the visualization to a file."""
        if self.figure is None:
            self.generate()
        # Export logic
```

#### 2.2.2 Performance Visualizations

We'll implement these key visualizations for performance data:

1. **KDA Comparison**
   - Stacked bar chart showing kills, deaths, assists for each player
   - Sorted by KDA ratio with team differentiation

2. **Damage Distribution**
   - Stacked area chart showing different damage types over time
   - Pie charts showing damage type breakdown per player

3. **Gold and Economy**
   - Line chart tracking gold difference over time
   - Stacked area chart showing gold from different sources

4. **Performance Overview**
   - Radar chart comparing key performance metrics
   - Heatmap showing relative performance across metrics

### 2.3 Visualization Implementation in SDK

```python
class PerformanceVisualizer:
    """Factory class for performance visualizations."""
    
    def __init__(self, analyzer):
        self.analyzer = analyzer
    
    def create_kda_chart(self, **config) -> Dict[str, Any]:
        """
        Create a KDA comparison chart.
        
        Returns:
            Dictionary with chart data, layout, and configuration
        """
        # Extract data from analyzer
        kda_data = self.analyzer.get_kda_metrics()
        
        if not kda_data or kda_data.empty:
            return {
                'error': 'No KDA data available',
                'data': None,
                'layout': None
            }
            
        # Build chart data structure
        chart_data = {
            'x': kda_data['player_name'].tolist(),
            'kills': kda_data['kills'].tolist(),
            'deaths': kda_data['deaths'].tolist(),
            'assists': kda_data['assists'].tolist(),
            'kda_ratio': kda_data['kda_ratio'].tolist(),
            'team_id': kda_data['team_id'].tolist() if 'team_id' in kda_data.columns else None
        }
        
        # Build chart layout
        chart_layout = {
            'title': 'Player KDA Comparison',
            'x_axis_label': 'Player',
            'y_axis_label': 'Count',
            'sort_by': 'kda_ratio',
            'ascending': False,
            'legend': True
        }
        
        # Add any additional configuration
        chart_config = {
            'stacked': True,
            'colors': {
                'kills': '#4CAF50',  # Green
                'deaths': '#F44336',  # Red
                'assists': '#2196F3'  # Blue
            }
        }
        
        return {
            'data': chart_data,
            'layout': chart_layout,
            'config': chart_config,
            'error': None
        }
        
    # Similar methods for other visualization types...
```

## 3. Streamlit Application Structure

### 3.1 Directory Structure

```
streamlit/
  app.py              # Main application entry point
  pages/
    home.py           # Home/dashboard page
    performance.py    # Performance analysis page
    farm.py           # Future farm analysis page (placeholder)
    timeline.py       # Future timeline analysis page (placeholder)
  components/
    sidebar.py        # Reusable sidebar components
    metrics.py        # Metrics display components
    filters.py        # Filter components
    upload.py         # File upload components
  utils/
    session.py        # Session state management
    config.py         # Configuration helpers
    caching.py        # Caching utilities
  assets/
    styles.css        # Custom styling
    images/           # Static images
  tests/
    test_components.py
    test_pages.py
```

### 3.2 Main Application Flow

```python
# app.py
import streamlit as st
from streamlit.components.sidebar import create_sidebar
from streamlit.utils.session import initialize_session
from streamlit.pages.home import show_home
from streamlit.pages.performance import show_performance

def main():
    # Initialize session state
    initialize_session()
    
    # Page configuration
    st.set_page_config(
        page_title="SMITE 2 CombatLog Analyzer",
        page_icon="⚔️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    with open("streamlit/assets/styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    
    # Create sidebar
    create_sidebar()
    
    # Page routing
    page = st.session_state.get("page", "home")
    
    if page == "home":
        show_home()
    elif page == "performance":
        show_performance()
    # Future pages...

if __name__ == "__main__":
    main()
```

### 3.3 SDK-Centric Performance Page Implementation

```python
# pages/performance.py
import streamlit as st
import matplotlib.pyplot as plt

from src.analytics.performance import PerformanceAnalyzer
from src.visualization.performance import PerformanceVisualizer

def show_performance():
    st.title("Performance Analysis")
    
    # Get parser from session state
    parser = st.session_state.get("parser")
    if not parser:
        st.warning("Please upload a CombatLog file first.")
        return
    
    # Initialize analyzer
    analyzer = PerformanceAnalyzer(parser)
    
    # Filter controls
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_player = st.selectbox("Player", ["All Players"] + analyzer.get_player_names())
    with col2:
        min_damage = st.slider("Min Player Damage", 0, 50000, 0, 1000)
    with col3:
        selected_team = st.selectbox("Team", ["Both", "Order", "Chaos"])
    
    # Update analyzer config based on filters
    analyzer.update_config(
        min_player_damage=min_damage,
        player_name=None if selected_player == "All Players" else selected_player,
        team_id=None if selected_team == "Both" else selected_team
    )
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Damage Analysis", "Economy", "Efficiency"])
    
    # Create visualizer
    visualizer = PerformanceVisualizer(analyzer)
    
    with tab1:
        st.subheader("Performance Overview")
        
        # Get KDA metrics data - already prepared by the SDK
        kda_result = visualizer.create_kda_chart()
        
        if kda_result.get('error'):
            st.info(kda_result['error'])
        else:
            # The chart data is already prepared by the SDK
            # We just need to display it using Streamlit
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Extract data from SDK-provided structure
            data = kda_result['data']
            layout = kda_result['layout']
            config = kda_result['config']
            
            # Plot using the data structure provided by SDK
            x = range(len(data['x']))
            
            if config.get('stacked', False):
                ax.bar(x, data['kills'], label='Kills', color=config['colors']['kills'])
                ax.bar(x, data['deaths'], bottom=data['kills'], label='Deaths', color=config['colors']['deaths'])
                ax.bar(x, data['assists'], bottom=[i+j for i,j in zip(data['kills'], data['deaths'])], 
                       label='Assists', color=config['colors']['assists'])
            else:
                width = 0.25
                ax.bar([i-width for i in x], data['kills'], width=width, label='Kills', color=config['colors']['kills'])
                ax.bar(x, data['deaths'], width=width, label='Deaths', color=config['colors']['deaths'])
                ax.bar([i+width for i in x], data['assists'], width=width, label='Assists', color=config['colors']['assists'])
            
            ax.set_title(layout['title'])
            ax.set_xlabel(layout['x_axis_label'])
            ax.set_ylabel(layout['y_axis_label'])
            ax.set_xticks(x)
            ax.set_xticklabels(data['x'])
            
            if layout.get('legend', True):
                ax.legend()
                
            st.pyplot(fig)
    
    # Other tabs with similar pattern of using SDK-prepared data for display
```

## 4. Testing Framework

### 4.1 SDK Unit Testing

We'll implement comprehensive unit tests for all SDK components:

```python
# tests/test_efficiency_metrics.py
import unittest
import pandas as pd
from src.analytics.performance import PerformanceAnalyzer
from src.parser import CombatLogParser

class TestEfficiencyMetrics(unittest.TestCase):
    def setUp(self):
        self.parser = CombatLogParser()
        self.parser.parse("tests/sample_data.json")
        self.analyzer = PerformanceAnalyzer(self.parser)
    
    def test_damage_efficiency(self):
        # Test damage efficiency calculation
        results = self.analyzer._calculate_efficiency_metrics()
        self.assertIn('damage_efficiency', results.columns)
        self.assertTrue(all(results['damage_efficiency'] >= 0))
    
    # Additional tests...
```

### 4.2 SDK Visualization Testing

```python
# tests/test_visualizations.py
import unittest
import pandas as pd
from src.visualization.performance import PerformanceVisualizer
from src.analytics.performance import PerformanceAnalyzer
from src.parser import CombatLogParser

class TestPerformanceVisualizations(unittest.TestCase):
    def setUp(self):
        self.parser = CombatLogParser()
        self.parser.parse("tests/sample_data.json")
        self.analyzer = PerformanceAnalyzer(self.parser)
        self.visualizer = PerformanceVisualizer(self.analyzer)
    
    def test_kda_visualization(self):
        # Test KDA chart creation
        chart_data = self.visualizer.create_kda_chart()
        
        # Verify chart data structure
        self.assertIsNone(chart_data.get('error'))
        self.assertIn('data', chart_data)
        self.assertIn('layout', chart_data)
        self.assertIn('config', chart_data)
        
        # Verify data content
        data = chart_data['data']
        self.assertIn('x', data)
        self.assertIn('kills', data)
        self.assertIn('deaths', data)
        self.assertIn('assists', data)
        
    # Additional tests...
```

### 4.3 Streamlit Component Testing

```python
# tests/test_streamlit_components.py
import unittest
from unittest.mock import patch, MagicMock
import streamlit as st

class TestStreamlitComponents(unittest.TestCase):
    @patch('streamlit.st')
    def test_performance_page(self, mock_st):
        # Mock SDK components
        mock_parser = MagicMock()
        mock_analyzer = MagicMock()
        mock_visualizer = MagicMock()
        
        # Mock SDK visualization results
        mock_visualizer.create_kda_chart.return_value = {
            'data': {
                'x': ['Player1', 'Player2'],
                'kills': [5, 3],
                'deaths': [2, 4],
                'assists': [7, 6]
            },
            'layout': {
                'title': 'Test Chart'
            },
            'config': {
                'stacked': True,
                'colors': {'kills': 'green', 'deaths': 'red', 'assists': 'blue'}
            },
            'error': None
        }
        
        # Set up session state
        mock_st.session_state = {'parser': mock_parser}
        
        # Test component
        from streamlit.pages.performance import show_performance
        
        # The test should verify that the component correctly uses the SDK
        # and displays the data without implementing its own logic
```

## 5. Debug Infrastructure

### 5.1 SDK Logging Framework

```python
# src/utils/logging.py
import logging
import os
from datetime import datetime

def setup_logging(module_name, log_level=logging.INFO, log_dir="logs"):
    """Set up logging for a module."""
    os.makedirs(log_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"{log_dir}/{module_name}_{timestamp}.log"
    
    logger = logging.getLogger(module_name)
    logger.setLevel(log_level)
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # Only warnings and above to console
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
```

## 6. Implementation Plan

### Phase 1: SDK Enhancement (1 Week)
1. Migrate validation utilities from dashboard to core SDK
2. Enhance PerformanceAnalyzer with defensive programming
3. Implement standard visualization generation in the SDK
4. Add thorough unit tests for SDK components

### Phase 2: Streamlit Refactoring (1 Week)
1. Refactor performance page to use SDK methods
2. Update metrics components to use pre-formatted data
3. Remove duplicate validation logic
4. Implement comprehensive testing for Streamlit components

### Phase 3: Integration and Testing (1 Week)
1. Verify integration between SDK and Streamlit app
2. Implement end-to-end testing
3. Optimize performance and usability
4. Document new architecture and approach

### Phase 4: Farm Analyzer Implementation (2 Weeks)
1. Begin implementing FarmAnalyzer with SDK-centric design
2. Create visualization components in the SDK for farm metrics
3. Implement Streamlit interface for farm analysis
4. Create comprehensive tests for SDK and Streamlit components

## 7. Conclusion

This technical specification outlines our approach to enhancing the Performance Analyzer with a proper SDK-centric design. By moving logic from the Streamlit layer to the core SDK, we'll create a more maintainable, testable, and reusable system.

The architecture prioritizes:
- **Separation of Concerns**: Clear boundaries between SDK and UI responsibilities
- **Reusability**: Core logic in the SDK for use by any application
- **Testability**: Logic concentrated in the SDK for easier testing
- **Maintainability**: Reduced duplication and clearer responsibility boundaries 