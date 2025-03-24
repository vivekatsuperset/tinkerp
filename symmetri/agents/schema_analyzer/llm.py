import json

from symmetri.api.domain.schema_analyzer import ColumnMetadata, TableMetadata
from symmetri.db.base import Column
from symmetri.llms.base import LLM
from symmetri.llms.factory import get_llm_instance
from symmetri.utils import sanitize_json_string

SCHEMA_ANALYSIS_SYSTEM_PROMPT: str = """You are an expert database schema analyst specializing in audience segmentation. 
Your task is to analyze database tables and their columns to identify their roles in audience segmentation.

For each column, you must assign exactly one of these roles:
- 'filter': Used in WHERE clauses to filter audiences (e.g., gender, loyalty_tier, product_category)
- 'metric': Used for aggregations or thresholds (e.g., purchase_amount, visit_count)
- 'identifier': Identifies entities like users or sessions (e.g., user_id, session_id)
- 'attribute': Additional attributes that might be useful but aren't primary filters
- 'timestamp': Used for time-based filtering
- 'other': Not directly relevant for audience segmentation

When analyzing columns, consider:
1. Column name and type
2. Common naming patterns (e.g., '_id' suffix for identifiers)
3. Typical audience segment requirements
4. Common filtering patterns
5. Business context
6. Data type appropriateness for each role

Your response must be in JSON format with these exact keys:
{
    "description": "Overall table description focusing on audience segmentation use cases",
    "columns": [
        {
            "name": "column_name",
            "description": "Column description and typical usage",
            "segmentation_role": "role from the list above",
            "examples": ["Example usage in audience segments"]
        }
    ],
    "primary_keys": ["list of primary key columns"],
    "segmentation_columns": ["columns good for WHERE clauses"],
    "metric_columns": ["columns good for aggregations"],
    "identifier_columns": ["columns that identify entities"],
    "timestamp_columns": ["columns for time-based filtering"]
}"""

SCHEMA_ANALYSIS_EXAMPLES: str = """Here are examples of correct schema analysis responses:

Example 1 - User Table:
{
    "description": "Contains user profile data including loyalty status and demographic information",
    "columns": [
        {
            "name": "user_id",
            "description": "Unique identifier for each user",
            "segmentation_role": "identifier",
            "examples": ["Used as join key for user-related queries"]
        },
        {
            "name": "email",
            "description": "User's email address",
            "segmentation_role": "attribute",
            "examples": ["Used for user identification but not for segmentation"]
        },
        {
            "name": "created_at",
            "description": "Timestamp when the user account was created",
            "segmentation_role": "timestamp",
            "examples": ["Used for cohort analysis and time-based filtering"]
        },
        {
            "name": "loyalty_tier",
            "description": "User's current loyalty program tier",
            "segmentation_role": "filter",
            "examples": ["Filter users by loyalty status"]
        }
    ],
    "primary_keys": ["user_id"],
    "segmentation_columns": ["loyalty_tier"],
    "metric_columns": [],
    "identifier_columns": ["user_id"],
    "timestamp_columns": ["created_at"]
}

Example 2 - Purchase Table:
{
    "description": "Records of user purchases including transaction details and amounts",
    "columns": [
        {
            "name": "transaction_id",
            "description": "Unique identifier for each transaction",
            "segmentation_role": "identifier",
            "examples": ["Primary key for purchase records"]
        },
        {
            "name": "user_id",
            "description": "Reference to the user who made the purchase",
            "segmentation_role": "identifier",
            "examples": ["Join key to user table"]
        },
        {
            "name": "amount",
            "description": "Total purchase amount",
            "segmentation_role": "metric",
            "examples": ["Calculate total spend, average order value"]
        },
        {
            "name": "product_category",
            "description": "Category of the purchased product",
            "segmentation_role": "filter",
            "examples": ["Filter by product interests"]
        }
    ],
    "primary_keys": ["transaction_id"],
    "segmentation_columns": ["product_category"],
    "metric_columns": ["amount"],
    "identifier_columns": ["transaction_id", "user_id"],
    "timestamp_columns": []
}"""

