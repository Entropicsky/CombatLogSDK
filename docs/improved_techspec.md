# Improved Technical Specification for SMITE 2 CombatLog Parser

## 1. Overview

The SMITE 2 CombatLog Parser will transform raw CombatLog data into a structured format optimized for analytical use cases. The raw data consists of newline-delimited JSON objects representing various game events, each with event-specific schemas.

### 1.1 Event Categories

Based on our analysis, the CombatLog contains the following event types:

| EventType | Subtypes | Description |
|-----------|----------|-------------|
| `start` | none | Match initialization containing metadata |
| `playermsg` | `RoleAssigned`, `GodHovered`, `GodPicked` | Player selection and assignment events |
| `itemmsg` | `ItemPurchase` | Item purchase events |
| `CombatMsg` | `Damage`, `CritDamage`, `CrowdControl`, `Healing`, `KillingBlow` | Combat interaction events |
| `RewardMsg` | `Currency`, `Experience` | Resource acquisition events |

Each event type has specific fields, and our parser needs to handle these variations while providing a unified structure for analysis.

## 2. Data Challenges and Design Requirements

### 2.1 Identified Challenges

1. **Heterogeneous JSON Schemas**: Different event types have different sets of fields.
2. **String Representations of Numeric Values**: Values that should be numeric (damage, coordinates) are stored as strings.
3. **Non-standard Time Format**: Timestamps are in `YYYY.MM.DD-HH.MM.SS` format.
4. **Relational Data Across Events**: Player-god relationships and team assignments are established in certain events but relevant to others.
5. **Spatial Data Availability**: Location data exists only for certain event types.

### 2.2 Design Requirements

1. **Unified Structure**: Create a normalized structure that allows analysis across all event types.
2. **Type Conversion**: Convert string values to appropriate data types (integers, floats, timestamps).
3. **Relational References**: Establish relationships between events, players, gods, teams, and items.
4. **Analytical Accessibility**: Design the structure to facilitate easy querying and aggregation.
5. **Extensibility**: Support additional event types or fields that may be added in the future.
6. **Performance Optimization**: Handle large log files efficiently.

## 3. Proposed Data Model

We propose a comprehensive data model that organizes the CombatLog data into a structure optimized for analytical use. The model follows a star schema design but is implemented in memory using Pandas DataFrames with appropriate relationships.

### 3.1 Core DataFrames

#### 3.1.1 Match DataFrame

Stores match-level metadata:
- `match_id`: Unique identifier (from the start event)
- `log_mode`: Logging format
- `start_time`: First timestamp in the match
- `end_time`: Last timestamp in the match
- Additional metadata as available

#### 3.1.2 Player DataFrame

Contains player information consolidated from various events:
- `player_id`: Generated surrogate key
- `player_name`: Player name (from sourceowner)
- `god_id`: God ID (from GodPicked events)
- `god_name`: God name (from GodPicked events)
- `role`: Player role (from RoleAssigned events)
- `team_id`: Team identifier

#### 3.1.3 Event DataFrame

The central fact table containing all events with normalized fields:
- `event_id`: Generated surrogate key
- `match_id`: Reference to Match DataFrame
- `event_timestamp`: Normalized timestamp
- `event_type`: One of the main event types
- `event_subtype`: The subtype of the event
- `source_player_id`: Reference to Player DataFrame (for sourceowner)
- `target_player_id`: Reference to Player DataFrame (for targetowner, if applicable)
- `location_x`, `location_y`: Spatial coordinates (if available)
- `item_id`, `item_name`: Item identifiers (if applicable)
- `value1`, `value2`: Normalized numeric values
- `raw_text`: Original text description
- `original_data`: JSON string of the original event data

### 3.2 Specialized DataFrames for Analysis

#### 3.2.1 Combat DataFrame

Focused view of combat events:
- `event_id`: Reference to Event DataFrame
- `combat_type`: Type of combat interaction
- `source_player_id`, `source_god`: Attacker information
- `target_player_id`, `target_god`: Target information
- `ability_id`, `ability_name`: The ability used
- `damage_amount`: Primary damage value
- `mitigated_amount`: Damage mitigated
- `is_critical`: Boolean indicating critical hit
- `timestamp`: When the combat occurred
- `location_x`, `location_y`: Where the combat occurred

#### 3.2.2 Economy DataFrame

Tracks currency and experience events:
- `event_id`: Reference to Event DataFrame
- `reward_type`: Type of reward (experience or currency)
- `source_entity`: Source of the reward
- `target_player_id`: Player receiving the reward
- `amount`: Quantity received
- `source_type`: Context of the reward (e.g., minion kill, objective)
- `timestamp`: When the reward was granted
- `location_x`, `location_y`: Where the reward was granted

#### 3.2.3 Item DataFrame

Tracks item purchases:
- `event_id`: Reference to Event DataFrame
- `player_id`: Player making the purchase
- `item_id`, `item_name`: Item purchased
- `timestamp`: When the purchase occurred
- `location_x`, `location_y`: Where the purchase occurred

## 4. Transformation Pipeline

### 4.1 Raw Data Processing

