# Phase 1: Vector Store Foundation

## Metadata
```yaml
task_id: phase1-vector-store-foundation
title: "Vector Store Foundation for AI Super-Assistant"
description: "Implement vector database infrastructure and embedding services for semantic workflow matching"
priority: high
estimated_effort: 1 week
dependencies:
  - swarm_director_core
  - openai_api_access
  - vector_database_service
created_date: 2025-06-19
status: ready
assignee: backend_team
tags: [vector-store, embeddings, infrastructure, tdd]
parent_task: ai-super-assistant-enhancement
```

## TDD Overview

This task follows strict Test-Driven Development principles:
1. **Write failing tests first** for each component
2. **Implement minimal code** to make tests pass
3. **Refactor** while keeping tests green
4. **Achieve >95% test coverage** for all new components

## Subtasks

### 1.1 Vector Store Abstraction Layer
**Estimated: 2 days**

#### Test Requirements
```python
# tests/test_vector_store_service.py
class TestVectorStoreService:
    def test_store_embedding_success(self):
        """Test storing embedding with metadata"""
        
    def test_search_similar_embeddings(self):
        """Test similarity search with threshold"""
        
    def test_batch_operations(self):
        """Test batch insert and search operations"""
        
    def test_connection_failure_handling(self):
        """Test graceful handling of connection failures"""
        
    def test_invalid_embedding_dimensions(self):
        """Test validation of embedding dimensions"""
```

#### Implementation Specs
- **File**: `src/swarm_director/services/vector_store_service.py`
- **Interface**: Abstract base class with Pinecone/Weaviate implementations
- **Error Handling**: Retry logic with exponential backoff
- **Performance**: Connection pooling and async operations

### 1.2 Embedding Generation Service
**Estimated: 1.5 days**

#### Test Requirements
```python
# tests/test_embedding_service.py
class TestEmbeddingService:
    def test_generate_single_embedding(self):
        """Test generating embedding for single text"""
        
    def test_batch_embedding_generation(self):
        """Test batch processing of multiple texts"""
        
    def test_caching_mechanism(self):
        """Test embedding caching for duplicate texts"""
        
    def test_rate_limiting_compliance(self):
        """Test API rate limiting and queuing"""
        
    def test_cost_tracking_integration(self):
        """Test integration with existing cost tracking"""
        
    def test_embedding_normalization(self):
        """Test L2 normalization of embeddings"""
```

#### Implementation Specs
- **File**: `src/swarm_director/services/embedding_service.py`
- **Model**: OpenAI text-embedding-3-small (1536 dimensions)
- **Caching**: Redis-based cache with TTL
- **Batching**: Process up to 100 texts per API call

### 1.3 Workflow Embedding Pipeline
**Estimated: 1.5 days**

#### Test Requirements
```python
# tests/test_workflow_embedding_pipeline.py
class TestWorkflowEmbeddingPipeline:
    def test_extract_workflow_text(self):
        """Test text extraction from workflow definitions"""
        
    def test_generate_workflow_embeddings(self):
        """Test embedding generation for workflows"""
        
    def test_index_existing_workflows(self):
        """Test indexing all existing workflows"""
        
    def test_incremental_indexing(self):
        """Test adding new workflows to index"""
        
    def test_embedding_update_on_workflow_change(self):
        """Test re-indexing when workflows are modified"""
```

#### Implementation Specs
- **File**: `src/swarm_director/services/workflow_embedding_pipeline.py`
- **Text Extraction**: Combine workflow name, description, and step descriptions
- **Indexing Strategy**: Incremental updates with change detection
- **Metadata**: Store workflow ID, category, usage stats

### 1.4 Database Schema Extensions
**Estimated: 1 day**

#### Test Requirements
```python
# tests/test_vector_models.py
class TestVectorModels:
    def test_workflow_embedding_model_creation(self):
        """Test creating workflow embedding records"""
        
    def test_embedding_vector_storage(self):
        """Test storing high-dimensional vectors"""
        
    def test_similarity_search_query(self):
        """Test database similarity search queries"""
        
    def test_embedding_metadata_relationships(self):
        """Test relationships with existing workflow models"""
        
    def test_migration_script_execution(self):
        """Test database migration without data loss"""
```