SCHEMA_ANALYZER_SYSTEM_PROMPTS = [
    SCHEMA_ANALYSIS_SYSTEM_PROMPT,
    SCHEMA_ANALYSIS_EXAMPLES
]


class SchemaAnalyzerLLM(object):

    def __init__(self, llm_name: str, model_name: str):
        self.llm: LLM = get_llm_instance(
            name=llm_name,
            model=model_name
        )

    def analyze_table(self, table_name: str, columns: list[Column]) -> TableMetadata:
        columns_map = {}
        for column in columns:
            columns_map[column.name] = column

        llm_response = self.llm.get_response(
            user_prompts=[self._format_description_prompt(table_name, columns)],
            system_prompts=SCHEMA_ANALYZER_SYSTEM_PROMPTS
        )

        return self._parse_llm_response(llm_response.content, table_name, columns_map)

    def _parse_llm_response(self, llm_response: str, table_name: str, columns_map: dict[str, Column]) -> TableMetadata:
        try:
            data = sanitize_json_string(llm_response)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON in LLM response")

        columns = []
        for col_meta in data.get("columns", []):
            col_name = col_meta["name"]
            column = columns_map.get(col_name, None)
            if column:
                columns.append(ColumnMetadata(
                    name=col_name,
                    type=column.data_type,
                    nullable=column.nullable,
                    description=col_meta["description"],
                    segmentation_role=col_meta["segmentation_role"],
                    sample_values=None  # Will be added later if needed
                ))

        return TableMetadata(
            name=table_name,
            description=data.get("description", f"Table {table_name}"),
            columns=columns,
            primary_keys=data.get("primary_keys", []),
            segmentation_columns=data.get("segmentation_columns", []),
            metric_columns=data.get("metric_columns", []),
            identifier_columns=data.get("identifier_columns", []),
            timestamp_columns=data.get("timestamp_columns", [])
        )

    def _format_description_prompt(self, table: str, columns: list[Column]) -> str:
        """Format the prompt for generating table and column descriptions."""
        return f"""
        Analyze the following database table and its columns in the context of audience segmentation.
        The goal is to identify which columns are useful for defining audience segments and how they should be used.

        Table Name: {table}

        Columns:
        {self._format_columns_for_prompt(columns)}

        For each column, determine its role in audience segmentation based on the column name and type:
        - 'filter': Used in WHERE clauses to filter audiences (e.g., gender, loyalty_tier, product_category)
        - 'metric': Used for aggregations or thresholds (e.g., purchase_amount, visit_count)
        - 'identifier': Identifies entities like users or sessions (e.g., user_id, session_id)
        - 'attribute': Additional attributes that might be useful but aren't primary filters
        - 'timestamp': Used for time-based filtering
        - 'other': Not directly relevant for audience segmentation

        Consider:
        1. Column name and type
        2. Common naming patterns (e.g., '_id' suffix for identifiers)
        3. Typical audience segment requirements
        4. Common filtering patterns
        5. Business context
        6. Data type appropriateness for each role

        Return the analysis in JSON format:
        {{
            "description": "Overall table description focusing on audience segmentation use cases",
            "columns": [
                {{
                    "name": "column_name",
                    "description": "Column description and typical usage",
                    "segmentation_role": "role from the list above",
                    "examples": ["Example usage in audience segments"]
                }}
            ],
            "primary_keys": ["list of primary key columns"],
            "segmentation_columns": ["columns good for WHERE clauses"],
            "metric_columns": ["columns good for aggregations"],
            "identifier_columns": ["columns that identify entities"],
            "timestamp_columns": ["columns for time-based filtering"]
        }}
        """

    def _format_columns_for_prompt(self, columns: list[Column]) -> str:
        formatted_columns = []
        for col in columns:
            constraints = []
            if col.primary_key:
                constraints.append("PRIMARY KEY")
            if not col.nullable:
                constraints.append("NOT NULL")
            if col.default_value:
                constraints.append(f"DEFAULT: {col.default_value}")

            constraints_str = f" ({', '.join(constraints)})" if constraints else ""
            formatted_columns.append(
                f"- {col.name}: {col.data_type}{constraints_str}"
            )

        return "\n        ".join(formatted_columns)