1. **File Reading**:
   - Read the raw log file with UTF-8-SIG encoding
   - Handle line delimiters and clean trailing commas
   - Parse each line as a JSON object

2. **Initial Parsing and Validation**:
   - Validate each event against expected schemas
   - Log any parsing errors or unexpected formats
   - Create initial DataFrame of raw events

### 4.2 Metadata Extraction

1. **Match Identification**:
   - Extract match metadata from the start event
   - Determine match time boundaries

2. **Player Identification**:
   - Extract player information from playermsg events
   - Match player names to god selections and roles
   - Assign team identifiers based on value1 field

### 4.3 Data Normalization

1. **Field Type Conversion**:
   - Convert string timestamps to datetime objects
   - Convert string coordinates to float values
   - Convert string numeric values to appropriate int/float types

2. **Event Categorization**:
   - Classify and organize events by type and subtype
   - Create relationships between events and entities (players, items)

3. **Spatial Data Processing**:
   - Normalize coordinate systems if needed
   - Handle missing coordinates for certain event types

### 4.4 Specialized DataFrame Creation

1. **Combat Events Processing**:
   - Extract and normalize combat-specific fields
   - Calculate derived combat metrics (DPS, healing efficiency)

2. **Economy Events Processing**:
   - Track resource flow through the match
   - Calculate economic advantage over time

3. **Item Events Processing**:
   - Track item acquisition sequence
   - Link items to subsequent combat performance

## 5. Implementation Approach

### 5.1 Core Class Structure

1. **CombatLogParser**: Main class that orchestrates the parsing process
   - Handles file reading and initial JSON parsing
   - Manages the overall transformation pipeline
   - Provides access to the resulting data structures

2. **EventProcessor**: Processes and normalizes raw events
   - Converts field types
   - Extracts and organizes metadata
   - Creates the unified event structure

3. **AnalyticalViews**: Creates specialized analytical views
   - Transforms the core data model into analysis-ready structures
   - Provides methods for common analytical queries

### 5.2 Processing Flow

1. Initialize the parser with the log file path
2. Read and parse the raw log data
3. Extract match metadata and player information
4. Process events and normalize fields
5. Create the core data structures
6. Generate analytical views as needed
7. Provide interfaces for querying and analysis

### 5.3 Error Handling and Logging

1. **Validation Errors**: Log and handle invalid JSON or unexpected field values
2. **Missing References**: Handle cases where referenced entities (players, items) are missing
3. **Data Inconsistencies**: Detect and report inconsistent data (e.g., timestamps out of order)
4. **Performance Monitoring**: Track and log processing time and memory usage

## 6. Analytical Capabilities

The transformed data model will support the following analytical capabilities:

### 6.1 Timeline Analysis

- Track events chronologically with normalized timestamps
- Analyze patterns and sequences of events
- Identify key moments in the match (first blood, objective kills)

### 6.2 Player Performance Analysis

- Calculate combat metrics per player (damage dealt/received, healing done)
- Track item build progression and its impact on performance
- Analyze player positioning and movement patterns

### 6.3 Team Dynamics

- Compare team performance metrics over time
- Analyze team fights and coordination
- Track resource distribution within teams

### 6.4 Spatial Analysis

- Create heatmaps of combat activity
- Analyze movement patterns and positioning
- Identify contested zones and key locations

## 7. Testing Strategy

### 7.1 Unit Testing

- Test individual components (parsing, normalization, view creation)
- Verify correct handling of all event types and edge cases
- Test error handling and recovery mechanisms

### 7.2 Integration Testing

- Test the complete transformation pipeline
- Verify relationships between different data structures
- Ensure consistency across the data model

### 7.3 Performance Testing

- Test with large log files to ensure scalability
- Measure memory usage and processing time
- Optimize bottlenecks in the pipeline

## 8. Implementation Timeline

1. **Phase 1**: Core parser implementation (2-3 days)
   - Implement the basic file reading and JSON parsing
   - Create the initial data structures
   - Handle the main event types

2. **Phase 2**: Data normalization and relationships (2-3 days)
   - Implement field type conversion
   - Create player and match metadata structures
   - Establish relationships between entities

3. **Phase 3**: Analytical views and querying (2-3 days)
   - Implement specialized analytical DataFrames
   - Create methods for common queries
   - Optimize data structures for performance

4. **Phase 4**: Testing and documentation (1-2 days)
   - Develop comprehensive test suite
   - Create documentation and examples
   - Ensure all requirements are met

## 9. Future Extensions

- **Advanced Analytics**: Implement ML models for player performance prediction
- **Visualization Layer**: Create a visualization interface for the parsed data
- **Real-time Processing**: Support streaming log parsing for live matches
- **Cross-match Analysis**: Enable analysis across multiple matches
- **Custom Event Detection**: Identify complex game events (team fights, objective contests)

## 10. Conclusion

This technical specification outlines the approach for transforming SMITE 2 CombatLog data into a structured, analysis-ready format. The proposed data model and transformation pipeline address the challenges of the raw data while providing powerful analytical capabilities. The implementation will be modular, well-tested, and optimized for performance and usability. 