# Memory Export/Import Utilities

## Subtask Metadata
```yaml
subtask_id: "subtask_003"
parent_task: "task_019"
title: "Memory Export/Import Utilities"
type: "backend_development"
priority: "medium"
estimated_effort: "2-3 days"
complexity: "medium"
dependencies:
  - subtask_001
  - subtask_002
assignee: "backend_developer"
status: "blocked"
```

## Objective

Implement comprehensive memory export and import utilities for agent debugging, backup, and analysis purposes. Enable developers to save, restore, and analyze agent memory states for troubleshooting and optimization.

## Technical Specifications

### Export/Import Formats

#### Memory Export Format (JSON)
```json
{
    "export_metadata": {
        "version": "1.0",
        "export_timestamp": "2025-06-19T10:30:00Z",
        "agent_id": 123,
        "agent_name": "EmailAgent_001",
        "export_type": "full_memory",
        "compression": "gzip",
        "checksum": "sha256:abc123..."
    },
    "memory_state": {
        "conversation_memory": {
            "conversations": [...],
            "message_history": [...],
            "context_summaries": [...]
        },
        "workflow_context": {
            "active_workflows": {...},
            "shared_context": {...},
            "agent_specific_context": {...}
        },
        "agent_configuration": {
            "capabilities": [...],
            "config": {...},
            "system_message": "...",
            "autogen_config": {...}
        },
        "activity_history": {
            "recent_logs": [...],
            "performance_metrics": {...},
            "error_history": [...]
        }
    },
    "memory_analytics": {
        "total_size_mb": 15.2,
        "conversation_count": 45,
        "message_count": 1234,
        "oldest_memory": "2025-06-01T00:00:00Z",
        "newest_memory": "2025-06-19T10:30:00Z"
    }
}
```

### Core Implementation Classes

#### Memory Export Service
```python
class MemoryExportService:
    """Service for exporting agent memory states"""
    
    def __init__(self):
        self.supported_formats = ['json', 'json_compressed', 'binary']
        self.max_export_size_mb = 100
        
    def export_agent_memory(self, agent_id: int, 
                           export_type: str = 'full_memory',
                           format: str = 'json_compressed',
                           include_history: bool = True,
                           date_range: Tuple[datetime, datetime] = None) -> MemoryExport:
        """Export complete agent memory state"""
        
    def export_conversation_memory(self, agent_id: int,
                                  conversation_ids: List[int] = None) -> MemoryExport:
        """Export specific conversation memory"""
        
    def export_workflow_context(self, agent_id: int,
                               workflow_ids: List[str] = None) -> MemoryExport:
        """Export workflow context memory"""
        
    def create_memory_backup(self, agent_id: int) -> str:
        """Create a complete memory backup"""
        
    def validate_export_size(self, export_data: Dict[str, Any]) -> bool:
        """Validate export size limits"""

class MemoryImportService:
    """Service for importing agent memory states"""
    
    def __init__(self):
        self.supported_versions = ['1.0']
        self.validation_enabled = True
        
    def import_agent_memory(self, agent_id: int, 
                           import_file: str,
                           import_mode: str = 'merge',
                           validate_integrity: bool = True) -> ImportResult:
        """Import agent memory from file"""
        
    def restore_memory_backup(self, agent_id: int, 
                             backup_file: str) -> ImportResult:
        """Restore agent memory from backup"""
        
    def preview_import(self, import_file: str) -> ImportPreview:
        """Preview import without applying changes"""
        
    def validate_import_file(self, import_file: str) -> ValidationResult:
        """Validate import file format and integrity"""

class MemoryExport:
    """Represents a memory export operation"""
    
    def __init__(self, agent_id: int, export_type: str):
        self.agent_id = agent_id
        self.export_type = export_type
        self.export_id = str(uuid.uuid4())
        self.created_at = datetime.utcnow()
        self.data: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}
        
    def add_memory_section(self, section_name: str, data: Any) -> None:
        """Add a memory section to the export"""
        
    def compress(self) -> bytes:
        """Compress export data"""
        
    def calculate_checksum(self) -> str:
        """Calculate SHA256 checksum"""
        
    def save_to_file(self, file_path: str) -> None:
        """Save export to file"""
        
    def to_json(self) -> str:
        """Convert export to JSON string"""
```

