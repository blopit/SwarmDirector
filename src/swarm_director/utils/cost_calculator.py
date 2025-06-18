"""
Cost calculation engine for AI API usage
Provides real-time cost calculations based on current API pricing
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP
from ..models.cost_tracking import APIProvider, UsageType

logger = logging.getLogger(__name__)


class APIpricing:
    """Current API pricing information (updated as of 2024)"""
    
    # OpenAI Pricing (per 1M tokens)
    OPENAI_PRICING = {
        "gpt-4": {
            "input": Decimal("30.00"),   # $30 per 1M input tokens
            "output": Decimal("60.00"),  # $60 per 1M output tokens
        },
        "gpt-4-turbo": {
            "input": Decimal("10.00"),   # $10 per 1M input tokens
            "output": Decimal("30.00"),  # $30 per 1M output tokens
        },
        "gpt-4o": {
            "input": Decimal("5.00"),    # $5 per 1M input tokens
            "output": Decimal("15.00"),  # $15 per 1M output tokens
        },
        "gpt-4o-mini": {
            "input": Decimal("0.15"),    # $0.15 per 1M input tokens
            "output": Decimal("0.60"),   # $0.60 per 1M output tokens
        },
        "gpt-3.5-turbo": {
            "input": Decimal("0.50"),    # $0.50 per 1M input tokens
            "output": Decimal("1.50"),   # $1.50 per 1M output tokens
        },
        "text-embedding-3-small": {
            "input": Decimal("0.02"),    # $0.02 per 1M tokens
            "output": Decimal("0.00"),   # No output cost for embeddings
        },
        "text-embedding-3-large": {
            "input": Decimal("0.13"),    # $0.13 per 1M tokens
            "output": Decimal("0.00"),   # No output cost for embeddings
        },
    }
    
    # Anthropic Pricing (per 1M tokens)
    ANTHROPIC_PRICING = {
        "claude-3-opus-20240229": {
            "input": Decimal("15.00"),   # $15 per 1M input tokens
            "output": Decimal("75.00"),  # $75 per 1M output tokens
        },
        "claude-3-sonnet-20240229": {
            "input": Decimal("3.00"),    # $3 per 1M input tokens
            "output": Decimal("15.00"),  # $15 per 1M output tokens
        },
        "claude-3-5-sonnet-20240620": {
            "input": Decimal("3.00"),    # $3 per 1M input tokens
            "output": Decimal("15.00"),  # $15 per 1M output tokens
        },
        "claude-3-haiku-20240307": {
            "input": Decimal("0.25"),    # $0.25 per 1M input tokens
            "output": Decimal("1.25"),   # $1.25 per 1M output tokens
        },
        "claude-3-7-sonnet-20250219": {
            "input": Decimal("3.00"),    # $3 per 1M input tokens (estimated)
            "output": Decimal("15.00"),  # $15 per 1M output tokens (estimated)
        },
    }
    
    # Perplexity Pricing (per 1M tokens)
    PERPLEXITY_PRICING = {
        "sonar-pro": {
            "input": Decimal("1.00"),    # $1 per 1M input tokens (estimated)
            "output": Decimal("3.00"),   # $3 per 1M output tokens (estimated)
        },
        "sonar-small": {
            "input": Decimal("0.20"),    # $0.20 per 1M input tokens (estimated)
            "output": Decimal("0.60"),   # $0.60 per 1M output tokens (estimated)
        },
    }
    
    # Google Pricing (per 1M tokens)
    GOOGLE_PRICING = {
        "gemini-pro": {
            "input": Decimal("0.50"),    # $0.50 per 1M input tokens
            "output": Decimal("1.50"),   # $1.50 per 1M output tokens
        },
        "gemini-pro-vision": {
            "input": Decimal("0.50"),    # $0.50 per 1M input tokens
            "output": Decimal("1.50"),   # $1.50 per 1M output tokens
        },
    }
    
    @classmethod
    def get_pricing(cls, provider: APIProvider, model: str) -> Optional[Dict[str, Decimal]]:
        """Get pricing for a specific provider and model"""
        pricing_map = {
            APIProvider.OPENAI: cls.OPENAI_PRICING,
            APIProvider.ANTHROPIC: cls.ANTHROPIC_PRICING,
            APIProvider.PERPLEXITY: cls.PERPLEXITY_PRICING,
            APIProvider.GOOGLE: cls.GOOGLE_PRICING,
            APIProvider.AZURE_OPENAI: cls.OPENAI_PRICING,  # Same as OpenAI
        }
        
        provider_pricing = pricing_map.get(provider, {})
        return provider_pricing.get(model)


class CostCalculator:
    """Main cost calculation engine"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.CostCalculator")
    
    def calculate_cost(
        self,
        provider: APIProvider,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        usage_type: UsageType = UsageType.CHAT_COMPLETION
    ) -> Tuple[Decimal, Decimal, Decimal, Decimal, Decimal]:
        """
        Calculate cost for API usage
        
        Returns:
            Tuple of (input_cost, output_cost, total_cost, input_price_per_token, output_price_per_token)
        """
        try:
            # Get pricing for the model
            pricing = APIpricing.get_pricing(provider, model)
            
            if not pricing:
                self.logger.warning(f"No pricing found for {provider.value}/{model}, using default rates")
                # Use default fallback pricing
                pricing = {"input": Decimal("1.00"), "output": Decimal("3.00")}
            
            # Get price per token (pricing is per 1M tokens)
            input_price_per_token = pricing["input"] / Decimal("1000000")
            output_price_per_token = pricing["output"] / Decimal("1000000")
            
            # Calculate costs
            input_cost = (Decimal(str(input_tokens)) * input_price_per_token).quantize(
                Decimal('0.000001'), rounding=ROUND_HALF_UP
            )
            output_cost = (Decimal(str(output_tokens)) * output_price_per_token).quantize(
                Decimal('0.000001'), rounding=ROUND_HALF_UP
            )
            total_cost = input_cost + output_cost
            
            self.logger.debug(
                f"Cost calculated for {provider.value}/{model}: "
                f"input={input_tokens} tokens (${input_cost}), "
                f"output={output_tokens} tokens (${output_cost}), "
                f"total=${total_cost}"
            )
            
            return input_cost, output_cost, total_cost, input_price_per_token, output_price_per_token
            
        except Exception as e:
            self.logger.error(f"Error calculating cost for {provider.value}/{model}: {e}")
            # Return zero costs on error
            return Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0")
    
    def estimate_cost(
        self,
        provider: APIProvider,
        model: str,
        estimated_input_tokens: int,
        estimated_output_tokens: int = None
    ) -> Dict[str, Any]:
        """
        Estimate cost for a planned API call
        
        Args:
            provider: API provider
            model: Model name
            estimated_input_tokens: Estimated input tokens
            estimated_output_tokens: Estimated output tokens (if None, assumes 1:1 ratio)
        
        Returns:
            Dictionary with cost estimates and pricing info
        """
        if estimated_output_tokens is None:
            estimated_output_tokens = estimated_input_tokens  # Default 1:1 ratio
        
        input_cost, output_cost, total_cost, input_price, output_price = self.calculate_cost(
            provider, model, estimated_input_tokens, estimated_output_tokens
        )
        
        return {
            "provider": provider.value,
            "model": model,
            "estimated_input_tokens": estimated_input_tokens,
            "estimated_output_tokens": estimated_output_tokens,
            "estimated_input_cost": float(input_cost),
            "estimated_output_cost": float(output_cost),
            "estimated_total_cost": float(total_cost),
            "input_price_per_token": float(input_price),
            "output_price_per_token": float(output_price),
            "pricing_currency": "USD",
            "estimated_at": datetime.utcnow().isoformat()
        }
    
    def get_model_pricing_info(self, provider: APIProvider, model: str) -> Dict[str, Any]:
        """Get pricing information for a specific model"""
        pricing = APIpricing.get_pricing(provider, model)
        
        if not pricing:
            return {
                "provider": provider.value,
                "model": model,
                "pricing_available": False,
                "message": "Pricing information not available for this model"
            }
        
        return {
            "provider": provider.value,
            "model": model,
            "pricing_available": True,
            "input_price_per_1m_tokens": float(pricing["input"]),
            "output_price_per_1m_tokens": float(pricing["output"]),
            "input_price_per_token": float(pricing["input"] / Decimal("1000000")),
            "output_price_per_token": float(pricing["output"] / Decimal("1000000")),
            "currency": "USD",
            "last_updated": "2024-12-01"  # Update this when pricing is updated
        }
    
    def get_all_pricing_info(self) -> Dict[str, Any]:
        """Get pricing information for all supported models"""
        all_pricing = {}
        
        for provider in APIProvider:
            provider_pricing = {}
            
            if provider == APIProvider.OPENAI:
                pricing_dict = APIpricing.OPENAI_PRICING
            elif provider == APIProvider.ANTHROPIC:
                pricing_dict = APIpricing.ANTHROPIC_PRICING
            elif provider == APIProvider.PERPLEXITY:
                pricing_dict = APIpricing.PERPLEXITY_PRICING
            elif provider == APIProvider.GOOGLE:
                pricing_dict = APIpricing.GOOGLE_PRICING
            elif provider == APIProvider.AZURE_OPENAI:
                pricing_dict = APIpricing.OPENAI_PRICING
            else:
                continue
            
            for model, pricing in pricing_dict.items():
                provider_pricing[model] = {
                    "input_price_per_1m_tokens": float(pricing["input"]),
                    "output_price_per_1m_tokens": float(pricing["output"]),
                    "input_price_per_token": float(pricing["input"] / Decimal("1000000")),
                    "output_price_per_token": float(pricing["output"] / Decimal("1000000")),
                }
            
            all_pricing[provider.value] = provider_pricing
        
        return {
            "pricing": all_pricing,
            "currency": "USD",
            "last_updated": "2024-12-01",
            "note": "Pricing is subject to change. Please verify with provider documentation."
        }


# Global cost calculator instance
cost_calculator = CostCalculator()
