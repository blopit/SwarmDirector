from ..utils.metrics import get_current_metrics_summary, metrics_collector

@app.route('/api/metrics/summary')
def get_metrics_summary():
    """Get comprehensive metrics summary"""
    try:
        summary = get_current_metrics_summary()
        return jsonify({
            'success': True,
            'data': summary
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/metrics/system')
def get_system_metrics():
    """Get current system metrics"""
    try:
        correlation_id = request.headers.get('X-Correlation-ID')
        system_metrics = metrics_collector.collect_system_metrics(correlation_id)
        
        metrics_data = {
            name: {
                'value': metric.value,
                'unit': metric.unit,
                'timestamp': metric.timestamp.isoformat(),
                'tags': metric.tags
            } for name, metric in system_metrics.items()
        }
        
        return jsonify({
            'success': True,
            'data': metrics_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/metrics/endpoints')
def get_endpoint_metrics():
    """Get endpoint performance statistics"""
    try:
        endpoint_stats = metrics_collector.get_all_endpoint_stats()
        return jsonify({
            'success': True,
            'data': endpoint_stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/metrics/endpoint/<path:endpoint_name>')
def get_endpoint_metric(endpoint_name):
    """Get metrics for a specific endpoint"""
    try:
        stats = metrics_collector.get_endpoint_stats(endpoint_name)
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500 