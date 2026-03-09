"""Test suite for progress_tracker.py module.

Demonstrates:
- Goal progress calculation
- Time remaining estimation
- Comprehensive progress analysis
- Goal highlights and metrics

Run with: python backend/finance/test_progress_tracker.py
"""

from datetime import date, timedelta
from progress_tracker import (
    calculate_goal_progress,
    calculate_time_remaining,
    get_goal_progress_analysis,
    calculate_goal_highlights,
)


def test_goal_progress():
    """Test goal progress percentage calculation."""
    print("=" * 70)
    print("TEST 1: Goal Progress Calculation")
    print("=" * 70)
    
    test_cases = [
        {
            'target': 500000,
            'current': 250000,
            'expected_status': 'In Progress'
        },
        {
            'target': 100000,
            'current': 100000,
            'expected_status': 'Complete'
        },
        {
            'target': 1000000,
            'current': 50000,
            'expected_status': 'Just Started'
        },
    ]
    
    for case in test_cases:
        result = calculate_goal_progress(case['target'], case['current'])
        print(f"\nTarget: ₹{case['target']:,} | Current: ₹{case['current']:,}")
        print(f"  Progress: {result['goal_progress_percent']}%")
        print(f"  Status: {result['progress_status']}")
        print(f"  Remaining: ₹{result['remaining_amount']:,}")
        assert result['progress_status'] == case['expected_status'], "Status mismatch"
    
    print("\n✓ All progress calculations passed")


def test_time_remaining():
    """Test time remaining calculation."""
    print("\n" + "=" * 70)
    print("TEST 2: Time Remaining Calculation")
    print("=" * 70)
    
    target_date = date.today() + timedelta(days=365*3)  # 3 years from now
    
    result = calculate_time_remaining(
        target_amount=500000,
        current_amount=200000,
        monthly_contribution=8000,
        target_date=target_date,
        annual_return=0.06,
    )
    
    print(f"\nTarget Amount: ₹500,000")
    print(f"Current Amount: ₹200,000")
    print(f"Monthly Contribution: ₹8,000")
    print(f"Target Date: {target_date.strftime('%Y-%m-%d')}")
    print(f"\nResults:")
    print(f"  Months Remaining: {result['months_remaining']}")
    print(f"  Expected Completion: {result['expected_completion_date']}")
    print(f"  On Track: {result['on_track']}")
    print(f"  Feasible: {result['feasible']}")
    print(f"  Message: {result['message']}")
    
    assert result['feasible'] == True, "Should be feasible"
    print("\n✓ Time remaining calculation passed")


def test_comprehensive_analysis():
    """Test comprehensive goal analysis."""
    print("\n" + "=" * 70)
    print("TEST 3: Comprehensive Goal Progress Analysis")
    print("=" * 70)
    
    # Scenario 1: Home Purchase Goal
    home_goal = get_goal_progress_analysis(
        goal_id="goal-001",
        goal_name="Home Purchase",
        target_amount=5000000,
        current_amount=1500000,
        target_date=date(2027, 12, 31),
        monthly_contribution=50000,
        annual_return=0.07,
        goal_type="INVESTMENT"
    )
    
    print("\nGoal: Home Purchase")
    print(f"  Target: ₹{home_goal['target_amount']:,}")
    print(f"  Current: ₹{home_goal['current_amount']:,}")
    print(f"  Progress: {home_goal['progress_percent']}%")
    print(f"  Status: {home_goal['goal_progress']['progress_status']}")
    print(f"  Expected Completion: {home_goal['expected_completion_date']}")
    print(f"  On Track: {home_goal['on_track']}")
    print(f"  Monthly Required: ₹{home_goal['monthly_required']:,}")
    print(f"  Current Monthly: ₹{home_goal['current_monthly_contribution']:,}")
    print(f"  Recommendation: {home_goal['priority_recommendation']}")
    
    # Scenario 2: Education Goal (Behind)
    education_goal = get_goal_progress_analysis(
        goal_id="goal-002",
        goal_name="Child Education",
        target_amount=1500000,
        current_amount=200000,
        target_date=date(2026, 12, 31),
        monthly_contribution=5000,
        annual_return=0.06,
        goal_type="EDUCATION"
    )
    
    print("\n\nGoal: Child Education")
    print(f"  Target: ₹{education_goal['target_amount']:,}")
    print(f"  Current: ₹{education_goal['current_amount']:,}")
    print(f"  Progress: {education_goal['progress_percent']}%")
    print(f"  Status: {education_goal['goal_progress']['progress_status']}")
    print(f"  Expected Completion: {education_goal['expected_completion_date']}")
    print(f"  On Track: {education_goal['on_track']}")
    print(f"  Monthly Required: ₹{education_goal['monthly_required']:,}")
    print(f"  Current Monthly: ₹{education_goal['current_monthly_contribution']:,}")
    print(f"  Recommendation: {education_goal['priority_recommendation']}")
    
    # Scenario 3: Completed Goal
    vacation_goal = get_goal_progress_analysis(
        goal_id="goal-003",
        goal_name="Dream Vacation",
        target_amount=500000,
        current_amount=500000,
        target_date=date(2025, 6, 30),
        monthly_contribution=0,
        annual_return=0.05,
        goal_type="SAVINGS"
    )
    
    print("\n\nGoal: Dream Vacation")
    print(f"  Target: ₹{vacation_goal['target_amount']:,}")
    print(f"  Current: ₹{vacation_goal['current_amount']:,}")
    print(f"  Progress: {vacation_goal['progress_percent']}%")
    print(f"  Status: {vacation_goal['goal_progress']['progress_status']}")
    print(f"  On Track: {vacation_goal['on_track']}")
    print(f"  Recommendation: {vacation_goal['priority_recommendation']}")
    
    print("\n✓ Comprehensive analysis passed")


