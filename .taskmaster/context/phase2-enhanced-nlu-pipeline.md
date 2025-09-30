# Phase 2: Enhanced NLU Pipeline

## Metadata
```yaml
task_id: phase2-enhanced-nlu-pipeline
title: "Enhanced NLU Pipeline with Semantic Workflow Discovery"
description: "Upgrade intent classification and implement semantic workflow discovery using vector similarity"
priority: high
estimated_effort: 1 week
dependencies:
  - phase1-vector-store-foundation
  - existing_director_agent
  - workflow_orchestrator
created_date: 2025-06-19
status: blocked
assignee: ai_team
tags: [nlu, semantic-search, intent-classification, tdd]
parent_task: ai-super-assistant-enhancement
```

## TDD Overview

This phase enhances the existing Director agent's NLU capabilities using Test-Driven Development:
1. **Write comprehensive tests** for semantic matching and intent classification
2. **Implement enhanced NLU pipeline** with vector similarity
3. **Integrate with existing Director agent** while maintaining backward compatibility
4. **Achieve >95% test coverage** with performance benchmarks

## Subtasks

### 2.1 Semantic Intent Classifier
**Estimated: 2 days**

#### Test Requirements
```python
# tests/test_semantic_intent_classifier.py
class TestSemanticIntentClassifier:
    def test_classify_with_high_confidence(self):
        """Test classification with clear intent match"""
        
    def test_classify_with_low_confidence_fallback(self):
        """Test fallback to keyword classification"""
        
    def test_multi_intent_disambiguation(self):
        """Test handling requests with multiple possible intents"""
        
    def test_confidence_score_calibration(self):
        """Test confidence scores are well-calibrated"""
        
    def test_classification_caching(self):
        """Test caching of classification results"""
        
    def test_performance_under_load(self):
        """Test classification performance with concurrent requests"""
```

#### Implementation Specs
- **File**: `src/swarm_director/services/semantic_intent_classifier.py`
- **Integration**: Extend existing `DirectorAgent.classify_intent_with_confidence()`
- **Fallback**: Graceful degradation to keyword-based classification
- **Performance**: <200ms average classification time

### 2.2 Workflow Discovery Service
**Estimated: 2 days**

#### Test Requirements
```python
# tests/test_workflow_discovery_service.py
class TestWorkflowDiscoveryService:
    def test_discover_exact_workflow_match(self):
        """Test finding exact workflow matches"""
        
    def test_discover_similar_workflows(self):
        """Test finding semantically similar workflows"""
        
    def test_ranking_by_relevance_score(self):
        """Test workflow ranking by relevance"""
        
    def test_filter_by_intent_category(self):
        """Test filtering workflows by intent category"""
        
    def test_no_matches_above_threshold(self):
        """Test behavior when no workflows meet threshold"""
        
    def test_workflow_usage_statistics_integration(self):
        """Test integration with workflow usage tracking"""
        
    def test_concurrent_discovery_requests(self):
        """Test handling multiple simultaneous discovery requests"""
```

#### Implementation Specs
- **File**: `src/swarm_director/services/workflow_discovery_service.py`
- **Ranking Algorithm**: Combine semantic similarity, usage stats, and success rates
- **Filtering**: Support filtering by department, complexity, and execution time
- **Caching**: Cache popular workflow searches

### 2.3 Enhanced Director Agent Integration
**Estimated: 1.5 days**

#### Test Requirements
```python
# tests/test_enhanced_director_agent.py
class TestEnhancedDirectorAgent:
    def test_semantic_workflow_routing(self):
        """Test routing using semantic workflow discovery"""
        
    def test_backward_compatibility_with_existing_routing(self):
        """Test existing routing logic still works"""
        
    def test_confidence_threshold_handling(self):
        """Test routing decisions based on confidence thresholds"""
        
    def test_fallback_to_dynamic_generation(self):
        """Test fallback when no suitable workflow found"""
        
    def test_routing_decision_logging(self):
        """Test comprehensive logging of routing decisions"""
        
    def test_performance_metrics_collection(self):
        """Test collection of routing performance metrics"""
```

#### Implementation Specs
- **File**: Extend `src/swarm_director/agents/director.py`
- **Method**: Enhance `route_task()` with semantic discovery
- **Compatibility**: Maintain all existing functionality
- **Metrics**: Track semantic vs keyword routing success rates

### 2.4 NLU Result Models and DTOs
**Estimated: 1 day**

#### Test Requirements
```python
# tests/test_nlu_models.py
class TestNLUModels:
    def test_nlu_result_creation(self):
        """Test creating NLU result objects"""
        
    def test_workflow_match_serialization(self):
        """Test serialization of workflow matches"""
        
    def test_confidence_score_validation(self):
        """Test validation of confidence scores"""
        
    def test_intent_classification_result_structure(self):
        """Test structure of classification results"""
        
    def test_similarity_score_normalization(self):
        """Test normalization of similarity scores"""
```

#### Implementation Specs
- **File**: `src/swarm_director/models/nlu_models.py`
- **DTOs**: Structured data transfer objects for NLU results
- **Validation**: Pydantic models with validation
- **Serialization**: JSON serialization for API responses

