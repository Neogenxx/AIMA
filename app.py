"""
AIMA - Autonomous Inventory Management Agent
Main Application Entry Point
"""

import sys
import argparse
from engine.core import AIMAEngine, AIMACommandProcessor
from ui.dashboard import run_interactive_dashboard
from tests.test_aima import run_tests

def main():
    """Main application entry point"""
    
    parser = argparse.ArgumentParser(
        description="AIMA - Autonomous Inventory Management Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python app.py demo              # Setup demo environment and run simulation
  python app.py dashboard         # Launch interactive dashboard
  python app.py monitor           # Run continuous monitoring
  python app.py analyze           # Analyze all products
  python app.py test              # Run test suite
  python app.py interactive       # Interactive command mode
        """
    )
    
    parser.add_argument(
        'command',
        choices=['demo', 'dashboard', 'monitor', 'analyze', 'test', 'interactive', 'simulate'],
        help='Command to execute'
    )
    
    parser.add_argument(
        '--db',
        default='data/aima.db',
        help='Database file path (default: data/aima.db)'
    )
    
    parser.add_argument(
        '--auto-execute',
        action='store_true',
        help='Enable automatic execution of restock orders'
    )
    
    parser.add_argument(
        '--products',
        type=int,
        default=20,
        help='Number of products for demo (default: 20)'
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Number of days to simulate (default: 30)'
    )
    
    args = parser.parse_args()
    
    # Execute command
    if args.command == 'test':
        # Run test suite
        print("\n🧪 Running AIMA Test Suite...\n")
        success = run_tests()
        sys.exit(0 if success else 1)
    
    elif args.command == 'dashboard':
        # Launch dashboard
        print(f"\n📊 Launching AIMA Dashboard...")
        print(f"Database: {args.db}\n")
        run_interactive_dashboard(args.db)
    
    elif args.command == 'demo':
        # Setup demo environment
        print("\n🚀 Setting up AIMA Demo Environment...\n")
        engine = AIMAEngine(db_path=args.db, auto_execute=args.auto_execute)
        
        result = engine.setup_demo_environment(
            num_products=args.products,
            simulate_days=args.days
        )
        
        print("\n" + "=" * 60)
        print("Demo Setup Complete!")
        print("=" * 60)
        print(f"Products created: {result['products_created']}")
        print(f"Days simulated: {result['days_simulated']}")
        print(f"Total sales: {result['simulation_results']['total_sales']}")
        print(f"Initial decisions: {result['initial_decisions']}")
        print("=" * 60)
        
        # Show performance report
        print("\n" + engine.generate_performance_report())
        
        print("\nNext steps:")
        print("  python app.py dashboard      # View dashboard")
        print("  python app.py interactive    # Interactive mode")
    
    elif args.command == 'monitor':
        # Run continuous monitoring
        print("\n🔄 Starting Continuous Monitoring Mode...\n")
        engine = AIMAEngine(db_path=args.db, auto_execute=args.auto_execute)
        engine.run_continuous_monitoring(interval_seconds=60)
    
    elif args.command == 'analyze':
        # Analyze all products
        print("\n📊 Analyzing All Products...\n")
        engine = AIMAEngine(db_path=args.db, auto_execute=args.auto_execute)
        decisions = engine.agent.analyze_all_products()
        
        print(f"\n✓ Analysis complete: {len(decisions)} products analyzed")
        print("\n" + engine.generate_performance_report())
    
    elif args.command == 'simulate':
        # Simulate sales day
        print("\n🎲 Simulating Sales Activity...\n")
        engine = AIMAEngine(db_path=args.db, auto_execute=args.auto_execute)
        result = engine.simulate_sales_day()
        
        print("\n" + engine.generate_performance_report())
    
    elif args.command == 'interactive':
        # Interactive command mode
        print("\n💬 AIMA Interactive Mode")
        print("Type 'help' for available commands, 'exit' to quit\n")
        
        engine = AIMAEngine(db_path=args.db, auto_execute=args.auto_execute)
        processor = AIMACommandProcessor(engine)
        
        try:
            while True:
                command = input("\nAIMA> ").strip()
                
                if command.lower() in ['exit', 'quit', 'q']:
                    break
                
                if command:
                    response = processor.process_command(command)
                    if response:
                        print(response)
        
        except KeyboardInterrupt:
            print("\n")
        
        engine.shutdown()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 AIMA terminated by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