### API Endpoints

#### Export Endpoints
```python
# POST /api/agents/{agent_id}/memory/export
{
    "export_type": "full_memory",  # full_memory, conversations, workflow_context
    "format": "json_compressed",   # json, json_compressed, binary
    "include_history": true,
    "date_range": {
        "start": "2025-06-01T00:00:00Z",
        "end": "2025-06-19T23:59:59Z"
    },
    "conversation_ids": [1, 2, 3],  # Optional: specific conversations
    "workflow_ids": ["wf_001", "wf_002"]  # Optional: specific workflows
}

# Response
{
    "success": true,
    "export_id": "exp_abc123",
    "download_url": "/api/memory/exports/exp_abc123/download",
    "export_info": {
        "size_mb": 15.2,
        "format": "json_compressed",
        "expires_at": "2025-06-26T10:30:00Z"
    }
}
```

#### Import Endpoints
```python
# POST /api/agents/{agent_id}/memory/import
# Content-Type: multipart/form-data
{
    "import_mode": "merge",  # merge, replace, append
    "validate_integrity": true,
    "dry_run": false
}

# Response
{
    "success": true,
    "import_id": "imp_xyz789",
    "import_result": {
        "conversations_imported": 45,
        "messages_imported": 1234,
        "workflows_imported": 3,
        "conflicts_resolved": 2,
        "errors": []
    }
}
```

## Implementation Steps

### Step 1: Core Export/Import Classes (Day 1)
1. Implement `MemoryExportService` class
2. Implement `MemoryImportService` class
3. Create `MemoryExport` and related data classes
4. Add compression and checksum utilities

### Step 2: File Format Handling (Day 2)
1. Implement JSON export/import format
2. Add compression support (gzip)
3. Create file validation utilities
4. Add integrity checking mechanisms

### Step 3: API Integration (Day 3)
1. Create export/import API endpoints
2. Add file upload/download handling
3. Implement temporary file management
4. Add progress tracking for large exports

## File Management

### Temporary File Handling
```python
class MemoryFileManager:
    """Manages temporary files for memory export/import"""
    
    def __init__(self):
        self.temp_dir = '/tmp/swarm_memory_exports'
        self.max_file_age_hours = 24
        self.max_total_size_gb = 10
        
    def create_export_file(self, export: MemoryExport) -> str:
        """Create temporary export file"""
        
    def cleanup_old_files(self) -> int:
        """Clean up old temporary files"""
        
    def validate_file_size(self, file_path: str) -> bool:
        """Validate file size limits"""
        
    def secure_file_access(self, file_path: str, user_id: str) -> bool:
        """Validate secure file access"""
```

### Storage Configuration
```python
class MemoryStorageConfig:
    """Configuration for memory export/import storage"""
    
    # File storage settings
    TEMP_EXPORT_DIR = '/tmp/swarm_memory_exports'
    MAX_EXPORT_SIZE_MB = 100
    MAX_IMPORT_SIZE_MB = 100
    FILE_RETENTION_HOURS = 24
    
    # Compression settings
    ENABLE_COMPRESSION = True
    COMPRESSION_LEVEL = 6
    
    # Security settings
    ENABLE_CHECKSUM_VALIDATION = True
    REQUIRE_SECURE_ACCESS = True
    MAX_CONCURRENT_EXPORTS = 10
```

## Data Validation and Integrity

### Export Validation
```python
class MemoryExportValidator:
    """Validates memory export data"""
    
    def validate_export_data(self, export_data: Dict[str, Any]) -> ValidationResult:
        """Validate export data structure and content"""
        
    def check_data_consistency(self, export_data: Dict[str, Any]) -> List[str]:
        """Check for data consistency issues"""
        
    def validate_memory_references(self, export_data: Dict[str, Any]) -> List[str]:
        """Validate memory reference integrity"""
        
    def sanitize_sensitive_data(self, export_data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove or mask sensitive data"""

class MemoryImportValidator:
    """Validates memory import data"""
    
    def validate_import_format(self, import_data: Dict[str, Any]) -> ValidationResult:
        """Validate import file format"""
        
    def check_version_compatibility(self, import_data: Dict[str, Any]) -> bool:
        """Check version compatibility"""
        
    def detect_import_conflicts(self, agent_id: int, 
                               import_data: Dict[str, Any]) -> List[ImportConflict]:
        """Detect potential import conflicts"""
        
    def validate_agent_compatibility(self, agent_id: int,
                                   import_data: Dict[str, Any]) -> bool:
        """Validate agent compatibility"""
```

