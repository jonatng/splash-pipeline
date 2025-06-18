"""
ELT Pipeline Runner for Splash Visual Trends Analytics
Orchestrates Extract, Load, Transform operations using dedicated classes
"""

import os
import subprocess
import logging
from datetime import datetime, date
from typing import Dict, Any
import sys

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.elt.extract.extractor import Extractor
from src.elt.load.loader import Loader
from src.elt.transform.transformer import Transformer

logger = logging.getLogger(__name__)


class PipelineRunner:
    """Orchestrates the ELT pipeline using Extract, Load, Transform pattern"""
    
    def __init__(self):
        self.dbt_project_dir = os.getenv('DBT_PROJECT_DIR', './dbt_project')
        self.dbt_profiles_dir = os.getenv('DBT_PROFILES_DIR', './dbt_project')
        self.extractor = Extractor()
    
    def run_dbt_command(self, command: str) -> Dict[str, Any]:
        """Run a dbt command and return the result"""
        full_command = f"dbt {command} --project-dir {self.dbt_project_dir} --profiles-dir {self.dbt_profiles_dir}"
        
        try:
            logger.info(f"Running dbt command: {full_command}")
            result = subprocess.run(
                full_command.split(),
                capture_output=True,
                text=True,
                check=True
            )
            
            return {
                'success': True,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.CalledProcessError as e:
            logger.error(f"dbt command failed: {e}")
            return {
                'success': False,
                'stdout': e.stdout,
                'stderr': e.stderr,
                'returncode': e.returncode,
                'error': str(e)
            }
    
    def extract_data(self, batch_size: int = 50) -> Dict[str, Any]:
        """Extract data from Unsplash API"""
        try:
            logger.info("🔄 Starting EXTRACT phase...")
            
            # Extract photos
            photos = self.extractor.extract_photos(batch_size=batch_size, order_by="latest")
            logger.info(f"Extracted {len(photos)} photos")
            
            # Extract trending data
            trending_data = self.extractor.extract_trending_data()
            logger.info(f"Extracted trending data with {len(trending_data.get('trending_searches', []))} search terms")
            
            return {
                'success': True,
                'photos': photos,
                'trending_data': trending_data,
                'photos_count': len(photos),
                'trending_count': len(trending_data.get('trending_searches', []))
            }
            
        except Exception as e:
            logger.error(f"❌ EXTRACT phase failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'photos': [],
                'trending_data': {},
                'photos_count': 0,
                'trending_count': 0
            }
    
    def load_data(self, photos: list, trending_data: dict) -> Dict[str, Any]:
        """Load extracted data into the data warehouse"""
        try:
            logger.info("🔄 Starting LOAD phase...")
            
            with Loader() as loader:
                # Load photos
                photo_count = loader.load_photos(photos)
                logger.info(f"Loaded {photo_count} photos")
                
                # Load trending data
                trending_count = loader.load_trending_data(trending_data)
                logger.info(f"Loaded {trending_count} trending items")
            
            return {
                'success': True,
                'photos_loaded': photo_count,
                'trending_loaded': trending_count
            }
            
        except Exception as e:
            logger.error(f"❌ LOAD phase failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'photos_loaded': 0,
                'trending_loaded': 0
            }
    
    def transform_data(self, analysis_date: date = None) -> Dict[str, Any]:
        """Run data transformations and analysis"""
        if not analysis_date:
            analysis_date = date.today()
            
        try:
            logger.info("🔄 Starting TRANSFORM phase...")
            
            transform_results = {
                'success': True,
                'python_transforms': {},
                'dbt_transforms': {},
                'errors': []
            }
            
            # Python-based transformations
            with Transformer() as transformer:
                try:
                    # Tag analysis
                    tag_count = transformer.analyze_tags(analysis_date)
                    transform_results['python_transforms']['tags_analyzed'] = tag_count
                    logger.info(f"Analyzed {tag_count} tags")
                    
                    # Photographer analysis
                    photographer_count = transformer.analyze_photographers(analysis_date)
                    transform_results['python_transforms']['photographers_analyzed'] = photographer_count
                    logger.info(f"Analyzed {photographer_count} photographers")
                    
                    # Daily trends
                    trends_generated = transformer.generate_daily_trends(analysis_date)
                    transform_results['python_transforms']['daily_trends_generated'] = trends_generated
                    logger.info(f"Generated daily trends: {trends_generated}")
                    
                except Exception as e:
                    logger.error(f"Python transformations failed: {e}")
                    transform_results['errors'].append(f"Python transforms: {str(e)}")
            
            # dbt transformations (if dbt project exists)
            if os.path.exists(self.dbt_project_dir):
                try:
                    # Install dbt dependencies
                    deps_result = self.run_dbt_command("deps")
                    transform_results['dbt_transforms']['deps'] = deps_result['success']
                    
                    if deps_result['success']:
                        # Run dbt models
                        run_result = self.run_dbt_command("run")
                        transform_results['dbt_transforms']['models'] = run_result['success']
                        
                        if not run_result['success']:
                            transform_results['errors'].append(f"dbt run failed: {run_result.get('stderr', 'Unknown error')}")
                        
                        # Run dbt tests
                        test_result = self.run_dbt_command("test")
                        transform_results['dbt_transforms']['tests'] = test_result['success']
                        
                        if not test_result['success']:
                            logger.warning("Some dbt tests failed")
                            transform_results['errors'].append(f"dbt tests failed: {test_result.get('stderr', 'Unknown error')}")
                    else:
                        transform_results['errors'].append(f"dbt deps failed: {deps_result.get('stderr', 'Unknown error')}")
                        
                except Exception as e:
                    logger.error(f"dbt transformations failed: {e}")
                    transform_results['errors'].append(f"dbt transforms: {str(e)}")
            else:
                logger.info("No dbt project found, skipping dbt transformations")
                transform_results['dbt_transforms']['skipped'] = True
            
            # Overall success
            transform_results['success'] = len(transform_results['errors']) == 0
            
            return transform_results
            
        except Exception as e:
            logger.error(f"❌ TRANSFORM phase failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'python_transforms': {},
                'dbt_transforms': {},
                'errors': [str(e)]
            }
    
    def generate_documentation(self) -> bool:
        """Generate dbt documentation"""
        try:
            if not os.path.exists(self.dbt_project_dir):
                logger.info("No dbt project found, skipping documentation generation")
                return True
                
            logger.info("📚 Generating documentation...")
            
            # Generate docs
            docs_result = self.run_dbt_command("docs generate")
            if not docs_result['success']:
                logger.error("dbt docs generate failed")
                return False
            
            logger.info("✅ Documentation generated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Documentation generation failed: {e}")
            return False
    
    def run_full_elt_pipeline(self, batch_size: int = 50, analysis_date: date = None) -> Dict[str, Any]:
        """Run the complete ELT pipeline"""
        start_time = datetime.now()
        results = {
            'start_time': start_time.isoformat(),
            'pipeline_type': 'ELT',
            'extract': {'success': False, 'photos_count': 0, 'trending_count': 0},
            'load': {'success': False, 'photos_loaded': 0, 'trending_loaded': 0},
            'transform': {'success': False, 'python_transforms': {}, 'dbt_transforms': {}},
            'documentation': False,
            'overall_success': False,
            'duration_seconds': 0,
            'errors': []
        }
        
        try:
            logger.info("🚀 Starting full ELT pipeline...")
            
            # EXTRACT Phase
            extract_result = self.extract_data(batch_size)
            results['extract'] = extract_result
            
            if extract_result['success']:
                logger.info("✅ EXTRACT phase completed")
                
                # LOAD Phase
                load_result = self.load_data(extract_result['photos'], extract_result['trending_data'])
                results['load'] = load_result
                
                if load_result['success']:
                    logger.info("✅ LOAD phase completed")
                    
                    # TRANSFORM Phase
                    transform_result = self.transform_data(analysis_date)
                    results['transform'] = transform_result
                    
                    if transform_result['success']:
                        logger.info("✅ TRANSFORM phase completed")
                    else:
                        results['errors'].extend(transform_result.get('errors', []))
                        logger.error("❌ TRANSFORM phase failed")
                else:
                    results['errors'].append(f"Load failed: {load_result.get('error', 'Unknown error')}")
                    logger.error("❌ LOAD phase failed")
            else:
                results['errors'].append(f"Extract failed: {extract_result.get('error', 'Unknown error')}")
                logger.error("❌ EXTRACT phase failed")
            
            # Generate documentation (optional)
            if self.generate_documentation():
                results['documentation'] = True
                logger.info("✅ Documentation generated")
            else:
                results['errors'].append("Documentation generation failed")
                logger.warning("⚠️ Documentation generation failed")
            
            # Overall success
            results['overall_success'] = (
                results['extract']['success'] and 
                results['load']['success'] and 
                results['transform']['success']
            )
            
            end_time = datetime.now()
            results['end_time'] = end_time.isoformat()
            results['duration_seconds'] = (end_time - start_time).total_seconds()
            
            if results['overall_success']:
                logger.info(f"🎉 ELT Pipeline completed successfully in {results['duration_seconds']:.2f} seconds")
                logger.info(f"📊 Summary: {results['extract']['photos_count']} photos extracted, "
                          f"{results['load']['photos_loaded']} photos loaded, "
                          f"{len(results['transform']['python_transforms'])} transform operations completed")
            else:
                logger.error(f"❌ ELT Pipeline failed. Errors: {results['errors']}")
            
            return results
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            results['errors'].append(str(e))
            results['duration_seconds'] = (datetime.now() - start_time).total_seconds()
            return results


def main():
    """Main function to run the ELT pipeline"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    runner = PipelineRunner()
    results = runner.run_full_elt_pipeline()
    
    if results['overall_success']:
        exit(0)
    else:
        exit(1)


if __name__ == "__main__":
    main() 