#### Implementation Specs
- **Migration**: `migrations/add_vector_support.py`
- **Models**: `src/swarm_director/models/workflow_embedding.py`
- **Indexes**: Vector similarity indexes for performance
- **Constraints**: Foreign key relationships with existing tables

### 1.5 Configuration and Environment Setup
**Estimated: 1 day**

#### Test Requirements
```python
# tests/test_vector_config.py
class TestVectorConfiguration:
    def test_vector_store_config_validation(self):
        """Test configuration validation for different providers"""
        
    def test_environment_variable_loading(self):
        """Test loading configuration from environment"""
        
    def test_fallback_configuration(self):
        """Test fallback to default values"""
        
    def test_connection_string_parsing(self):
        """Test parsing of vector store connection strings"""
        
    def test_security_credential_handling(self):
        """Test secure handling of API keys"""
```

#### Implementation Specs
- **File**: `src/swarm_director/config/vector_config.py`
- **Environment Variables**: Comprehensive validation
- **Security**: Encrypted credential storage
- **Flexibility**: Support multiple vector store providers

## Detailed Test Specifications

### Unit Tests (Target: 95% coverage)

#### Vector Store Service Tests
```python
@pytest.fixture
def mock_vector_store():
    return MockVectorStore()

@pytest.fixture
def vector_service(mock_vector_store):
    return VectorStoreService(mock_vector_store)

class TestVectorStoreService:
    def test_store_embedding_with_metadata(self, vector_service):
        # Arrange
        embedding = [0.1] * 1536
        metadata = {"workflow_id": "test_workflow", "category": "communication"}
        
        # Act
        result = vector_service.store_embedding("test_id", embedding, metadata)
        
        # Assert
        assert result.success is True
        assert result.id == "test_id"
        
    def test_search_similar_embeddings_with_threshold(self, vector_service):
        # Arrange
        query_embedding = [0.1] * 1536
        threshold = 0.8
        
        # Act
        results = vector_service.search_similar(query_embedding, threshold=threshold, top_k=5)
        
        # Assert
        assert len(results) <= 5
        assert all(result.similarity >= threshold for result in results)
        
    def test_batch_operations_performance(self, vector_service):
        # Arrange
        embeddings = [[0.1] * 1536 for _ in range(100)]
        metadata_list = [{"id": f"test_{i}"} for i in range(100)]
        
        # Act
        start_time = time.time()
        results = vector_service.batch_store(embeddings, metadata_list)
        duration = time.time() - start_time
        
        # Assert
        assert len(results) == 100
        assert duration < 5.0  # Should complete within 5 seconds
```

#### Embedding Service Tests
```python
class TestEmbeddingService:
    @pytest.mark.asyncio
    async def test_generate_embedding_success(self, embedding_service):
        # Arrange
        text = "Send welcome email to new customer"
        
        # Act
        embedding = await embedding_service.generate(text)
        
        # Assert
        assert len(embedding) == 1536
        assert all(isinstance(x, float) for x in embedding)
        assert -1.0 <= max(embedding) <= 1.0
        
    @pytest.mark.asyncio
    async def test_caching_reduces_api_calls(self, embedding_service, mock_openai):
        # Arrange
        text = "Test text for caching"
        
        # Act
        embedding1 = await embedding_service.generate(text)
        embedding2 = await embedding_service.generate(text)
        
        # Assert
        assert embedding1 == embedding2
        assert mock_openai.call_count == 1  # Only one API call
        
    @pytest.mark.asyncio
    async def test_batch_processing_efficiency(self, embedding_service):
        # Arrange
        texts = [f"Test text {i}" for i in range(50)]
        
        # Act
        embeddings = await embedding_service.batch_generate(texts)
        
        # Assert
        assert len(embeddings) == 50
        assert all(len(emb) == 1536 for emb in embeddings)
```

### Integration Tests

