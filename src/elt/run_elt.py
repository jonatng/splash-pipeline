#!/usr/bin/env python3
"""
CLI script to run the ELT pipeline
"""

import argparse
import logging
import sys
from datetime import date, datetime
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.elt import PipelineRunner


def setup_logging(level: str = "INFO"):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f'elt_pipeline_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        ]
    )


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description='Run the Splash Visual Trends ELT Pipeline')
    
    parser.add_argument(
        '--batch-size', 
        type=int, 
        default=50, 
        help='Number of photos to extract in each batch (default: 50)'
    )
    
    parser.add_argument(
        '--analysis-date',
        type=str,
        help='Analysis date in YYYY-MM-DD format (default: today)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--extract-only',
        action='store_true',
        help='Run only the extract phase'
    )
    
    parser.add_argument(
        '--load-only',
        action='store_true',
        help='Run only the load phase (requires extracted data)'
    )
    
    parser.add_argument(
        '--transform-only',
        action='store_true',
        help='Run only the transform phase'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # Parse analysis date
    analysis_date = None
    if args.analysis_date:
        try:
            analysis_date = datetime.strptime(args.analysis_date, '%Y-%m-%d').date()
        except ValueError:
            logger.error(f"Invalid date format: {args.analysis_date}. Use YYYY-MM-DD")
            sys.exit(1)
    
    # Initialize pipeline runner
    runner = PipelineRunner()
    
    try:
        if args.extract_only:
            logger.info("Running EXTRACT phase only...")
            result = runner.extract_data(args.batch_size)
            success = result['success']
            
        elif args.load_only:
            logger.error("Load-only mode requires pre-extracted data. Use full pipeline instead.")
            sys.exit(1)
            
        elif args.transform_only:
            logger.info("Running TRANSFORM phase only...")
            result = runner.transform_data(analysis_date)
            success = result['success']
            
        else:
            # Run full ELT pipeline
            logger.info("Running full ELT pipeline...")
            result = runner.run_full_elt_pipeline(args.batch_size, analysis_date)
            success = result['overall_success']
        
        # Print summary
        logger.info("=" * 60)
        logger.info("PIPELINE EXECUTION SUMMARY")
        logger.info("=" * 60)
        
        if success:
            logger.info("✅ Pipeline completed successfully!")
            if 'extract' in result:
                logger.info(f"📥 Extracted: {result['extract'].get('photos_count', 0)} photos")
            if 'load' in result:
                logger.info(f"💾 Loaded: {result['load'].get('photos_loaded', 0)} photos")
            if 'transform' in result:
                transforms = result['transform'].get('python_transforms', {})
                logger.info(f"🔄 Transforms: {len(transforms)} operations completed")
        else:
            logger.error("❌ Pipeline failed!")
            if 'errors' in result:
                for error in result['errors']:
                    logger.error(f"   - {error}")
        
        if 'duration_seconds' in result:
            logger.info(f"⏱️  Duration: {result['duration_seconds']:.2f} seconds")
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed with unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 