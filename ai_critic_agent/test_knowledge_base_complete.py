"""
Complete Knowledge Base Test Suite
Tests: Data Loading → Index Building → Retrieval → Quality Evaluation

Run this after placing .md files in knowledge_base/data/
"""

import os
import sys
from pathlib import Path
from typing import List, Dict
import time
import json

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from knowledge_base.ingest.build_index import FAISSIndexBuilder
from knowledge_base.retriever import CriticKnowledgeBase
from common.schemas import RiskCategory


class KnowledgeBaseTestSuite:
    """
    Comprehensive test suite for knowledge base
    """
    
    def __init__(self):
        self.data_dir = Path("knowledge_base/data")
        self.index_dir = Path("knowledge_base/vector_store")
        self.test_results = {
            "data_loading": {},
            "index_building": {},
            "retrieval": {},
            "quality": {}
        }
    
    def print_header(self, title: str):
        """Print formatted section header"""
        print("\n" + "=" * 80)
        print(f"  {title}")
        print("=" * 80 + "\n")
    
    def test_1_data_loading(self) -> bool:
        """Test 1: Check if .md files are present and readable"""
        self.print_header("TEST 1: Data Loading")
        
        print("📂 Scanning data directory...\n")
        
        # Check directory structure
        expected_categories = ["market", "competition", "execution", 
                             "monetization", "user_behavior", "timing", "general"]
        
        found_categories = {}
        total_files = 0
        
        for category in expected_categories:
            cat_dir = self.data_dir / category
            if cat_dir.exists():
                md_files = list(cat_dir.glob("*.md"))
                # Exclude TEMPLATE.md
                md_files = [f for f in md_files if f.name != "TEMPLATE.md"]
                found_categories[category] = len(md_files)
                total_files += len(md_files)
                
                status = "✅" if len(md_files) > 0 else "⚠️"
                print(f"{status} {category:15} → {len(md_files):2} files")
                
                # Show file names
                if len(md_files) > 0:
                    for f in md_files[:3]:  # Show first 3
                        print(f"     - {f.name}")
                    if len(md_files) > 3:
                        print(f"     ... and {len(md_files) - 3} more")
            else:
                found_categories[category] = 0
                print(f"❌ {category:15} → Directory not found")
        
        print(f"\n{'─' * 80}")
        print(f"📊 Total: {total_files} markdown files found")
        print(f"📁 Categories: {len([c for c in found_categories.values() if c > 0])}/{len(expected_categories)}")
        
        # Test reading a sample file
        print(f"\n🔍 Testing file readability...")
        sample_file = None
        for cat_dir in self.data_dir.iterdir():
            if cat_dir.is_dir():
                md_files = [f for f in cat_dir.glob("*.md") if f.name != "TEMPLATE.md"]
                if md_files:
                    sample_file = md_files[0]
                    break
        
        if sample_file:
            try:
                with open(sample_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                print(f"✅ Successfully read: {sample_file.name}")
                print(f"   Size: {len(content)} characters")
                print(f"   Lines: {len(content.splitlines())}")
                
                # Check for ## sections
                sections = [line for line in content.split('\n') if line.startswith('## ')]
                print(f"   Sections: {len(sections)} (## headers found)")
                
                if sections:
                    print(f"\n   Sample sections:")
                    for section in sections[:5]:
                        print(f"   - {section}")
                
            except Exception as e:
                print(f"❌ Error reading file: {e}")
                return False
        else:
            print("❌ No sample file found")
            return False
        
        # Store results
        self.test_results["data_loading"] = {
            "total_files": total_files,
            "categories": found_categories,
            "passed": total_files > 0
        }
        
        print(f"\n{'═' * 80}")
        if total_files > 0:
            print("✅ TEST 1 PASSED: Data files are present and readable")
            return True
        else:
            print("❌ TEST 1 FAILED: No data files found")
            return False
    
    def test_2_index_building(self) -> bool:
        """Test 2: Build FAISS index"""
        self.print_header("TEST 2: Index Building")
        
        print("🔨 Building FAISS index from markdown files...\n")
        
        start_time = time.time()
        
        try:
            builder = FAISSIndexBuilder()
            builder.build()
            
            build_time = time.time() - start_time
            
            # Check if files were created
            index_path = self.index_dir / "faiss_index.bin"
            metadata_path = self.index_dir / "metadata.pkl"
            stats_path = self.index_dir / "index_stats.json"
            
            if not index_path.exists():
                print("❌ FAISS index file not created")
                return False
            
            if not metadata_path.exists():
                print("❌ Metadata file not created")
                return False
            
            # Load stats
            if stats_path.exists():
                with open(stats_path, 'r') as f:
                    stats = json.load(f)
                
                print(f"\n📊 Index Statistics:")
                print(f"   Total documents: {stats['total_documents']}")
                print(f"   Total chunks: {stats['total_chunks']}")
                print(f"   Embedding dimension: {stats['embedding_dimension']}")
                print(f"\n   Chunks by category:")
                for cat, count in stats['categories'].items():
                    print(f"   - {cat:15} → {count:3} chunks")
                
                self.test_results["index_building"] = {
                    "build_time": round(build_time, 2),
                    "stats": stats,
                    "passed": True
                }
            
            print(f"\n⏱️  Build time: {build_time:.2f} seconds")
            print(f"💾 Index size: {index_path.stat().st_size / 1024:.1f} KB")
            
            print(f"\n{'═' * 80}")
            print("✅ TEST 2 PASSED: Index built successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error building index: {e}")
            import traceback
            traceback.print_exc()
            self.test_results["index_building"] = {
                "passed": False,
                "error": str(e)
            }
            return False
    
    def test_3_basic_retrieval(self) -> bool:
        """Test 3: Basic retrieval functionality"""
        self.print_header("TEST 3: Basic Retrieval")
        
        try:
            kb = CriticKnowledgeBase()
            print("✅ Knowledge base loaded successfully\n")
        except Exception as e:
            print(f"❌ Failed to load knowledge base: {e}")
            return False
        
        # Test queries
        test_queries = [
            {
                "assumption": "Users will pay for subscription services",
                "category": RiskCategory.MARKET,
                "expected_min_results": 1
            },
            {
                "assumption": "We can compete with large tech companies",
                "category": RiskCategory.COMPETITION,
                "expected_min_results": 1
            },
            {
                "assumption": "Our technology is production-ready",
                "category": RiskCategory.EXECUTION,
                "expected_min_results": 1
            }
        ]
        
        print("🔍 Testing retrieval with sample queries...\n")
        
        passed = True
        for i, test in enumerate(test_queries, 1):
            print(f"Query {i}: \"{test['assumption'][:60]}...\"")
            print(f"Category: {test['category'].value}")
            
            try:
                result = kb.query(
                    assumption=test['assumption'],
                    category=test['category'],
                    top_k=3
                )
                
                if result.total_retrieved >= test['expected_min_results']:
                    print(f"✅ Found {result.total_retrieved} results")
                    
                    if result.evidence:
                        top = result.evidence[0]
                        print(f"   Top match: {top.source}")
                        print(f"   Relevance: {top.relevance_score:.3f}")
                else:
                    print(f"⚠️  Only found {result.total_retrieved} results (expected >= {test['expected_min_results']})")
                    passed = False
                
            except Exception as e:
                print(f"❌ Query failed: {e}")
                passed = False
            
            print()
        
        self.test_results["retrieval"] = {
            "basic_queries_passed": passed
        }
        
        print(f"{'═' * 80}")
        if passed:
            print("✅ TEST 3 PASSED: Basic retrieval working")
            return True
        else:
            print("⚠️  TEST 3 WARNING: Some queries returned fewer results than expected")
            return False
    
    def test_4_quality_evaluation(self) -> bool:
        """Test 4: Evaluate retrieval quality"""
        self.print_header("TEST 4: Quality Evaluation")
        
        kb = CriticKnowledgeBase()
        
        # Comprehensive test cases
        test_cases = [
            {
                "name": "Payment Willingness",
                "assumption": "College students will pay $20/month for AI tutoring",
                "category": RiskCategory.MARKET,
                "expected_keywords": ["pay", "subscription", "price", "student", "cost"],
                "min_score": 0.5
            },
            {
                "name": "Free Alternative Competition",
                "assumption": "Users will prefer our premium service over free alternatives",
                "category": RiskCategory.COMPETITION,
                "expected_keywords": ["free", "alternative", "competition", "competitor"],
                "min_score": 0.5
            },
            {
                "name": "Technical Feasibility",
                "assumption": "AI technology is mature enough for production",
                "category": RiskCategory.EXECUTION,
                "expected_keywords": ["technology", "technical", "production", "quality"],
                "min_score": 0.4
            },
            {
                "name": "CAC/LTV Balance",
                "assumption": "Customer acquisition cost will be lower than lifetime value",
                "category": RiskCategory.MONETIZATION,
                "expected_keywords": ["acquisition", "cost", "cac", "ltv", "customer"],
                "min_score": 0.4
            },
            {
                "name": "User Behavior Change",
                "assumption": "Users will adopt this new habit",
                "category": RiskCategory.USER_BEHAVIOR,
                "expected_keywords": ["user", "behavior", "habit", "adoption"],
                "min_score": 0.4
            },
            {
                "name": "Market Timing",
                "assumption": "The market is ready for this innovation now",
                "category": RiskCategory.TIMING,
                "expected_keywords": ["timing", "market", "trend", "ready"],
                "min_score": 0.4
            }
        ]
        
        print("📊 Running comprehensive quality tests...\n")
        
        results_table = []
        total_passed = 0
        
        for test in test_cases:
            print(f"Test: {test['name']}")
            print(f"Query: \"{test['assumption'][:50]}...\"")
            
            result = kb.query(
                assumption=test['assumption'],
                category=test['category'],
                top_k=5
            )
            
            # Evaluate results
            score = 0
            found_results = result.total_retrieved > 0
            score_pass = False
            keyword_pass = False
            
            if result.evidence:
                top_score = result.evidence[0].relevance_score
                score_pass = top_score >= test['min_score']
                
                # Check keywords
                top_content = result.evidence[0].content.lower()
                found_keywords = [kw for kw in test['expected_keywords'] if kw in top_content]
                keyword_pass = len(found_keywords) > 0
                
                print(f"   Results: {result.total_retrieved}")
                print(f"   Top score: {top_score:.3f} {'✅' if score_pass else '⚠️'}")
                print(f"   Keywords: {len(found_keywords)}/{len(test['expected_keywords'])} {'✅' if keyword_pass else '⚠️'}")
                print(f"   Source: {result.evidence[0].source}")
                
                test_passed = found_results and score_pass and keyword_pass
                
            else:
                print(f"   ❌ No results found")
                test_passed = False
            
            if test_passed:
                total_passed += 1
                status = "✅ PASS"
            else:
                status = "⚠️  FAIL"
            
            results_table.append({
                "test": test['name'],
                "results": result.total_retrieved if result.evidence else 0,
                "top_score": top_score if result.evidence else 0,
                "status": status
            })
            
            print(f"   {status}\n")
        
        # Summary table
        print(f"{'─' * 80}")
        print(f"📊 Quality Evaluation Summary\n")
        print(f"{'Test Name':<30} {'Results':<10} {'Top Score':<12} {'Status'}")
        print(f"{'─' * 80}")
        
        for row in results_table:
            score_str = f"{row['top_score']:.3f}" if row['top_score'] > 0 else "N/A"
            print(f"{row['test']:<30} {row['results']:<10} {score_str:<12} {row['status']}")
        
        print(f"{'─' * 80}")
        print(f"\nPassed: {total_passed}/{len(test_cases)} tests")
        
        pass_rate = total_passed / len(test_cases)
        
        self.test_results["quality"] = {
            "pass_rate": pass_rate,
            "passed_tests": total_passed,
            "total_tests": len(test_cases),
            "details": results_table
        }
        
        print(f"\n{'═' * 80}")
        if pass_rate >= 0.7:
            print(f"✅ TEST 4 PASSED: {pass_rate:.1%} tests passed (threshold: 70%)")
            return True
        else:
            print(f"⚠️  TEST 4 WARNING: Only {pass_rate:.1%} tests passed (threshold: 70%)")
            return False
    
    def test_5_cross_category_retrieval(self) -> bool:
        """Test 5: Cross-category retrieval (no filter)"""
        self.print_header("TEST 5: Cross-Category Retrieval")
        
        kb = CriticKnowledgeBase()
        
        # Query without category filter
        query = "This startup idea will fail"
        
        print(f"🔍 Query: \"{query}\"")
        print(f"Filter: None (search all categories)\n")
        
        result = kb.query(
            assumption=query,
            category=None,  # No filter
            top_k=10
        )
        
        # Check category distribution
        category_counts = {}
        for evidence in result.evidence:
            cat = evidence.category.value
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        print(f"📊 Results across categories:\n")
        for cat, count in sorted(category_counts.items()):
            print(f"   {cat:15} → {count} results")
        
        print(f"\nTotal: {result.total_retrieved} results from {len(category_counts)} categories")
        
        passed = len(category_counts) >= 2  # Should span multiple categories
        
        self.test_results["cross_category"] = {
            "categories_found": len(category_counts),
            "passed": passed
        }
        
        print(f"\n{'═' * 80}")
        if passed:
            print("✅ TEST 5 PASSED: Cross-category retrieval working")
            return True
        else:
            print("⚠️  TEST 5 WARNING: Limited category coverage")
            return False
    
    def generate_report(self):
        """Generate final test report"""
        self.print_header("FINAL TEST REPORT")
        
        # Summary
        total_tests = 5
        passed_tests = sum([
            self.test_results.get("data_loading", {}).get("passed", False),
            self.test_results.get("index_building", {}).get("passed", False),
            self.test_results.get("retrieval", {}).get("basic_queries_passed", False),
            self.test_results.get("quality", {}).get("pass_rate", 0) >= 0.7,
            self.test_results.get("cross_category", {}).get("passed", False)
        ])
        
        print(f"📊 Overall Results: {passed_tests}/{total_tests} tests passed\n")
        
        # Detailed results
        print("Detailed Breakdown:")
        print(f"{'─' * 80}")
        
        # Test 1
        if self.test_results.get("data_loading"):
            data = self.test_results["data_loading"]
            status = "✅" if data.get("passed") else "❌"
            print(f"{status} Test 1: Data Loading")
            print(f"   Files: {data.get('total_files', 0)}")
            print(f"   Categories: {len([c for c in data.get('categories', {}).values() if c > 0])}")
        
        # Test 2
        if self.test_results.get("index_building"):
            data = self.test_results["index_building"]
            status = "✅" if data.get("passed") else "❌"
            print(f"\n{status} Test 2: Index Building")
            if "stats" in data:
                print(f"   Build time: {data.get('build_time', 0)}s")
                print(f"   Total chunks: {data['stats'].get('total_chunks', 0)}")
        
        # Test 3
        if self.test_results.get("retrieval"):
            data = self.test_results["retrieval"]
            status = "✅" if data.get("basic_queries_passed") else "⚠️"
            print(f"\n{status} Test 3: Basic Retrieval")
        
        # Test 4
        if self.test_results.get("quality"):
            data = self.test_results["quality"]
            status = "✅" if data.get("pass_rate", 0) >= 0.7 else "⚠️"
            print(f"\n{status} Test 4: Quality Evaluation")
            print(f"   Pass rate: {data.get('pass_rate', 0):.1%}")
            print(f"   Passed: {data.get('passed_tests', 0)}/{data.get('total_tests', 0)}")
        
        # Test 5
        if self.test_results.get("cross_category"):
            data = self.test_results["cross_category"]
            status = "✅" if data.get("passed") else "⚠️"
            print(f"\n{status} Test 5: Cross-Category Retrieval")
            print(f"   Categories: {data.get('categories_found', 0)}")
        
        print(f"\n{'─' * 80}")
        
        # Save report to file
        report_path = Path("knowledge_base/test_report.json")
        with open(report_path, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_path}")
        
        print(f"\n{'═' * 80}")
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED! Knowledge base is ready to use.")
        elif passed_tests >= 3:
            print("✅ CORE TESTS PASSED. System is functional with minor issues.")
        else:
            print("⚠️  TESTS FAILED. Please review issues above.")
        
        print(f"{'═' * 80}\n")
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("\n" + "🧪" * 40)
        print("KNOWLEDGE BASE COMPLETE TEST SUITE")
        print("🧪" * 40)
        
        # Run tests in sequence
        if not self.test_1_data_loading():
            print("\n❌ Cannot proceed: No data files found")
            return
        
        if not self.test_2_index_building():
            print("\n❌ Cannot proceed: Index building failed")
            return
        
        self.test_3_basic_retrieval()
        self.test_4_quality_evaluation()
        self.test_5_cross_category_retrieval()
        
        # Generate report
        self.generate_report()


def main():
    """Main entry point"""
    suite = KnowledgeBaseTestSuite()
    suite.run_all_tests()


if __name__ == "__main__":
    main()