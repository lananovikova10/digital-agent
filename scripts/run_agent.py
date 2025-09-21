#!/usr/bin/env python3
"""
Script to run the weekly intelligence agent manually
"""
import os
import sys
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.weekly_intel import WeeklyIntelAgent
import structlog

logger = structlog.get_logger()


async def main():
    """Run the weekly intelligence agent"""
    # Default topics
    topics = ["AI", "machine learning", "startup funding", "fintech"]
    
    # Override with command line arguments if provided
    if len(sys.argv) > 1:
        topics = sys.argv[1:]
    
    logger.info("Starting weekly intelligence agent", topics=topics)
    
    try:
        # Initialize and run agent
        agent = WeeklyIntelAgent()
        report = await agent.run_weekly_intel(topics)
        
        # Print report
        print("\n" + "="*80)
        print("WEEKLY INTELLIGENCE REPORT")
        print("="*80)
        print(report)
        print("="*80)
        
        logger.info("Weekly intelligence agent completed successfully")
        
    except Exception as e:
        logger.error("Weekly intelligence agent failed", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())