def test_goal_highlights():
    """Test goal highlights calculation."""
    print("\n" + "=" * 70)
    print("TEST 4: Goal Highlights & Metrics")
    print("=" * 70)
    
    # Create multiple goals
    goals = [
        get_goal_progress_analysis(
            goal_id="goal-001",
            goal_name="Home",
            target_amount=5000000,
            current_amount=2500000,
            target_date=date(2027, 12, 31),
            monthly_contribution=50000,
            annual_return=0.07,
            goal_type="INVESTMENT"
        ),
        get_goal_progress_analysis(
            goal_id="goal-002",
            goal_name="Education",
            target_amount=1500000,
            current_amount=1200000,
            target_date=date(2026, 6, 30),
            monthly_contribution=8000,
            annual_return=0.06,
            goal_type="EDUCATION"
        ),
        get_goal_progress_analysis(
            goal_id="goal-003",
            goal_name="Vacation",
            target_amount=500000,
            current_amount=100000,
            target_date=date(2025, 12, 31),
            monthly_contribution=15000,
            annual_return=0.05,
            goal_type="SAVINGS"
        ),
    ]
    
    highlights = calculate_goal_highlights(goals)
    
    print(f"\nTotal Goals: {highlights['total_goals']}")
    print(f"Completed: {highlights['goals_completed']}")
    print(f"Completion Rate: {highlights['completion_rate']}%")
    print(f"On Track: {highlights['goals_on_track']}")
    print(f"Behind Schedule: {highlights['goals_behind']}")
    print(f"Average Progress: {highlights['average_progress']}%")
    
    if highlights['highest_priority_goal']:
        print(f"\nHighest Priority Goal: {highlights['highest_priority_goal']['goal_name']}")
        print(f"  Current Progress: {highlights['highest_priority_goal']['progress_percent']}%")
    
    if highlights['closest_completion']:
        print(f"\nClosest to Completion: {highlights['closest_completion']['goal_name']}")
        print(f"  Current Progress: {highlights['closest_completion']['progress_percent']}%")
    
    assert highlights['total_goals'] == 3, "Should have 3 goals"
    print("\n✓ Goal highlights passed")


def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n" + "=" * 70)
    print("TEST 5: Edge Cases & Error Handling")
    print("=" * 70)
    
    # Test 1: Negative target (invalid)
    result = calculate_goal_progress(-100000, 50000)
    assert 'error' in result, "Should have error for negative target"
    print("\n✓ Negative target handled correctly")
    
    # Test 2: Zero monthly contribution
    result = calculate_time_remaining(
        target_amount=100000,
        current_amount=50000,
        monthly_contribution=0,
    )
    assert result['feasible'] == False, "Should be infeasible with 0 contribution"
    print("✓ Zero contribution handled correctly")
    
    # Test 3: Already achieved goal
    result = calculate_goal_progress(100000, 150000)
    assert result['goal_progress_percent'] == 100, "Should be capped at 100%"
    print("✓ Over-achievement capped correctly")
    
    # Test 4: Empty goals list
    highlights = calculate_goal_highlights([])
    assert highlights['total_goals'] == 0, "Should handle empty list"
    print("✓ Empty goals list handled correctly")
    
    print("\n✓ All edge cases passed")


if __name__ == "__main__":
    print("\n" + "🎯 GOAL PROGRESS TRACKER TEST SUITE 🎯".center(70))
    print()
    
    try:
        test_goal_progress()
        test_time_remaining()
        test_comprehensive_analysis()
        test_goal_highlights()
        test_edge_cases()
        
        print("\n" + "=" * 70)
        print("✓ ALL TESTS PASSED SUCCESSFULLY!".center(70))
        print("=" * 70)
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
