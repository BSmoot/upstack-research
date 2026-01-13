#!/usr/bin/env python3
"""
Standalone API Connection Test Script

Quick verification script to test Anthropic Claude API connection.
Can be run directly without pytest: python test_api_connection.py

Tests:
1. API key configuration
2. Basic client initialization
3. Simple message exchange
4. Model availability
5. Token tracking
6. Error handling
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from anthropic import AsyncAnthropic
import anthropic


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class APIConnectionTester:
    """Test Anthropic API connection and basic functionality."""
    
    def __init__(self):
        """Initialize tester with API key from environment."""
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        self.client = None
        self.test_results = []
        
    def log_result(self, test_name: str, passed: bool, message: str = ""):
        """Log test result."""
        status = "✓ PASS" if passed else "✗ FAIL"
        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'message': message
        })
        logger.info(f"{status}: {test_name} - {message}")
    
    def test_1_api_key_present(self) -> bool:
        """Test 1: Verify API key is configured."""
        logger.info("\n=== Test 1: API Key Configuration ===")
        
        if not self.api_key:
            self.log_result(
                "API Key Present",
                False,
                "ANTHROPIC_API_KEY not found in environment"
            )
            return False
        
        if not self.api_key.startswith('sk-ant-'):
            self.log_result(
                "API Key Format",
                False,
                "API key doesn't match expected format (should start with 'sk-ant-')"
            )
            return False
        
        # Mask key for logging
        masked_key = self.api_key[:10] + "..." + self.api_key[-4:]
        self.log_result(
            "API Key Present",
            True,
            f"Key found: {masked_key}"
        )
        return True
    
    def test_2_client_initialization(self) -> bool:
        """Test 2: Initialize Anthropic client."""
        logger.info("\n=== Test 2: Client Initialization ===")
        
        try:
            self.client = AsyncAnthropic(api_key=self.api_key)
            self.log_result(
                "Client Initialization",
                True,
                "AsyncAnthropic client created successfully"
            )
            return True
        except Exception as e:
            self.log_result(
                "Client Initialization",
                False,
                f"Failed to create client: {str(e)}"
            )
            return False
    
    async def test_3_simple_message(self) -> bool:
        """Test 3: Send a simple message and verify response."""
        logger.info("\n=== Test 3: Simple Message Exchange ===")
        
        if not self.client:
            self.log_result(
                "Simple Message",
                False,
                "Client not initialized"
            )
            return False
        
        try:
            logger.info("Sending test message to Claude...")
            
            response = await self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=100,
                messages=[{
                    "role": "user",
                    "content": "Reply with exactly: 'API connection test successful'"
                }]
            )
            
            # Extract text from response
            response_text = ""
            for block in response.content:
                if hasattr(block, 'type') and block.type == "text":
                    response_text += block.text
            
            # Verify response
            if response_text and len(response_text) > 0:
                self.log_result(
                    "Simple Message",
                    True,
                    f"Received response ({len(response_text)} chars): {response_text[:100]}"
                )
                
                # Log token usage
                if hasattr(response, 'usage'):
                    logger.info(f"  Input tokens: {response.usage.input_tokens}")
                    logger.info(f"  Output tokens: {response.usage.output_tokens}")
                
                return True
            else:
                self.log_result(
                    "Simple Message",
                    False,
                    "Empty response received"
                )
                return False
                
        except anthropic.AuthenticationError as e:
            self.log_result(
                "Simple Message",
                False,
                f"Authentication failed: {str(e)}"
            )
            return False
        except anthropic.RateLimitError as e:
            self.log_result(
                "Simple Message",
                False,
                f"Rate limit exceeded: {str(e)}"
            )
            return False
        except Exception as e:
            self.log_result(
                "Simple Message",
                False,
                f"Unexpected error: {str(e)}"
            )
            return False
    
    async def test_4_model_availability(self) -> bool:
        """Test 4: Verify specific model is available."""
        logger.info("\n=== Test 4: Model Availability ===")
        
        if not self.client:
            self.log_result(
                "Model Availability",
                False,
                "Client not initialized"
            )
            return False
        
        model_to_test = "claude-sonnet-4-20250514"
        
        try:
            logger.info(f"Testing model: {model_to_test}")
            
            response = await self.client.messages.create(
                model=model_to_test,
                max_tokens=50,
                messages=[{
                    "role": "user",
                    "content": "Respond with 'OK'"
                }]
            )
            
            self.log_result(
                "Model Availability",
                True,
                f"Model {model_to_test} is accessible"
            )
            return True
            
        except anthropic.NotFoundError as e:
            self.log_result(
                "Model Availability",
                False,
                f"Model {model_to_test} not found: {str(e)}"
            )
            return False
        except Exception as e:
            self.log_result(
                "Model Availability",
                False,
                f"Error testing model: {str(e)}"
            )
            return False
    
    async def test_5_token_tracking(self) -> bool:
        """Test 5: Verify token usage tracking."""
        logger.info("\n=== Test 5: Token Usage Tracking ===")
        
        if not self.client:
            self.log_result(
                "Token Tracking",
                False,
                "Client not initialized"
            )
            return False
        
        try:
            response = await self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=200,
                messages=[{
                    "role": "user",
                    "content": "Write a haiku about API testing."
                }]
            )
            
            if hasattr(response, 'usage'):
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens
                total_tokens = input_tokens + output_tokens
                
                # Estimate cost (Claude Sonnet 4 pricing)
                input_cost = (input_tokens / 1_000_000) * 3.0
                output_cost = (output_tokens / 1_000_000) * 15.0
                total_cost = input_cost + output_cost
                
                self.log_result(
                    "Token Tracking",
                    True,
                    f"Tracked {total_tokens} tokens (${total_cost:.6f})"
                )
                logger.info(f"  Input: {input_tokens} tokens (${input_cost:.6f})")
                logger.info(f"  Output: {output_tokens} tokens (${output_cost:.6f})")
                return True
            else:
                self.log_result(
                    "Token Tracking",
                    False,
                    "Usage information not available in response"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Token Tracking",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    async def test_6_error_handling(self) -> bool:
        """Test 6: Verify error handling for invalid requests."""
        logger.info("\n=== Test 6: Error Handling ===")
        
        if not self.client:
            self.log_result(
                "Error Handling",
                False,
                "Client not initialized"
            )
            return False
        
        # Test invalid model
        try:
            await self.client.messages.create(
                model="invalid-model-name",
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )
            self.log_result(
                "Error Handling",
                False,
                "Expected NotFoundError but request succeeded"
            )
            return False
        except anthropic.NotFoundError:
            self.log_result(
                "Error Handling",
                True,
                "Correctly caught NotFoundError for invalid model"
            )
            return True
        except Exception as e:
            self.log_result(
                "Error Handling",
                False,
                f"Unexpected error type: {type(e).__name__}"
            )
            return False
    
    async def run_all_tests(self):
        """Run all tests in sequence."""
        logger.info("=" * 70)
        logger.info("Anthropic API Connection Test Suite")
        logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 70)
        
        # Test 1: API Key
        if not self.test_1_api_key_present():
            logger.error("\n❌ Cannot proceed without valid API key")
            return False
        
        # Test 2: Client Initialization
        if not self.test_2_client_initialization():
            logger.error("\n❌ Cannot proceed without client initialization")
            return False
        
        # Test 3: Simple Message
        await self.test_3_simple_message()
        
        # Test 4: Model Availability
        await self.test_4_model_availability()
        
        # Test 5: Token Tracking
        await self.test_5_token_tracking()
        
        # Test 6: Error Handling
        await self.test_6_error_handling()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test results summary."""
        logger.info("\n" + "=" * 70)
        logger.info("TEST SUMMARY")
        logger.info("=" * 70)
        
        passed = sum(1 for r in self.test_results if r['passed'])
        total = len(self.test_results)
        
        for result in self.test_results:
            status = "✓" if result['passed'] else "✗"
            logger.info(f"{status} {result['test']}")
        
        logger.info("=" * 70)
        logger.info(f"Results: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("✓ ALL TESTS PASSED - API connection is working correctly")
        else:
            logger.warning("✗ SOME TESTS FAILED - Check errors above")
        
        logger.info("=" * 70)


async def main():
    """Main entry point."""
    tester = APIConnectionTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