### 2.5 Configuration and Tuning System
**Estimated: 1.5 days**

#### Test Requirements
```python
# tests/test_nlu_configuration.py
class TestNLUConfiguration:
    def test_similarity_threshold_configuration(self):
        """Test configurable similarity thresholds"""
        
    def test_intent_category_weights(self):
        """Test configurable weights for intent categories"""
        
    def test_fallback_strategy_configuration(self):
        """Test configurable fallback strategies"""
        
    def test_performance_tuning_parameters(self):
        """Test performance-related configuration"""
        
    def test_a_b_testing_configuration(self):
        """Test A/B testing configuration for NLU variants"""
```

#### Implementation Specs
- **File**: `src/swarm_director/config/nlu_config.py`
- **Tuning**: Runtime configuration updates
- **A/B Testing**: Support for testing different NLU approaches
- **Monitoring**: Configuration change tracking

## Detailed Test Specifications

### Unit Tests (Target: 95% coverage)

#### Semantic Intent Classifier Tests
```python
@pytest.fixture
def semantic_classifier():
    return SemanticIntentClassifier(
        vector_store=MockVectorStore(),
        embedding_service=MockEmbeddingService()
    )

class TestSemanticIntentClassifier:
    @pytest.mark.asyncio
    async def test_classify_communication_intent_high_confidence(self, semantic_classifier):
        # Arrange
        request_text = "Send welcome email to new customer John Doe"
        expected_intent = "communications"
        expected_confidence_min = 0.85
        
        # Act
        result = await semantic_classifier.classify(request_text)
        
        # Assert
        assert result.intent == expected_intent
        assert result.confidence >= expected_confidence_min
        assert result.method == "semantic"
        assert len(result.similar_workflows) > 0
        
    @pytest.mark.asyncio
    async def test_classify_ambiguous_request_with_context(self, semantic_classifier):
        # Arrange
        request_text = "Process the customer request"  # Ambiguous
        context = {"department": "communications", "previous_tasks": ["email_sent"]}
        
        # Act
        result = await semantic_classifier.classify(request_text, context=context)
        
        # Assert
        assert result.confidence > 0.5
        assert result.context_used is True
        assert "communications" in result.possible_intents
        
    @pytest.mark.asyncio
    async def test_fallback_to_keyword_classification(self, semantic_classifier):
        # Arrange
        request_text = "xyz unknown request format"
        semantic_classifier.vector_store.should_fail = True
        
        # Act
        result = await semantic_classifier.classify(request_text)
        
        # Assert
        assert result.method == "keyword_fallback"
        assert result.confidence < 0.5
        assert result.fallback_reason == "vector_store_error"
```

#### Workflow Discovery Service Tests
```python
class TestWorkflowDiscoveryService:
    @pytest.fixture
    def discovery_service(self):
        return WorkflowDiscoveryService(
            vector_store=MockVectorStore(),
            workflow_registry=MockWorkflowRegistry()
        )
        
    @pytest.mark.asyncio
    async def test_discover_workflows_with_ranking(self, discovery_service):
        # Arrange
        query = "send notification email to customer"
        expected_workflows = ["email_notification", "customer_communication"]
        
        # Act
        results = await discovery_service.discover(query, top_k=5)
        
        # Assert
        assert len(results) <= 5
        assert results[0].workflow_id in expected_workflows
        assert results[0].relevance_score > results[1].relevance_score
        assert all(r.relevance_score >= 0.0 for r in results)
        
    @pytest.mark.asyncio
    async def test_filter_workflows_by_department(self, discovery_service):
        # Arrange
        query = "process customer data"
        department_filter = "communications"
        
        # Act
        results = await discovery_service.discover(
            query, 
            filters={"department": department_filter}
        )
        
        # Assert
        assert all(r.workflow.department == department_filter for r in results)
        
    @pytest.mark.asyncio
    async def test_no_workflows_above_threshold(self, discovery_service):
        # Arrange
        query = "completely unrelated request about quantum physics"
        high_threshold = 0.9
        
        # Act
        results = await discovery_service.discover(query, threshold=high_threshold)
        
        # Assert
        assert len(results) == 0
        assert discovery_service.last_search_stats.below_threshold_count > 0
```

### Integration Tests

#### End-to-End NLU Pipeline Tests
```python
class TestNLUPipelineIntegration:
    @pytest.mark.integration
    async def test_complete_nlu_pipeline_flow(self, app_context):
        # Arrange
        director_agent = create_test_director_agent()
        task = create_test_task(
            title="Send welcome email",
            description="Send personalized welcome email to new customer"
        )
        
        # Act
        routing_result = await director_agent.enhanced_route_task(task)
        
        # Assert
        assert routing_result["status"] == "success"
        assert routing_result["routing_method"] == "semantic"
        assert routing_result["confidence"] > 0.8
        assert "workflow_matches" in routing_result
        
    @pytest.mark.integration
    async def test_semantic_to_keyword_fallback_integration(self, app_context):
        # Arrange
        director_agent = create_test_director_agent()
        # Simulate vector store failure
        director_agent.vector_store.simulate_failure = True
        
        task = create_test_task(
            title="Send email notification",
            description="Email notification to customer"
        )
        
        # Act
        routing_result = await director_agent.enhanced_route_task(task)
        
        # Assert
        assert routing_result["status"] == "success"
        assert routing_result["routing_method"] == "keyword_fallback"
        assert routing_result["fallback_reason"] == "vector_store_unavailable"
```