## Import Modes and Conflict Resolution

### Import Modes
```python
class ImportMode(enum.Enum):
    MERGE = "merge"          # Merge with existing memory
    REPLACE = "replace"      # Replace existing memory
    APPEND = "append"        # Append to existing memory
    SELECTIVE = "selective"  # Import selected components only

class ConflictResolution(enum.Enum):
    SKIP = "skip"           # Skip conflicting items
    OVERWRITE = "overwrite" # Overwrite existing items
    RENAME = "rename"       # Rename conflicting items
    MERGE_CONTENT = "merge_content"  # Merge content where possible
```

### Conflict Detection and Resolution
```python
class ImportConflictResolver:
    """Resolves conflicts during memory import"""
    
    def detect_conversation_conflicts(self, agent_id: int,
                                    import_conversations: List[Dict]) -> List[ImportConflict]:
        """Detect conversation ID conflicts"""
        
    def resolve_conversation_conflicts(self, conflicts: List[ImportConflict],
                                     resolution: ConflictResolution) -> List[ConflictResolution]:
        """Resolve conversation conflicts"""
        
    def detect_workflow_conflicts(self, agent_id: int,
                                import_workflows: List[Dict]) -> List[ImportConflict]:
        """Detect workflow context conflicts"""
        
    def merge_agent_configurations(self, existing_config: Dict[str, Any],
                                 import_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge agent configurations intelligently"""
```

## Testing Requirements

### Unit Tests
```python
class TestMemoryExportService:
    def test_full_memory_export(self):
        """Test complete memory export"""
        
    def test_selective_export(self):
        """Test selective memory export"""
        
    def test_export_compression(self):
        """Test export compression"""
        
    def test_export_validation(self):
        """Test export data validation"""

class TestMemoryImportService:
    def test_memory_import_merge(self):
        """Test memory import with merge mode"""
        
    def test_memory_import_replace(self):
        """Test memory import with replace mode"""
        
    def test_conflict_resolution(self):
        """Test import conflict resolution"""
        
    def test_import_validation(self):
        """Test import file validation"""
```

### Integration Tests
- Test export/import round-trip accuracy
- Test large memory export/import operations
- Test concurrent export/import operations
- Test file corruption handling

### Performance Tests
- Export/import performance with large datasets
- Compression efficiency testing
- File I/O performance optimization
- Memory usage during export/import

## Security Considerations

### Data Privacy
- Sanitize sensitive information in exports
- Encrypt export files containing sensitive data
- Implement secure file access controls
- Audit trail for export/import operations

### Access Control
- Validate user permissions for export/import
- Restrict export/import to authorized users
- Log all export/import activities
- Implement rate limiting for operations

## Success Criteria

### Functional Requirements
- [ ] Complete memory export in multiple formats
- [ ] Reliable memory import with conflict resolution
- [ ] Data integrity validation and checksums
- [ ] Support for selective export/import
- [ ] Backup and restore capabilities

### Performance Requirements
- [ ] Export/import operations complete within 5 minutes for 100MB
- [ ] Compression reduces file size by 60%+
- [ ] Support for concurrent export/import operations
- [ ] Minimal memory usage during operations

### Quality Requirements
- [ ] 95%+ unit test coverage
- [ ] Integration tests for all export/import scenarios
- [ ] Comprehensive error handling
- [ ] Data integrity validation

## Related Files
- `src/swarm_director/services/memory_export.py` - Export service
- `src/swarm_director/services/memory_import.py` - Import service
- `src/swarm_director/utils/memory_validation.py` - Validation utilities
- `src/swarm_director/api/memory_export_routes.py` - API endpoints
