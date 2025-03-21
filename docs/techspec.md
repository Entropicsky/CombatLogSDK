Below is a full technical specification for restructuring SMITE 2 CombatLog data into a model suitable for robust analysis.

1. Overview  
The raw CombatLog consists of newline‐delimited JSON objects. Each record corresponds to an event in a match. Event types include:  
• start (match metadata)  
• playermsg (subtypes RoleAssigned, GodHovered, GodPicked)  
• CombatMsg (subtypes Damage, CritDamage, CrowdControl, Healing, KillingBlow)  
• RewardMsg (subtypes Currency, Experience)  
• itemmsg (subtype ItemPurchase)  

The objective is to produce a structure that supports timeline, player, team, and event aggregation analysis in dataframes and databases.

2. Data Challenges and Objectives  
• Heterogeneous JSON schemas across event types require a unified superset of columns.  
• Time values are stored as strings in the “YYYY.MM.DD-HH.MM.SS” format; these must be normalized.  
• Player identity (sourceowner) is scattered; player–god relationships are recorded in GodPicked events.  
• Spatial information (locationx, locationy) appears only in some events.  
• The final model must support grouping events by event type, subtype, player, and match and enable drill-down analysis.

3. Proposed Data Model  
The design uses a star schema.

A. Fact Table – Events_Fact  
Each record in Events_Fact represents one log event. Key fields include:  
• event_id: Surrogate key  
• match_id: Foreign key to Match_Dim  
• player_id: Foreign key to Player_Dim (derived from sourceowner)  
• target_id: (Optional) Foreign key for targetowner if applicable  
• event_type: One of {start, playermsg, CombatMsg, RewardMsg, itemmsg}  
• event_subtype: Corresponds to the “type” field (e.g., RoleAssigned, GodPicked, Damage)  
• event_time: Timestamp, derived from the time field  
• numeric_metrics: Fields such as value1, value2 (converted to numbers)  
• location_x, location_y: Spatial coordinates when present  
• raw_text: The original text field for audit  
• Other fields: itemid, itemname, and any extra fields from the superset of JSON keys  

B. Dimension Tables  
• Match_Dim  
  – match_id, logMode, start_time, and other match-level metadata from the “start” event.  
• Player_Dim  
  – player_id, player_name (sourceowner), role (from RoleAssigned events), and god_picked (from GodPicked events).  
  – Optional team assignment (derived from role or external mapping).  
• Item_Dim  
  – item_id, item_name, and additional item properties (for itemmsg events).  
• (Optional) God_Dim  
  – god_id, god_name, and other attributes if further analysis requires separate god properties.  

4. Transformation Pipeline  
The transformation follows these steps:

A. Preprocessing  
• Read raw file with UTF-8-SIG to remove BOM.  
• Strip trailing commas and newline delimiters.  
• Parse each line as JSON and log errors.

B. Time Field Normalization  
• Extract the time string from each record.  
• Convert “YYYY.MM.DD-HH.MM.SS” to ISO 8601 datetime objects.  
• Store both the original string and the converted timestamp for reference.

C. Extraction of Player Information  
• Filter playermsg records with subtype RoleAssigned to extract player names and roles.  
• For each player, join the corresponding GodPicked event to capture the selected god.  
• Assign a surrogate player_id and, where possible, derive team membership from role names or external logic.

D. Consolidation of Events  
• Create a superset of columns across all event types.  
• Map each event’s fields to the Events_Fact table; assign nulls for fields that do not apply.  
• Preserve numeric fields (e.g., damage values) and spatial coordinates.  
• Maintain the raw text field.

E. Loading into Target Structure  
• Populate the dimension tables (Match_Dim, Player_Dim, Item_Dim, etc.) with unique entities from the log.  
• Link each event record in Events_Fact with the corresponding dimension keys.  
• Validate referential integrity.

F. Data Quality and Error Handling  
• Log parsing errors and missing values.  
• Define rules for duplicate events and missing time or player data.  
• Create unit tests for time conversion and field extraction.

5. Analytical Capabilities  
This design supports:  
• Timeline analysis by aggregating event_time and filtering by event_type and event_subtype.  
• Drill-down analysis by player, god, or team via the Player_Dim.  
• Aggregated damage, rewards, or purchase events grouped by match or event type.  
• Spatial analysis using location_x and location_y for events such as ItemPurchase or CombatMsg.

6. Implementation Considerations  
• ETL Implementation: Use Python with Pandas for parsing and transformation.  
• Data Storage: Load into an SQL database (e.g., PostgreSQL) or maintain as structured JSON for dataframes.  
• Performance: Index on event_time, match_id, and player_id.  
• Scalability: Use batch processing for large log files and plan for schema evolution.  
• Documentation: Maintain a data dictionary, versioned schema diagrams, and transformation scripts.

7. Documentation and Governance  
• Produce detailed technical documentation covering the schema diagrams, data dictionary, and ETL process.  
• Define data governance policies and periodic audits to ensure data quality.  
• Include version control for schema changes and transformation logic.

8. Future Extensions  
• Expand the God_Dim or add new dimensions if additional game metrics become available.  
• Integrate real-time processing if analysis requires near real-time dashboards.  
• Update team assignment logic as SMITE 2 evolves.

The specification provides a clear, normalized structure for the CombatLog data. This model supports efficient aggregation and drill-down analyses by event type, player, god, and match. The transformation pipeline ensures data quality and consistency, with time normalization and a star schema design that facilitates robust analytical use.  
 
####