### Performance Tests

#### Load Testing Specifications
```python
class TestNLUPerformance:
    @pytest.mark.performance
    async def test_concurrent_intent_classification(self):
        # Test 100 concurrent classifications
        classifier = SemanticIntentClassifier()
        requests = [f"Send email notification {i}" for i in range(100)]
        
        # Act
        start_time = time.time()
        results = await asyncio.gather(*[
            classifier.classify(req) for req in requests
        ])
        duration = time.time() - start_time
        
        # Assert
        assert len(results) == 100
        assert duration < 5.0  # Complete within 5 seconds
        assert all(r.confidence > 0.0 for r in results)
        
    @pytest.mark.performance
    async def test_workflow_discovery_latency(self):
        # Test discovery latency under load
        discovery_service = WorkflowDiscoveryService()
        
        # Act
        latencies = []
        for i in range(50):
            start = time.time()
            await discovery_service.discover(f"test query {i}")
            latencies.append(time.time() - start)
        
        # Assert
        avg_latency = sum(latencies) / len(latencies)
        assert avg_latency < 0.2  # Average under 200ms
        assert max(latencies) < 0.5  # No request over 500ms
```

### A/B Testing Framework Tests
```python
class TestNLUABTesting:
    def test_semantic_vs_keyword_classification_comparison(self):
        # Arrange
        test_requests = load_test_dataset("classification_test_set.json")
        semantic_classifier = SemanticIntentClassifier()
        keyword_classifier = KeywordIntentClassifier()
        
        # Act
        semantic_results = [semantic_classifier.classify(req) for req in test_requests]
        keyword_results = [keyword_classifier.classify(req) for req in test_requests]
        
        # Assert
        semantic_accuracy = calculate_accuracy(semantic_results, test_requests)
        keyword_accuracy = calculate_accuracy(keyword_results, test_requests)
        
        assert semantic_accuracy > keyword_accuracy
        assert semantic_accuracy > 0.85  # Minimum accuracy threshold
        
    def test_confidence_score_calibration(self):
        # Test that confidence scores correlate with actual accuracy
        classifier = SemanticIntentClassifier()
        test_cases = load_calibration_dataset()
        
        # Act
        results = [classifier.classify(case.text) for case in test_cases]
        
        # Assert
        high_confidence_results = [r for r in results if r.confidence > 0.9]
        high_confidence_accuracy = calculate_accuracy(high_confidence_results, test_cases)
        
        assert high_confidence_accuracy > 0.95  # High confidence should be very accurate
```

## Implementation Dependencies

### Required Packages
```python
# requirements-phase2.txt
scikit-learn==1.3.2
numpy==1.24.3
pydantic==2.5.0
asyncio-throttle==1.0.2
pytest-benchmark==4.0.0
```

### Configuration Extensions
```python
# src/swarm_director/config/nlu_config.py
@dataclass
class NLUConfig:
    # Similarity thresholds
    semantic_similarity_threshold: float = 0.75
    keyword_fallback_threshold: float = 0.5
    
    # Performance settings
    max_concurrent_classifications: int = 50
    classification_timeout_seconds: int = 5
    
    # A/B testing
    semantic_classification_percentage: float = 0.8  # 80% semantic, 20% keyword
    
    # Caching
    classification_cache_ttl: int = 3600
    workflow_discovery_cache_ttl: int = 1800
```

## Success Criteria

### Functional Requirements
- [ ] **Semantic intent classification** with >85% accuracy
- [ ] **Workflow discovery** with relevance ranking
- [ ] **Backward compatibility** with existing Director agent
- [ ] **Graceful fallback** to keyword classification
- [ ] **A/B testing framework** for comparing approaches

### Performance Requirements
- [ ] **Classification latency**: <200ms average
- [ ] **Discovery latency**: <300ms for top-10 results
- [ ] **Concurrent handling**: 50+ simultaneous requests
- [ ] **Cache efficiency**: >80% hit rate for repeated queries

### Quality Requirements
- [ ] **Test coverage**: >95% for all new components
- [ ] **Confidence calibration**: High confidence correlates with accuracy
- [ ] **Error handling**: Graceful degradation on failures
- [ ] **Monitoring**: Comprehensive metrics and alerting

## Risk Mitigation

### Technical Risks
- **Vector store latency**: Implement aggressive caching
- **Classification accuracy**: Continuous model evaluation
- **Fallback complexity**: Comprehensive fallback testing

### Quality Risks
- **Test data quality**: Curated test datasets
- **Performance regression**: Automated performance testing
- **Integration complexity**: Incremental integration approach
