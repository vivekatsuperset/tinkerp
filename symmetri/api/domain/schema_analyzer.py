from dataclasses import dataclass
from typing import List, Any, Optional, Dict


@dataclass
class ColumnMetadata:
    name: str
    type: str
    nullable: bool
    description: str
    segmentation_role: str  # One of: 'filter', 'metric', 'identifier', 'attribute', 'timestamp', 'other'
    sample_values: Optional[List[Any]] = None  # Only used locally, never sent to LLM

    def to_json(self) -> Dict[str, Any]:
        """Convert ColumnMetadata to a JSON-serializable dictionary."""
        return {
            'name': self.name,
            'type': self.type,
            'nullable': self.nullable,
            'description': self.description,
            'segmentation_role': self.segmentation_role,
            'sample_values': self.sample_values
        }

    def to_summary_json(self) -> Dict[str, Any]:
        """Convert ColumnMetadata to a lightweight JSON-serializable dictionary."""
        return {
            'name': self.name,
            'type': self.type,
            'segmentation_role': self.segmentation_role
        }

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> 'ColumnMetadata':
        """Create a ColumnMetadata instance from a JSON dictionary."""
        return cls(
            name=data['name'],
            type=data['type'],
            nullable=data['nullable'],
            description=data['description'],
            segmentation_role=data['segmentation_role'],
            sample_values=data.get('sample_values')
        )


@dataclass
class TableMetadata:
    name: str
    description: str
    columns: List[ColumnMetadata]
    primary_keys: List[str]
    segmentation_columns: List[str]  # Columns that can be used in WHERE clauses for segmentation
    metric_columns: List[str]  # Columns that can be used for metrics/aggregations
    identifier_columns: List[str]  # Columns that identify entities (users, sessions, etc.)
    timestamp_columns: List[str]  # Columns used for time-based filtering

    def to_summary_json(self) -> Dict[str, Any]:
        """
        Convert TableMetadata to a lightweight JSON-serializable dictionary for list views.
        Only includes essential information needed for table cards.
        """
        return {
            'name': self.name,
            'description': self.description,
            'column_count': len(self.columns),
            'metric_count': len(self.metric_columns),
            'has_timestamp': bool(self.timestamp_columns),
            'primary_keys': self.primary_keys,
            # Include a few key columns for quick reference
            'key_columns': {
                'metrics': self.metric_columns[:3],  # First 3 metric columns
                'timestamps': self.timestamp_columns[:1],  # First timestamp column
                'identifiers': self.identifier_columns[:2]  # First 2 identifier columns
            }
        }

    def to_json(self) -> Dict[str, Any]:
        """Convert TableMetadata to a JSON-serializable dictionary."""
        return {
            'name': self.name,
            'description': self.description,
            'columns': [col.to_json() for col in self.columns],
            'primary_keys': self.primary_keys,
            'segmentation_columns': self.segmentation_columns,
            'metric_columns': self.metric_columns,
            'identifier_columns': self.identifier_columns,
            'timestamp_columns': self.timestamp_columns
        }

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> 'TableMetadata':
        """Create a TableMetadata instance from a JSON dictionary."""
        return cls(
            name=data['name'],
            description=data['description'],
            columns=[ColumnMetadata.from_json(col) for col in data['columns']],
            primary_keys=data['primary_keys'],
            segmentation_columns=data['segmentation_columns'],
            metric_columns=data['metric_columns'],
            identifier_columns=data['identifier_columns'],
            timestamp_columns=data['timestamp_columns']
        )

    def __str__(self) -> str:
        """Returns a human-readable string representation of the table metadata."""
        output = []
        output.append(f"Table: {self.name}")
        output.append(f"Description: {self.description}")
        output.append("\nColumns:")
        
        # Print each column with its details
        for col in self.columns:
            col_info = [
                f"  - {col.name}",
                f"    Type: {col.type}",
                f"    Nullable: {'Yes' if col.nullable else 'No'}",
                f"    Role: {col.segmentation_role}",
                f"    Description: {col.description}"
            ]
            if col.sample_values:
                col_info.append(f"    Sample Values: {col.sample_values[:3]}")
            output.extend(col_info)
        
        # Print special column categories
        if self.primary_keys:
            output.append(f"\nPrimary Keys: {', '.join(self.primary_keys)}")
        if self.segmentation_columns:
            output.append(f"Segmentation Columns: {', '.join(self.segmentation_columns)}")
        if self.metric_columns:
            output.append(f"Metric Columns: {', '.join(self.metric_columns)}")
        if self.identifier_columns:
            output.append(f"Identifier Columns: {', '.join(self.identifier_columns)}")
        if self.timestamp_columns:
            output.append(f"Timestamp Columns: {', '.join(self.timestamp_columns)}")
        
        return "\n".join(output)