#### End-to-End Workflow Indexing
```python
class TestWorkflowIndexingIntegration:
    @pytest.mark.integration
    def test_index_existing_workflows_complete_pipeline(self, db_session, vector_store):
        # Arrange
        workflows = create_test_workflows(db_session, count=10)
        pipeline = WorkflowEmbeddingPipeline(vector_store)
        
        # Act
        results = pipeline.index_all_workflows()
        
        # Assert
        assert results.indexed_count == 10
        assert results.failed_count == 0
        
        # Verify searchability
        search_results = vector_store.search_similar(
            query="send email notification",
            threshold=0.7
        )
        assert len(search_results) > 0
        
    @pytest.mark.integration
    def test_incremental_workflow_updates(self, db_session, vector_store):
        # Arrange
        workflow = create_test_workflow(db_session)
        pipeline = WorkflowEmbeddingPipeline(vector_store)
        pipeline.index_workflow(workflow)
        
        # Act - Update workflow
        workflow.description = "Updated workflow description"
        db_session.commit()
        pipeline.update_workflow_embedding(workflow)
        
        # Assert
        updated_embedding = vector_store.get_embedding(workflow.id)
        assert updated_embedding is not None
        assert updated_embedding.metadata["updated_at"] > workflow.created_at
```

### Performance Tests

#### Load Testing Specifications
```python
class TestVectorStorePerformance:
    @pytest.mark.performance
    def test_concurrent_search_operations(self, vector_service):
        # Test 100 concurrent searches
        async def search_task():
            return await vector_service.search_similar([0.1] * 1536, top_k=10)
        
        # Act
        start_time = time.time()
        results = asyncio.gather(*[search_task() for _ in range(100)])
        duration = time.time() - start_time
        
        # Assert
        assert duration < 2.0  # All searches complete within 2 seconds
        assert len(results) == 100
        
    @pytest.mark.performance
    def test_embedding_generation_throughput(self, embedding_service):
        # Test processing 1000 texts
        texts = [f"Test workflow description {i}" for i in range(1000)]
        
        # Act
        start_time = time.time()
        embeddings = embedding_service.batch_generate(texts, batch_size=100)
        duration = time.time() - start_time
        
        # Assert
        assert len(embeddings) == 1000
        assert duration < 30.0  # Complete within 30 seconds
```

## Implementation Dependencies

### Required Packages
```python
# requirements-phase1.txt
pinecone-client==2.2.4
weaviate-client==3.25.3
openai==1.3.7
redis==5.0.1
numpy==1.24.3
pytest-asyncio==0.21.1
pytest-mock==3.12.0
```

### Environment Configuration
```bash
# .env.test
VECTOR_STORE_TYPE=mock
OPENAI_API_KEY=test_key
REDIS_URL=redis://localhost:6379/1
EMBEDDING_CACHE_TTL=3600
VECTOR_STORE_TIMEOUT=30
```

## Success Criteria

### Functional Requirements
- [ ] **Vector store abstraction** supports multiple providers
- [ ] **Embedding generation** with caching and batching
- [ ] **Workflow indexing** for all existing workflows
- [ ] **Similarity search** with configurable thresholds
- [ ] **Database integration** with proper migrations

### Performance Requirements
- [ ] **Search latency**: <100ms for similarity queries
- [ ] **Embedding generation**: <5s for 100 texts
- [ ] **Concurrent operations**: Handle 50+ simultaneous requests
- [ ] **Memory efficiency**: <500MB for 10K workflow embeddings

### Quality Requirements
- [ ] **Test coverage**: >95% for all new components
- [ ] **Error handling**: Graceful degradation on failures
- [ ] **Documentation**: Complete API documentation
- [ ] **Security**: Encrypted credential storage

## Risk Mitigation

### Technical Risks
- **Vector store latency**: Implement local caching layer
- **API rate limits**: Queue management with backoff
- **Memory usage**: Streaming for large batch operations

### Testing Risks
- **External dependencies**: Mock all external services
- **Data consistency**: Isolated test databases
- **Performance variability**: Baseline measurements

## Monitoring & Observability

### Metrics to Track
- **Embedding generation rate** and latency
- **Vector store query performance**
- **Cache hit rates** and efficiency
- **Error rates** by component

### Logging Requirements
- **Structured logging** with correlation IDs
- **Performance metrics** for each operation
- **Error details** with stack traces
- **Usage statistics** for cost tracking
